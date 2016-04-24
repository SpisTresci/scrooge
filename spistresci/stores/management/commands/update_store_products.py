import logging

from django_docopt_command import DocOptCommand

from spistresci.stores.manager import StoreManager
from spistresci.stores.utils.datastoragemanager import DataStorageManager

logger = logging.getLogger(__name__)


class Command(DocOptCommand):
    docs = '''Usage:
    update_store_products <store_name>...
    update_store_products --all

    Options:
      -a --all     Updates all stores configured in config
    '''

    def handle_docopt(self, arguments):
        try:
            manager = StoreManager(store_names=arguments['<store_name>'] if not arguments['--all'] else None)
        except StoreManager.MissingStoreInStoresConfigException as e:
            exit(e.args[0])

        for store in manager.get_stores():
            try:
                store.update()
            except DataStorageManager.NoRevision:
                logger.warn('{} cannot be updated. There is no fetched data for it.'.format(store.name))
