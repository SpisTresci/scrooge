from test_plus.test import TestCase

from scrooge.datasource.models import XmlDataSourceModel, XmlDataField, DataSourceFieldName


class TestXmlDataSourceModel(TestCase):

    def setUp(self):
        pass

    def test__version_hash_should_be_different_if_offers_xpath_changed(self):

        data_source = XmlDataSourceModel.objects.create(
            name='Foo',
            offers_xpath='/offers/offer',
            url='http://foo.com/xml'
        )

        version_hash = data_source.version_hash

        data_source.offers_xpath = '/offers'
        data_source.save()
        self.assertNotEqual(version_hash, data_source.version_hash)

    def test__version_hash_should_be_different_if_fields_changed(self):
        data_source = XmlDataSourceModel.objects.create(
            name='Foo',
            offers_xpath='/offers/offer',
            url='http://foo.com/xml'
        )

        external_id, _ = DataSourceFieldName.objects.get_or_create(name='external_id')
        name, _ = DataSourceFieldName.objects.get_or_create(name='name')
        name2, _ = DataSourceFieldName.objects.get_or_create(name='name2')

        f1 = XmlDataField.objects.create(name=external_id, xpath='./id/text()', data_source=data_source)
        f2 = XmlDataField.objects.create(name=name, xpath='./name/text()', data_source=data_source)

        version_hash = data_source.version_hash
        f1.xpath = './new_id/text()'
        f1.save()
        self.assertNotEqual(version_hash, data_source.version_hash)
        version_hash = data_source.version_hash

        f2.name = name2
        f2.save()
        self.assertNotEqual(version_hash, data_source.version_hash)
