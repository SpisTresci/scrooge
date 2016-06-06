import logging
import re
from lxml import etree
from urllib.request import urlopen, Request

from spistresci.stores.utils.datastoragemanager import DataStorageManager

logger = logging.getLogger(__name__)


class DataSourceImpl:

    def __init__(self, store):
        self.store = store
        self.ds_manager = DataStorageManager(self.store.name)

    @staticmethod
    def get_all_subclasses():
        """
        Returns all subclasses, not only direct subclasses, but also
        all subclasses of subclasses, and so on.
        """
        subclasses = {}

        def get_subclasses(subclasses, cls):
            if cls.__name__ != DataSourceImpl.__name__:
                subclasses[cls.__name__] = cls

            for subclass in cls.__subclasses__():
                get_subclasses(subclasses, subclass)

        get_subclasses(subclasses, DataSourceImpl)

        return subclasses

    def fetch(self):
        pass

    def _extract(self, revision):
        pass

    def _filter(self, products, prev_rev_number):
        pass

    def update(self):
        logger.info('[Store:{}] Updating products...'.format(self.store.name))
        available_revision = self.ds_manager.last_revision_number()

        if self.store.last_update_revision is None:
            products = self._extract(available_revision)
            self.store.update_products(revision_number=available_revision, added=products)
        elif self.store.last_update_revision < available_revision:
            products = self._extract(available_revision)
            filtered = self._filter(products, self.store.last_update_revision)
            self.store.update_products(
                revision_number=available_revision,
                added=filtered['added'],
                deleted=filtered['deleted'],
                modified=filtered['modified']
            )
        else:
            logger.info('[Store:{}] There are no new revision available!')


class XmlDataSourceImpl(DataSourceImpl):

    def fetch(self, headers=None):
        """
        Fetch data from url specified in __init__ and save
        this data with data_storage_manage, from where this data
        can be retrieved later by providing name and filename
        """
        data_source_url = self.store.data_source.child.url

        logger.info('[Store:{}] Fetching data from {}'.format(self.store.name, data_source_url))

        filename = '{}.xml'.format(self.store.name.lower())

        request = Request(data_source_url, headers=headers or {})
        response = urlopen(request)

        chunk_size = 16 * 1024
        with self.ds_manager.save(filename) as buffer:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break

                buffer.write(chunk)

        return filename

    def _extract(self, revision):
        logger.info('[Store:{}] Extracting data from XML (revision:{})...'.format(self.store.name, revision))

        file_name = '{}.xml'.format(self.store.name.lower())
        file_content = self.ds_manager.get(file_name, revision)
        unique_offers = {}

        for node in self._get_list_of_offers(file_content):
            offer = self._node_to_dict(node)
            external_id = offer['external_id']  # TODO: add exception - external_id is required

            if external_id not in unique_offers.keys():
                unique_offers[external_id] = offer
            else:
                logger.warning(
                    '[Store:{}] Offer with external_id "{}" is not unique!'.format(self.store.name, external_id)
                )

        return list(unique_offers.values())

    def _filter(self, products, prev_rev_number):
        logger.info(
            '[Store:{}] Filtering by data from previous version of XML (revision:{})...'.format(
                self.store.name, prev_rev_number
            )
        )
        old_products = self._extract(prev_rev_number)

        old_product_dicts = {product['external_id']: product for product in old_products}
        new_product_dicts = {product['external_id']: product for product in products}

        products_added = [
            new_product_dicts[key]
            for key in list(set(new_product_dicts.keys()) - set(old_product_dicts.keys()))
        ]
        products_deleted = [
            old_product_dicts[key]
            for key in list(set(old_product_dicts.keys()) - set(new_product_dicts.keys()))
        ]

        products_modified = [
            new_product_dicts[key]
            for key in set(old_product_dicts.keys()).intersection(set(new_product_dicts.keys()))
            if old_product_dicts[key] != new_product_dicts[key]
        ]

        return {
            'added': products_added,
            'deleted': products_deleted,
            'modified': products_modified,
        }

    def _get_list_of_offers(self, file_content):
        logger.info('[Store:{}] Parsing XML...'.format(self.store.name))
        parser = etree.XMLParser(huge_tree=True)
        logger.info('[Store:{}] Parsing went well :)'.format(self.store.name))
        root = etree.fromstring(str.encode(file_content), parser)
        offers = list(root.xpath(self.store.data_source.child.offers_xpath))
        return offers

    def _node_to_dict(self, node):
        offer_dict = {}
        for field in self.store.data_source.child.fields:
            if not field.xpath:
                offer_dict[field.name] = None
                continue

            offer_dict[field.name] = node.xpath(field.xpath)

            if len(offer_dict[field.name]) == 0:
                offer_dict[field.name] = None
            elif len(offer_dict[field.name]) == 1:
                offer_dict[field.name] = self._node_to_string(offer_dict[field.name][0])
            else:
                offer_dict[field.name] = [self._node_to_string(li) for li in offer_dict[field.name]]

        return offer_dict

    def _node_to_string(self, node):
        """
        Converts lxml.etree._ElementUnicodeResult to str,
        or whole node to str
        """
        return str(node) if isinstance(node, str) else etree.tostring(node, encoding='unicode')
