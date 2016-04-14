from django.conf import settings
from django_docopt_command import DocOptCommand

from spistresci.stores.config import Config


class Command(DocOptCommand):
    docs = '''Usage:
    fetch_store_products <store_name>...
    fetch_store_products --all
    '''

    def handle_docopt(self, arguments):
        config = Config.get()

        stores = None
        if arguments['--all']:
            stores = config['stores']
        else:
            try:
                stores = [config['stores'][store_name] for store_name in arguments['<store_name>']]
            except KeyError as e:
                exit('{} store is not defined in {}'.format(e, settings.ST_STORES_CONFIG))

        for store in stores:
            print(store['name'])
