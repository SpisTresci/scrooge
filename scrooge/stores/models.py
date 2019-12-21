import logging
from datetime import datetime

from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _

from scrooge.offers.models import Offer
from scrooge.datasource.models import DataSourceModel


logger = logging.getLogger(__name__)


class Store(models.Model):
    enabled = models.BooleanField(
        default=True,
        help_text=_('If checked, Store will be updated according to schedule of defined jobs')
    )
    name = models.CharField(max_length=32)
    url = models.URLField(help_text=_('Url to main site of store'))
    last_update_revision = models.IntegerField(null=True, default=None)
    last_update_data_source_version_hash = models.CharField(max_length=32, editable=False, default='')
    last_successful_update = models.DateTimeField(_('Time of last successful update'), default=None, null=True)
    last_changing_offers_update = models.DateTimeField(
        _('Time of last successful update which changed any offer'),
        default=None,
        null=True
    )
    data_source = models.ForeignKey(DataSourceModel, on_delete=models.PROTECT)

    def data_source_instance(self):
        return self.data_source.child.impl_class(self)

    def __str__(self):
        return '{} - {}'.format(self.name, self.url)

    def update(self):
        self.data_source_instance().update()

    def fetch(self):
        self.data_source_instance().fetch()

    def update_offers(self, revision_number, added=None, deleted=None, modified=None):
        added = added or []
        deleted = deleted or []
        modified = modified or []

        with transaction.atomic():

            self.__add_offers(added)
            self.__delete_offers(deleted)
            self.__modify_offers(modified)

            # print('After modify {}'.format(len(connection.queries)))

            self.last_update_revision = revision_number
            self.last_successful_update = datetime.now()
            self.last_update_data_source_version_hash = self.data_source.version_hash

            if added or deleted or modified:
                self.last_changing_offers_update = datetime.now()

            self.save()

            logger.info('[Store:{}] {} offers added'.format(self.name, len(added)))
            logger.info('[Store:{}] {} offers deleted'.format(self.name, len(deleted)))
            logger.info('[Store:{}] {} offers modified'.format(self.name, len(modified)))

    def __add_offers(self, offers):
        if not offers:
            return

        field_names = [f.name for f in Offer._meta.get_fields()]
        for offer_dict in offers:
            data = {}

            for offer_key in list(offer_dict.keys()):  # list is needed because of offer_dict.pop
                if offer_key not in field_names:
                    data[offer_key] = offer_dict.pop(offer_key)
                elif offer_dict[offer_key] is None:
                    offer_dict.pop(offer_key)


            offer = Offer.objects.create(store=self, data=data, **offer_dict)  # TODO: change to bulk_create?
            logger.info('[Store:{}] New offer: {}'.format(self.name, str(offer)))

    def __delete_offers(self, offers):
        if not offers:
            return

        # TODO: "deactivate" offer instead deleting it
        id_of_offers_to_delete = [offer_dict['external_id'] for offer_dict in offers]
        Offer.objects.filter(external_id__in=id_of_offers_to_delete).delete()

    def __modify_offers(self, offers):
        # TODO: change to buld_update? - https://github.com/aykut/django-bulk-update

        # print('Before modify {}'.format(len(connection.queries)))
        if not offers:
            return

        class ChangeLogger:
            def __init__(self, store_name, offer_id, logger):
                self.store_name = store_name
                self.offer_id = offer_id
                self.logger = logger
                self.changes__info = []
                self.changes__warn = []

            def add(self, key, db_value, new_value, db_value_type=None, new_value_type=None, mode='info'):
                db_value_type = db_value_type or type(db_value)
                new_value_type = new_value_type or type(new_value)
                changes = self.changes__info if mode == 'info' else self.changes__warn
                changes.append(
                    '[{}] {} ({}) => {} ({})'.format(key, db_value, db_value_type, new_value, new_value_type)
                )

            def log(self):

                if not self.changes__info and not self.changes__warn:
                    logger.warning(
                        '[Store:{}][Offer:{}]\n\t'
                        'No changes, but offer was on "modified" list'.format(self.store_name, self.offer_id)
                    )

                if self.changes__info:
                    logger.info(
                        '[Store:{}][Offer:{}]\n\t'
                        '{}'.format(self.store_name, self.offer_id, '\n\t'.join(self.changes__info))
                    )

                if self.changes__warn:
                    logger.warn(
                        '[Store:{}][Offer:{}]\n\t'
                        '{}'.format(self.store_name, self.offer_id, '\n\t'.join(self.changes__warn))
                    )

        core_fields = []

        for field in Offer._meta.fields:
            if field.get_internal_type() != 'ForeignKey' and field.name not in ['data', 'id']:
                core_fields.append(field.name)

        sorted_modified = sorted(offers, key=lambda d: int(d['external_id']))

        sorted_offers_queryset = Offer.objects.filter(
            external_id__in=[offer_dict['external_id'] for offer_dict in offers]
        ).order_by('external_id')

        for offer_db, offer_dict in zip(sorted_offers_queryset, sorted_modified):
            changes = ChangeLogger(self.name, offer_db.external_id, logger)
            for key in set(list(offer_db.to_dict().keys()) + list(offer_dict.keys())):

                if key in core_fields:
                    default_value = Offer._meta.get_field_by_name(key)[0].default
                    if key not in offer_dict:
                        changes.add(key, '<no_value>', default_value, db_value_type='<no_type>')
                        setattr(offer_db, key, default_value)
                    elif offer_dict[key] is None:
                        changes.add(key, getattr(offer_db, key), default_value, mode='warn')
                        setattr(offer_db, key, default_value)
                    elif getattr(offer_db, key) != type(getattr(offer_db, key))(offer_dict[key]):
                        changes.add(key, getattr(offer_db, key), offer_dict[key])
                        setattr(offer_db, key, offer_dict[key])
                else:
                    if key in offer_db.data and key in offer_dict and offer_db.data[key] != offer_dict[key]:
                        changes.add(key, offer_db.data[key], offer_dict[key])
                        offer_db.data[key] = offer_dict[key]
                    elif key in offer_db.data and key not in offer_dict:
                        changes.add(key, offer_db.data[key], '<no_value>', new_value_type='<no_type>')
                        del offer_db.data[key]
                    elif key not in offer_db.data and key in offer_dict:
                        changes.add(key, '<no_value>', offer_dict[key], db_value_type='<no_type>')
                        offer_db.data[key] = offer_dict[key]  # TODO: add initializing by type .price = Decimal(price)

            changes.log()
            offer_db.save()
