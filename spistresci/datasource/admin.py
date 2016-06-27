from django.contrib import admin
from django.db.models.fields import NOT_PROVIDED
from django.forms import ValidationError
from django.forms.models import BaseInlineFormSet

from spistresci.datasource.models import XmlDataSourceModel, XmlDataField, DataSourceFieldName
from spistresci.offers.models import Offer


def dict_of_required_fields():
    return [
        {'name': DataSourceFieldName.objects.get(name=field.name).id}
        for field in Offer._meta.fields
        if field.name not in ['id', 'store', 'data']
    ]


def list_of_required_fields():
    return [field['name'] for field in dict_of_required_fields()]


class RequiredInlineFormSet(BaseInlineFormSet):
    initial_data = dict_of_required_fields()

    def _construct_form(self, i, **kwargs):
        form = super(RequiredInlineFormSet, self)._construct_form(i, **kwargs)
        if 'name' in form.initial and form.initial['name'] in [initial['name'] for initial in self.initial_data]:
            form.fields['name'].disabled = True
            form.fields['name'].queryset = DataSourceFieldName.objects.filter(id=form.initial['name'])
            form.fields['name'].widget.can_add_related = False
            form.fields['name'].widget.can_change_related = False

        if 'name' in form.initial and form.initial['name'] == DataSourceFieldName.objects.get(name='external_id').id:
            form.fields['xpath'].required = True

        self.can_delete = False
        return form

    def __init__(self, *args, **kwargs):
        super(RequiredInlineFormSet, self).__init__(*args, **kwargs)
        if not kwargs['instance'].pk:
            self.initial = self.initial_data

    def get_queryset(self):
        return super(RequiredInlineFormSet, self).get_queryset().filter(name__in=list_of_required_fields())


class NotRequiredInlineFormSet(BaseInlineFormSet):
    def _construct_form(self, i, **kwargs):
        form = super(NotRequiredInlineFormSet, self)._construct_form(i, **kwargs)

        qs = DataSourceFieldName.objects.exclude(name__in=list_of_required_fields())

        if self.instance.id:
            qs = qs.exclude(
                id__in=[
                    field.name.id
                    for field in self.instance.child.fields
                    if not form.initial or field.name.id != form.initial['name']
                ]
            )

        form.fields['name'].queryset = qs
        return form

    def clean(self):
        super(NotRequiredInlineFormSet, self).clean()
        for form in self.forms:
            if form.cleaned_data and form.cleaned_data.get('name', '') == 'data':
                raise ValidationError("Name 'data' is forbidden. Use different name.")

    def get_queryset(self):
        return super(NotRequiredInlineFormSet, self).get_queryset().exclude(name__in=list_of_required_fields())


class XmlDataRequiredFieldInline(admin.TabularInline):
    model = XmlDataField
    formset = RequiredInlineFormSet
    max_num = len(RequiredInlineFormSet.initial_data)
    min_num = len(RequiredInlineFormSet.initial_data)
    extra = 0
    verbose_name = "Required Xml Data Field"
    verbose_name_plural = "Required Xml Data Fields"


class XmlDataNotRequiredFieldInline(admin.TabularInline):
    extra = 1
    model = XmlDataField
    formset = NotRequiredInlineFormSet
    verbose_name = "Additional Xml Data Field"
    verbose_name_plural = "Additional Xml Data Fields"


class XmlDataSourceModelAdmin(admin.ModelAdmin):
    inlines = [XmlDataRequiredFieldInline, XmlDataNotRequiredFieldInline]

    def get_readonly_fields(self, request, obj=None):
        return ['version_hash']


admin.site.register(XmlDataSourceModel, XmlDataSourceModelAdmin)
admin.site.register(DataSourceFieldName)
