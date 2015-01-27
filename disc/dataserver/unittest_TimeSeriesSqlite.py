from TimeSeriesSqlite_QdMem import SqliteEngine, TimeSeriesTable_Queue
import os
import sys
import datetime
import time
import numpy as np
import random
import logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
console = logging.StreamHandler(stream=sys.stdout)
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)-40s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)
logger.debug('started logger')

#import pdb;pdb.set_trace()

USE_SQLITE_QUEUED_MEMORY_MANAGER = True

datatable = None
if USE_SQLITE_QUEUED_MEMORY_MANAGER:
	from TimeSeriesSqlite_QdMem import SqliteEngine, TimeSeriesTable_Queue
	try:
		SE = SqliteEngine(
				PathToDatastore=os.path.join(os.path.abspath('.'),'datastore'),
				dictInitialDefaultValues={},
				MINUTES_BETWEEN_COPY_MEMORY_TO_FILE = 30,
				MEMORY_ONLY = False,
				USE_JOURNAL_WITH_MEMORY_DB = False,
				JOURNAL_PATH = '',
				INITIALIZE_MEMORY_WITH_FILE_DATA = True,
				UnitTest=True
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
	datatable = TimeSeriesSqlite.TimeSeriesTable(TimeSeriesSqlite.DBConnectionManager(MemoryDB=False,PathToDatastore=os.path.join(os.path.abspath('.'),'datastore')),UnitTest=True)


def view_data(ID,StartTime,points,Timebase):
	if Timebase == 'seconds':
		dt = StartTime + datetime.timedelta(seconds=points)
	if Timebase == 'minutes':
		dt = StartTime + datetime.timedelta(minutes=points)
	if Timebase == 'hours':
		dt = StartTime + datetime.timedelta(hours=points)
	if Timebase == 'days':
		dt = StartTime + datetime.timedelta(days=points)
		
	datatable.set_unittest_now(dt)
	
	import matplotlib.pyplot as plt
	fig, ax = plt.subplots(1)
	
	logger.info('>>> plot for ID {} and timebase {}, plotting {} points before time {}'.format(ID,Timebase,points,dt))
	y = datatable.get_data_records_before_time(ID,dt,points,Timebase)
#	print y
	y = np.array([x[0] for x in y])
	
	ax.plot(y)
	plt.show()	

def count_up(Usematplotlib = True):
	'''Test all timebases over a large time period; verifying all data.
	
		Load data in each timebase
		use time for the value
	'''
	
	StartTime = datetime.datetime.fromtimestamp(time.mktime(time.strptime('2000-1-1 00:00:00','%Y-%m-%d %H:%M:%S')))
	#using the timbase as the ID (this may create confusion)
	LastUpdate = {'seconds':StartTime,'minutes':StartTime,'hours':StartTime,'days':StartTime}
	Period = 1
	TotalSeconds = 1 * 24 * 60 * 60

	for Timebase in ['seconds','minutes','hours','days']:
		ID = Timebase
		datatable.set_unittest_now(StartTime)
		datatable.update_copy(ID,120)
		datatable.update_default_value(ID,-999)
		
	for c in range(TotalSeconds):
		dt = StartTime + datetime.timedelta(seconds=c)
		datatable.set_unittest_now(dt)
		for Timebase in ['seconds','minutes','hours','days']:
			ID = Timebase
			QueryNow = False
			
			if Timebase == 'seconds':
				if LastUpdate[ID] <= dt:
					QueryNow = True
					LastUpdate[ID] = (dt + datetime.timedelta(seconds=Period)).replace(microsecond=0)
					value = dt.second
			elif Timebase == 'minutes':
				if LastUpdate[ID] <= dt:
					QueryNow = True
					LastUpdate[ID] = (dt + datetime.timedelta(minutes=Period)).replace(second=0,microsecond=0)
					value = dt.minute
					print 'update minute',value,Timebase
			elif Timebase == 'hours':
				if LastUpdate[ID] <= dt:
					QueryNow = True
					LastUpdate[ID] = (dt + datetime.timedelta(hours=Period)).replace(minute=0,second=0,microsecond=0)
					value = dt.hour
					print 'update hour',value,Timebase
			elif Timebase == 'days':
				if LastUpdate[ID] <= dt:
					QueryNow = True
					LastUpdate[ID] = (dt + datetime.timedelta(days=Period)).replace(hour=0,minute=0,second=0,microsecond=0)
					value = dt.day
					print 'update day',value,Timebase
			if QueryNow:
				datatable.update_record(ID,str(dt),value,Timebase,None,None,True)

	logger.info('save memory data to file')
	datatable.sync_to_file()
	
	if Usematplotlib:
		import matplotlib.pyplot as plt
		fig, ax = plt.subplots(1)
		ID = 'seconds'
		y = datatable.get_data_records_before_time(ID,dt,TotalSeconds,'seconds')
		ax.plot(y)

		plt.show()	


def generate_data(Timebase = 'minutes', points = 4*24, sourcedata = 'sine', Usematplotlib = True, MissingInputPercentage=10):
	ID = '{}_{}'.format(Timebase,sourcedata)
	try:
		path = os.path.join(SE.PathToDatastore,'dataid_'+ID+'.db')
		if os.path.isfile(path):
			os.remove(path)
	except:
		pass
	StartTime = datetime.datetime.fromtimestamp(time.mktime(time.strptime('2000-1-1 00:00:00','%Y-%m-%d %H:%M:%S')))
#	import pdb;pdb.set_trace()
	datatable.set_unittest_now(StartTime)
	datatable.update_copy(ID,1000)
	datatable.update_default_value(ID,-1)
	
	from math import sin,pi
	from decimal import Decimal as Dec
	for c in range(points):
		dt = StartTime + datetime.timedelta(hours=c)
		datatable.set_unittest_now(dt)
		if sourcedata == 'sine':
			s = round(100*sin(Dec(dt.hour)/Dec(24)*2*Dec(pi)) + 10*sin(Dec(dt.minute)/Dec(60)*2*Dec(pi)) + sin(Dec(dt.second)/Dec(60)*2*Dec(pi)),2)
		if sourcedata == 'sawtooth':
			s = datetime.datetime.now().day + datetime.datetime.now().hour + datetime.datetime.now().minute + datetime.datetime.now().second
		logger.info('{} {}'.format(c,s))
		if random.randint(1,10) <= MissingInputPercentage:
			datatable.update_record(ID,str(dt),s,Timebase,None,None,True)

	logger.info('****************************************')
	y = datatable.get_data_records_before_time(ID,dt,points,Timebase)
#	logger.info(str([x[0] for x in y]))
	
	logger.info('save memory data to file')
	datatable.sync_to_file()

	if Usematplotlib:
		multiplier = {}
		multiplier['seconds'] = {'seconds':1,'minutes':float(1)/60,'hours':float(1)/60/60,'days':float(1)/60/60/24}
		multiplier['minutes'] = {'seconds':60,'minutes':1,'hours':float(1)/60,'days':float(1)/60/24}
		multiplier['hours'] = {'seconds':60*60,'minutes':60,'hours':1,'days':float(1)/24}
		multiplier['days'] = {'seconds':60*60*24,'minutes':60*24,'hours':24,'days':1}
		view_data(ID,StartTime,points*multiplier[Timebase]['seconds'],'seconds')
		view_data(ID,StartTime,points*multiplier[Timebase]['minutes'],'minutes')
		view_data(ID,StartTime,points*multiplier[Timebase]['hours'],'hours')
		view_data(ID,StartTime,points*multiplier[Timebase]['days'],'days')


StartTime = datetime.datetime.fromtimestamp(time.mktime(time.strptime('2000-1-1 00:00:00','%Y-%m-%d %H:%M:%S')))
#count_up(False)
#generate_data('hours',4*24,'sine',True,10)
generate_data('hours',3*24,'sawtooth',True,7)

#view_data('hours_sine',StartTime,4*24,'hours')
#view_data('hours_sine',StartTime,4,'days')

view_data('hours_sawtooth',StartTime,7*24*60*60,'seconds')
view_data('hours_sawtooth',StartTime,7*24*60,'minutes')
view_data('hours_sawtooth',StartTime,7*24,'hours')
view_data('hours_sawtooth',StartTime,7,'days')

if USE_SQLITE_QUEUED_MEMORY_MANAGER:
	SE.quit()
