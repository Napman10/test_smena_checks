from django.contrib import admin
from .models import Check, Printer, CHECK_TYPES, ORDER_STATUSES
from django.contrib.admin import SimpleListFilter

admin.site.register(Check)
admin.site.register(Printer)

class CheckStatusListFilter(SimpleListFilter):
    title = 'Status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return CHECK_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())


class CheckTypeListFilter(SimpleListFilter):
    title = 'Type'
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return ORDER_STATUSES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(type=self.value())

class CheckAdmin(admin.ModelAdmin):
    list_filter = (CheckStatusListFilter, CheckTypeListFilter)
# Register your models here.
