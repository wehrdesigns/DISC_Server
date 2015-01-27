'''Copyright (c) 2014 Nathan A Wehr'''
__version__ = '1.0.0'
from Queue import Queue
import threading
import os
import sys
import time
import datetime
import random
import csv
import json
from multiprocessing import Lock
from decimal import Decimal
import TimeSeriesSqlite
#import traceback
import logging

class TimeSeriesTable_Queue():
	def __init__(self,Qin,Qout):
		"""
		Timebase: seconds, minutes, hours, days
		Functions available by queue:
			update_record
			average_seconds_for_minute
			average_minutes_for_hour
			average_hours_for_day
			stop_sqlite_engine
			calculate_start_time
			get_data_record
			get_data_records_before_time
			get_value
			get_value_date_time
		"""
		self.Qin = Qin
		self.Qout = Qout
		self.__Qcounter = 0
		self.logger = logging.getLogger(__name__+'.TimeSeriesTable_Queue')

	def q_ticket(self):
		lock = Lock()
		lock.acquire()
		try:
			self.__Qcounter += 1
			if self.__Qcounter > 65535:
				self.__Qcounter = 0
			#it might be good to clean out the queue here.  If the queue is rolling to zero, then remove stranded items between 0-32765 and when moving to 32767, remove stranded items from 32767 to 66635
		finally:
			lock.release()
			return self.__Qcounter

	def update_record(self,ID,TimeStamp,Value,timebase,Copy=None,DefaultValue=None,UpdateAverages=False):
		resp = (-1,)
		c = self.q_ticket()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('update_record put: {} {} {} {} {} {} {} {}'.format(c,str(ID),TimeStamp,Value,Copy,timebase,DefaultValue,UpdateAverages))
		self.Qin.put(('update_record',timebase,c,str(ID),TimeStamp,Value,Copy,DefaultValue,UpdateAverages))
		while resp[0] != c:
			resp = self.Qout.get()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('update_record get: '+str(resp))
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def get_data_record(self,ID,TimeStamp,timebase,DecimalPlaces=12):
		resp = (-1,)
		c = self.q_ticket()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_data_record put: {} {} {} {}'.format(c,str(ID),TimeStamp,DecimalPlaces))
		self.Qin.put(('get_data_record',timebase,c,str(ID),TimeStamp,DecimalPlaces))
		while resp[0] != c:
			resp = self.Qout.get()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_data_record get: '+str(resp))
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def get_data_records_before_time(self,ID,StopTime,Points,timebase):
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('get_data_records_before_time',timebase,c,str(ID),StopTime,Points))
		while resp[0] != c:
			resp = self.Qout.get()
		return resp[1]

	def average_seconds_for_minute(self,ID,strTimeStamp):
		timebase = ''
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('average_seconds_for_minute',timebase,c,str(ID),strTimeStamp))
		while resp[0] != c:
			resp = self.Qout.get()
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def average_minutes_for_hour(self,ID,strTimeStamp):
		timebase = ''
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('average_minutes_for_hour',timebase,c,str(ID),strTimeStamp))
		while resp[0] != c:
			resp = self.Qout.get()
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def average_hours_for_day(self,ID,strTimeStamp):
		timebase = ''
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('average_hours_for_day',timebase,c,str(ID),strTimeStamp))
		while resp[0] != c:
			resp = self.Qout.get()
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def calculate_start_time(self,StopTime,Points,timebase):
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('calculate_start_time',timebase,c,None,StopTime,Points))
		while resp[0] != c:
			resp = self.Qout.get()
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def stop_sqlite_engine(self):
		timebase = ''
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('Stop',timebase,c,None,0))
		while resp[0] != c:
			resp = self.Qout.get()
			if resp[0] != c:
				self.Qout.put(resp)
		return

	def sync_to_file(self):
		timebase = ''
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('sync_to_file',timebase,c,None,0))
		while resp[0] != c:
			resp = self.Qout.get()
			if resp[0] != c:
				self.Qout.put(resp)
		return

	def get_value(self,ID,DecimalPlaces,timebase):
		resp = (-1,)
		c = self.q_ticket()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_value put: {} {} {} {} {}'.format(timebase,c,str(ID),0,DecimalPlaces))
		self.Qin.put(('get_value',timebase,c,str(ID),0,DecimalPlaces))
		while resp[0] != c:
			resp = self.Qout.get()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_value get: '+str(resp))
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def get_value_date_time(self,ID,timebase):
		resp = (-1,)
		c = self.q_ticket()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_value_date_time put: {} {} {} {} {}'.format(timebase,c,str(ID),0,0))
		self.Qin.put(('get_value_date_time',timebase,c,str(ID),0,0))
		while resp[0] != c:
			resp = self.Qout.get()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_value_date_time get: '+str(resp))
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def update_default_value(self,ID,DefaultValue):
		resp = (-1,)
		c = self.q_ticket()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('update_default_value put: {} {} {} {} {}'.format(DefaultValue,c,str(ID),0,0))
		self.Qin.put(('update_default_value',DefaultValue,c,str(ID),0,0))
		while resp[0] != c:
			resp = self.Qout.get()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('update_default_value get: '+str(resp))
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def update_copy(self,ID,Copy):
		resp = (-1,)
		c = self.q_ticket()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('update_copy put: {} {} {} {} {}'.format(Copy,c,str(ID),0,0))
		self.Qin.put(('update_copy',Copy,c,str(ID),0,0))
		while resp[0] != c:
			resp = self.Qout.get()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('update_copy get: '+str(resp))
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def get_latest_update_from_status_table(self,ID,timebase):
		resp = (-1,)
		c = self.q_ticket()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_latest_update_from_status_table put: {} {} {} {} {}'.format(timebase,c,str(ID),0,0))
		self.Qin.put(('get_latest_update_from_status_table',timebase,c,str(ID),0,0))
		while resp[0] != c:
			resp = self.Qout.get()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_latest_update_from_status_table get: '+str(resp))
			if resp[0] != c:
				self.Qout.put(resp)
		return resp[1]

	def set_unittest_now(self,datetime):
		timebase = ''
		resp = (-1,)
		c = self.q_ticket()
		self.Qin.put(('set_unittest_now',timebase,c,None,datetime))
		while resp[0] != c:
			resp = self.Qout.get()
			if resp[0] != c:
				self.Qout.put(resp)
		return

