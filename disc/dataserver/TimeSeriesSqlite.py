'''Copyright (c) 2014 Nathan A Wehr'''
__version__ = '1.0.0'
import os
import sys
import sqlite3
import datetime
import time
from decimal import Decimal
import logging

class TimeSeriesTable():
	def __init__(self, ConnectionManager, UnitTest=False):
		self.CM = ConnectionManager
		self.dictLatestValue = {}
		self.dictLatestUpdate = {}
		self.dictLastRecordTime = {}
		self.UnitsPerDay = {'seconds':86400,'minutes':1440,'hours':24,'days':1}
		self.dictOldDataUpdated = {} #This is a flag 0/1, it is set if data is updated that is equal to or older than the latest update
		self.dictTimebaseToSecondsMultiplier = {'seconds':1,'minutes':60,'hours':3600,'days':86400}
		self.IntervalMax = {'seconds':59,'minutes':59,'hours':23,'days':999}
		self.PurgeTimeDelta = {'seconds':3600,'minutes':11520,'hours':744,'days':90}
		self.CreateHistoricalTemplateInDays = {'seconds':0.1,'minutes':3,'hours':7,'days':90}
		self.TemplateExtensionDaysOfRecords = {'seconds':0.003,'minutes':0.5,'hours':7,'days':90}
		self.CloseNow = False and not self.CM.Memory #It is inefficient to close the database immediately if it might be accessed several times (close it at a higher level if possible).  If might be accessed by multiple sources, then it is best to close it as soon as possible.
		self.dictDefaultValue = {}
		self.dictCopy = {}
		self.dictNextInterval = {'seconds':'minutes','minutes':'hours','hours':'days','days':''}
		self.MinimumInitData = False
		self.dictUpdateList = {'seconds':['minutes','hours','days'],'minutes':['hours','days'],'hours':['days'],'days':[]}
		self.logger = logging.getLogger(__name__+'.TimeSeriesTable')
		self.boolUnitTest = UnitTest
		self.unittest_datetime_now = datetime.datetime.now()

	def format_time_stamp(self,TimeStamp,timebase):
		if str(type(TimeStamp)) <> '<type \'datetime.datetime\'>':
			TimeStamp = self.string_to_time(TimeStamp)
		if timebase == 'seconds': return TimeStamp.replace(microsecond=0)
		if timebase == 'minutes': return TimeStamp.replace(second=0,microsecond=0)
		if timebase == 'hours': return TimeStamp.replace(minute=0,second=0,microsecond=0)
		if timebase == 'days': return TimeStamp.replace(hour=0,minute=0,second=0,microsecond=0)

	def get_time_delta(self,Units,timebase):
		if timebase == 'seconds': return datetime.timedelta(seconds=Units)
		if timebase == 'minutes': return datetime.timedelta(minutes=Units)
		if timebase == 'hours': return datetime.timedelta(hours=Units)
		if timebase == 'days': return datetime.timedelta(days=Units)

	def get_units_from_time_delta(self, MyTimeDelta,timebase):
		if timebase == 'seconds': return int(MyTimeDelta.total_seconds())
		if timebase == 'minutes': return int(MyTimeDelta.total_seconds()/60)
		if timebase == 'hours': return int(MyTimeDelta.total_seconds()/3600)
		if timebase == 'days': return int(MyTimeDelta.total_seconds()/86400)

	def get_unit(self,TimeStamp,timebase):
		if timebase == 'seconds': return TimeStamp.second
		if timebase == 'minutes': return TimeStamp.minute
		if timebase == 'hours': return TimeStamp.hour
		if timebase == 'days': return TimeStamp.day

	def string_to_time(self,stringTimeStamp):
		return datetime.datetime.fromtimestamp(time.mktime(time.strptime(stringTimeStamp,'%Y-%m-%d %H:%M:%S')))

	def string_to_time2(self,stringTimeStamp):
		return datetime.datetime.fromtimestamp(time.mktime(time.strptime(stringTimeStamp,'%m/%d/%Y %H:%M:%S')))

	def insert_template_records(self,ID,StartTime,timebase,DefaultValue=0,points=0):
		try:
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Inserting template records for '+str(points)+' points on table '+timebase[0:1]+'data')
			StartTime = self.format_time_stamp(StartTime,timebase)
			cur = self.CM.connect_to_db(ID).cursor()
			ts = StartTime
			td = self.get_time_delta(1,timebase)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Inserting Template Records starting:'+str(ts))
			for i in range(points):
	#			print 'insert_template_records:',ID,ts
				cur.execute('insert into '+timebase[0:1]+'data (ts, v) values (?, ?)', (ts, DefaultValue))
				ts += td
			self.CM.connect_to_db(ID).commit()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Insert Template Records complete. Extension to: '+str(ts))
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		finally:
			if self.CloseNow:
				self.CM.db_close(ID)

	def get_first_time_record(self,ID,timebase):
		try:
			dt = None
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select ts from '+timebase[0:1]+'data order by ts asc limit 1')
			row = cur.fetchone()
			if row:
				dt = row[0]
			if self.CloseNow:
				self.CM.db_close(ID)
			return dt
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		finally:
			if self.CloseNow:
				self.CM.db_close(ID)
			return dt

	def get_last_record_time(self,ID,timebase):
		try:
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select ts from '+timebase[0:1]+'data order by ts desc limit 1')
			row = cur.fetchone()
			if row:
				dt = row[0]
			else:
				dt = self.get_time_now()
			if self.CloseNow:
				self.CM.db_close(ID)
			self.dictLastRecordTime[ID+timebase] = dt
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_last_record_time:'+str(ID)+str(self.dictLastRecordTime[ID+timebase]))
			return dt
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
			if self.CloseNow:
				self.CM.db_close(ID)
			return self.get_time_now()

	def get_latest_update_from_status_table(self, ID,timebase):
		try:
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select LatestUpdate from status where TableName=?', (timebase[0:1]+'data',))
			row = cur.fetchone()
			if row:
				dt = row[0]
			else:
				dt = self.get_time_now()
			self.dictLatestUpdate[ID+timebase] = dt
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug(str(ID)+' get_latest_update_from_status_table '+str(self.dictLatestUpdate[ID+timebase]))
			if self.CloseNow:
				self.CM.db_close(ID)
			return dt
		except:
			self.dictLatestUpdate[ID+timebase] = self.get_time_now()
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
			if self.CloseNow:
				self.CM.db_close(ID)
			return self.get_time_now()

	def init_id(self,ID,TimeStamp,timebase):
		''' Initialize the data table, the Status table and the quick reference dictionaries

			1)Verify that this ID is in the database
			2)If it does not exist, initialize the data table with a value 1 week before the timestamp
				(most likely the timestamp is approximately now() so the template will be filled out with records)
			3)Update quick reference dictionaries (dictLatestUpdate, dictLatestValue, dictLastRecordTime)
		'''
		try:
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Initializing ID: '+str(ID)+' for interval table '+timebase[0:1]+'data')
			TimeStamp = self.format_time_stamp(TimeStamp,timebase)
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select ts from '+timebase[0:1]+'data order by ts desc limit 1')
			row = cur.fetchone()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('GetRecord: {} {} {} {}'.format(ID,TimeStamp,row,timebase[0:1]+'data'))
			dv = self.get_default_value(ID)
			if not row:
				if self.MinimumInitData:
					ts = TimeStamp
				else:
					ts = TimeStamp - self.get_time_delta(int(self.UnitsPerDay[timebase] * self.CreateHistoricalTemplateInDays[timebase]),timebase)
				cur.execute('insert into '+timebase[0:1]+'data (ts, v) values (?, ?)', (ts , dv))
				self.CM.connect_to_db(ID).commit()
			lrt = self.get_last_record_time(ID,timebase)
	#		self.dictLastRecordTime[ID+timebase] = lrt
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select LatestUpdate from status where TableName=?', (timebase[0:1]+'data',))
			row = cur.fetchone()
			if not row:
				cur.execute('insert into status values (?,?)', (timebase[0:1]+'data',TimeStamp))
				self.CM.connect_to_db(ID).commit()
			lts = self.get_latest_update_from_status_table(ID,timebase)
			self.dictLatestValue[ID+timebase] = self.get_data_record(ID,lts,timebase)
			if self.CloseNow:
				self.CM.db_close(ID)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('** Initialized: {} {} {} {}'.format(ID,self.dictLastRecordTime[ID+timebase],self.dictLatestUpdate[ID+timebase],self.CM))
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)

	def update_record(self,ID,TimeStamp,Value,timebase,Copy=None,DefaultValue=None,UpdateAverages=False):
		''' update_record initializes the tables and dictionaries for an ID and self extends the template

			If there more that 1 unit interval between the timestamp and the last timestamp, the present value
			will be copied backwards to fill the space between these timestamps

			return True if the interval is 59 (for second, minute, hour) or 23 for day
			OR if a value was copied back over this interval
			return False otherwise
		'''
		try:
