from test_plus.test import TestCase
from unittest.mock import patch, Mock, MagicMock, call

from django.test.utils import override_settings

from spistresci.stores.config import Config
from spistresci.stores.datasource.generic import XmlDataSource
from spistresci.stores.manager import StoreManager


@override_settings(ST_STORES_CONFIG='spistresci/stores/tests/datasource/configs/test_xmldatasource.yml')
class TestXmlDataSource(TestCase):

    def setUp(self):
        Config.read()
        self.data_source = StoreManager().get_store('xmldatasource')

    def test_data_source_is_instance_of_XmlDataSource(self):
        self.assertIsInstance(self.data_source, XmlDataSource)

    @patch('spistresci.stores.datasource.generic.DataStorageManager')
    @patch('spistresci.stores.datasource.generic.urlopen')
    def test_fetch_and_save_data_to_storage_manager(self, urlopen, data_storage_manager):
        mocked_response = Mock()
        mocked_response.read.side_effect = [b'data1', b'data1', None]
        urlopen.return_value = mocked_response

        data_storage_manager.return_value.save = MagicMock()

        self.data_source.fetch()

        data_storage_manager.assert_has_calls([call('Foo')])
        data_storage_manager.return_value.save.assert_has_calls([call('foo.xml')])
