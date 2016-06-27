from unittest.mock import patch, Mock, MagicMock, call

from test_plus.test import TestCase

from spistresci.datasource.generic import XmlDataSourceImpl
from spistresci.datasource.models import XmlDataSourceModel, XmlDataField, DataSourceFieldName
from spistresci.stores.models import Store
from spistresci.stores.utils.datastoragemanager import DataStorageManager


class TestXmlDataSourceImpl(TestCase):

    def setUp(self):
        data_source = XmlDataSourceModel.objects.create(name='Foo', offers_xpath='/whatever', url='http://foo.com/xml')
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

    @patch('spistresci.stores.models.Store.update_offers')
    @patch('spistresci.datasource.generic.DataStorageManager')
    def test_update_should_update_data_only_if_new_revision_is_available(self, data_storage_manager, update_offers):
        self.store.last_update_revision = 42
        self.store.save()

        data_storage_manager.return_value.get.return_value = '<offers></offers>'

        data_storage_manager.return_value.last_revision_number.return_value = 42
        self.store.update()
        self.assertEqual(update_offers.call_count, 0)

        data_storage_manager.return_value.last_revision_number.return_value = 43
        self.store.update()
        update_offers.assert_called_once_with(revision_number=43, added=[], deleted=[], modified=[])

    @patch('spistresci.datasource.generic.DataStorageManager')
    def test_update_passes_no_revision_exception_if_there_is_no_data_in_ds(self, data_storage_manager):
        data_storage_manager.return_value.last_revision_number.side_effect = DataStorageManager.NoRevision()

        with self.assertRaises(DataStorageManager.NoRevision):
            self.store.update()


