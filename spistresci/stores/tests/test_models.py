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

    def test_update_products__modify_core_fields_of_products(self):
        products = [
            {'external_id': 1, 'title': 'some bar 1', 'url': 'http://bar.com/1', 'price': '1.99'},
            {'external_id': 2, 'title': 'some bar 2', 'url': 'http://bar.com/2', 'price': '9.00'},
            {'external_id': 3, 'title': 'some bar 3', 'url': 'http://bar.com/3', 'price': '5.00'},
            {'external_id': 4, 'title': 'some bar 4', 'url': 'http://bar.com/4', 'price': '29.99'},
        ]
        Product.objects.bulk_create([Product(store=self.store, **product) for product in products])

        products[0]['title'] += ' - 2nd edition'
        products[1]['price'] = '18.00'
        del products[2]['price']  # should reset to default 0

        self.store.update_products(revision_number=0, modified=products[0:3])
        self.assertEqual(Product.objects.count(), 4)

        products[2]['price'] = '0.00'
        self.assertListEqual(
            [True]*4,
            [Product.objects.filter(store=self.store, **product).exists() for product in products]
        )

    def test_update_products__modify_additional_fields_of_products(self):
        core_data = [
            {'external_id': 2, 'title': '2', 'url': 'http://bar.com/2', 'price': '9.00'},
            {'external_id': 1, 'title': '1', 'url': 'http://bar.com/1', 'price': '1.99'},
            {'external_id': 3, 'title': '3', 'url': 'http://bar.com/3', 'price': '5.00'},
            {'external_id': 4, 'title': '4', 'url': 'http://bar.com/4', 'price': '29.99'},
            {'external_id': 5, 'title': '5', 'url': 'http://bar.com/5', 'price': '0.00'},
        ]

        additional_data = [
            {'format': 'mp3'},
            {'size': 42},
            {'promo_price': '3.99'},
            {'a': 0, 'b': 1},
            {'field': 'data'},

        ]
        Product.objects.bulk_create([
            Product(store=self.store, **core, data=data)
            for core, data in zip(core_data, additional_data)
        ])

        additional_data[0]['format'] = 'pdf'
        additional_data[1]['size'] = '20x30'
        del additional_data[2]['promo_price']
        additional_data[3]['c'] = 2

        products = [{}, {}, {}, {}, {}]
        for product, core, data in zip(products, core_data, additional_data):
            product.update(core)
            product.update(data)

        self.store.update_products(revision_number=0, modified=products[0:4])
        self.assertEqual(Product.objects.count(), 5)

        self.assertListEqual(
            [True]*5,
            [
                Product.objects.filter(store=self.store, **core, data=data).exists()
                for core, data in zip(core_data, additional_data)
            ]
        )