class SqliteEngine(threading.Thread):
	'''
		Contains the sqlite database thread
		Exports input and output queues (Qin & Qout) to be used by TimeSeriesTable_Queue()
		Optional to 
	'''
	def __init__(self,
				PathToDatastore = '',
				dictInitialDefaultValues={},
				MEMORY_ONLY = True,
				USE_JOURNAL_WITH_MEMORY_DB = True,
				MINUTES_BETWEEN_COPY_MEMORY_TO_FILE = 0,
				JOURNAL_PATH = '',
				INITIALIZE_MEMORY_WITH_FILE_DATA = True,
				UnitTest=False
				):
		threading.Thread.__init__(self)
		self.__active = True
		self.MEMORY_ONLY = MEMORY_ONLY
		self.USE_JOURNAL_WITH_MEMORY_DB = USE_JOURNAL_WITH_MEMORY_DB
		self.MINUTES_BETWEEN_COPY_MEMORY_TO_FILE = MINUTES_BETWEEN_COPY_MEMORY_TO_FILE
		self.JOURNAL_PATH = JOURNAL_PATH
#		self.COPY_SECONDS_FROM_MEMORY_TO_FILE = True
		self.INITIALIZE_MEMORY_WITH_FILE_DATA = INITIALIZE_MEMORY_WITH_FILE_DATA
		self.memCM = TimeSeriesSqlite.DBConnectionManager(MemoryDB=True,PathToDatastore=PathToDatastore)
		self.memdb = TimeSeriesSqlite.TimeSeriesTable(self.memCM,UnitTest=UnitTest)
		if not self.MEMORY_ONLY:
			self.fileCM = TimeSeriesSqlite.DBConnectionManager(MemoryDB=False,PathToDatastore=PathToDatastore)
			self.filedb = TimeSeriesSqlite.TimeSeriesTable(self.fileCM,UnitTest=UnitTest)
		self.Qin = Queue()
		self.Qout = Queue()
		csv.register_dialect('csv',delimiter=',')
		self.Values = {}
		self.ValuesDateTime = {}
		self.dictInitialDefaultValues = dictInitialDefaultValues		
		self.logger = logging.getLogger(__name__+'.SqliteEngine')
		self.boolUnitTest = UnitTest
		self.unittest_datetime_now = datetime.datetime.now()
		self.PathToDatastore = PathToDatastore

	def quit(self):
		'''Stop without writing to file'''
		self.__active = False
		self.Qin.put(('',None,None,None,None))
	
	def run(self):
		while(self.__active):
			q = self.Qin.get()
			if self.logger.isEnabledFor(logging.DEBUG):
				for i in range(len(q)):
					self.logger.debug('{} {}'.format(i, q[i]))
			if not self.memCM.connection_exists(q[3]) and q[3] <> None:
