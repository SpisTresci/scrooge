from tempfile import TemporaryDirectory

from django.test.utils import override_settings
from test_plus.test import TestCase
# from pyfakefs.fake_filesystem_unittest import TestCase

from spistresci.stores.utils.data_storage_manager import data_storage_manager


class TestDataStorageManager(TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_data_are_saved(self):

        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            with data_storage_manager('the store name', 'file.xml') as storage:
                storage.write(b'data part 1')
                storage.write(b'data part 2')

            content = data_storage_manager('the store name', 'file.xml').get('file.xml')

        self.assertEqual(content, 'data part 1data part 2')
