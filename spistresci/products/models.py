from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField
from django.utils.translation import ugettext_lazy as _

# Create your models here.


class Product(models.Model):
    external_id = models.IntegerField()
    title = models.CharField(_('Title of Product'), max_length=255)
    url = models.URLField(max_length=2048, default='')

    store = models.ForeignKey('stores.Store')

    price = models.DecimalField(max_digits=8, decimal_places=2, default=Decimal(0.00))
    data = JSONField(default=dict)

    class Meta:
        unique_together = (("store", "external_id"),)

    def __str__(self):
        return "{} - {} - {}".format(self.external_id, self.title, str(self.price))

    def to_dict(self):
        _dict = {
            'external_id': self.external_id,
            'title': self.title,
            'url': self.url,
            'price': str(self.price),
        }
        _dict.update(self.data)
        return _dict