#			import pdb;pdb.set_trace()
			#force the value to numeric
			try:
				Value = str(float(Value))
			except:
				Value = 0
			if Copy == None:
				Copy = self.get_copy(ID)
			else:
				Copy = int(Copy)				
			if DefaultValue == None:
				DefaultValue = self.get_default_value(ID)
			else:
				try:
					DefaultValue = str(float(DefaultValue))
				except:
					DefaultValue = '0'
			self.isOldDataUpdated = False
			TimeStamp = self.format_time_stamp(TimeStamp,timebase)
			TimeStamp_now = self.format_time_stamp(self.get_time_now(),timebase)
			if TimeStamp > TimeStamp_now:
				self.logger.warning('for '+str(ID)+' error: *attempt to update a value in the future*; '+'timestamp '+str(TimeStamp)+'; now '+str(TimeStamp_now)+'; --forcing timestamp to now for value '+str(Value))
				TimeStamp = TimeStamp_now
			self.isIntervalMax = False
			if self.get_unit(TimeStamp,timebase) == self.IntervalMax[timebase]:
				self.isIntervalMax = True
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Update Record TimeStamp '+str(TimeStamp)+' in table '+timebase[0:1]+'data')
			#Check that ID is initalized in tables and dictionaries
			if not self.dictLatestUpdate.has_key(ID+timebase) or not self.dictLastRecordTime.has_key(ID+timebase) or not self.dictLatestValue.has_key(ID+timebase):
				self.init_id(ID,TimeStamp,timebase)
			while (self.dictLastRecordTime[ID+timebase] - TimeStamp) <= self.get_time_delta(1,timebase):
	#			print self.dictLastRecordTime[ID+timebase], TimeStamp, str(self.dictLastRecordTime[ID+timebase] - TimeStamp), self.get_time_delta(1,timebase)
				self.extended_template(ID,timebase,DefaultValue,DaysOfRecords=0)
			self.isNextInterval = False
			if timebase != 'days':
				ts_interval = self.get_unit(TimeStamp,self.dictNextInterval[timebase])
				last_interval = self.get_unit(self.dictLatestUpdate[ID+timebase],self.dictNextInterval[timebase])
				if ts_interval > last_interval:
					self.isNextInterval = True
				if ts_interval == 0 and ts_interval < last_interval:
					self.isNextInterval = True
			#Update Table Here
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('update '+timebase[0:1]+'data SET v=? WHERE ts=?', (Value,TimeStamp))
			self.CM.connect_to_db(ID).commit()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Update: {} {} {} {} {}'.format(timebase[0:1]+'data',Value,ID,TimeStamp,self.CM.connect_to_db(ID)))
			#If the unit interval is more than 1 then copy this value backwards
			if (TimeStamp - self.dictLatestUpdate[ID+timebase]) > self.get_time_delta(1,timebase) and Copy <> 0:
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Copy required for ID: '+str(ID))
				td = self.get_time_delta(1,timebase) #timedelta for a single time unit
				ctd = self.get_time_delta(abs(Copy),timebase) #copy timedelta
				mdstd = TimeStamp - self.dictLatestUpdate[ID+timebase] #missing data segment time delta - time between the timestamp and the last update
				if Copy < 0:#Copy the new value backward
					CopyValue = Value #Copy new value backward
					CopyStopTime = TimeStamp #The stop time is the timestamp
					if mdstd < ctd: #if the time since the last update is less than length that might be filled then use the smaller timedelta
						ts = TimeStamp - mdstd
					else:
						ts = TimeStamp - ctd
				else:#Copy the last value forward
					CopyValue = self.dictLatestValue[ID+timebase] #Copy last value forward
					ts = self.dictLatestUpdate[ID+timebase]
					if mdstd < ctd: #if the
						CopyStopTime = ts + mdstd - td #don't copy over the latest value that has already been recorded
					else:
						CopyStopTime = ts + ctd
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Copy starting at time stamp:'+str(ts))
				its = ts #iterate stop time
				while (CopyStopTime > its):
					its = its + td
					cur.execute('update '+timebase[0:1]+'data SET v=? WHERE ts=?', (CopyValue,its))
					if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug("Copying {}{}{}".format(CopyValue,' to ',its))
				self.CM.connect_to_db(ID).commit()
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Copy complete. Copied value '+str(CopyValue)+' between: '+str(ts)+' and '+str(CopyStopTime))
#				if (self.get_units_from_time_delta(CopyStopTime-ts,timebase) > self.IntervalMax[timebase]):# or (self.get_unit(ts,timebase) < self.get_unit(CopyStopTime,timebase)):
#					self.isIntervalMax = True

			if self.dictLatestUpdate[ID+timebase] <= TimeStamp:
				cur.execute('update status SET LatestUpdate=? WHERE TableName=?', (TimeStamp,timebase[0:1]+'data'))
				self.CM.connect_to_db(ID).commit()
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Update status: {} {} {}'.format(TimeStamp,ID,timebase[0:1]+'data'))
				self.dictLatestUpdate[ID+timebase] = TimeStamp
				self.dictLatestValue[ID+timebase] = Value
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format(ID,' LatestValue, LatestUpdate: ',self.dictLatestValue[ID+timebase],self.dictLatestUpdate[ID+timebase]))
			else:
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{}{}{}'.format(ID,' The TimeStamp is < the LatestUpdate: ',str(self.dictLatestUpdate[ID+timebase])))
				self.isOldDataUpdated = True
			if self.CloseNow:
				self.CM.db_close(ID)
