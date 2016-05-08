from django.conf import settings
from django.core.management.base import BaseCommand

from spistresci.stores.manager import StoreManager


class Command(BaseCommand):
    help = '''
    Fetches and update data for stores defined in file {}.
    You can use different config file by setting
    ST_STORES_CONFIG environment variable
    '''.format(settings.ST_STORES_CONFIG)

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument('--all', action='store_true', help='Fetches and update data for all stores in config')
        group.add_argument('store_names', metavar='store_name', nargs='*', default=[])

    def handle(self, *args, **options):
        try:
            manager = StoreManager(store_names=options['store_names'] if not options['all'] else None)
        except (
            StoreManager.MissingStoreInStoresConfigException,
            StoreManager.MissingStoreDataSourceImplementationException
        ) as e:
            exit(e.args[0])

        for store in manager.get_stores():
            store.fetch()
            store.update()
