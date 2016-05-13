from django.conf import settings

from spistresci.stores.config import Config
from spistresci.stores.datasource.generic import DataSource

# import statement used for autodiscover
# TODO: replace with http://stackoverflow.com/questions/32335967/
from spistresci.stores.datasource.specific import *
# from spistresci.stores.models import Store


class StoreManager:

    class MissingStoreDataSourceImplementationException(Exception):
        def __init__(self, store_name):
            Exception.__init__(
                self,
                "There is no 'class {}(DataSource)' defined in '{}'. "
                "You should provide it. Instead DataSource as base class "
                "you can use generic class like XmlDataSource or similar.".format(
                    store_name,
                    settings.APPS_DIR('stores/datasource/specific/')
                )
            )

    # def __init__(self, store_names=None):
    #     stores = Store.objects.all()
    #
    #     stores = Config.get()['stores']
    #
    #     try:
    #         stores = stores if not store_names else {name.lower(): stores[name.lower()] for name in store_names}
    #     except KeyError as e:
    #         raise StoreManager.MissingStoreInStoresConfigException(e.args[0])
    #
    #     self.__stores = {name: self.create_data_source_instance(name, conf) for name, conf in stores.items()}

    # def get_stores(self):
    #     # return self.__stores.values()
    #     stores = Store.objects.all()
    #
    #     return stores

    def get_store(self, name):
        return self.__stores[name]

    @staticmethod
    def get_all_subclasses():
        return DataSource.get_all_subclasses()

    @staticmethod
    def create_data_source_instance(store_name, store_conf):
        for subclass_name, subclass in DataSource.get_all_subclasses().items():
            if subclass_name.lower() == store_name:
                return subclass(store_conf)
        else:
            raise StoreManager.MissingStoreDataSourceImplementationException(store_name.title())
