from urllib.request import urlopen, Request
from spistresci.stores.utils.datastoragemanager import DataStorageManager


class DataSource:

    def __init__(self, store_config):
        self.name = store_config['name']
        self.url = store_config['data_source']['url']
        self.type = store_config['data_source']['type']

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


class XmlDataSource(DataSource):

    def fetch(self, headers=None):
        """
        Fetch data from url specified in __init__ and save
        this data with data_storage_manage, from where this data
        can be retrieved later by providing name and filename
        """

        print('fetch files for {}'.format(self.name))

        filename = '{}.xml'.format(self.name.lower())

        request = Request(self.url, headers=headers or {})
        response = urlopen(request)

        chunk_size = 16 * 1024
        ds_manager = DataStorageManager(self.name)
        with ds_manager.save(filename) as buffer:
            while True:
                chunk = response.read(chunk_size)
                if not chunk:
                    break

                buffer.write(chunk)

        return filename
