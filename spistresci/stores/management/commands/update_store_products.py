from django_docopt_command import DocOptCommand

from spistresci.stores.manager import StoreManager


class Command(DocOptCommand):
    docs = '''Usage:
    update_store_products <store_name>...
    update_store_products --all
    '''

    def handle_docopt(self, arguments):
        manager = StoreManager(stores=arguments['<store_name>'] if not arguments['--all'] else None)

        for store in manager.get_stores():
            store.update()
