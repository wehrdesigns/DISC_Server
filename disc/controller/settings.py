
#Controller Settings

TEMORARY_DATA_STORAGE_PATH = ''#hardcode a path here if needed
if TEMORARY_DATA_STORAGE_PATH == '':
    import os
    TEMORARY_DATA_STORAGE_PATH = os.path.abspath('.')
    
INTERFACES = []#if this is empty, the controller will retrieve the list of active interfaces from the disc server
POST_ACCESSCODE = '123'
CONTROLLER_NAME = 'LocalController'
CONTROLLER_PORT = '11111'
CONTROLLER_PROXY_PATH = 'controller'
HTTP_HOST = 'localhost'
HTTP_PORT = '8000'
HTTP_PROXY_PATH = 'disc'
HTTP_POST_HOST = 'localhost'
HTTP_POST_PORT = '9000'
HTTP_POST_PROXY_PATH = ''
#URL_POST_SENSOR_DATA = '/'+HTTP_POST_PROXY_PATH+'/env/post_data'
URL_POST_SENSOR_DATA = '/post_data'
HTTP_POST_TIMEOUT = 30
WEB_ACCESS_CODE = '11111'
USE_DISC_SERVER_TIME_OFFSET = False

import logging
#uncomment the desired logging level
#LOGGING_LEVEL = logging.CRITICAL
#LOGGING_LEVEL = logging.ERROR
#LOGGING_LEVEL = logging.WARNING
LOGGING_LEVEL = logging.INFO
#LOGGING_LEVEL = logging.DEBUG
#LOGGING_LEVEL = logging.NOTSET