#				self.Values[q[3]] = 0
#				self.ValuesDateTime[q[3]] = ''
				if self.USE_JOURNAL_WITH_MEMORY_DB:
					self.recover_from_journal('seconds',q[3])
					self.recover_from_journal('minutes',q[3])
					self.recover_from_journal('hours',q[3])
					self.recover_from_journal('days',q[3])
					self.logger.info('Finished recovering journal data for ID {}'.format(q[3]))
				if not self.MEMORY_ONLY:
					self.load_memory_db_with_initial_data('seconds',q[3],self.INITIALIZE_MEMORY_WITH_FILE_DATA)
					self.load_memory_db_with_initial_data('minutes',q[3],self.INITIALIZE_MEMORY_WITH_FILE_DATA)
					self.load_memory_db_with_initial_data('hours',q[3],self.INITIALIZE_MEMORY_WITH_FILE_DATA)
					self.load_memory_db_with_initial_data('days',q[3],self.INITIALIZE_MEMORY_WITH_FILE_DATA)
					self.logger.info('Finished configuring memory db for ID {}'.format(q[3]))
			if q[0] == 'update_record':
				self.logger.info('update_record {} {} {} {} {} {} {}'.format(q[1],q[3],q[4],q[5],q[6],q[7],q[8]))
				if q[1] == 'seconds' or q[1] == 'minutes':
					if self.USE_JOURNAL_WITH_MEMORY_DB:
						self.write_to_journal(q[1],q[3],q[4],q[5])
					resp = self.memdb.update_record(q[3],q[4],q[5],q[1],q[6],q[7],q[8])
					if not self.MEMORY_ONLY:
						self.copy_to_file_db(q[1],q[3])
						self.fileCM.db_close(q[3])
				else:
					resp = self.memdb.update_record(q[3],q[4],q[5],q[1],q[6],q[7],q[8])
					if not self.MEMORY_ONLY:
						self.copy_to_file_db(q[1],q[3])
						self.fileCM.db_close(q[3])
				self.Qout.put((q[2],resp))
			elif q[0] == 'get_data_record':
#				import pdb;pdb.set_trace()
#				print 'get_data_record',q[1],q[3],q[4],q[5]
				value = self.memdb.get_data_record(q[3],q[4],q[1],q[5])
				#the response value is 0 if nothing is found...
				#since zero is a legitimate value, maybe another value would be better?
				#or maybe it is okay because the file (below) will probably return 0 also...
				if not value and not self.MEMORY_ONLY:
					value = self.filedb.get_data_record(q[3],q[4],q[1],q[5])
					self.fileCM.db_close(q[3])
				self.Qout.put((q[2],value))
			elif q[0] == 'get_data_records_before_time':
				#check date range of memdb and retrieve remaining items from filedb
#				if q[1] == 'days': import pdb;pdb.set_trace()
				try:
					FirstMemRecord = self.memdb.get_first_time_record(q[3],q[1])