#			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format(ID,self.isIntervalMax,self.isNextInterval,self.isOldDataUpdated))
			sync_setback = False
			if UpdateAverages:
#				import pdb;pdb.set_trace()
				try:
					for updatetimebase in self.dictUpdateList[timebase]:
						formatted_timestamp = self.format_time_stamp(TimeStamp,updatetimebase)
						if self.dictLatestUpdate.has_key(ID+updatetimebase):
							latestupdate = self.dictLatestUpdate[ID+updatetimebase]
						else:
							latestupdate = self.get_latest_update_from_status_table(ID,updatetimebase)
						#check if updating old data
						if self.isOldDataUpdated:
							if formatted_timestamp < latestupdate:
								if updatetimebase == 'minutes':avevalue = str(self.average_seconds_for_minute(ID,TimeStamp))
								elif updatetimebase == 'hours':avevalue = str(self.average_minutes_for_hour(ID,TimeStamp))
								elif updatetimebase == 'days':avevalue = str(self.average_hours_for_day(ID,TimeStamp))
								self.update_record(ID,TimeStamp,avevalue,TimeStamp,None,None,False)
#								print 'ave:',TimeStamp,timebase,updatetimebase,avevalue,'update old data'
								sync_setback = True
						else:
							#calc the number of points to update in the larger timebase
