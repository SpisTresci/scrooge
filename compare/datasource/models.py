import textwrap
from lxml import etree
from hashlib import md5

from django.core.exceptions import ValidationError
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
    version_hash = models.CharField(max_length=32, editable=False)

    def save(self, *args, **kwargs):
        self.recalculate_version_hash()
        super(DataSourceModel, self).save(*args, **kwargs)

    def recalculate_version_hash(self):
        return NotImplemented

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


class DataSourceFieldName(models.Model):
    name = models.CharField(_('Name'), max_length=32, unique=True)

    def __str__(self):
        return self.name


class XmlDataSourceModel(DataSourceModel):
    SINGLE_XML = 1
    DATA_SOURCE_TYPE_CHOICES = (
        (SINGLE_XML, _('Single XML')),
    )
    type = models.IntegerField(_('Data source type'), choices=DATA_SOURCE_TYPE_CHOICES, default=SINGLE_XML)
    url = models.URLField(help_text=_('URL address of data source'), default=None, blank=False)
    offers_xpath = models.CharField(
        default='',
        max_length=64,
        help_text=_(textwrap.dedent("""
            XPath to offer elements.

            For document below, that would be /root/book
            <root>
              <book></book>
              <book></book>
            </root>

            For document below, that would be /root/offers/offer
            <root>
              <store>
                <location></location>
              </store>
              <offers>
                <offer></offer>
                <offer></offer>
              </offers>
            </root>
            """)
        ).replace('<', '&lt;').replace('>', '&gt;').replace(' ', '&nbsp;').replace('\n', '<br />')
    )
    custom_class = models.CharField(max_length=32, choices=get_data_source_classes(), default='XmlDataSourceImpl')

    def __init__(self, *args, **kwargs):
        super(XmlDataSourceModel, self).__init__(*args, **kwargs)
        self._old_offers_xpath = self.offers_xpath

    def recalculate_version_hash(self):
        content = self.offers_xpath.encode('utf-8')
        content += ''.join(['{}{}'.format(field.name, field.xpath) for field in self.fields]).encode('utf-8')
        self.version_hash = md5(content).hexdigest()

    @property
    def impl_class(self):
        return XmlDataSourceImpl

    @property
    def fields(self):
        return XmlDataField.objects.filter(data_source=self).order_by('id')

    def __str__(self):
        return '{} - class {}'.format(self.name, self.custom_class)


def xpath_validator(value):
    root = etree.fromstring('<root></root>')
    try:
        root.xpath(value)
    except Exception:
        raise ValidationError(
            _("'%(value)s' is not valid xpath"),
            params={'value': value},
        )


class XmlDataField(models.Model):
    name = models.ForeignKey(DataSourceFieldName, null=True)
    xpath = models.CharField(
        default='',
        blank=True,
        help_text=_('Relative xpath needed to extract value of field'),
        max_length=256,
        validators=[xpath_validator]
    )
    data_source = models.ForeignKey(XmlDataSourceModel)

    class Meta:
        unique_together = (("name", "data_source"),)

    def save(self, *args, **kwargs):
        super(XmlDataField, self).save(*args, **kwargs)
        self.data_source.recalculate_version_hash()

    def __str__(self):
        return '{} - {}'.format(self.name, self.xpath)
