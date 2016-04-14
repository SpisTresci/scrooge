from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.


class Product(models.Model):
    title = models.CharField(_('Title of Product'), max_length=255)
    store = models.ForeignKey('stores.Store')
    external_id = models.IntegerField()
    url = models.URLField(max_length=2048, default='')
