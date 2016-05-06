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

            self.last_update_revision = revision_number
            self.save()

            print('{} products added'.format(len(added)))