#					print q[3],'FirstMemRecord',FirstMemRecord
					if self.MEMORY_ONLY:
						data = self.memdb.get_data_records_before_time(q[3],q[4],q[5],q[1])
					else:
						StartTime = self.memdb.calculate_start_time(q[4],q[5],q[1])
						if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {} {} {}'.format(q[3],q[1],'FirstMemRecord',FirstMemRecord,'StartTime',StartTime))
						if FirstMemRecord == None:
							data = self.memdb.get_data_records_before_time(q[3],q[4],q[5],q[1])
						elif FirstMemRecord < StartTime:
							data = self.memdb.get_data_records_before_time(q[3],q[4],q[5],q[1])
						else:
							purge_time = self.get_time_now() - datetime.timedelta(seconds=(self.memdb.PurgeTimeDelta[q[1]] * self.memdb.dictTimebaseToSecondsMultiplier[q[1]]))
							if StartTime > purge_time:
								self.load_memory_db_with_initial_data(q[1],q[3],True)
								data = self.memdb.get_data_records_before_time(q[3],q[4],q[5],q[1])
							else:
								if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {} {} {}'.format(q[3],q[1],'FirstTime',FirstMemRecord,' forced to read data from file for starttime ',StartTime))
								if q[1] == 'seconds':
									self.copy_to_file_db('seconds',q[3],True)
								self.copy_to_file_db('minutes',q[3],True)
								self.copy_to_file_db('hours',q[3],True)
								self.copy_to_file_db('days',q[3],True)
								data = self.filedb.get_data_records_before_time(q[3],q[4],q[5],q[1])
								self.fileCM.db_close(q[3])
								if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('*** read data from file')
				except:
					data = []
					self.logger.exception('')
#					import sys
#					exc_type, exc_value, exc_traceback = sys.exc_info()
#					import traceback
#					traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
				self.Qout.put((q[2],data))
				#self.Qout.put((q[2],self.filedb.get_data_records_before_time(q[3],q[4],q[5])))
			elif q[0] == 'average_seconds_for_minute':
				self.Qout.put((q[2],self.memdb.average_seconds_for_minute(q[3],q[4])))
			elif q[0] == 'average_minutes_for_hour':
				self.Qout.put((q[2],self.memdb.average_minutes_for_hour(q[3],q[4])))
			elif q[0] == 'average_hours_for_day':
				self.Qout.put((q[2],self.memdb.average_hours_for_day(q[3],q[4])))
			elif q[0] == 'calculate_start_time':
				self.Qout.put((q[2],self.memdb.calculate_start_time(q[4],q[5],q[1])))
			elif q[0] == 'Stop' or q[0] == 'sync_to_file':
