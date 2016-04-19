from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.


class Store(models.Model):
    name = models.CharField(_('Store name'), max_length=32)
    url = models.URLField(_('Store url address'))
    last_update_revision = models.IntegerField(null=True)

    def update_products(self, revision, added=None, deleted=None, modified=None):
        added = added or []
        deleted = deleted or []
        modified = modified or []
