from django.db import models
from django.utils.translation import ugettext_lazy as _

from spistresci.datasource.utils import get_data_source_classes

# noinspection PyUnresolvedReferences
# statement used for autodiscover,
# TODO: replace with http://stackoverflow.com/questions/32335967/
from spistresci.datasource.specific import *


class DataSourceModel(models.Model):
    name = models.CharField(_('Name'), max_length=32)

    @staticmethod
    def get_all_subclasses():
        """
        Returns all subclasses, not only direct subclasses, but also
        all subclasses of subclasses, and so on.
        """
        subclasses = {}

        def get_subclasses(subclasses, cls):
            if cls.__name__ != DataSourceModel.__name__:
                subclasses[cls.__name__] = cls

            for subclass in cls.__subclasses__():
                get_subclasses(subclasses, subclass)

        get_subclasses(subclasses, DataSourceModel)

        return subclasses

    @property
    def child(self):
        data_source_field_names = [name.lower() for name in self.get_all_subclasses().keys()]
        for field_name in data_source_field_names:
            child = getattr(self, field_name)
            if child:
                return child

    def __str__(self):
        return str(self.child)



class XmlDataSourceModel(DataSourceModel):
    """
    Example of XML file with depth 1:
    <root>
        <product></product>
        <product></product>
    </root>

    Example of XML file with depth 2:
    <root>
        <group>
            <product></product>
            <product></product>
        </group>
    </root>
    """
    depth = models.IntegerField(_('On which level offers are located'))

    SINGLE_XML = 1

    DATA_SOURCE_TYPE_CHOICES = (
        (SINGLE_XML, _('Single XML')),
    )

    type = models.IntegerField(_('Data source type'), choices=DATA_SOURCE_TYPE_CHOICES, default=SINGLE_XML)
    url = models.URLField(_('URL address of data source'), default=None, blank=False)
    custom_class = models.CharField(max_length=32, choices=get_data_source_classes(), default='XmlDataSource')


    def __str__(self):
        return '{} - class {}'.format(self.name, self.custom_class)



class XmlDataField(models.Model):
    name = models.CharField(_('Name of field'), max_length=32)
    xpath = models.CharField(_('xpath needed to extract value of field'), max_length=256)
    data_source = models.ForeignKey(XmlDataSourceModel)

    def __str__(self):
        return '{} - {}'.format(self.name, self.xpath)
