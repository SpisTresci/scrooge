from decimal import Decimal
from django.db.utils import IntegrityError
from test_plus.test import TestCase

from spistresci.products.models import Product
from spistresci.stores.models import Store


class TestStore(TestCase):

    def setUp(self):
        self.store = Store.objects.create(name='Foo', url='http://foo.com/')

    def test_update_products__update_revision_number(self):
        self.assertEqual(self.store.last_update_revision, None)
        self.store.update_products(revision_number=0)
        self.assertEqual(self.store.last_update_revision, 0)

    def test_update_products__revision_number_is_not_updated_if_update_aborted(self):
        products_to_add = [{'external_id': 1, 'title': 'some bar', 'url': 'http://bar.com/1'}]

        self.assertEqual(self.store.last_update_revision, None)
        self.store.update_products(revision_number=0, added=products_to_add)
        self.assertEqual(self.store.last_update_revision, 0)

        with self.assertRaises(IntegrityError):  # product with the same external_id cannot be added twice
            self.store.update_products(revision_number=1, added=products_to_add)

        self.assertEqual(self.store.last_update_revision, 0)

    def test_update_products__added(self):
        product_1 = {
            'external_id': 1,
            'title': 'some bar',
            'url': 'http://bar.com/1'
        }

        self.store.update_products(revision_number=0, added=[product_1])
        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(Product.objects.filter(store=self.store, **product_1, price=Decimal(0)).exists())

    def test_update_products__additional_data_stored_in_data_json_field(self):
        core_data_1 = {
            'external_id': 1,
            'title': 'some bar',
            'url': 'http://bar.com/1',
            'price': '3.14',
        }
        additional_data_1 = {
            'cover_size': 42,
            'author': 'Darth Vader',
            'midichlorians': 27700
        }

        product_1 = {}
        product_1.update(core_data_1)
        product_1.update(additional_data_1)
        self.store.update_products(revision_number=0, added=[product_1])
        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(Product.objects.filter(store=self.store, **core_data_1, data=additional_data_1).exists())

    def test_update_products__deletes_products(self):
        products = [
            {'external_id': 1, 'title': 'some bar 1', 'url': 'http://bar.com/1'},
            {'external_id': 2, 'title': 'some bar 2', 'url': 'http://bar.com/2'},
            {'external_id': 3, 'title': 'some bar 3', 'url': 'http://bar.com/3'},
        ]
        Product.objects.bulk_create([Product(store=self.store, **product) for product in products])

        self.store.update_products(revision_number=0, deleted=products[0:2])
        self.assertEqual(Product.objects.count(), 1)
        self.assertTrue(Product.objects.filter(store=self.store, **products[2]).exists())
