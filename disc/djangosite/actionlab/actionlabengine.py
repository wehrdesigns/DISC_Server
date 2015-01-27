from Queue import Queue
import threading, os, datetime, time, sys, socket
from threading import Lock
import logging
logger = logging.getLogger(__name__)
import numpy
import imp
import actionlab
from actionlab.models import *
import json
import traceback
from djangosite.settings import APP_BASE_PATH
#from discengines import USE_SQLITE_QUEUED_MEMORY_MANAGER
import discengines

sys.path.append(os.path.join(APP_BASE_PATH,'user'))

def get_data_from_dataid(DataID):
#	import pdb;pdb.set_trace()
	try:
		t = discengines.dictData[DataID]['Type']
		try:
			v = str(round(float(discengines.dictValues[unicode(DataID)]),int(discengines.dictDataType[t]['DecimalPlaces'])))
		except:
			v = str(discengines.dictDataType[t]['DefaultValue'])
			logger.exception('retrieving value for DataID (). returned default value'.format(DataID))
	except:
		v = 0
		logger.exception('retrieving value for DataID (). returned zero'.format(DataID))
	finally:
		return v
#	o = Data.objects.get(ID=DataID)
#	ts = datatable.calculate_start_time(datetime.datetime.now(),1+int(o.Period),o.Timebase)
#	try:
#		if USE_SQLITE_QUEUED_MEMORY_MANAGER:
#			#Get the last value stored in the Value dictionary rather than querying from memory based on a delayed timestamp
#			#first check the age of the data
#			try:
#				dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(datatable.get_value_date_time(DataID,o.Timebase),'%Y-%m-%d %H:%M:%S')))
#			except:
#				dt = ts
#			if ts < dt:
#				return float(datatable.get_value(DataID,o.Type.DecimalPlaces,o.Timebase))
#			else:
#				return float(0)
#		else:
#			value = datatable.get_data_record(DataID,ts,o.Timebase,int(o.Type.DecimalPlaces))
#			if not USE_SQLITE_QUEUED_MEMORY_MANAGER:
#				datatable.db_close(DataID)
#			return float(value)
#	except:
#		print 'error in get_dataFromID'
#		print sys.exc_type
##				print sys.exc_value
#		return float(0)


def send_socket(strMessage,formateddatetime,host,port):
#	self.msgLog += '\n'+formateddatetime+'  '+strMessage
#	host, port = "192.168.1.100", 247
	sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	try:
		# Connect to server and send data
		sock.connect((str(host), int(port)))
		sock.sendall(strMessage + "\n")

		# Receive data from the server and shut down
#			received = sock.recv(1024)
	except:
		logger.warn('unable to send message to '+host+':'+str(port))	
	finally:
		sock.close()

def get_numpy_data_from_dataid(dataid,timebase,stoptime,points):
	lock = Lock()
	with lock:
		try:
			y = datatable.get_data_records_before_time(dataid,stoptime.replace(microsecond=0),points,timebase)
			return numpy.array(y)
		except:
			logger.exception('')
			return numpy.array(range(points))
	

class ActionLabEngine(threading.Thread):
	'''
	'''
	def __init__(self):
		threading.Thread.__init__(self)
		self.logger = logging.getLogger(__name__+'.ActionLabEngine')
		self.__active = True
		self.__complete = False
		self.dictModules = {}
		self.dictModified = {}
		self.LastUpdate = {}
		self.load_modules()
		self.reload_modules = False
		self.msg = ''
		
	def load_modules(self):
		try:
			self.dictModules = {}
			self.dictModified = {}
			self.LastUpdate = {}
			for a in ActionLab.objects.exclude(Active=False):
				logger.info('Load ActionLab Module: '+str(a.Name))
