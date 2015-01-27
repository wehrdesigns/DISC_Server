from samewire.models import *
from django.contrib import admin

class MasterInline(admin.StackedInline):
	model = Master
	extra = 1

class SerfInline(admin.StackedInline):
	model = Serf
	extra = 1

class SensorInline(admin.StackedInline):
	model = Sensor
	extra = 1

class MasterAdmin(admin.ModelAdmin):
	list_display = ('Name', 'Controller', 'CommPort')
	list_diplay_links = ('Name', 'Controller')
	list_editable = ('CommPort',)
	inlines = [SerfInline,]

class SerfAdmin(admin.ModelAdmin):
#	list_display = ('Address', 'Combine_Commands', 'CRC')
	list_diplay_links = ('Address',)
	inlines = [SensorInline,]
		
class SensorAdmin(admin.ModelAdmin):
	list_display = ('Serf','DataID','Command','ScaleFactors')
	list_filter = ['Serf']
	list_editable = ('Command','ScaleFactors')
	save_as = True

Sensor.short_description = "____Samewire - Sensor list..."


class BackupDetailInline(admin.StackedInline):
	model = BackupDetail

class BackupAdmin(admin.ModelAdmin):
	list_display = ('Serf','CreationDate','FirmwareVersion','PinFunction')
	inlines = [BackupDetailInline,]

class CommandAdmin(admin.ModelAdmin):
	list_display = ('Serf','Name','Command','ValidationRegex')
	list_editable = ('Name', 'Command', 'ValidationRegex')
	list_filter = ['Serf']

admin.site.register(Master, MasterAdmin)
admin.site.register(Serf, SerfAdmin)
admin.site.register(Sensor, SensorAdmin)
admin.site.register(Backup, BackupAdmin)
admin.site.register(Command,CommandAdmin)
