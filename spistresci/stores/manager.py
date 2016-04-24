from django.conf import settings

from spistresci.stores.config import Config
from spistresci.stores.datasource.generic import DataSource

# import statement used for autodiscover
# TODO: replace with http://stackoverflow.com/questions/32335967/
from spistresci.stores.datasource.specific import *


class StoreManager:

    class MissingStoreInStoresConfigException(Exception):
        def __init__(self, store_name):
            Exception.__init__(
                self,
                "There is no '{}' store defined in '{}'.\n"
                "You can use different config by specifying its location "
                "by ST_STORES_CONFIG environment variable.".format(store_name, settings.ST_STORES_CONFIG)
            )

    def __init__(self, store_names=None):
        stores = Config.get()['stores']

        try:
            stores = stores if not store_names else {name: stores[name] for name in store_names}
        except KeyError as e:
            raise StoreManager.MissingStoreInStoresConfigException(e.args[0])

        self.__stores = {name: self.create_data_source_instance(name, conf) for name, conf in stores.items()}

    def get_stores(self):
        return self.__stores.values()

    def get_store(self, name):
        return self.__stores[name]

    @staticmethod
    def create_data_source_instance(store_name, store_conf):
        for subclass_name, subclass in DataSource.get_all_subclasses().items():
            if subclass_name.lower() == store_name:
                return subclass(store_conf)
        else:
            exit("There is no 'class {}(DataSource)' defined.".format(store_name.title()))