class TestUpdateOfXmlDataSourceImpl(TestCase):

    def setUp(self):
        self.patcher1 = patch('spistresci.datasource.generic.DataStorageManager')
        self.patcher2 = patch('spistresci.stores.models.Store.update_offers')
        self.addCleanup(self.patcher1.stop)
        self.addCleanup(self.patcher2.stop)
        self.data_storage_manager = self.patcher1.start()
        self.update_offers = self.patcher2.start()

        self.data_source = XmlDataSourceModel.objects.create(name='Foo', offers_xpath='/offers/offer', url='http://foo.com/xml')

        external_id, _ = DataSourceFieldName.objects.get_or_create(name='external_id')
        name, _ = DataSourceFieldName.objects.get_or_create(name='name')

        XmlDataField.objects.create(name=external_id, xpath='./id/text()', data_source=self.data_source)
        XmlDataField.objects.create(name=name, xpath='./name/text()', data_source=self.data_source)
        self.store = Store.objects.create(
            name='Foo',
            data_source=self.data_source,
            last_update_revision=0,
            last_update_data_source_version_hash=self.data_source.version_hash
        )

        self.data_storage_manager.return_value.last_revision_number.return_value = 1

        self.rev0 = '''
            <offers>
                <offer><id>1</id><name>AAA</name><price>0.00</price></offer>
                <offer><id>2</id><name>BBB</name><price>9.99</price></offer>
            </offers>
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

    def test_update__offers_were_added_to_existing_store(self):
        self.rev1 = '''
            <offers>
                <offer><id>1</id><name>AAA</name></offer>
                <offer><id>2</id><name>BBB</name></offer>
                <offer><id>3</id><name>CCC</name></offer>
                <offer><id>4</id><name>DDD</name></offer>
            </offers>
            '''

        self.store.update()

        expected = {
            'added': [
                {'external_id': '3', 'name': 'CCC'},
                {'external_id': '4', 'name': 'DDD'},
            ],
            'deleted': [],
            'modified': [],
            'revision_number': 1
        }

        self.assertEqual(self.update_offers.call_count, 1)
        self.assert_helper(self.update_offers.call_args, expected)

    def test_update__offers_were_modified(self):
        self.rev1 = '''
            <offers>
                <offer><id>1</id><name>AAA - aaa</name></offer>
                <offer><id>2</id><name>BBB - bbb</name></offer>
            </offers>
            '''

        self.store.update()

        expected = {
            'added': [],
            'deleted': [],
            'modified': [
                {'external_id': '1', 'name': 'AAA - aaa'},
                {'external_id': '2', 'name': 'BBB - bbb'},
            ],
            'revision_number': 1
        }

        self.assertEqual(self.update_offers.call_count, 1)
        self.assert_helper(self.update_offers.call_args, expected)

    def test_update__offers_were_deleted(self):
        self.rev1 = "<offers></offers>"

        self.store.update()

        expected = {
            'added': [],
            'deleted': [
                {'external_id': '1', 'name': 'AAA'},
                {'external_id': '2', 'name': 'BBB'},
            ],
            'modified': [],
            'revision_number': 1
        }

        self.assertEqual(self.update_offers.call_count, 1)
        self.assert_helper(self.update_offers.call_args, expected)

    def test_update__offers_were_added_modified_and_deleted(self):
        self.rev1 = '''
            <offers>
                <offer><id>1</id><name>AAA - aaa</name></offer>
                <offer><id>3</id><name>CCC</name></offer>
            </offers>
            '''

        self.store.update()

        self.update_offers.assert_called_once_with(
            revision_number=1,
            added=[{'external_id': '3', 'name': 'CCC'}],
            deleted=[{'external_id': '2', 'name': 'BBB'}],
            modified=[{'external_id': '1', 'name': 'AAA - aaa'}]
        )

    def test_update__offers_were_not_changed(self):
        self.rev1 = self.rev0
        self.store.update()
        self.update_offers.assert_called_once_with(revision_number=1, added=[], deleted=[], modified=[])

    def test_update__duplicated_offers_are_ignored(self):
        self.rev1 = '''
            <offers>
                <offer><id>1</id><name>AAA</name></offer>
                <offer><id>2</id><name>BBB</name></offer>

                <offer><id>3</id><name>CCC</name></offer>
                <offer><id>3</id><name>CCC - 2</name></offer>

                <offer><id>4</id><name>DDD</name></offer>
                <offer><id>4</id><name>DDD - 2</name></offer>
                <offer><id>4</id><name>DDD - 3</name></offer>

                <offer><id>5</id><name>EEE</name></offer>
            </offers>
            '''

        with self.assertLogs(level='WARNING') as cm:
            self.store.update()

        self.assertEqual(cm.output, [
            'WARNING:spistresci.datasource.generic:[Store:Foo] Offer with external_id "3" is not unique!',
            'WARNING:spistresci.datasource.generic:[Store:Foo] Offer with external_id "4" is not unique!',
            'WARNING:spistresci.datasource.generic:[Store:Foo] Offer with external_id "4" is not unique!'
        ])

        expected = {
            'added': [
                {'external_id': '3', 'name': 'CCC'},
                {'external_id': '4', 'name': 'DDD'},
                {'external_id': '5', 'name': 'EEE'},
            ],
            'deleted': [],
            'modified': [],
            'revision_number': 1
        }

        self.assert_helper(self.update_offers.call_args, expected)

    def test_update__redefinition_of_datasource_should_cause_update_of_all_offers(self):
        price, _ = DataSourceFieldName.objects.get_or_create(name='price')
        XmlDataField.objects.create(name=price, xpath='./price/text()', data_source=self.data_source)
        self.rev1 = self.rev0

        self.store.update()

        expected = {
            'added': [],
            'deleted': [],
            'modified': [
                {'external_id': '1', 'name': 'AAA', 'price': '0.00'},
                {'external_id': '2', 'name': 'BBB', 'price': '9.99'},
            ],
            'revision_number': 1
        }

        self.assertEqual(self.update_offers.call_count, 1)
        self.assert_helper(self.update_offers.call_args, expected)
