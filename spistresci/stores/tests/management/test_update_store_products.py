from django.test.utils import override_settings
from test_plus.test import TestCase
from unittest.mock import patch, Mock, MagicMock, call

from django.conf import settings
from django.core.management import get_commands, load_command_class

from spistresci.stores.config import Config
from .util import capture_standard_out


@override_settings(ST_STORES_CONFIG='spistresci/stores/tests/datasource/configs/test_xmldatasource.yml')
class TestUpdateStoreProducts(TestCase):

    def setUp(self):
        Config.read()
        self.store_config = Config.get()['stores']['xmldatasource']
        pass

    @patch('spistresci.stores.management.commands.update_store_products.StoreManager')
    def test__all_stores_are_updated(self, store_manager):
        mocked_store = MagicMock()
        store_manager.return_value.get_stores.return_value = [mocked_store] * 13

        call_docopt_command('update_store_products', '--all')

        self.assertEqual(mocked_store.update.call_count, 13)

    @patch('spistresci.stores.management.commands.update_store_products.StoreManager')
    def test__selected_stores_are_updated(self, store_manager):
        foo = MagicMock()
        bar = MagicMock()
        store_manager.return_value.get_stores.return_value = [foo, bar]

        call_docopt_command('update_store_products', 'Foo Bar')

        foo.update.assert_called_once_with()
        bar.update.assert_called_once_with()

    def test__not_existing_store_in_config_as_param_cause_cmd_to_fail(self):
        not_existing_store_name = 'NoFoo'

        expected_msg = "There is no '{}' store defined in '{}'".format(
            not_existing_store_name, settings.ST_STORES_CONFIG
        )

        with self.assertRaisesMessage(SystemExit, expected_msg):
            call_docopt_command('update_store_products', not_existing_store_name)


def call_docopt_command(name, arg_string):
    arguments = ['manage.py', name] + arg_string.split(' ')

    command = get_command(name)

    with capture_standard_out() as out:
        command.run_from_argv(arguments)

    stdout, _ = out
    return stdout


def get_command(name):
    app_name = get_commands()[name]
    return load_command_class(app_name, name)
