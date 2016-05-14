from django.contrib import admin

from spistresci.stores.models import Store


class StoreAdmin(admin.ModelAdmin):

    def get_readonly_fields(self, request, obj=None):
        return ['last_update_revision']

admin.site.register(Store, StoreAdmin)
