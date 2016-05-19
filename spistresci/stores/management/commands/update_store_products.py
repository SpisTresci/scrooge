import logging
import traceback
from django.core.management.base import BaseCommand

from spistresci.stores.models import Store

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '''Fetch and update data for ENABLED stores defined in the database.'''

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument(
            '--all', action='store_true', help='Fetch and update data for all enabled stores defined in database'
        )
        group.add_argument('store_names', metavar='store_name', nargs='*', default=[])

    def handle(self, *args, **options):

        stores = Store.objects.all() if options['all'] else self.get_stores(options['store_names'])
        err_messages = []
        for store in stores:
            try:
                if not store.enabled:
                    logger.info('Store {} is disabled'.format(store.name))
                else:
                    store.fetch()
                    store.update()
            except Exception as e:
                logger.critical('[Store:{}] {}\n{}'.format(store.name, str(e), traceback.format_exc()))
                err_messages.append(e)
                logger.info('Update for {} failed, but trying to finish job for other stores...'.format(store.name))

        if err_messages:
            exit(1)

    def get_stores(self, store_names):
        err_messages = []
        for name in store_names:
            try:
                yield Store.objects.get(name__iexact=name)
            except Store.DoesNotExist as e:
                logger.error("There is no '{}' store defined in database".format(name.lower()))
                err_messages.append(e)
                logger.info('Update for {} failed, but trying to finish job for other stores...'.format(name.lower()))

        if err_messages:
            exit(1)