#				import pdb;pdb.set_trace()
				if self.USE_JOURNAL_WITH_MEMORY_DB:
					self.logger.info('Writing journal data to db file')
					for ID,c in self.memCM.dictIDconn.iteritems():	
						try:
							self.logger.info('...writing from ID '+str(ID))
							self.recover_from_journal('seconds',ID)
							self.recover_from_journal('minutes',ID)
							self.recover_from_journal('hours',ID)
							self.recover_from_journal('days',ID)
							self.fileCM.db_close(ID)
						except:
							self.logger.exception('Error while recovering ID '+str(ID))
					self.fileCM.db_close_all()
					self.logger.info('Journal recovery complete')
				else:
					if not self.MEMORY_ONLY:
						self.logger.info('Writing memory data to file')
						for ID,c in self.memCM.dictIDconn.iteritems():	
							try:
								self.logger.info(str(ID)+' copy seconds from mem to file...')
								self.copy_to_file_db('seconds',ID,True)
								self.logger.info(str(ID)+' copy minutes from mem to file...')
								self.copy_to_file_db('minutes',ID,True)
								self.logger.info(str(ID)+' copy hours from mem to file...')
								self.copy_to_file_db('hours',ID,True)
								self.logger.info(str(ID)+' copy days from mem to file...')
								self.copy_to_file_db('days',ID,True)
								self.fileCM.db_close(ID)
							except:
								self.logging.exception('Error while copying memory data to file for ID '+str(ID))
						self.fileCM.db_close_all()
						self.logger.info('Copied data from memory DB to file DB')
				self.Qout.put((q[2],0))
				if q[0] == 'Stop':
					self.__active = False
			elif q[0] == 'get_value':
				try:
					r = str(Decimal(str(self.memdb.dictLatestValue[q[3]+q[1]])).quantize(Decimal(10) ** (-1*q[5])))
				except:
					r = 0
					self.logger.warning('error retrieving: get_value')
				self.Qout.put((q[2],r))
			elif q[0] == 'get_value_date_time':
				try:
					r = self.memdb.dictLatestUpdate[q[3]+q[1]]
				except:
					r = self.get_time_now()
					self.logger.warning('error retrieving: get_value_date_time')
				self.Qout.put((q[2],r))
			elif q[0] == 'update_default_value':
				try:
					self.memdb.update_default_value(q[3],q[1])
					if not self.MEMORY_ONLY:
						self.filedb.update_default_value(q[3],q[1])
				except:
					self.logger.warning('error retrieving: update_default_value')
				finally:
					self.Qout.put((q[2],0))
			elif q[0] == 'update_copy':
				try:
					self.memdb.update_copy(q[3],q[1])
					if not self.MEMORY_ONLY:
						self.filedb.update_copy(q[3],q[1])
				except:
					self.logger.warning('error retrieving: update_copy')
				finally:
					self.Qout.put((q[2],0))
			elif q[0] == 'get_latest_update_from_status_table':
				try:
					if self.memdb.dictLatestUpdate['q[3]+q[1]'].has_key():
						dt = self.memdb.dictLatestUpdate['q[3]+q[1]']
					elif not self.MEMORY_ONLY:
						dt = self.filedb.get_latest_update_from_status_table(q[3],q[1])
				except:
					self.logger.warning('error retrieving: get_latest_update')
				finally:
					self.Qout.put((q[2],dt))
			elif q[0] == 'set_unittest_now':
				self.unittest_datetime_now = q[4]
				self.logger.info('set unittest datetime')
				self.memdb.set_unittest_now(self.unittest_datetime_now)
				if not self.MEMORY_ONLY:
					dt = self.filedb.set_unittest_now(self.unittest_datetime_now)
				self.Qout.put((q[2],0))
		self.logger.info('Exiting NOW!')
		time.sleep(1)
		os._exit(os.R_OK)

	def load_memory_db_with_initial_data(self,timebase,ID,load_mem_to_purgetime):
		'''	Load memory DB with data from file
			Load a minimum number of points (maybe 120) before the most recently updated record in the file.
			If there is no minimum restriction, load data as far back as the purge length.  Set the sync time to the most recent value in the file
			If there is no file data, set the sync time to now
			If the file data is older than the historical template length:
				fill in the file template backwards as far as the historical template length
				set the sync time to now
		'''
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Load memory db with initial data for id {}'.format(ID))
		Time2 = self.get_time_now()
		dtnow = self.get_time_now()
		try:
			defaultvalue = self.dictInitialDefaultValues[ID]
		except:
			defaultvalue = 0
		try:
			Time2 = self.filedb.get_latest_update_from_status_table(ID,timebase)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format(ID,timebase,' latest update from status table ',Time2))
			lasttime = self.filedb.get_last_record_time(ID,timebase)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format(ID,timebase,' timestamp for the last record ',lasttime))
			if lasttime:
				#Time1 = dtnow - self.filedb.get_time_delta(int(self.filedb.UnitsPerDay[timebase] * self.filedb.CreateHistoricalTemplateInDays[timebase]),timebase)
				Time1 = dtnow - self.filedb.get_time_delta(int(self.filedb.PurgeTimeDelta[timebase]),timebase)
				if lasttime < Time1:
					#create historical Template in filedb
					#There will be a break in the timeseries data that should be cleaned up if a continuous record is required
					points = self.filedb.get_points_between_time_stamps(Time1,dtnow,timebase)
					if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {} {}'.format(ID,timebase,' creating historical template in filedb with ',points,' points'))
					self.filedb.insert_template_records(ID,Time1,timebase,defaultvalue,points)
					#set sync time to now
					Time2 = dtnow
				else:
					if  lasttime < dtnow:
						#extend the template to now
						td = self.filedb.get_time_delta(1,timebase)
						points = self.filedb.get_points_between_time_stamps(lasttime+td,dtnow,timebase)
						if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {} {}'.format(ID,timebase,' creating template in filedb with ',points,' points'))
						self.filedb.insert_template_records(ID,lasttime+td,timebase,defaultvalue,points)
					#if Time2 > than the purge time or the minimum then load that data to memory
					if load_mem_to_purgetime:
						Time1 = self.memdb.calculate_start_time(dtnow,self.memdb.PurgeTimeDelta[timebase],timebase)
					else:
						Time1 = self.memdb.calculate_start_time(dtnow,120,timebase)
					if Time2 > Time1:
							data = self.filedb.get_time_data_records_between_time_stamps(ID,Time1,dtnow,timebase)
							if data:
