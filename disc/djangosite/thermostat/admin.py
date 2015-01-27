from thermostat.models import *
from django.contrib import admin

class ThermostatAdmin(admin.ModelAdmin):
	list_display = ('Controller','Name','CommPort','Baudrate')
	list_editable = ('CommPort', 'Baudrate')

class SensorAdmin(admin.ModelAdmin):
	list_display = ('Thermostat','DataID','Command','ResponseTermination','Slice','ScaleFactors')
	list_editable = ('Command', 'ScaleFactors')


admin.site.register(Thermostat,ThermostatAdmin)
admin.site.register(Sensor,SensorAdmin)
