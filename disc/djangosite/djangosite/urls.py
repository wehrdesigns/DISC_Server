from django.conf.urls import *

#these two for serving static files
from django.conf import settings
from django.conf.urls.static import static

from django.contrib import admin
from django.contrib.auth.views import login
admin.autodiscover()
#from djangosite.views import login_fix
import djangosite.settings

pp = '^'+djangosite.settings.HTTP_PROXY_PATH

urlpatterns = patterns('',
        url(pp+r'/admin/login/', login,name='login'),
        url(pp+r'/admin/doc/', include('django.contrib.admindocs.urls')),
        url(pp+r'/admin/', include(admin.site.urls), name='admin:index'),
        url(pp+r'/media/(?P<path>.*)$', 'django.views.static.serve',{'document_root': djangosite.settings.MEDIA_ROOT}),
        url(pp+r'/static/(?P<path>.*)$', 'django.views.static.serve',{'document_root': djangosite.settings.STATIC_ROOT}),
        url(pp+r'/env/', include('env.urls')),
        url(pp+r'/actionlab/', include('actionlab.urls')),
        url(pp+r'/samewire/', include('samewire.urls')),
        url(pp+r'/htmltable/', include('htmltable.urls')),
        url(pp+r'/thermostat/', include('thermostat.urls')),
        url(pp+r'/servertime$', 'djangosite.views.servertime'),

        url(pp+r'/logout', 'djangosite.views.logout'),
        url(pp+r'/login', 'djangosite.views.login'),
        url(pp+r'/', 'env.views.index'),
)# + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
