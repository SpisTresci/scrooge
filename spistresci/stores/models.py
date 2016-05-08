from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _

from spistresci.products.models import Product


class Store(models.Model):
    name = models.CharField(_('Store name'), max_length=32)
    url = models.URLField(_('Store url address'))
    last_update_revision = models.IntegerField(null=True)

    def __str__(self):
        return '{} ({}) - {}'.format(self.name, self.last_update_revision, self.url)

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
            self.save()

            print('{} products added'.format(len(added)))
            print('{} products deleted'.format(len(deleted)))
            print('{} products modified'.format(len(modified)))

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
            print('New product: {}'.format(str(product)))

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
            def __init__(self, product_id):
                self.product_id = product_id
                self.changes = []

            def log(self, key, db_value, new_value, db_value_type=None, new_value_type=None):
                db_value_type = db_value_type or type(db_value)
                new_value_type = new_value_type or type(new_value)
                self.changes.append(
                    '[{}] {} ({}) => {} ({})'.format(key, db_value, db_value_type, new_value, new_value_type)
                )

            def __str__(self):
                if not self.changes:
                    return '{}\n\tWARN - no changes, but product was on "modified" list'.format(self.product_id)
                else:
                    return '{}\n\t'.format(self.product_id) + '\n\t'.join(self.changes)

        core_fields = []

        for field in Product._meta.fields:
            if field.get_internal_type() != 'ForeignKey' and field.name not in ['data', 'id']:
                core_fields.append(field.name)

        sorted_modified = sorted(products, key=lambda d: int(d['external_id']))

        sorted_products_queryset = Product.objects.filter(
            external_id__in=[product_dict['external_id'] for product_dict in products]
        ).order_by('external_id')

        for product_db, product_dict in zip(sorted_products_queryset, sorted_modified):
            logger = ChangeLogger(product_id=product_db.external_id)
            for key in set(list(product_db.to_dict().keys()) + list(product_dict.keys())):

                if key in core_fields:
                    if key not in product_dict:
                        new_val = Product._meta.get_field_by_name(key)[0].default
                        logger.log(key, '<no_value>', new_val, db_value_type='<no_type>')
                        setattr(product_db, key, new_val)
                    elif getattr(product_db, key) != type(getattr(product_db, key))(product_dict[key]):
                        logger.log(key, getattr(product_db, key), product_dict[key])
                        setattr(product_db, key, product_dict[key])
                else:
                    if key in product_db.data and key in product_dict and product_db.data[key] != product_dict[key]:
                        logger.log(key, product_db.data[key], product_dict[key])
                        product_db.data[key] = product_dict[key]
                    elif key in product_db.data and key not in product_dict:
                        logger.log(key, product_db.data[key], '<no_value>', new_value_type='<no_type>')
                        del product_db.data[key]
                    elif key not in product_db.data and key in product_dict:
                        logger.log(key, '<no_value>', product_dict[key], db_value_type='<no_type>')
                        product_db.data[key] = product_dict[key]  # TODO: add initializing by type .price = Decimal(price)

            print(logger)
            product_db.save()
