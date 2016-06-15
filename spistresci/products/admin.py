from django.contrib import admin
from django.core.urlresolvers import reverse

from spistresci.products.models import Product


def get_url(obj):
    return '<a href="{url}">{url}</a>'.format(url=obj.url)

get_url.allow_tags = True
get_url.short_description = 'url'


def get_store(obj):
    return '<a href="{}">{}</a>'.format(
        reverse('admin:stores_store_change', args=(obj.store.id,)),
        obj.store.name
    )

get_store.short_description = 'Store'
get_store.allow_tags = True
get_store.admin_order_field = 'store__name'


class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'external_id',
        'name',
        get_url,
        'price',
        get_store
    )


admin.site.register(Product, ProductAdmin)
