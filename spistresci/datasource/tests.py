from unittest.mock import patch, Mock, MagicMock, call

from test_plus.test import TestCase

from spistresci.datasource.generic import XmlDataSourceImpl
from spistresci.datasource.models import XmlDataSourceModel, XmlDataField
from spistresci.stores.models import Store
from spistresci.stores.utils.datastoragemanager import DataStorageManager


class TestXmlDataSource(TestCase):

    def setUp(self):
        data_source = XmlDataSourceModel.objects.create(name='Foo', depth=0, url='http://foo.com/xml')
        self.store = Store.objects.create(name='Foo', data_source=data_source)

    def test_default_data_source_is_instance_of_XmlDataSource(self):
        self.assertIsInstance(self.store.data_source_instance(), XmlDataSourceImpl)

    @patch('spistresci.datasource.generic.DataStorageManager')
    @patch('spistresci.datasource.generic.urlopen')
    def test_fetch_and_save_data_to_storage_manager(self, urlopen, data_storage_manager):
        mocked_response = Mock()
        mocked_response.read.side_effect = [b'data1', b'data1', None]
        urlopen.return_value = mocked_response

        data_storage_manager.return_value.save = MagicMock()

        self.store.fetch()

        data_storage_manager.assert_has_calls([call(self.store.name)])
        data_storage_manager.return_value.save.assert_has_calls([call('foo.xml')])

    @patch('spistresci.stores.models.Store.update_products')
    @patch('spistresci.datasource.generic.DataStorageManager')
    def test_update_should_update_data_only_if_new_revision_is_available(self, data_storage_manager, update_products):
        self.store.last_update_revision = 42
        self.store.save()

        data_storage_manager.return_value.get.return_value = '<products></products>'

        data_storage_manager.return_value.last_revision_number.return_value = 42
        self.store.update()
        self.assertEqual(update_products.call_count, 0)

        data_storage_manager.return_value.last_revision_number.return_value = 43
        self.store.update()
        update_products.assert_called_once_with(revision_number=43, added=[], deleted=[], modified=[])

    @patch('spistresci.datasource.generic.DataStorageManager')
    def test_update_passes_no_revision_exception_if_there_is_no_data_in_ds(self, data_storage_manager):
        data_storage_manager.return_value.last_revision_number.side_effect = DataStorageManager.NoRevision()

        with self.assertRaises(DataStorageManager.NoRevision):
            self.store.update()


class TestUpdateOfXmlDataSource(TestCase):

    def setUp(self):
        self.patcher1 = patch('spistresci.datasource.generic.DataStorageManager')
        self.patcher2 = patch('spistresci.stores.models.Store.update_products')
        self.addCleanup(self.patcher1.stop)
        self.addCleanup(self.patcher2.stop)
        self.data_storage_manager = self.patcher1.start()
        self.update_products = self.patcher2.start()

        data_source = XmlDataSourceModel.objects.create(name='Foo', depth=0, url='http://foo.com/xml')
        self.store = Store.objects.create(name='Foo', data_source=data_source, last_update_revision=0)

        XmlDataField.objects.create(name='external_id', xpath='./id', default_value='', data_source=data_source)
        XmlDataField.objects.create(name='title', xpath='./title', default_value='', data_source=data_source)

        self.data_storage_manager.return_value.last_revision_number.return_value = 1

        self.rev0 = '''
            <products>
                <product><id>1</id><title>AAA</title></product>
                <product><id>2</id><title>BBB</title></product>
            </products>
            '''
        self.rev1 = None

        self.data_storage_manager.return_value.get.side_effect = lambda f, rev: self.rev0 if rev == 0 else self.rev1

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

        self.store.update()

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

        self.store.update()

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

        self.store.update()

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

        self.store.update()

        self.update_products.assert_called_once_with(
            revision_number=1,
            added=[{'external_id': '3', 'title': 'CCC'}],
            deleted=[{'external_id': '2', 'title': 'BBB'}],
            modified=[{'external_id': '1', 'title': 'AAA - aaa'}]
        )

    def test_update__products_were_not_changed(self):
        self.rev1 = self.rev0
        self.store.update()
        self.update_products.assert_called_once_with(revision_number=1, added=[], deleted=[], modified=[])

    def test_update__duplicated_products_are_ignored(self):
        self.rev1 = '''
            <products>
                <product><id>1</id><title>AAA</title></product>
                <product><id>2</id><title>BBB</title></product>

                <product><id>3</id><title>CCC</title></product>
                <product><id>3</id><title>CCC - 2</title></product>

                <product><id>4</id><title>DDD</title></product>
                <product><id>4</id><title>DDD - 2</title></product>
                <product><id>4</id><title>DDD - 3</title></product>

                <product><id>5</id><title>EEE</title></product>
            </products>
            '''

        with self.assertLogs(level='WARNING') as cm:
            self.store.update()

        self.assertEqual(cm.output, [
            'WARNING:spistresci.datasource.generic:[Store:Foo] Product with external_id "3" is not unique!',
            'WARNING:spistresci.datasource.generic:[Store:Foo] Product with external_id "4" is not unique!',
            'WARNING:spistresci.datasource.generic:[Store:Foo] Product with external_id "4" is not unique!'
        ])

        expected = {
            'added': [
                {'external_id': '3', 'title': 'CCC'},
                {'external_id': '4', 'title': 'DDD'},
                {'external_id': '5', 'title': 'EEE'},
            ],
            'deleted': [],
            'modified': [],
            'revision_number': 1
        }

        self.assert_helper(self.update_products.call_args, expected)
