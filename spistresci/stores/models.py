from django.db import models, transaction
from django.utils.translation import ugettext_lazy as _

# Create your models here.
from spistresci.products.models import Product


class Store(models.Model):
    name = models.CharField(_('Store name'), max_length=32)
    url = models.URLField(_('Store url address'))
    last_update_revision = models.IntegerField(null=True)

    def update_products(self, revision_number, added=None, deleted=None, modified=None):
        added = added or []
        deleted = deleted or []
        modified = modified or []

        with transaction.atomic():

            field_names = Product._meta.get_all_field_names()
            for product_dict in added:
                data = {}

                for product_key in list(product_dict.keys()):  # list is needed because of product_dict.pop
                    if product_key not in field_names:
                        data[product_key] = product_dict.pop(product_key)

                product = Product.objects.create(store=self, data=data, **product_dict)  # TODO: change to bulk_create?
                print('New product: {}'.format(str(product)))

            # TODO: "deactivate" product instead deleting it
            id_of_products_to_delete = [product_dict['external_id'] for product_dict in deleted]
            Product.objects.filter(external_id__in=id_of_products_to_delete).delete()

            # print('Before modify {}'.format(len(connection.queries)))

            # TODO: change to buld_update? - https://github.com/aykut/django-bulk-update

            core_fields = []

            for field in Product._meta.fields:
                if field.get_internal_type() != 'ForeignKey' and field.name not in ['data', 'id']:
                    core_fields.append(field.name)

            sorted_modified = sorted(modified, key=lambda d: int(d['external_id']))

            sorted_products_queryset = Product.objects.filter(
                external_id__in=[product_dict['external_id'] for product_dict in modified]
            ).order_by('external_id')

            for product, product_dict in zip(sorted_products_queryset, sorted_modified):
                changes = []
                for key in set(list(product.to_dict().keys()) + list(product_dict.keys())):

                    if key in core_fields:
                        if key not in product_dict:
                            new_val = Product._meta.get_field_by_name(key)[0].default
                            setattr(product, key, new_val)
                            changes.append(
                                '[{}] {}({}) => {}({})'.format(key, '<no_value>', 'NE', new_val, str(type(new_val)))
                            )
                        elif getattr(product, key) != type(getattr(product, key))(product_dict[key]):  # TODO: add compare by types
                            changes.append(
                                '[{}] {}({}) => {}({})'.format(
                                    key,
                                    getattr(product, key),
                                    str(type(getattr(product, key))),
                                    product_dict[key],
                                    str(type(product_dict[key]))
                                )
                            )
                            setattr(product, key, product_dict[key])
                        # else:
                        #     pass
                        #     print('{} - case, when field is not updated, because it has still the same value\n'
                        #           '{} == {}'.format(key, getattr(product, key), product_dict[key]))

                    else:
                        if key in product.data and key in product_dict and product.data[key] != product_dict[key]:
                            changes.append(
                                '[{}] {}({}) => {}({})'.format(
                                    key,
                                    product.data[key],
                                    str(type(product.data[key])),
                                    product_dict[key],
                                    str(type(product_dict[key]))
                                )
                            )

                            product.data[key] = product_dict[key]
                        elif key in product.data and key not in product_dict:
                            changes.append(
                                '[{}] {}({}) => {}({})'.format(
                                    key,
                                    product.data[key],
                                    str(type(product.data[key])),
                                    '<no_value>',
                                    'NE'
                                )
                            )

                            del product.data[key]
                        elif key not in product.data and key in product_dict:
                            changes.append(
                                '[{}] {}({}) => {}({})'.format(
                                    key,
                                    '<no_value>',
                                    'NE',
                                    product_dict[key],
                                    str(type(product_dict[key]))
                                )
                            )
                            product.data[key] = product_dict[key]  # TODO: add initializing by type .price = Decimal(price)
                        # else:
                        #     print('{} - case, when field is not updated, because it has still the same value\n'
                        #           '{} == {}'.format(key, product.data[key], product_dict[key]))

                if len(changes) == 0:
                    print('ERROR - no changes, but product was on "modified" list')
                else:
                    print('{}'.format(product.external_id))
                    print('\t' + '\n\t'.join(changes))

                product.save()

            # print('After modify {}'.format(len(connection.queries)))

            self.last_update_revision = revision_number
            self.save()

            print('{} products added'.format(len(added)))
            print('{} products deleted'.format(len(deleted)))
            print('{} products modified'.format(len(modified)))

