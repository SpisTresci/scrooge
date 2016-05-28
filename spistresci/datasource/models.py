import textwrap

from django.db import models
from django.utils.translation import ugettext_lazy as _

from spistresci.datasource.generic import XmlDataSourceImpl
from spistresci.datasource.utils import get_data_source_classes

# noinspection PyUnresolvedReferences
# statement used for autodiscover,
# TODO: replace with http://stackoverflow.com/questions/32335967/
from spistresci.datasource.specific import *


class DataSourceModel(models.Model):
    name = models.CharField(_('Name'), max_length=32, unique=True)

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
    def impl_class(self):
        return NotImplemented

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

    offers_root_xpath = models.CharField(
        max_length=64,
        help_text=_(textwrap.dedent("""
            XPath to element which children are offers elements.

            For document below, that would be /root
            <root>
              <book></book>
              <book></book>
            </root>

            and in that case, that would be /root/offers
            <root>
              <store>
                <location></location>
              <store>
              <offers>
                <offer></offer>
                <offer></offer>
              </offers>
            </root>
            """)
        ).replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;').replace('\n', '<br />')
    )

    SINGLE_XML = 1

    DATA_SOURCE_TYPE_CHOICES = (
        (SINGLE_XML, _('Single XML')),
    )

    type = models.IntegerField(_('Data source type'), choices=DATA_SOURCE_TYPE_CHOICES, default=SINGLE_XML)
    url = models.URLField(help_text=_('URL address of data source'), default=None, blank=False)
    custom_class = models.CharField(max_length=32, choices=get_data_source_classes(), default='XmlDataSourceImpl')

    @property
    def impl_class(self):
        return XmlDataSourceImpl

    @property
    def fields(self):
        return XmlDataField.objects.filter(data_source=self)

    def __str__(self):
        return '{} - class {}'.format(self.name, self.custom_class)



class XmlDataField(models.Model):

    # TODO: make sure, that user cannot create field with name 'data'.

    name = models.CharField(max_length=32)
    xpath = models.CharField(help_text=_('Relative xpath needed to extract value of field'), max_length=256)
    default_value = models.CharField(max_length=32, default='', blank=True)
    data_source = models.ForeignKey(XmlDataSourceModel)

    def __str__(self):
        return '{} - {}'.format(self.name, self.xpath)
