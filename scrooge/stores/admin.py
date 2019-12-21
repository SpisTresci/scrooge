from django.contrib import admin
from django.contrib.humanize.templatetags.humanize import naturaltime

from scrooge.offers.models import Offer
from scrooge.stores.models import Store


def get_enabled(obj):
    return obj.enabled

get_enabled.short_description = 'Enabled'
get_enabled.boolean = True


def get_number_of_offers(obj):
    return Offer.objects.filter(store=obj).count()

get_number_of_offers.short_description = 'Number of offers'


def get_last_successful_update(obj):
    return naturaltime(obj.last_successful_update)

get_last_successful_update.short_description = 'Updated successfully last time'


def get_last_changing_offers_update(obj):
    return naturaltime(obj.last_changing_offers_update)

get_last_changing_offers_update.short_description = 'Offer(s) changed last time'


def get_data_source(obj):
    return '{}, class {}'.format(obj.data_source.name, obj.data_source.child.__class__.__name__)

get_data_source.short_description = 'Data Source'


class StoreAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        get_enabled,
        get_number_of_offers,
        get_last_successful_update,
        get_last_changing_offers_update,
        get_data_source
    )

    def get_readonly_fields(self, request, obj=None):
        return ['last_update_revision', 'last_successful_update', 'last_changing_offers_update']

admin.site.register(Store, StoreAdmin)
