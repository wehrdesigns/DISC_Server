from htmltable.models import *
from django.contrib import admin

class SensorAdmin(admin.ModelAdmin):
	list_display = ('id','HTMLTable','TableIndex','Row','Column','ScaleFactors')
	list_editable = ('TableIndex','Row','Column','ScaleFactors')

class HTMLTableAdmin(admin.ModelAdmin):
	list_display = ('id','Name','URL')
	list_editable = ('Name','URL')

admin.site.register(HTMLTable,HTMLTableAdmin)
admin.site.register(Sensor,SensorAdmin)
