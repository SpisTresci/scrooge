from django.apps import AppConfig
from spistresci.stores.config import Config


class StoresConfig(AppConfig):
    name = 'spistresci.stores'

    def ready(self):
        Config.read()