#							print 'latest update',updatetimebase,self.dictLatestUpdate[ID+updatetimebase]
#							print 'formatted timebase,',updatetimebase,formatted_timestamp
							points = self.get_points_between_time_stamps(latestupdate,formatted_timestamp,updatetimebase)
							for p in range(points,0,-1):
#								print 'ave point',p
								updatetimestamp = self.calculate_start_time(TimeStamp,p,updatetimebase)
								if updatetimebase == 'minutes':avevalue = str(self.average_seconds_for_minute(ID,updatetimestamp))
								elif updatetimebase == 'hours':avevalue = str(self.average_minutes_for_hour(ID,updatetimestamp))
								elif updatetimebase == 'days':avevalue = str(self.average_hours_for_day(ID,updatetimestamp))
								self.update_record(ID,TimeStamp,avevalue,updatetimebase,None,None,False)
#								print 'ave:',TimeStamp,timebase,updatetimebase,avevalue
				except:
					self.logger.exception('')
#					exc_type, exc_value, exc_traceback = sys.exc_info()
#					traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
			return sync_setback#(self.isIntervalMax,self.isNextInterval,self.isOldDataUpdated)
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
			return False#(False,False,False)

	def extended_template(self,ID,timebase,DefaultValue=0,DaysOfRecords=0):
		#force the DefaultValue to numeric
		try:
			DefaultValue = str(float(DefaultValue))
		except:
			DefaultValue = '0'
#		cur = self.CM.connect_to_db(ID).cursor()
		lts = self.get_last_record_time(ID,timebase)
		nts = lts + self.get_time_delta(1,timebase)
		if DaysOfRecords == 0:
				DaysOfRecords = self.TemplateExtensionDaysOfRecords[timebase]
		points = int(self.UnitsPerDay[timebase]*DaysOfRecords)
		self.insert_template_records(ID,nts,timebase,DefaultValue,points)
#		if self.CloseNow:
#			self.CM.db_close(ID)

	def get_data_record(self,ID,TimeStamp,timebase,DecimalPlaces=12):
		try:
			TimeStamp = self.format_time_stamp(TimeStamp,timebase)
