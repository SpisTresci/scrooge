from tempfile import TemporaryDirectory
from test_plus.test import TestCase

from django.test.utils import override_settings

from spistresci.stores.utils.datastoragemanager import DataStorageManager


class TestDataStorageManager(TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_data_are_saved(self):

        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager('the store name')
            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')
                buffer.write(b'data part 2')

            content = ds_manager.get('file.xml')

        self.assertEqual(content, 'data part 1data part 2')
