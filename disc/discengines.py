import os
import sys
import threading
import time
import json
import traceback
import logging
logger = logging.getLogger(__name__)

APP_BASE_PATH = os.path.abspath('.')
sys.path.append(os.path.join(APP_BASE_PATH,'dataserver'))

sys.path.append(os.path.join(APP_BASE_PATH,'djangosite'))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "djangosite.settings")

import django
django.setup()

from django.db.models.signals import post_save
from django.dispatch import receiver
from actionlab.models import ActionLab
from env.models import *

datatable = None
#dictionary of latest values for quick reference
dictValues = {}
dictDateTime = {}
dictData = {}
dictDataType = {}
htmlloggingbuffer = None

jsondict = json.load(open(os.path.join(os.path.join(APP_BASE_PATH,'user'),'config.json'),'r'))
USE_SQLITE_QUEUED_MEMORY_MANAGER = jsondict['USE_SQLITE_QUEUED_MEMORY_MANAGER']['value'] == 'true'
START_ACTIONLABENGINE = jsondict['START_ACTIONLABENGINE']['value'] == 'true'
POST_ACCESSCODE = jsondict['POST_ACCESSCODE']['value']

def dict_initial_default_values():
	dictDefaultValues = {}
	for d in Data.objects.all().filter(Active=True):
		try:
			T = DataType.objects.get(Type = Data.objects.get(ID=d.ID).Type)
			dictDefaultValues[str(d.ID)] = str(T.DefaultValue)
		except:
			logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
	return dictDefaultValues

@receiver(post_save, sender=DataType)
def load_default_values(sender, **kwargs):
	for d in Data.objects.all().filter(Active=True):
		try:
			T = DataType.objects.get(Type = Data.objects.get(ID=d.ID).Type)
			datatable.update_default_value(d.ID,str(T.DefaultValue))
		except:
			logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
	logger.info('Loaded Default Values from Data Type model')

@receiver(post_save, sender=Data)
def load_copy(sender, **kwargs):
	for d in Data.objects.all().filter(Active=True):
		try:
			C = Data.objects.get(ID=d.ID)
			datatable.update_copy(d.ID,int(C.Copy))
		except:
			logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
	logger.info('Loaded Copy from Data model')

@receiver(post_save, sender=Data)
def load_data_model(sender, **kwargs):
	grouplist = []
	[grouplist.append(g.name) for g in Group.objects.all()]
	for d in Data.objects.all().filter(Active=True):
		try:
			model = {}
			C = Data.objects.get(ID=d.ID)
			model['Type'] = C.Type_id
			model['Name'] = C.Name
			model['Color'] = C.Color
			model['Active'] = C.Active
			model['Timebase'] = C.Timebase
			model['Period'] = C.Period
			model['Copy'] = C.Copy
			dgl = []
			for g in grouplist:
				if Data.objects.all().filter(ID=d.ID).filter(Group__name__in=[g]):
					dgl.append(g)
			model['GroupList'] = dgl
			dictData[d.ID] = model
		except:
			logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
	logger.info('Loaded Data model')
	
@receiver(post_save, sender=DataType)
def load_datatype_model(sender, **kwargs):
	for d in DataType.objects.all():
		try:
			model = {}
			C = DataType.objects.get(id=d.id)
			model['Type'] = C.Type
			model['DecimalPlaces'] = C.DecimalPlaces
			model['Units'] = C.Units
			model['DefaultValue'] = C.DefaultValue
			model['PlotYmax'] = C.PlotYmax
			model['PlotYmin'] = C.PlotYmin
			model['Boolean'] = C.Boolean
			dictDataType[C.id] = model
		except:
			logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
	logger.info('Loaded DataType model')
#	print dictDataType

@receiver(post_save, sender=ActionLab)
def ale_callback(sender, **kwargs):
	if START_ACTIONLABENGINE:
		ALE.signal_reload_modules()

if USE_SQLITE_QUEUED_MEMORY_MANAGER:
	from TimeSeriesSqlite_QdMem import SqliteEngine, TimeSeriesTable_Queue
	try:
		SE = SqliteEngine(
				PathToDatastore=os.path.join(os.path.abspath('.'),'user','datastore'),
				dictInitialDefaultValues=dict_initial_default_values(),
				MINUTES_BETWEEN_COPY_MEMORY_TO_FILE = int(jsondict['MINUTES_BETWEEN_COPY_MEMORY_TO_FILE']['value']),
				MEMORY_ONLY = (str(jsondict['MEMORY_ONLY']['value']).lower() == 'true'),
				USE_JOURNAL_WITH_MEMORY_DB = False,
				JOURNAL_PATH = '',
				INITIALIZE_MEMORY_WITH_FILE_DATA = True
			)
		SE.start()
		logger.info('Started SqliteEngine')
		
		datatable = TimeSeriesTable_Queue(Qin=SE.Qin, Qout=SE.Qout)
		loaded = True
		logger.info('Initialized TimeSeriesTable\'s')
	except:
		logger.info('error starting SqliteEngine or initializing TimeSeriesTable_Queue\'s')
else:
	import TimeSeriesSqlite
	datatable = TimeSeriesSqlite.TimeSeriesTable(TimeSeriesSqlite.DBConnectionManager(MemoryDB=False,PathToDatastore=os.path.join(APP_BASE_PATH,'user','datastore')))

load_default_values(datatable)
load_copy(datatable)
load_data_model(dictData)
load_datatype_model(dictDataType)
logger.info('Disc Engines loaded.')

if START_ACTIONLABENGINE:
	from actionlab.actionlabengine import ActionLabEngine
	ALE = ActionLabEngine()
	ALE.start()
	logger.info('Started ActionLabEngine')
