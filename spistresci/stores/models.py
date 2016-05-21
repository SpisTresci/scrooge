import logging
from datetime import datetime

from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _

from spistresci.products.models import Product
from spistresci.datasource.generic import DataSource

# noinspection PyUnresolvedReferences
# statement used for autodiscover, TODO: replace with http://stackoverflow.com/questions/32335967/
from spistresci.datasource.specific import *

logger = logging.getLogger(__name__)


def get_data_source_classes():  # TODO: Move to utils
    subclasses = sorted(DataSource.get_all_subclasses().keys())
    assert 'XmlDataSource' in subclasses  # XmlDataSource is default, so we want to make sure it is available
    return zip(subclasses, subclasses)


class Store(models.Model):
    enabled = models.BooleanField(
        default=True,
        help_text=_('If checked, Store will be updated according to schedule of defined jobs')
    )
    name = models.CharField(_('Store name'), max_length=32)
    url = models.URLField(_('Store url address'))
    last_update_revision = models.IntegerField(null=True)

    SINGLE_XML = 1

    DATA_SOURCE_TYPE_CHOICES = (
        (SINGLE_XML, _('Single XML')),
    )

    data_source_type = models.IntegerField(_('Data source type'), choices=DATA_SOURCE_TYPE_CHOICES, default=SINGLE_XML)
    data_source_url = models.URLField(_('URL address of data source'), default=None, blank=False)
    data_source_class = models.CharField(max_length=32, choices=get_data_source_classes(), default='XmlDataSource')

    last_successful_update = models.DateTimeField(_('Time of last successful update'), default=None, null=True)
    last_changing_products_update = models.DateTimeField(
        _('Time of last successful update which changed any product'),
        default=None,
        null=True
    )

    def data_source(self):
        data_source_class = DataSource.get_all_subclasses()[self.data_source_class]
        return data_source_class(self)

    def __str__(self):
        return '{} - {}'.format(self.name, self.url)

    def update(self):
        self.data_source().update()

    def fetch(self):
        self.data_source().fetch()

    def update_products(self, revision_number, added=None, deleted=None, modified=None):
        added = added or []
        deleted = deleted or []
        modified = modified or []

        with transaction.atomic():

            self.__add_products(added)
            self.__delete_products(deleted)
            self.__modify_products(modified)

            # print('After modify {}'.format(len(connection.queries)))

            self.last_update_revision = revision_number
            self.last_successful_update = datetime.now()

            if added or deleted or modified:
                self.last_changing_products_update = datetime.now()

            self.save()

            logger.info('[Store:{}] {} products added'.format(self.name, len(added)))
            logger.info('[Store:{}] {} products deleted'.format(self.name, len(deleted)))
            logger.info('[Store:{}] {} products modified'.format(self.name, len(modified)))

    def __add_products(self, products):
        if not products:
            return

        field_names = Product._meta.get_all_field_names()
        for product_dict in products:
            data = {}

            for product_key in list(product_dict.keys()):  # list is needed because of product_dict.pop
                if product_key not in field_names:
                    data[product_key] = product_dict.pop(product_key)

            product = Product.objects.create(store=self, data=data, **product_dict)  # TODO: change to bulk_create?
            logger.info('[Store:{}] New product: {}'.format(self.name, str(product)))

    def __delete_products(self, products):
        if not products:
            return

        # TODO: "deactivate" product instead deleting it
        id_of_products_to_delete = [product_dict['external_id'] for product_dict in products]
        Product.objects.filter(external_id__in=id_of_products_to_delete).delete()

    def __modify_products(self, products):
        # TODO: change to buld_update? - https://github.com/aykut/django-bulk-update

        # print('Before modify {}'.format(len(connection.queries)))
        if not products:
            return

        class ChangeLogger:
            def __init__(self, store_name, product_id, logger):
                self.store_name = store_name
                self.product_id = product_id
                self.logger = logger
                self.changes = []

            def add(self, key, db_value, new_value, db_value_type=None, new_value_type=None):
                db_value_type = db_value_type or type(db_value)
                new_value_type = new_value_type or type(new_value)
                self.changes.append(
                    '[{}] {} ({}) => {} ({})'.format(key, db_value, db_value_type, new_value, new_value_type)
                )

            def log(self):

                if not self.changes:
                    logger.warning(
                        '[Store:{}][Product:{}]\n\t'
                        'No changes, but product was on "modified" list'.format(self.store_name, self.product_id)
                    )
                else:
                    logger.info(
                        '[Store:{}][Product:{}]\n\t'
                        '{}'.format(self.store_name, self.product_id, '\n\t'.join(self.changes))
                    )

        core_fields = []

        for field in Product._meta.fields:
            if field.get_internal_type() != 'ForeignKey' and field.name not in ['data', 'id']:
                core_fields.append(field.name)

        sorted_modified = sorted(products, key=lambda d: int(d['external_id']))

        sorted_products_queryset = Product.objects.filter(
            external_id__in=[product_dict['external_id'] for product_dict in products]
        ).order_by('external_id')

        for product_db, product_dict in zip(sorted_products_queryset, sorted_modified):
            changes = ChangeLogger(self.name, product_db.external_id, logger)
            for key in set(list(product_db.to_dict().keys()) + list(product_dict.keys())):

                if key in core_fields:
                    if key not in product_dict:
                        new_val = Product._meta.get_field_by_name(key)[0].default
                        changes.add(key, '<no_value>', new_val, db_value_type='<no_type>')
                        setattr(product_db, key, new_val)
                    elif getattr(product_db, key) != type(getattr(product_db, key))(product_dict[key]):
                        changes.add(key, getattr(product_db, key), product_dict[key])
                        setattr(product_db, key, product_dict[key])
                else:
                    if key in product_db.data and key in product_dict and product_db.data[key] != product_dict[key]:
                        changes.add(key, product_db.data[key], product_dict[key])
                        product_db.data[key] = product_dict[key]
                    elif key in product_db.data and key not in product_dict:
                        changes.add(key, product_db.data[key], '<no_value>', new_value_type='<no_type>')
                        del product_db.data[key]
                    elif key not in product_db.data and key in product_dict:
                        changes.add(key, '<no_value>', product_dict[key], db_value_type='<no_type>')
                        product_db.data[key] = product_dict[key]  # TODO: add initializing by type .price = Decimal(price)

            changes.log()
            product_db.save()