#			print ID,TimeStamp,timebase,DecimalPlaces,'get_data_record'
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select v from '+timebase[0:1]+'data where ts=?', (TimeStamp,))
			row = cur.fetchone()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_data_record: {} {} {} {} {}'.format(ID,TimeStamp,row,timebase[0:1]+'data',self.CM.connect_to_db(ID)))
			if row:
				resp = row[0]
			else:
				try:
					#check larger timebases
					resp = self.try_larger_get_data_record(ID,TimeStamp,timebase,DecimalPlaces)
				except:
					resp = self.get_default_value(ID)
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
			resp = self.self.get_default_value(ID)
		finally:
			if self.CloseNow:
				self.CM.db_close(ID)
			D = Decimal
			return str(D(str(resp)).quantize(Decimal(10) ** (-1*DecimalPlaces)))

	def try_larger_get_data_record(self,ID,TimeStamp,timebase,DecimalPlaces=12):
		try_timebase,source_points = self.get_larger_timebase(timebase,Points)
		v = None
		while try_timebase and v == None:
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Try timebase '+try_timebase+' for ID '+str(ID))
			resp = self.get_data_record(ID,TimeStamp,try_timebase,DecimalPlaces)
			if resp:
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Found data at timebase '+try_timebase+' for ID '+str(ID)+' to use at timebase '+timebase)
				v = resp
				break
			try_timebase,source_points = self.get_larger_timebase(try_timebase,1)
		if v == None:
			return self.self.get_default_value(ID)
		else:
			return v

	def get_time_data_records(self,ID,StartTime,Points,timebase,DecimalPlaces=12):
		lst = []
		D = Decimal
		try:
			StartTime = self.format_time_stamp(StartTime,timebase)
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select ts, v from '+timebase[0:1]+'data where ts>=? order by ts asc limit ?', (StartTime,Points))
			for i in range(Points):
				row = cur.fetchone()
				if row:
					lst.append((row[0],str(D(str(row[1])).quantize(Decimal(10) ** (-1*DecimalPlaces)))))
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		finally:
			if self.CloseNow:
				self.CM.db_close(ID)
			return lst

	def get_points_between_time_stamps(self,StartTime,StopTime,timebase):
		ts = (StopTime - StartTime).total_seconds()
		if timebase == 'seconds':
			points = int(ts)
		if timebase == 'minutes':
			points = int(ts/60)
		if timebase == 'hours':
			points = int(ts/3600)
		if timebase == 'days':
			points = int(ts/3600/24)
		return points

	def get_time_data_records_between_time_stamps(self,ID,StartTime,StopTime,timebase):
		points = self.get_points_between_time_stamps(StartTime,StopTime,timebase)
		return self.get_time_data_records(ID,StartTime,points,timebase)

	def calculate_start_time(self,StopTime,Points,timebase):
		return self.format_time_stamp(StopTime,timebase) - self.get_time_delta(Points,timebase)

	def get_time_data_records_before_time(self,ID,StopTime,Points,timebase):
		StartTime = self.calculate_start_time(StopTime,Points,timebase)
		return self.get_time_data_records(ID,StartTime,Points,timebase)

	def get_data_records(self,ID,StartTime,Points,timebase,DecimalPlaces=12):
		lst = []
		StartTime = self.format_time_stamp(StartTime,timebase)
		try:
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select v from '+timebase[0:1]+'data where ts>=? order by ts asc limit ?', (StartTime,Points))
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_data_records: {} {} {}'.format(ID,timebase[0:1]+'data',self.CM.connect_to_db(ID)))
			row = cur.fetchall()
			if row == []:
				row = self.try_larger_get_data_records(ID,StartTime,Points,timebase,DecimalPlaces)
			if self.CloseNow:
				lst = [v[0] for v in row]
				self.CM.db_close(ID)
			else:
				lst = [v[0] for v in row]
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		finally:
			return lst

	def try_larger_get_data_records(self,ID,StartTime,Points,timebase,DecimalPlaces=12):
		try:
			lst = []
			try_timebase,source_points = self.get_larger_timebase(timebase,Points)
			while try_timebase and lst == []:
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Try timebase '+try_timebase+' for ID '+str(ID))
				lst = self.get_data_records(ID,StartTime,source_points,try_timebase,DecimalPlaces)
				if lst:
					if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Found data at timebase '+try_timebase+' for ID '+str(ID))
					lst = self.interpolate_for_lower_timebase(StartTime,try_timebase,lst,timebase,Points)
					if self.logger.isEnabledFor(logging.DEBUG):
						if lst:
							if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Interpolated data from timebase '+try_timebase+' for ID '+str(ID)+' at timebase '+timebase)
					break
				try_timebase,source_points = self.get_larger_timebase(try_timebase,source_points)
		except:
			self.logger.exception('')
