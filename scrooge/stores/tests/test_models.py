from decimal import Decimal
from django.db.utils import IntegrityError
from test_plus.test import TestCase

from scrooge.datasource.models import XmlDataSourceModel
from scrooge.offers.models import Offer
from scrooge.stores.models import Store


class TestStore(TestCase):

    def setUp(self):
        data_source = XmlDataSourceModel.objects.create(name='Foo', offers_xpath='/whatever', url='http://foo.com/xml')
        self.store = Store.objects.create(name='Foo', data_source=data_source)

    def test_update_offers__update_revision_number(self):
        self.assertEqual(self.store.last_update_revision, None)
        self.store.update_offers(revision_number=0)
        self.assertEqual(self.store.last_update_revision, 0)

    def test_update_offers__revision_number_is_not_updated_if_update_aborted(self):
        offers_to_add = [{'external_id': 1, 'name': 'some bar', 'url': 'http://bar.com/1'}]

        self.assertEqual(self.store.last_update_revision, None)
        self.store.update_offers(revision_number=0, added=offers_to_add)
        self.assertEqual(self.store.last_update_revision, 0)

        with self.assertRaises(IntegrityError):  # offer with the same external_id cannot be added twice
            self.store.update_offers(revision_number=1, added=offers_to_add)

        self.assertEqual(self.store.last_update_revision, 0)

    def test_update_offers__added(self):
        offer_1 = {
            'external_id': 1,
            'name': 'some bar',
            'url': 'http://bar.com/1'
        }

        self.store.update_offers(revision_number=0, added=[offer_1])
        self.assertEqual(Offer.objects.count(), 1)
        self.assertTrue(Offer.objects.filter(store=self.store, price=Decimal(0), **offer_1).exists())

    def test_update_offers__additional_data_stored_in_data_json_field(self):
        core_data_1 = {
            'external_id': 1,
            'name': 'some bar',
            'url': 'http://bar.com/1',
            'price': '3.14',
        }
        additional_data_1 = {
            'cover_size': 42,
            'author': 'Darth Vader',
            'midichlorians': 27700
        }

        offer_1 = {}
        offer_1.update(core_data_1)
        offer_1.update(additional_data_1)
        self.store.update_offers(revision_number=0, added=[offer_1])
        self.assertEqual(Offer.objects.count(), 1)
        self.assertTrue(Offer.objects.filter(store=self.store, data=additional_data_1, **core_data_1).exists())

    def test_update_offers__deletes_offers(self):
        offers = [
            {'external_id': 1, 'name': 'some bar 1', 'url': 'http://bar.com/1'},
            {'external_id': 2, 'name': 'some bar 2', 'url': 'http://bar.com/2'},
            {'external_id': 3, 'name': 'some bar 3', 'url': 'http://bar.com/3'},
        ]
        Offer.objects.bulk_create([Offer(store=self.store, **offer) for offer in offers])

        self.store.update_offers(revision_number=0, deleted=offers[0:2])
        self.assertEqual(Offer.objects.count(), 1)
        self.assertTrue(Offer.objects.filter(store=self.store, **offers[2]).exists())

    def test_update_offers__modify_core_fields_of_offers(self):
        offers = [
            {'external_id': 1, 'name': 'some bar 1', 'url': 'http://bar.com/1', 'price': '1.99'},
            {'external_id': 2, 'name': 'some bar 2', 'url': 'http://bar.com/2', 'price': '9.00'},
            {'external_id': 3, 'name': 'some bar 3', 'url': 'http://bar.com/3', 'price': '5.00'},
            {'external_id': 4, 'name': 'some bar 4', 'url': 'http://bar.com/4', 'price': '29.99'},
        ]
        Offer.objects.bulk_create([Offer(store=self.store, **offer) for offer in offers])

        offers[0]['name'] += ' - 2nd edition'
        offers[1]['price'] = '18.00'
        del offers[2]['price']  # should reset to default 0

        self.store.update_offers(revision_number=0, modified=offers[0:3])
        self.assertEqual(Offer.objects.count(), 4)

        offers[2]['price'] = '0.00'
        self.assertListEqual(
            [True]*4,
            [Offer.objects.filter(store=self.store, **offer).exists() for offer in offers]
        )

    def test_update_offers__modify_core_field_of_offers_with_None(self):
        offers = [
            {'external_id': 1, 'name': 'some bar 1', 'url': 'http://bar.com/1', 'price': '1.99'},
        ]
        Offer.objects.bulk_create([Offer(store=self.store, **offer) for offer in offers])

        offers[0]['price'] = None

        with self.assertLogs(level='WARNING') as logger_cm:
            self.store.update_offers(revision_number=0, modified=offers)

        self.assertEqual(logger_cm.output, [
            "WARNING:spistresci.stores.models:[Store:Foo][Offer:1]\n"
            "\t[price] 1.99 (<class 'decimal.Decimal'>) => 0.00 (<class 'decimal.Decimal'>)"
        ])

        self.assertEqual(Offer.objects.count(), 1)
        offers[0]['price'] = '0.00'
        self.assertEqual(
            True,
            Offer.objects.filter(store=self.store, **offers[0]).exists()
        )

    def test_update_offers__modify_additional_fields_of_offers(self):
        core_data = [
            {'external_id': 2, 'name': '2', 'url': 'http://bar.com/2', 'price': '9.00'},
            {'external_id': 1, 'name': '1', 'url': 'http://bar.com/1', 'price': '1.99'},
            {'external_id': 3, 'name': '3', 'url': 'http://bar.com/3', 'price': '5.00'},
            {'external_id': 4, 'name': '4', 'url': 'http://bar.com/4', 'price': '29.99'},
            {'external_id': 5, 'name': '5', 'url': 'http://bar.com/5', 'price': '0.00'},
        ]

        additional_data = [
            {'format': 'mp3'},
            {'size': 42},
            {'promo_price': '3.99'},
            {'a': 0, 'b': 1},
            {'field': 'data'},

        ]
        Offer.objects.bulk_create([
            Offer(store=self.store, data=data, **core)
            for core, data in zip(core_data, additional_data)
        ])

        additional_data[0]['format'] = 'pdf'
        additional_data[1]['size'] = '20x30'
        del additional_data[2]['promo_price']
        additional_data[3]['c'] = 2

        offers = [{}, {}, {}, {}, {}]
        for offer, core, data in zip(offers, core_data, additional_data):
            offer.update(core)
            offer.update(data)

        self.store.update_offers(revision_number=0, modified=offers[0:4])
        self.assertEqual(Offer.objects.count(), 5)

        self.assertListEqual(
            [True]*5,
            [
                Offer.objects.filter(store=self.store, data=data, **core).exists()
                for core, data in zip(core_data, additional_data)
            ]
        )