#								print timebase+' '+str(ID)+' load memory db from '+str(Time1)
								if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {} {} {} {} {}'.format(ID,timebase,' writing ',len(data),' items from file to memory from ',data[0][0],' to ',data[-1][0]))
								self.memdb.insert_filtered_time_data_records(ID,data,timebase)
								latest_update_value_filedb = self.filedb.get_data_record(ID,Time2,timebase)
								if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format(ID,timebase,' latest_update_value_filedb ',latest_update_value_filedb))
								#initialize these values so the db initialization code does not run in the TimeSeriesSqlite update_record function
								self.memdb.update_status_table_latest_update(ID,timebase,Time2,latest_update_value_filedb)
								self.memdb.dictLastRecordTime[ID+timebase] = data[-1][0]
								if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug(timebase+' '+str(ID)+' loaded memory db to '+str(dtnow))
								if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format(ID,timebase,len(self.memdb.get_time_data_records_between_time_stamps(ID,Time1,dtnow,timebase)),' items written to memory'))
							else:
								if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug(timebase+' '+str(ID)+'  no records to load from file')
					else:
						Time2 = dtnow
			else:
				Time2 = dtnow
		except:
			self.logger.exception(timebase+' '+str(ID)+'  Error: no records loaded from file to memory')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		finally:
			self.fileCM.db_close(ID)
			self.memdb.create_sync_time(ID,Time2,timebase)
#			self.memdb.dictLatestUpdate[ID+timebase] = Time2

	def copy_to_file_db(self,timebase,ID,ForceCopy=False):
		'''Copy at a predefined interval
		Copy since last sync time in memory db
			get sync time from memory db
			if no sync time then copy the "copy interval" from memory to file
			else copy > sync time to file
			update sync time to last time written to file
		'''
#		if timebase == 'seconds' and self.COPY_SECONDS_FROM_MEMORY_TO_FILE == False:
#			return
		SyncTime = self.memdb.get_sync_time(ID,timebase)
		if not SyncTime:
			SyncTime = self.memdb.calculate_start_time(self.get_time_now(),self.memdb.IntervalMax[timebase]+1,timebase)
		latest_update = self.memdb.get_latest_update_from_status_table(ID,timebase)
		
		if SyncTime >= latest_update:
			return
		
		#randomize the sync time so that syncronization of multiple ID's does not happen in the same short time span
		syncinterval = int(random.random() * 5) + self.MINUTES_BETWEEN_COPY_MEMORY_TO_FILE
		if SyncTime <= (self.get_time_now() - datetime.timedelta(minutes=syncinterval)) or ForceCopy:
#			import pdb;pdb.set_trace()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {} {}'.format('synctime: ',SyncTime.strftime('%H:%M:%S.%f'),ID,timebase,ForceCopy))
			data = self.memdb.get_time_data_records_between_time_stamps(ID,SyncTime,latest_update,timebase)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {} {}'.format(ID,timebase,' writing ',len(data),' items to file'))
			#import pdb;pdb.set_trace()
			if data:
				try:
					if self.filedb.write_filtered_time_data_records(ID,data,timebase,True):
						#delete journal file
						try:
							fn = os.path.join(self.JOURNAL_PATH,str(ID)+'_'+timebase+'_journal.csv')
							os.remove(fn)
							self.logger.info('Deleted journal file: '+fn)
						except:
							pass
						timestamp,value = data[-1]
#						print 'Update SyncTime to:',timestamp, value
						self.memdb.update_sync_time(ID,timestamp,timebase)
						if not ForceCopy:
							#purge memory db
							self.memdb.purge_records(ID,timebase)
							if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Purged Records from Memory DB')
					else:
						self.logger.info('failed to write filtered time data records to file for ID '+str(ID))
				except:
						self.logger.exception('Error writing filtered time data records to file for ID '+str(ID))