#			exc_type, exc_value, exc_traceback = sys.exc_info()
#			traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		finally:
			return lst

	def get_data_records_before_time(self,ID,StopTime,Points,timebase):
		StartTime = self.calculate_start_time(StopTime,Points,timebase)
		return self.get_data_records(ID,StartTime,Points,timebase)

	def get_data_records_between_time_stamps(self,ID,StartTime,StopTime,timebase):
		ts = (StopTime - StartTime).total_seconds()
		if timebase == 'seconds':
			points = int(ts)
		if timebase == 'minutes':
			points = int(ts/60)
		if timebase == 'hours':
			points = int(ts/3600)
		if timebase == 'days':
			points = int(ts/3600/24)
		#include the value at the StopTime record
		points += 1
		return self.get_data_records(ID,StartTime,points,timebase)

	def average_seconds_for_minute(self,ID,strTimeStamp):
		'''Accepts a timestamp anywhere within the Minute to be averaged. Averages seconds 0-59'''
		try:
			timebase = 'seconds'
			TimeStamp = self.format_time_stamp(strTimeStamp,'minutes')
	#		TimeStamp = TimeStamp.replace(second=0,microsecond=0)
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select v from sdata where ts>=? order by ts asc limit ?', (TimeStamp,60))
			s = 0
			for i in range(60):
				row = cur.fetchone()
				if not row:
					logger.warning('Failed to average all seconds for ID {} at timestamp {}'.formate(ID,strTimeStamp))
					break
				s += row[0]
			if self.CloseNow:
				self.CM.db_close(ID)
			return s/60
		except:
			self.logger.exception('')			
			return self.get_default_value(ID)

	def average_minutes_for_hour(self,ID,strTimeStamp):
		'''Accepts a timestamp anywhere within the hour to be averaged. Averages minutes 0-59'''
		try:
			timebase = 'minutes'
			TimeStamp = self.format_time_stamp(strTimeStamp,'hours')
	#		TimeStamp = TimeStamp.replace(minute=0,second=0,microsecond=0)
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select v from mdata where ts>=? order by ts asc limit ?', (TimeStamp,60))
			s = 0
			for i in range(60):
				row = cur.fetchone()
				if not row:
					logger.warning('Failed to average all minutes for ID {} at timestamp {}'.formate(ID,strTimeStamp))
					break
				s += row[0]
			if self.CloseNow:
				self.CM.db_close(ID)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {}'.format(ID,'Averaged minutes for hour: ',s/60))
			return s/60
		except:
			self.logger.exception('')
			return self.get_default_value(ID)

	def average_hours_for_day(self,ID,strTimeStamp):
		'''Accepts a timestamp anywhere within the day to be averaged. Averages hours 0-23'''
		try:
			timebase = 'hours'
			TimeStamp = self.format_time_stamp(strTimeStamp,'days')
	#		TimeStamp = TimeStamp.replace(hour=0,minute=0,second=0,microsecond=0)
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select v from hdata where ts>=? order by ts asc limit ?', (TimeStamp,24))
			s = 0
			for i in range(24):
				row = cur.fetchone()
				if not row:
					logger.warning('Failed to average all hours for ID {} at timestamp {}'.formate(ID,strTimeStamp))
					break
				s += row[0]
			if self.CloseNow:
				self.CM.db_close(ID)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {}'.format(ID,'Averaged hours for day: ',s/24))
			return s/24
		except:
			self.logger.exception('')
			return self.get_default_value(ID)

	def create_sync_time(self,ID,TimeStamp,timebase):
		try:
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select LatestUpdate from status where TableName=?', (timebase[0:1]+'data_sync',))
			row = cur.fetchone()
			if not row:
				cur.execute('insert into status values (?,?)', (timebase[0:1]+'data_sync',TimeStamp))
				self.CM.connect_to_db(ID).commit()
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {}'.format('Insert Sync Time',ID,TimeStamp))
			else:
				cur.execute('update status SET LatestUpdate=? WHERE TableName=?', (TimeStamp,timebase[0:1]+'data_sync'))
				self.CM.connect_to_db(ID).commit()
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {}'.format('Create>>Updated Sync Time',ID,TimeStamp))
			if self.CloseNow:
				self.CM.db_close(ID)
		except:
			self.logger.exception('')

	def update_sync_time(self,ID,TimeStamp,timebase):
		try:
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('update status SET LatestUpdate=? WHERE TableName=?', (TimeStamp,timebase[0:1]+'data_sync'))
			self.CM.connect_to_db(ID).commit()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {}'.format('********* Updated Sync Time',ID,TimeStamp))
			if self.CloseNow:
				self.CM.db_close(ID)
		except:
			self.logger.exception('')

	def get_sync_time(self,ID,timebase):
		try:
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('select LatestUpdate from status where TableName=?', (timebase[0:1]+'data_sync',))
			time = cur.fetchone()
			if self.CloseNow:
				self.CM.db_close(ID)
			if time == []:
				return None
			else:
				return time[0]
		except:
			self.logger.exception('')
			if self.CloseNow:
				self.CM.db_close(ID)
			return None

	def purge_records(self,ID,timebase):
