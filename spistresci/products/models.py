from decimal import Decimal

from django.db import models
from django.contrib.postgres.fields import JSONField


class Product(models.Model):
    store = models.ForeignKey('stores.Store')

    external_id = models.IntegerField()
    name = models.CharField(max_length=255, blank=True, default='')
    url = models.URLField(max_length=2048, blank=True, default='')
    price = models.DecimalField(max_digits=8, decimal_places=2, blank=True, default=Decimal('0.00'))

    data = JSONField(default=dict, blank=True)

    class Meta:
        unique_together = (("store", "external_id"),)

    def __str__(self):
        return "{} - {} - {}".format(self.external_id, self.name, str(self.price))

    def to_dict(self):
        _dict = {
            'external_id': self.external_id,
            'name': self.name,
            'url': self.url,
            'price': str(self.price),
        }
        _dict.update(self.data)
        return _dict