#						exc_type, exc_value, exc_traceback = sys.exc_info()
#						traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
				finally:
					self.fileCM.db_close(ID)

	def write_to_journal(self,timebase,ID,TimeStamp,Value):
		try:
			#save to journal file
			fn = os.path.join(self.JOURNAL_PATH,str(ID)+'_'+timebase+'_journal.csv')
			f = open(fn,'ab')#w to replace contents, a to append
			writer = csv.writer(f,'csv')
			writer.writerow((Value,TimeStamp))
			f.close()
		except:
			self.logger.exception('Failed to write data to journal file '+fn)

	def recover_from_journal(self,timebase,ID):
		try:
			fn = os.path.join(self.JOURNAL_PATH,str(ID)+'_'+timebase+'_journal.csv')
			f = open(fn,'rb')
			f.close()
		except:
			self.logger.debug('No journal file to recover: '+fn)
			return
		try:
			self.logger.info('Begin recovery from journal file: '+fn)
			f = open(fn,'rb')
			reader = csv.reader(f,'csv')
			for row in reader:
				try:
					value,timestamp = row
					if value <> '' and timestamp <> '':
						self.filedb.update_record(ID,timestamp,value,timebase,None,None,True)
				except:
					self.logger.debug('recover_from_journal> continuing with next row')
			f.close()
			self.logger.info('Completed recovery from journal file: '+fn)
			os.remove(fn)
		except IOError:
			self.logger.warning('IO Error while reading journal file '+fn)
		except:
			self.logger.exception('Error while reading journal file '+fn)
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)

	def get_time_now(self):
		if not self.boolUnitTest:
			return datetime.datetime.now()
		else:
			return self.unittest_datetime_now

	def set_unittest_now(self,datetime):
		self.unittest_datetime_now = datetime


''' Items for config file

    "DATASTORE_ABSOLUTE_FOLDER_PATH": {
        "options": [], 
        "value": "", 
        "description": "Leave empty to use '<APP_BASE_PATH>/user/datastore/'.  Files stored here include <SQLITE_DB_FILENAME> as well as sqlite databases for Timeseries data."
    },

    "USE_SQLITE_QUEUED_MEMORY_MANAGER": {
        "options": ["true","false"], 
        "value": "true", 
        "description": "Turn on this option to cache data in memory before writing to file.  This may speed up data access and reduce wear on a harddrive.  Cached data is susceptible to loss by power failure if journaling is turned off."
    },
    "MEMORY_ONLY": {
        "options": ["true","false"], 
        "value": "false", 
        "description": "Only used with *USE_SQLITE_QUEUED_MEMORY_MANAGER=true*.  Set whether to only store data in memory (nothing is written to, or read from, file)."
    },

	"INITIALIZE_MEMORY_WITH_FILE_DATA": {
		"options": ["true","false"],
		"value": "true",
		"description": "Only used with *USE_SQLITE_QUEUED_MEMORY_MANAGER=true and MEMORY_ONLY=false*.  Initializes the memory cache with file data for the length defined by PurgeTimeDelta.  The system starts more slowly when set to true."
	},

    "USE_JOURNAL_WITH_MEMORY_DB": {
        "options": ["true","false"], 
        "value": "false", 
        "description": "Only used with *USE_SQLITE_QUEUED_MEMORY_MANAGER=true and MEMORY_ONLY=false*.  The Journal File contains a copy of the data in the sqlite memory database (memory cache which has not been written to the sqlite file database).  Why would I use this?  If a memory database is used to speed up data access, and reduce hard drive wear, write the journal data to a flash drive.  Don't use a journal if there is no chance of power loss or if the data lost in the time period <MINUTES_BETWEEN_COPY_MEMORY_TO_FILE> is not a concern."
    },
    "JOURNAL_PATH": {
        "options": [], 
        "value": "/tmp/journal/", 
        "description": "Only used with *USE_SQLITE_QUEUED_MEMORY_MANAGER=true* and *USE_JOURNAL_WITH_MEMORY_DB=true*."
    },

'''