#		import pdb;pdb.set_trace()
		try:
			ts = self.get_time_now() - datetime.timedelta(seconds=(self.PurgeTimeDelta[timebase] * self.dictTimebaseToSecondsMultiplier[timebase]))
			cur = self.CM.connect_to_db(ID).cursor()
			cur.execute('delete from '+timebase[0:1]+'data where ts<=?', (ts,))
			self.CM.connect_to_db(ID).commit()
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Purged Records before '+str(ts)+' for {} {}'.format(ID,timebase))
		except:
			self.logger.exception('')
		if self.CloseNow:
			self.CM.db_close(ID)

	def write_filtered_time_data_records(self,ID,data,timebase,CreateTemplate=False):
		try:
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug(str(ID)+'*** write filtered time data records ***')
			if CreateTemplate:
				#Update to the first value (to create a template)
				timestamp,value = data[0]
				self.update_record(ID,timestamp,value,timebase,None,None,False)
				#update to the most recent value (to create a template)
				timestamp,value = data[-1]
				self.update_record(ID,timestamp,value,timebase,None,None,False)
			#then write all the data
			cur = self.CM.connect_to_db(ID).cursor()
			for timestamp,value in data:
				cur.execute('update '+timebase[0:1]+'data SET v=? WHERE ts=?', (value,timestamp))
			self.CM.connect_to_db(ID).commit()
#						print value,timestamp
			if self.CloseNow:
				self.CM.db_close(ID)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug(str(ID)+'*** write filtered time data records ***  COMPLETE  ***')
			return True
		except:
			self.logger.exception('')
			if self.CloseNow:
				self.CM.db_close(ID)
			return False

	def insert_filtered_time_data_records(self,ID,data,timebase):
		try:
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug(str(ID)+'*** insert filtered time data records ***')
			cur = self.CM.connect_to_db(ID).cursor()
			for timestamp,value in data:
				cur.execute('insert into '+timebase[0:1]+'data (ts, v) values (?, ?)', (timestamp,value))
			self.CM.connect_to_db(ID).commit()
			if self.CloseNow:
				self.CM.db_close(ID)
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug(str(ID)+'*** insert filtered time data records ***  COMPLETE  ***')
			return True
		except:
			self.logger.exception('')
			if self.CloseNow:
				self.CM.db_close(ID)
			return False

	def db_close(self,ID):
		self.CM.db_close(ID)

	def get_larger_timebase(self,timebase,points):
		if timebase == 'seconds': return ('minutes',int(points/60)+1)
		if timebase == 'minutes': return ('hours',int(points/60)+1)
		if timebase == 'hours': return ('days',int(points/24)+1)
		if timebase == 'days': return ('',0)
		return ('',0)

	def interpolate_for_lower_timebase(self,StartTime,source_timebase,source_data,target_timebase,target_points):
		if source_timebase == 'minutes' and target_timebase == 'seconds':
			lst = []
			i = 0
			v = source_data[i]
			if StartTime.second == 0:#if starting with zero, don't increment prematurely
				i -= 1
			for x in range(target_points):
				if (StartTime + datetime.timedelta(seconds=x)).second == 0:
					i += 1
					try:
						v = source_data[i]
					except:
						pass
				lst.append((v,))#downstream code expects the data to be a list of tuples
			return lst
		if source_timebase == 'hours' and target_timebase == 'minutes':
			lst = []
			i = 0
			v = source_data[i]
			if StartTime.minute == 0:#if starting with zero, don't increment prematurely
				i -= 1
			for x in range(target_points):
				if (StartTime + datetime.timedelta(minutes=x)).minute == 0:
					i += 1
					try:
						v = source_data[i]
					except:
						pass
				lst.append((v,))#downstream code expects the data to be a list of tuples
			return lst
		if source_timebase == 'days' and target_timebase == 'hours':
			lst = []
			i = 0
			v = source_data[i]
			if StartTime.hour == 0:#if starting with zero, don't increment prematurely
				i -= 1
			for x in range(target_points):
				if (StartTime + datetime.timedelta(minutes=x)).hour == 0:
					i += 1
					try:
						v = source_data[i]
					except:
						pass
				lst.append((v,))#downstream code expects the data to be a list of tuples
			return lst

	def update_default_value(self,ID,DefaultValue):
		self.dictDefaultValue[ID] = DefaultValue

	def get_default_value(self,ID):
		if self.dictDefaultValue.has_key(ID):
			return self.dictDefaultValue[ID]
		else:
			return 0

	def update_status_table_latest_update(self,ID,timebase,TimeStamp,Value):
		cur = self.CM.connect_to_db(ID).cursor()
		cur.execute('select LatestUpdate from status where TableName=?', (timebase[0:1]+'data',))
		row = cur.fetchone()
		if not row:
			cur.execute('insert into status values (?,?)', (timebase[0:1]+'data',TimeStamp))
			self.CM.connect_to_db(ID).commit()
		else:
			cur.execute('update status SET LatestUpdate=? WHERE TableName=?', (TimeStamp,timebase[0:1]+'data'))
			self.CM.connect_to_db(ID).commit()
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format('Update status:',TimeStamp,ID,timebase[0:1]+'data'))
		self.dictLatestUpdate[ID+timebase] = TimeStamp
		self.dictLatestValue[ID+timebase] = Value
		if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('{} {} {} {}'.format(ID,' LatestValue, LatestUpdate: ',self.dictLatestValue[ID+timebase],self.dictLatestUpdate[ID+timebase]))

	def update_copy(self,ID,Copy):
		self.dictCopy[ID] = int(Copy)

	def get_copy(self,ID):
		if self.dictCopy.has_key(ID):
			return self.dictCopy[ID]
		else:
			return 0

	def stop_sqlite_engine(self):
		'''This is a hard stop!'''
		self.CM.db_close_all()
		time.sleep(1)
		os._exit(os.R_OK)

	def sync_to_file(self):
		self.CM.db_close_all()

	def get_time_now(self):
		if not self.boolUnitTest:
			return datetime.datetime.now()
		else:
			if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('get_time_now {}'.format(self.unittest_datetime_now))
			return self.unittest_datetime_now

	def set_unittest_now(self,datetime):
		self.unittest_datetime_now = datetime


