from unittest.mock import patch, MagicMock
from test_plus.test import TestCase

from django.conf import settings
from django.core.management import call_command
from django.test.utils import override_settings


@override_settings(ST_STORES_CONFIG='spistresci/stores/tests/datasource/configs/test_xmldatasource.yml')
class TestUpdateStoreProducts(TestCase):

    @patch('spistresci.stores.management.commands.update_store_products.StoreManager')
    def test__all_stores_are_updated(self, store_manager):
        mocked_store = MagicMock()
        store_manager.return_value.get_stores.return_value = [mocked_store] * 13

        call_command('update_store_products', '--all')

        self.assertEqual(mocked_store.update.call_count, 13)
        self.assertEqual(mocked_store.fetch.call_count, 13)

    @patch('spistresci.stores.management.commands.update_store_products.StoreManager')
    def test__selected_stores_are_updated(self, store_manager):
        foo = MagicMock()
        bar = MagicMock()
        store_manager.return_value.get_stores.return_value = [foo, bar]

        call_command('update_store_products', 'Foo Bar')

        foo.update.assert_called_once_with()
        bar.update.assert_called_once_with()

        foo.fetch.assert_called_once_with()
        bar.fetch.assert_called_once_with()

    def test__not_existing_store_in_config_as_param_cause_cmd_to_fail(self):
        not_existing_store_name = 'NoFoo'

        expected_msg = "There is no '{}' store defined in '{}'".format(
            not_existing_store_name, settings.ST_STORES_CONFIG
        )

        with self.assertRaisesMessage(SystemExit, expected_msg):
            call_command('update_store_products', not_existing_store_name)
