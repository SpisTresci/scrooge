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

    def test__all_enabled_stores_are_updated(self, fetch, update):
        with self.assertLogs(level='INFO') as cm:
            call_command('update_store_products', '--all')

        self.assertEqual(cm.output, [
            "INFO:spistresci.stores.management.commands.update_store_products:Store Baz is disabled"
        ])

        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(update.call_count, 3)

    def test__selected_stores_are_updated_if_they_are_enabled(self, fetch, update):
        with self.assertLogs(level='INFO') as cm:
            call_command('update_store_products', 'Foo', 'Bar', 'Baz')

        self.assertEqual(cm.output, [
            "INFO:spistresci.stores.management.commands.update_store_products:Store Baz is disabled"
        ])

        self.assertEqual(fetch.call_count, 2)
        self.assertEqual(update.call_count, 2)

    def test__name_of_stores_are_case_insensitive(self, fetch, update):
        with self.assertLogs(level='INFO') as cm:
            call_command('update_store_products', 'FOO',  'bar', 'BaZ', 'Qux')

        self.assertEqual(cm.output, [
            "INFO:spistresci.stores.management.commands.update_store_products:Store Baz is disabled"
        ])

        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(update.call_count, 3)

    def test__not_existing_store_in_db_as_param_cause_cmd_to_fail_at_the_end(self, fetch, update):
        not_existing_stores = ['NoFoo', 'NoBar']

        with self.assertRaises(SystemExit) as exception_cm:
            with self.assertLogs(level='WARNING') as logger_cm:
                call_command('update_store_products', 'Foo', not_existing_stores[0], 'Bar', not_existing_stores[1])

        self.assertEqual(logger_cm.output, [
            "ERROR:spistresci.stores.management.commands.update_store_products:"
            "There is no '{}' store defined in database".format(name.lower()) for name in not_existing_stores
        ])

        self.assertEqual(exception_cm.exception.code, 1)

    def test__all_exceptions_are_logged(self, fetch, update):
        update.side_effect = [Exception('Error1'), Exception('2nd Error')]

        with self.assertRaises(SystemExit) as exception_cm:
            with self.assertLogs(level='WARNING') as logger_cm:
                call_command('update_store_products', 'Foo', 'Bar')

        self.assertIn(
            "CRITICAL:spistresci.stores.management.commands.update_store_products:[Store:Foo] Error1",
            logger_cm.output[0]
        )
        self.assertIn(
            "CRITICAL:spistresci.stores.management.commands.update_store_products:[Store:Bar] 2nd Error",
            logger_cm.output[1]
        )

        self.assertEqual(exception_cm.exception.code, 1)

    def test__update_is_not_stopped_for_next_store_if_update_of_prev_store_failed(self, fetch, update):
        fetch.side_effect = [Exception('Error1'), Exception('2nd Error'), None]

        with self.assertRaises(SystemExit) as exception_cm:
            with self.assertLogs(level='WARNING') as logger_cm:
                call_command('update_store_products', 'Foo', 'Bar', 'Qux')

        self.assertEqual(len(logger_cm.output), 2)
        self.assertEqual(fetch.call_count, 3)
        self.assertEqual(update.call_count, 1)

        self.assertIn(
            "CRITICAL:spistresci.stores.management.commands.update_store_products:[Store:Foo] Error1",
            logger_cm.output[0]
        )
        self.assertIn(
            "CRITICAL:spistresci.stores.management.commands.update_store_products:[Store:Bar] 2nd Error",
            logger_cm.output[1]
        )

        self.assertEqual(exception_cm.exception.code, 1)
