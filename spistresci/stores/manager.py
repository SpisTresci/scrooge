from spistresci.stores.config import Config
from spistresci.stores.datasource.generic import DataSource

# import statement used for autodiscover
# TODO: replace with http://stackoverflow.com/questions/32335967/
from spistresci.stores.datasource.specific import *


class StoreManager:
    def __init__(self, stores=None):
        config = Config.get()
        stores = config['stores'].items()
        self.__stores = [
            self.create_data_source_instance(store_name, store_conf)
            for store_name, store_conf in stores
        ]

    def get_stores(self):
        return self.__stores

    @staticmethod
    def create_data_source_instance(store_name, store_conf):
        for subclass_name, subclass in DataSource.get_all_subclasses().items():
            if subclass_name.lower() == store_name:
                return subclass(store_conf)
        else:
            exit("There is no 'class {}(DataSource)' defined.".format(store_name.title()))