#				import pdb; pdb.set_trace()
				try:					
					self.load_module(a)
				except:
					pass
		except:
			self.logger.warning('failed while loading actionlab modules')
		self.reload_modules = False

	def load_module(self,actionlabmodule):
		#m = 'actionlab.actionlabmodules.'+actionlabmodule.Module
		m = 'actionlabmodules.'+actionlabmodule.Module
		initdict = False
		if not sys.modules.has_key(m):
			logger.info('trying to import: '+str(m))
			try:
				self.actionlabmodules = __import__(m)
				self.logger.info('sucessfully imported: '+str(m))
				initdict = True
			except:
				self.logger.exception('failed to import: '+str(m))
		else:
			try:
				self.logger.info('trying to reload: '+str(m))
				eval('reload(self.'+m+')')
				self.logger.info('successfully reloaded: '+str(m))
				initdict = True
			except:
				self.logger.warn('unable to reload ... trying to reimport and reload: '+str(m))
				try:
					self.actionlabmodules = __import__(m)
					self.logger.warn('imported okay')
					eval('reload(self.'+m+')')
					self.logger.info('successfully reloaded: '+str(m))
					initdict = True
				except:
					self.logger.exception('unable to re-import and reload: '+str(m))
		if initdict:			
			self.dictModules[str(actionlabmodule.id)] = actionlabmodule.Module
			self.dictModified[str(actionlabmodule.id)] = os.path.getmtime(os.path.join(APP_BASE_PATH,'user','actionlabmodules',str(actionlabmodule.Module)+'.py'))
			self.LastUpdate[str(actionlabmodule.id)] = datetime.datetime.now()
			self.logger.info('initialized dictionaries for '+str(m))

	def signal_reload_modules(self):
		self.reload_modules = True
		self.logger.info('received signal to reload actionlab modules')
	
	def quit(self):
		self.__active = False
		while not self.__complete:
			time.sleep(0.2)
		self.logger.info('ActionLab stopped')
		
	def run(self):
		while self.__active:
			if self.reload_modules:
				self.load_modules()
			LastSecond = datetime.datetime.now().second
#			import pdb;pdb.set_trace()
			for k,m in self.dictModules.iteritems():
				AL = ActionLab.objects.get(id=k)
#				import pdb;pdb.set_trace()
				try:
					ALID = str(AL.id)
					QueryNow = False
					Timebase = AL.Timebase
					Period = int(AL.Period)
#					print ALID,self.LastUpdate[ALID],datetime.datetime.now()
					if Timebase == 'Second':
						if self.LastUpdate[ALID] <= datetime.datetime.now():
							QueryNow = True
							self.LastUpdate[ALID] = (datetime.datetime.now() + datetime.timedelta(seconds=Period)).replace(microsecond=0)
					elif Timebase == 'Minute':
						if self.LastUpdate[ALID] <= datetime.datetime.now():
							QueryNow = True
							self.LastUpdate[ALID] = (datetime.datetime.now() + datetime.timedelta(minutes=Period)).replace(second=0,microsecond=0)
					elif Timebase == 'Hour':
						if self.LastUpdate[ALID] <= datetime.datetime.now():
							QueryNow = True
							self.LastUpdate[ALID] = (datetime.datetime.now() + datetime.timedelta(hours=Period)).replace(minute=0,second=0,microsecond=0)
					elif Timebase == 'Day':
						if self.LastUpdate[ALID] <= datetime.datetime.now():
							QueryNow = True
							self.LastUpdate[ALID] = (datetime.datetime.now() + datetime.timedelta(days=Period)).replace(hour=0,minute=0,second=0,microsecond=0)
	
					if QueryNow:
#						self.print1("execute: "+AL.Name)
						#check if module was modified
						m = 'actionlabmodules.'+str(AL.Module)
						if not sys.modules.has_key(m):
							self.load_module(AL)
						else:
							if self.dictModified[ALID] != os.path.getmtime(os.path.join(APP_BASE_PATH,'user','actionlabmodules',str(AL.Module)+'.py')):
								self.load_module(AL)
						eval('self.'+m+'.ComputeAndAct(datatable)')
						self.logger.info('executed: '+AL.Name)
						
				except KeyboardInterrupt:
					raise KeyboardInterrupt
				except:
					self.logger.error('Error while processing '+AL.Name)
#					self.print1(str(sys.exc_type))

			while datetime.datetime.now().second == LastSecond and self.__active:
				time.sleep(0.2)
						
		self.__complete = True

from discengines import datatable