class DBConnectionManager():
	def __init__(self, MemoryDB = False, PathToDatastore = ''):
		"""
		timebase: seconds, minutes, hours, days
		"""
		self.__debug=False
		self.dbconn = None
		self.dictIDconn = {} #Dictionary of active Database connections
		self.Memory = MemoryDB
		self.logger = logging.getLogger(__name__+'.DBConnectionManager')
		self.PathToDatastore = PathToDatastore

	def connection_exists(self,ID):
		return self.dictIDconn.has_key(ID)

	def connect_to_db(self,ID):
		if self.dictIDconn.has_key(ID):
			if self.dictIDconn[ID] <> None:
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Connection found for ID: '+str(ID))
				return self.dictIDconn[ID]
		if self.Memory:
			self.dbconn = sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
			self.dictIDconn[ID] = self.dbconn
			self.create_tables(ID,self.dbconn)
			self.dbconn.commit()
			self.logger.info('Created memory DB for ID: '+str(ID))
		else:
			if self.PathToDatastore == '':
				FileName = os.path.join(os.path.abspath('.'),'dataid_'+str(ID)+'.db')
			else:
				FileName = os.path.join(self.PathToDatastore,'dataid_'+str(ID)+'.db')
			if not os.access(FileName, os.R_OK):
				self.dbconn = sqlite3.connect(FileName, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
				if self.dbconn:
					self.dictIDconn[ID] = self.dbconn
					self.create_tables(ID, self.dbconn)
					self.dbconn.commit()
					self.dbconn.close()
					self.dbconn = sqlite3.connect(FileName, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
					if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Created file DB for ID: '+str(ID))
			else:
				self.dbconn = sqlite3.connect(FileName, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
		if not self.dbconn:
			if self.Memory:
				self.logger.warning('Failed to create memory database')
			else:
				self.logger.warning('Failed to create/connect to database file: '+FileName)
		else:
			self.dictIDconn[ID] = self.dbconn
			if not self.Memory:
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Connected to file db: '+FileName)
		return self.dbconn

	def create_tables(self,ID, dbconn):
		cur = dbconn.cursor()
		cur.execute("create table sdata(ts timestamp, v real)")
		cur.execute("create table mdata(ts timestamp, v real)")
		cur.execute("create table hdata(ts timestamp, v real)")
		cur.execute("create table ddata(ts timestamp, v real)")
		cur.execute('create table status(TableName text, LatestUpdate timestamp)')
		cur.execute('create index sdata_index on mdata (ts)')
		cur.execute('create index mdata_index on mdata (ts)')
		cur.execute('create index hdata_index on hdata (ts)')
		cur.execute('create index ddata_index on ddata (ts)')
#		cur.execute('pragma journal_mode = OFF')
		cur.execute('pragma syncronous = OFF')
		cur.execute('pragma temp_store = MEMORY')
		dbconn.commit()

	def dbconnection(self,ID):
		if not self.connect_to_db(ID):
			self.logger.warning('Database connection requested but it is closed')
		return self.connect_to_db(ID)

	def db_close(self,ID):
		if self.dictIDconn.has_key(ID):
			try:
				if self.dictIDconn[ID] <> None:
					self.dictIDconn[ID].close()
					del self.dictIDconn[ID]
					if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Closed DB for ID: '+str(ID))
			except:
				self.logger.exception('')

	def db_close_all(self):
#		print self.dictIDconn
		for k in self.dictIDconn.iterkeys():
			try:
				self.db_close(k)
			finally:
				if self.logger.isEnabledFor(logging.DEBUG):self.logger.debug('Closed DB for ID: '+str(k))
		self.dictIDconn = {}
