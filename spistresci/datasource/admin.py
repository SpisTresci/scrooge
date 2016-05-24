from django.contrib import admin
from django import forms
from django.core.urlresolvers import reverse
from django.forms.widgets import Textarea

from spistresci.datasource.models import DataSourceModel, XmlDataSourceModel, XmlDataField


class XmlDataSourceAdminForm(forms.ModelForm):
    data_fields = forms.CharField(widget=Textarea, required=False)

    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            data_fields = XmlDataField.objects.filter(data_source=instance)
            self.base_fields['data_fields'].initial = '\n'.join([str(field) for field in data_fields])

        self.base_fields['data_fields'].widget.attrs['disabled'] = True
        forms.ModelForm.__init__(self, *args, **kwargs)

    class Meta:
        model = XmlDataSourceModel
        fields = "__all__"


class XmlDataSourceModelAdmin(admin.ModelAdmin):
    form = XmlDataSourceAdminForm


def get_data_source(obj):
    return '<a href="{}">{}</a>'.format(
        reverse('admin:datasource_xmldatasource_change', args=(obj.data_source.id,)),
        obj.data_source.name
    )
get_data_source.allow_tags = True
get_data_source.admin_order_field = 'data_source__name'


class XmlDataFieldAdmin(admin.ModelAdmin):
    list_display = ('name', 'xpath', get_data_source,)


admin.site.register(DataSourceModel)
admin.site.register(XmlDataSourceModel, XmlDataSourceModelAdmin)
admin.site.register(XmlDataField, XmlDataFieldAdmin)
