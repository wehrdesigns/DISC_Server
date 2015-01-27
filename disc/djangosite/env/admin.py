from env.models import *
from django.contrib import admin

def set_zero_copy(modeladmin, request, queryset):
	queryset.update(Copy='0')
def set_copy_foward_10pts(modeladmin, request, queryset):
	queryset.update(Copy='10')
def set_copy_foward_60pts(modeladmin, request, queryset):
	queryset.update(Copy='60')
def set_copy_foward_180pts(modeladmin, request, queryset):
	queryset.update(Copy='180')
def set_copy_back_10pts(modeladmin, request, queryset):
	queryset.update(Copy='-10')
def set_copy_back_60pts(modeladmin, request, queryset):
	queryset.update(Copy='-60')
def set_copy_back_180pts(modeladmin, request, queryset):
	queryset.update(Copy='-180')
def set_period_1(modeladmin, request, queryset):
	queryset.update(Period='1')
def set_period_2(modeladmin, request, queryset):
	queryset.update(Period='2')
def set_period_3(modeladmin, request, queryset):
	queryset.update(Period='3')
def set_period_5(modeladmin, request, queryset):
	queryset.update(Period='5')
def set_period_10(modeladmin, request, queryset):
	queryset.update(Period='10')
def set_period_20(modeladmin, request, queryset):
	queryset.update(Period='20')
def set_period_30(modeladmin, request, queryset):
	queryset.update(Period='30')
def set_period_40(modeladmin, request, queryset):
	queryset.update(Period='40')
	
class DataTypeAdmin(admin.ModelAdmin):
	list_display = ('Type','DecimalPlaces','Units','DefaultValue','PlotYmax','PlotYmin','Boolean')
	list_editable = ('DecimalPlaces','PlotYmax','PlotYmin','Boolean')

class DataAdmin(admin.ModelAdmin):
	list_display = ('ID', 'Type', 'Name', 'Active', 'Timebase', 'Period', 'Copy', 'Color')
	list_filter = ['Active', 'Timebase', 'Type']
	list_editable = ('Type', 'Name', 'Color', 'Timebase', 'Active')
	actions = [set_zero_copy,
				set_copy_foward_10pts,
				set_copy_foward_60pts,
				set_copy_foward_180pts,
				set_copy_back_10pts,
				set_copy_back_60pts,
				set_copy_back_180pts,
				set_period_1,
				set_period_2,
				set_period_3,
				set_period_5,
				set_period_10,
				set_period_20,
				set_period_30,
				set_period_40]

class ControllerAdmin(admin.ModelAdmin):
	list_display = ('Name','Host','Port','Path')
	list_editable = ('Host','Port','Path')

admin.site.register(DataType, DataTypeAdmin)
admin.site.register(Data, DataAdmin)

admin.site.register(Controller, ControllerAdmin)
