import logging
import re
from lxml import etree
from urllib.request import urlopen, Request

from spistresci.stores.models import Store
from spistresci.stores.utils.datastoragemanager import DataStorageManager

logger = logging.getLogger(__name__)


class DataSource:

    def __init__(self, store_config):
        self.name = store_config['name']
        self.store_url = store_config['url']
        self.url = store_config['data_source']['url']
        self.type = store_config['data_source']['type']
        self.ds_manager = DataStorageManager(self.name)

    @staticmethod
    def get_all_subclasses():
        """
        Returns all subclasses, not only direct subclasses, but also
        all subclasses of subclasses, and so on.
        """
        subclasses = {}

        def get_subclasses(subclasses, cls):
            subclasses[cls.__name__] = cls
            for subclass in cls.__subclasses__():
                get_subclasses(subclasses, subclass)

        get_subclasses(subclasses, DataSource)

        return subclasses

    def fetch(self):
        pass

    def _extract(self, revision):
        pass

    def _filter(self, products, prev_rev_number):
        pass

    def update(self):
        available_revision = self.ds_manager.last_revision_number()
        store, new = Store.objects.get_or_create(name=self.name, url=self.store_url)

        if new or store.last_update_revision is None:
            products = self._extract(available_revision)
            store.update_products(revision_number=available_revision, added=products)
        elif store.last_update_revision < available_revision:
            products = self._extract(available_revision)
            filtered = self._filter(products, store.last_update_revision)
            store.update_products(
                revision_number=available_revision,
                added=filtered['added'],
                deleted=filtered['deleted'],
                modified=filtered['modified']
            )


class XmlDataSource(DataSource):

    def fetch(self, headers=None):
        """
        Fetch data from url specified in __init__ and save
        this data with data_storage_manage, from where this data
        can be retrieved later by providing name and filename
        """

        logger.info('fetch files for {}'.format(self.name))

        filename = '{}.xml'.format(self.name.lower())

        request = Request(self.url, headers=headers or {})
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

        file_name = '{}.xml'.format(self.name.lower())
        file_content = self.ds_manager.get(file_name, revision)

        products = [
            self._make_dict(product_xml_node)
            for product_xml_node in self._get_product_list(file_content)
        ]

        return products

    def _filter(self, products, prev_rev_number):
        new_product_dicts = {product['external_id']: product for product in products}
        file_name = '{}.xml'.format(self.name.lower())
        file_content = self.ds_manager.get(file_name, prev_rev_number)

        old_products = [
            self._make_dict(product_xml_node)
            for product_xml_node in self._get_product_list(file_content)
        ]

        old_product_dicts = {product['external_id']: product for product in old_products}

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

    # code below is inherited from SpisTresci 1.0. Refactor is welcome :)

    xml_tag_dict = None
    xmls_namespace = ''
    depth = 0

    def _get_product_list(self, file_content):
        root = etree.fromstring(str.encode(file_content))
        return list(self._we_have_to_go_deeper(root, self.depth))

    def _we_have_to_go_deeper(self, root, depth):
        for i in range(int(depth)):
            root = root[0]
        return root

    def _make_dict(self, product, xml_tag_dict=None):
        """
        Translate product xml into dictionary used to insert into database
        :param product: product xml root
        :param xml_tag_dict: dictionary of xpaths used to translate
        :return: created dictionary
        """

        xml_tag_dict = xml_tag_dict or self.xml_tag_dict

        product_dict = {}
        for (dict_key, xpath) in xml_tag_dict.items():
            (tag, default_0) = xpath
            regex = re.compile("([^{]*)({.*})?")
            recurency = regex.search(tag).groups()
            ntag = recurency[0]
            elems = product.xpath(ntag, namespaces=self.xmls_namespace)
            for elem in elems:
                if recurency[1] is not None:
                    self._get_dict_from_elem(eval(recurency[1]), dict_key, elem, tag, product_dict)
                else:
                    self._get_value_from_elem(dict_key, default_0, elem, ntag, product_dict)

            product_dict.setdefault(dict_key, (str(default_0) if default_0 is not None else None))

            if product_dict[dict_key] is not None and len(product_dict[dict_key]) == 1:
                product_dict[dict_key] = product_dict[dict_key][0]

        return product_dict

    def _get_dict_from_elem(self, xml_tag_dict, new_tag, elem, tag, product_dict):
        if elem is not None:
            if product_dict.get(new_tag) is None:
                product_dict[new_tag] = []

            product_dict[new_tag].append(self._make_dict(elem, xml_tag_dict))

    def _get_value_from_elem(self, new_tag, default_0, elem, tag, product_dict):
        if elem is not None:
            if product_dict.get(new_tag) is None:
                product_dict[new_tag] = []
            if isinstance(elem, str):
                product_dict[new_tag].append(str(elem))
            else:
                product_dict[new_tag].append(str(elem.text if elem.text != "" and elem.text is not None else default_0))
