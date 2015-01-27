from django.conf.urls import *

urlpatterns = patterns('thermostat.views',
	url(r'^all_sensors', 'all_sensors'),
	url(r'^active_sensors', 'active_sensors'),
)
