from unittest.mock import patch
from test_plus.test import TestCase

from django.core.management import call_command

from spistresci.stores.models import Store


@patch('spistresci.stores.management.commands.update_store_products.Store.update')
@patch('spistresci.stores.management.commands.update_store_products.Store.fetch')
class TestUpdateStoreProducts(TestCase):

    def setUp(self):
        Store.objects.bulk_create(
            Store(**kwargs) for kwargs in [
                {'name': 'Foo', 'enabled': True, 'url': 'http://foo.com/', 'data_source_url': 'http://foo.com/xml'},
                {'name': 'Bar', 'enabled': True, 'url': 'http://bar.com/', 'data_source_url': 'http://bar.com/xml'},
                {'name': 'Baz', 'enabled': False, 'url': 'http://baz.com/', 'data_source_url': 'http://baz.com/xml'},
                {'name': 'Qux', 'enabled': True, 'url': 'http://qux.com/', 'data_source_url': 'http://qux.com/xml'},

            ]
        )

    def test__all_enabled_stores_are_updated(self, update, fetch):
        call_command('update_store_products', '--all')

        self.assertEqual(update.call_count, 3)
        self.assertEqual(fetch.call_count, 3)

    def test__selected_stores_are_updated_if_they_are_enabled(self, update, fetch):
        call_command('update_store_products', 'Foo', 'Bar', 'Baz')

        self.assertEqual(update.call_count, 2)
        self.assertEqual(fetch.call_count, 2)

    def test__name_of_stores_are_case_insensitive(self, update, fetch):
        call_command('update_store_products', 'FOO',  'bar', 'BaZ', 'Qux')

        self.assertEqual(update.call_count, 3)
        self.assertEqual(fetch.call_count, 3)

    def test__not_existing_store_in_db_as_param_cause_cmd_to_fail(self, update, fetch):
        not_existing_store_name = 'NoFoo'
        expected_msg = "There is no '{}' store defined in database".format(
            not_existing_store_name.lower()
        )

        with self.assertRaisesMessage(SystemExit, expected_msg):
            call_command('update_store_products', 'Foo', 'Bar', not_existing_store_name)
