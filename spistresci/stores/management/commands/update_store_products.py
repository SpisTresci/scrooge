from django.conf import settings
from django.core.management.base import BaseCommand

from spistresci.stores.models import Store


class Command(BaseCommand):
    # TODO: correct help message
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

        stores = Store.objects.all() if options['all'] else self.get_stores(options['store_names'])

        for store in stores:
            if not store.enabled:
                print('Store {} is disabled'.format(store.name))
            else:
                store.fetch()
                store.update()

    def get_stores(self, store_names):
        for name in store_names:
            try:
                yield Store.objects.get(name__iexact=name)
            except Store.DoesNotExist as e:
                raise exit("There is no '{}' store defined in database".format(name.lower()))
