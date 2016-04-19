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

    def test_data_source_is_instance_of_XmlDataSource(self):
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
    @patch('spistresci.stores.datasource.generic.DataStorageManager.get')
    @patch('spistresci.stores.datasource.generic.DataStorageManager.last_revision_number')
    def test_update_should_update_data_only_if_new_revision_is_available(self, last_revision_number, get, update_products):
        Store.objects.create(name=self.store_config['name'], url=self.store_config['url'], last_update_revision=42)
        data_source = StoreManager().get_store('xmldatasource')
        get.return_value = '<products></products>'

        last_revision_number.return_value = 42
        data_source.update()
        self.assertEqual(update_products.call_count, 0)

        last_revision_number.return_value = 43
        data_source.update()
        update_products.assert_called_once_with(revision_number=43, added=[], deleted=[], modified=[])

    @patch('spistresci.stores.datasource.generic.Store.update_products')
    @patch('spistresci.stores.datasource.generic.DataStorageManager.get')
    @patch('spistresci.stores.datasource.generic.DataStorageManager.last_revision_number')
    def test_update_creates_store_if_it_does_not_exist(self, last_revision_number, get, update_products):
        self.assertEqual(Store.objects.count(), 0)

        get.return_value = '<products></products>'
        last_revision_number.return_value = 0

        data_source = StoreManager().get_store('xmldatasource')
        data_source.update()
        self.assertEqual(Store.objects.count(), 1)

    def test_update_raises_no_revision_exception_if_there_is_no_data_in_ds(self):
        data_source = StoreManager().get_store('xmldatasource')
        with self.assertRaises(DataStorageManager.NoRevision):
            data_source.update()
