import os
import yaml

from django.conf import settings


class Config:
    __data = None

    @classmethod
    def read(cls):
        #TODO: add pykwalify based yml validation for STORES_CONFIG

        if not os.path.isfile(settings.ST_STORES_CONFIG):
            exit("'{}' config file is missing!".format(settings.ST_STORES_CONFIG))

        with open(settings.ST_STORES_CONFIG, 'r') as stream:
            try:
                cls.__data = yaml.load(stream)
            except yaml.YAMLError:
                exit('Your YAML contains errors.')

    @classmethod
    def get(cls):
        return cls.__data
