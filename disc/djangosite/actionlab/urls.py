from django.conf.urls import *

urlpatterns = patterns('actionlab.views',
	url(r'^output', 'output'),
	url(r'^edit_module','edit_module'),
)
