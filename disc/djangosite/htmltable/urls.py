from django.conf.urls import *

urlpatterns = patterns('htmltable.views',
	url(r'^all_sensors', 'all_sensors'),
	url(r'^active_sensors', 'active_sensors'),
	url(r'^parse_and_index_htmltable','parse_and_index_htmltable'),
)
