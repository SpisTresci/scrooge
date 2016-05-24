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

    def test_get_raises_no_revision_at_the_beginning(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            with self.assertRaises(DataStorageManager.NoRevision):
                ds_manager.get('file.xml')

    def test_get_raises_no_revision_for_not_existing_revision(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')

            with self.assertRaises(DataStorageManager.NoRevision):
                ds_manager.get('file.xml', revision=999)

    def test_get_raises_no_file_when_there_is_no_file(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')

            with self.assertRaises(DataStorageManager.NoFile):
                ds_manager.get('other_file.xml')

    def test_get_returns_proper_revision(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())

            for rev in range(10):
                with ds_manager.save('file.xml') as buffer:
                    buffer.write('file content {}'.format(rev).encode())

                self.assertEqual(ds_manager.last_revision_number(), rev)

            for rev in range(10):
                self.assertEqual(
                    'file content {}'.format(rev),
                    ds_manager.get('file.xml', rev)
                )

            # without rev argument, last revision should be returned
            self.assertEqual('file content 9', ds_manager.get('file.xml'))

    def test_last_revision_number_raises_no_revisions_at_the_beginning(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())
            with self.assertRaises(DataStorageManager.NoRevision):
                ds_manager.last_revision_number()

    def test_last_revision_number_increase_after_each_save(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())

            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), DataStorageManager.FIRST_REV_NUMBER)

            with ds_manager.save('file.xml') as buffer:
                buffer.write(b'data part 1')
                buffer.write(b'data part 2')

            self.assertEqual(ds_manager.last_revision_number(), DataStorageManager.FIRST_REV_NUMBER + 1)

    def test_last_revision_number_do_not_depend_on_filename(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name())

            with ds_manager.save('file1.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), DataStorageManager.FIRST_REV_NUMBER)

            with ds_manager.save('file2.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), DataStorageManager.FIRST_REV_NUMBER + 1)

    def test_last_revision_number_do_not_depend_on_store_name(self):
        with override_settings(ST_STORES_DATA_DIR=self.temp_dir.name):
            ds_manager = DataStorageManager(self._func_name() + '1')
            with ds_manager.save('file1.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), DataStorageManager.FIRST_REV_NUMBER)

            ds_manager = DataStorageManager(self._func_name() + '2')
            with ds_manager.save('file1.xml') as buffer:
                buffer.write(b'data part 1')

            self.assertEqual(ds_manager.last_revision_number(), DataStorageManager.FIRST_REV_NUMBER)
