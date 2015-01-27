# Django settings for djangosite project.

import os, json

APP_BASE_PATH = os.path.abspath('.')
if APP_BASE_PATH.rfind('djangosite') > -1:
    APP_BASE_PATH = os.path.split(os.path.abspath('.'))[0]
    
jsondict = json.load(open(os.path.join(os.path.join(APP_BASE_PATH,'user'),'config.json'),'r'))
HTTP_PROXY_PATH = jsondict['HTTP_PROXY_PATH']['value']
DATASTORE_ABSOLUTE_FOLDER_PATH = ''#jsondict['DATASTORE_ABSOLUTE_FOLDER_PATH']['value']
SQLITE_DB_FILENAME = jsondict['SQLITE_DB_FILENAME']['value']
DEBUG = jsondict['DJANGO_DEBUG']['value'] == 'true'

TEMPLATE_DEBUG = DEBUG

database = APP_BASE_PATH+'/user/datastore/'+SQLITE_DB_FILENAME
if DATASTORE_ABSOLUTE_FOLDER_PATH != '':
    database = os.path.join(DATASTORE_ABSOLUTE_FOLDER_PATH,SQLITE_DB_FILENAME)

ADMINS = (
    # ('DISC User', 'user@disc.net'),
)

ALLOWED_HOSTS = ['localhost','192.168.254.7']

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': database,                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/New_York'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False
    #Turned this off because the timestamps from Sqlite are not timezone aware and it caused conflicts

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = APP_BASE_PATH+'/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/'+HTTP_PROXY_PATH+'/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = APP_BASE_PATH+'/static/'

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/'+HTTP_PROXY_PATH+'/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    #APP_BASE_PATH+'/static_for_apps/',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '3x@7=cejk2tsppds7w0omx2v&amp;g077u7bc0o5=lp(t6kz5151347'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
#    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'djangosite.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'djangosite.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    APP_BASE_PATH+'/html',
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
#    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    'django.contrib.admindocs',
#    'south',
    'env',
    'samewire',
    'htmltable',
    'thermostat',
    'actionlab',
#    'epiceditor',
)

LOGIN_URL = '/'+HTTP_PROXY_PATH+'/login/'
LOGIN_REDIRECT_URL = '/'+HTTP_PROXY_PATH+'/'

#this is needed so the request context can be passed to a django template
from django.conf.global_settings import TEMPLATE_CONTEXT_PROCESSORS as TCP
TEMPLATE_CONTEXT_PROCESSORS = TCP + (
    'django.core.context_processors.request',
)



