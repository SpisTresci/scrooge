from django.conf import settings
from django.core.management.base import BaseCommand

from spistresci.stores.models import Store


class Command(BaseCommand):
    help = '''Fetch and update data for ENABLED stores defined in the database.'''

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
        err_messages = []
        for name in store_names:
            try:
                yield Store.objects.get(name__iexact=name)
            except Store.DoesNotExist:
                err_messages.append("There is no '{}' store defined in database".format(name.lower()))

        if err_messages:
            exit('\n'.join(err_messages))
