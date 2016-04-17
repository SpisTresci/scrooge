import traceback
from tempfile import TemporaryDirectory
from test_plus.test import TestCase

from django.test.utils import override_settings

from spistresci.stores.utils.datastoragemanager import DataStorageManager


class TestDataStorageManager(TestCase):

    def setUp(self):
        self.temp_dir = TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def _func_name(self):
        """
        To avoid using the same store_name for different tests, you can
        use testcase function name as store_name
        """
        return traceback.extract_stack(None, 2)[0][2]

    def test_data_are_saved(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')
                buffer.write(b'data part 2')

            content = ds_manager.get('file.xml')

        self.assertEqual(content, 'data part 1data part 2')

    def test_last_revision_number_is_0_at_the_beginning(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            self.assertEqual(ds_manager.last_revision_number(), 0)

    def test_last_revision_number_increase_after_each_save(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            self.assertEqual(ds_manager.last_revision_number(), 0)

            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), 1)

            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')
                buffer.write(b'data part 2')

            self.assertEqual(ds_manager.last_revision_number(), 2)

    def test_last_revision_number_do_not_depend_on_filename(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            self.assertEqual(ds_manager.last_revision_number(), 0)

            with ds_manager.save('file1.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), 1)

            with ds_manager.save('file2.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), 2)

    def test_last_revision_number_do_not_depend_on_store_name(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name() + '1')
            self.assertEqual(ds_manager.last_revision_number(), 0)

            with ds_manager.save('file1.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), 1)

            ds_manager = DataStorageManager(self._func_name() + '2')
            self.assertEqual(ds_manager.last_revision_number(), 0)

            with ds_manager.save('file1.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), 1)
