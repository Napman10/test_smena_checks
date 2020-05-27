from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from .models import Printer, Check, ORDER_STATUSES, CHECK_TYPES

admin.site.register(Printer)

#фильтр чеков по статусу
class CheckStatusListFilter(SimpleListFilter):
    title = 'status'
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return ORDER_STATUSES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())

#фильтр чеков по типу
class CheckTypeListFilter(SimpleListFilter):
    title = 'type'
    parameter_name = 'ctype'

    def lookups(self, request, model_admin):
        return CHECK_TYPES

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(ctype=self.value())

#в лист фильтре находится фиьты по типу и статусу
#также по всем полям можно сортировать, включая сортировку по принтеру
@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ('id','printer_id', 'ctype', 'status',)
    list_filter = (CheckStatusListFilter, CheckTypeListFilter,)
    search_fields = ('id','printer_id__name', 'ctype', 'status',)
