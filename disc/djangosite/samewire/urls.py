from django.conf.urls import *

urlpatterns = patterns('samewire.views',
	url(r'^all_sensors', 'all_sensors'),
	url(r'^active_sensors', 'active_sensors'),
	url(r'^load_serf_power_monitor_db_configuration', 'load_serf_power_monitor_db_configuration'),
	url(r'^load_serf_power_monitor_firmware_configuration', 'load_serf_power_monitor_firmware_configuration'),
	url(r'^load_serf', 'load_serf'),
	url(r'^calibrate_sensor', 'calibrate_sensor'),
	url(r'^backup_serf', 'backup_serf'),
	url(r'^send_serf_command', 'serf_command'),
)
