from test_plus.test import TestCase
from unittest.mock import patch, Mock, MagicMock, call

from django.test.utils import override_settings

from spistresci.stores.config import Config
from spistresci.stores.datasource.generic import XmlDataSource
from spistresci.stores.manager import StoreManager
from spistresci.stores.models import Store
from spistresci.stores.utils.datastoragemanager import DataStorageManager


@override_settings(ST_STORES_CONFIG='spistresci/stores/tests/datasource/configs/test_xmldatasource.yml')
class TestXmlDataSource(TestCase):

    def setUp(self):
        Config.read()
        self.store_config = Config.get()['stores']['xmldatasource']

    @patch('spistresci.stores.datasource.generic.DataStorageManager')
    def test_data_source_is_instance_of_XmlDataSource(self, data_storage_manager):
        data_source = StoreManager().get_store('xmldatasource')
        self.assertIsInstance(data_source, XmlDataSource)

    @patch('spistresci.stores.datasource.generic.DataStorageManager')
    @patch('spistresci.stores.datasource.generic.urlopen')
    def test_fetch_and_save_data_to_storage_manager(self, urlopen, data_storage_manager):
        mocked_response = Mock()
        mocked_response.read.side_effect = [b'data1', b'data1', None]
        urlopen.return_value = mocked_response

        data_storage_manager.return_value.save = MagicMock()

        data_source = StoreManager().get_store('xmldatasource')
        data_source.fetch()

        data_storage_manager.assert_has_calls([call(self.store_config['name'])])
        data_storage_manager.return_value.save.assert_has_calls([call('foo.xml')])

    @patch('spistresci.stores.datasource.generic.Store.update_products')
    @patch('spistresci.stores.datasource.generic.DataStorageManager')
    def test_update_should_update_data_only_if_new_revision_is_available(self, data_storage_manager, update_products):
        Store.objects.create(name=self.store_config['name'], url=self.store_config['url'], last_update_revision=42)
        data_source = StoreManager().get_store('xmldatasource')
        data_storage_manager.return_value.get.return_value = '<products></products>'

        data_storage_manager.return_value.last_revision_number.return_value = 42
        data_source.update()
        self.assertEqual(update_products.call_count, 0)

        data_storage_manager.return_value.last_revision_number.return_value = 43
        data_source.update()
        update_products.assert_called_once_with(revision_number=43, added=[], deleted=[], modified=[])

    @patch('spistresci.stores.datasource.generic.Store.update_products')
    @patch('spistresci.stores.datasource.generic.DataStorageManager')
    def test_update_creates_store_if_it_does_not_exist(self, data_storage_manager, update_products):
        self.assertEqual(Store.objects.count(), 0)

        data_storage_manager.return_value.get.return_value = '<products></products>'
        data_storage_manager.return_value.last_revision_number.return_value = 0

        data_source = StoreManager().get_store('xmldatasource')
        data_source.update()
        self.assertEqual(Store.objects.count(), 1)

    @patch('spistresci.stores.datasource.generic.DataStorageManager')
    def test_update_passes_no_revision_exception_if_there_is_no_data_in_ds(self, data_storage_manager):
        data_storage_manager.return_value.last_revision_number.side_effect = DataStorageManager.NoRevision()

        data_source = StoreManager().get_store('xmldatasource')
        with self.assertRaises(DataStorageManager.NoRevision):
            data_source.update()


@override_settings(ST_STORES_CONFIG='spistresci/stores/tests/datasource/configs/test_xmldatasource.yml')
class TestXmlDataSource2(TestCase):

    def setUp(self):
        self.patcher1 = patch('spistresci.stores.datasource.generic.DataStorageManager')
        self.patcher2 = patch('spistresci.stores.datasource.generic.Store.update_products')
        self.addCleanup(self.patcher1.stop)
        self.addCleanup(self.patcher2.stop)

        Config.read()
        self.store_config = Config.get()['stores']['xmldatasource']
        self.data_storage_manager = self.patcher1.start()
        self.update_products = self.patcher2.start()

        Store.objects.create(name=self.store_config['name'], url=self.store_config['url'], last_update_revision=0)
        self.data_storage_manager.return_value.last_revision_number.return_value = 1

        self.rev0 = '''
            <products>
                <product><id>1</id><title>AAA</title></product>
                <product><id>2</id><title>BBB</title></product>
            </products>
            '''
        self.rev1 = None

        self.data_storage_manager.return_value.get.side_effect = lambda f, rev: self.rev0 if rev == 0 else self.rev1

        self.data_source = StoreManager().get_store('xmldatasource')
        self.data_source.xml_tag_dict = {
            'external_id': ('./id', ''),
            'title': ('./title', ''),
        }

    def assert_helper(self, call_args, expected):
        """
        equivalent of: assert_called_once_with(revision_number=1, added=expected_added)
        without caring about order of items in list passed as parameter.
        Is there a better way to do that?
        """
        for name, value in call_args[1].items():
            if isinstance(value, list):
                self.assertListEqual(
                    sorted(value, key=lambda k: k['external_id']),
                    expected[name]
                )
            else:
                self.assertEqual(value, expected[name])

    def test_update__products_were_added_to_existing_store(self):
        self.rev1 = '''
            <products>
                <product><id>1</id><title>AAA</title></product>
                <product><id>2</id><title>BBB</title></product>
                <product><id>3</id><title>CCC</title></product>
                <product><id>4</id><title>DDD</title></product>
            </products>
            '''

        self.data_source.update()

        expected = {
            'added': [
                {'external_id': '3', 'title': 'CCC'},
                {'external_id': '4', 'title': 'DDD'},
            ],
            'deleted': [],
            'modified': [],
            'revision_number': 1
        }

        self.assertEqual(self.update_products.call_count, 1)
        self.assert_helper(self.update_products.call_args, expected)

    def test_update__products_were_modified(self):
        self.rev1 = '''
            <products>
                <product><id>1</id><title>AAA - aaa</title></product>
                <product><id>2</id><title>BBB - bbb</title></product>
            </products>
            '''

        self.data_source.update()

        expected = {
            'added': [],
            'deleted': [],
            'modified': [
                {'external_id': '1', 'title': 'AAA - aaa'},
                {'external_id': '2', 'title': 'BBB - bbb'},
            ],
            'revision_number': 1
        }

        self.assertEqual(self.update_products.call_count, 1)
        self.assert_helper(self.update_products.call_args, expected)

    def test_update__products_were_deleted(self):
        self.rev1 = "<products></products>"

        self.data_source.update()

        expected = {
            'added': [],
            'deleted': [
                {'external_id': '1', 'title': 'AAA'},
                {'external_id': '2', 'title': 'BBB'},
            ],
            'modified': [],
            'revision_number': 1
        }

        self.assertEqual(self.update_products.call_count, 1)
        self.assert_helper(self.update_products.call_args, expected)

    def test_update__products_were_added_modified_and_deleted(self):
        self.rev1 = '''
            <products>
                <product><id>1</id><title>AAA - aaa</title></product>
                <product><id>3</id><title>CCC</title></product>
            </products>
            '''

        self.data_source.update()

        self.update_products.assert_called_once_with(
            revision_number=1,
            added=[{'external_id': '3', 'title': 'CCC'}],
            deleted=[{'external_id': '2', 'title': 'BBB'}],
            modified=[{'external_id': '1', 'title': 'AAA - aaa'}]
        )

    def test_update__products_were_not_changed(self):
        self.rev1 = self.rev0
        self.data_source.update()
        self.update_products.assert_called_once_with(revision_number=1, added=[], deleted=[], modified=[])
