import socket
import sys
import time, datetime
import logging
logger = logging.getLogger('actionlab_usermodule.'+__name__)
logger.info('loaded usermodule '+__name__)
from actionlab.actionlabengine import get_data_from_dataid, send_socket, get_numpy_data_from_dataid

from utilities import send_email, say_msg

import urllib2

def ComputeAndAct(dictTable):
	try:
#		import pdb;pdb.set_trace()
		dt = datetime.datetime.now()
		ampm = 'A,M'
		if dt.hour > 11:
			ampm = 'P,M'
		wd = ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[dt.weekday()]
		fdt = wd+' '+dt.strftime('%m/%d %H:%M')
		thishour = dt.strftime('%H '+ampm)
		#define data variables and query data
		outtemp = int(float(get_data_from_dataid(27)))
		outhum = int(float(get_data_from_dataid(28)))
		dayroomtemp = int(float(get_data_from_dataid(35)))
#		out3temp = int(float(get_data_from_dataid(56)))
#		out6temp = int(float(get_data_from_dataid(57)))
#		logger.info('ID 1 '+str(test1))
#		logger.info('ID 2 '+str(test2))
#		logger.info('ID 3 '+str(test3))
		
		#verify that this data is valid
		#the data should be set to None if it was invalid or if it is equal to the default value
		#then check for none here and skip the calculations using that value
		if outtemp and outhum:
			msg = '{} hundred hours. {} percent. {} degrees.'.format(dt.strftime('%H'),outhum,outtemp)
#			send_socket(msg,'',"192.168.1.101", 247)
#			say_msg(msg)
			logger.info(msg)
		
		if outtemp and dayroomtemp and (23 >= dt.hour >= 19):
			if dayroomtemp > 72:
				lowesttemp = get_numpy_data_from_dataid(58,'hours',dt,12).min()
				if outtemp < dayroomtemp - 3:
					msg = 'Outside cooler than inside.'
#					send_socket(msg,'',"192.168.1.101", 247)
#					say_msg(msg)
				if (65 < outtemp < dayroomtemp-3) and (55 < lowesttemp < 65) and (lowesttemp < dayroomtemp - 8):
					msg = 'Open windows.  12 hour low is {} degrees'.format(lowesttemp)
#					send_socket(msg,'',"192.168.1.101", 247)
#					say_msg(msg)
					logger.info(msg)
					send_email(msg)
			
	except:
		logger.exception('')
		
	try:
		if dt.hour == 9:
			msg = 'http://localhost/disc/env/stats/12/'+dt.strftime('%Y-%m-%d')+'_08-00-00'
#			send_email(msg)
#			logger.info(msg)
		if dt.hour == 21:
			msg = 'http://localhost/disc/env/stats/24/'+dt.strftime('%Y-%m-%d')+'_21-00-00'
#			send_email(msg)
#			logger.info(msg)
	except:
		logger.exception('sending stat email')
		
	try:
		if dt.hour == 9:
#			get_numpy_data_from_dataid(58,'hours',dt,12).min()
			msg = ''
#			send_email(msg)
	except:
		logger.exception('sending report')

	try:
		if dt.hour > 7:
			import discengines
			from env.models import *
			datatable = discengines.datatable
			qs = Data.objects.all().filter(Active=True)
			missingdata = False
			for d in qs:
				o = Data.objects.get(ID=d.ID)
				cts = datatable.calculate_start_time(dt,int(o.Period),o.Timebase)
				dtr = datatable.get_value_date_time(d.ID,o.Timebase)
				if dtr < cts:
					missingdata = True
			if missingdata:
				msg = 'DISC value out of date'
				send_email(msg)
				logger.info(msg)
	except:
		logger.exception('checking for last update')

	try:
		stoptime = dt.replace(second=0,microsecond=0)
		data = get_numpy_data_from_dataid(110,'minutes',stoptime,60)
		if data.max() > 300:
			cnt = 0
			for x in data:
				if x > 300:
					cnt += 1
			if cnt > 14:
				msg = 'Upstairs heater on '+str(cnt)+' min'
				send_email(msg)
				say_msg(msg)
				logger.info(msg)
	except:
		logger.exception('checking upstairs heating time')


	try:
		if dt.hour == 8:
			stoptime = dt.replace(second=0,microsecond=0)
			data = get_numpy_data_from_dataid(108,'minutes',stoptime,180)
			if data.max() > 300:
				cnt = 0
				for x in data:
					if x > 300:
						cnt += 1
				msg = 'Water heater on '+str(cnt)+' min'
				send_email(msg)
				say_msg(msg)
				logger.info(msg)
	except:
		logger.exception('checking water heating time')
		

	try:
		if dt.hour == 20:
			stoptime = dt.replace(second=0,microsecond=0)
			data = get_numpy_data_from_dataid(110,'minutes',stoptime,1440)
			if data.max() > 300:
				cnt = 0
				for x in data:
					if x > 300:
						cnt += 1
				if cnt > 9:
					p = round(cnt/1440*100)
					msg = '24hr upstairs heating '+str(p)+'% on '+ftd
					send_email(msg)
#					say_msg(msg)
					logger.info(msg)
	except:
		logger.exception('checking upstairs heating time')


	try:
		if dt.hour >= 19 and dt.hour <= 21:
			stoptime = dt.replace(second=0,microsecond=0)
			lowtemp = get_numpy_data_from_dataid(58,'minutes',stoptime,720).min()
			if lowtemp <= 25:
				msg = 'Forecast low of '+str(lowtemp)+' degrees on '+ftd
				send_email(msg)
				say_msg(msg)
				logger.info(msg)
	except:
		logger.exception('checking low temperature forecast')
		
	try:
		if dt.hour == 21:
			stoptime = dt.replace(second=0,microsecond=0)
			main1 = get_numpy_data_from_dataid(104,'minutes',stoptime,1440).sum()/1440*24
			main2 = get_numpy_data_from_dataid(105,'minutes',stoptime,1440).sum()/1440*24
			cost = (main1 + main2)/1000*0.1
			msg = '24hr electricity cost $'+str(round(cost,2))
			send_email(msg)
#			say_msg(msg)
			logger.info(msg)
	except:
		logger.exception('Calculating electricity cost')
		
	try:
		if dt.hour == 9:
			stoptime = dt.replace(second=0,microsecond=0)
			activity = get_numpy_data_from_dataid(18,'minutes',stoptime,720).sum()
			p = round(activity/720*100)
			msg = 'Nursery night activity (12hr): '+str(p)+'%'
			send_email(msg)
#			say_msg(msg)
			logger.info(msg)
	except:
		logger.exception('Nursery night activity')
		
	try:
		mins = 600
		if dt.hour == 17:
			stoptime = dt.replace(second=0,microsecond=0)
			office = get_numpy_data_from_dataid(38,'minutes',stoptime,mins).sum()
			nursery = get_numpy_data_from_dataid(18,'minutes',stoptime,mins).sum()
			poffice = round(office/mins*100)
			pnursery = round(nursery/mins*100)
			msg = 'Office/Nursery day activity (10hr): '+str(poffice)+'%/'+str(pnursery)+'%'
			send_email(msg)
#			say_msg(msg)
			logger.info(msg)
	except:
		logger.exception('Office/Nursery day activity')

	try:
		mins = 1440
		if dt.hour == 18:
			stoptime = dt.replace(second=0,microsecond=0)
			data = get_numpy_data_from_dataid(108,'minutes',stoptime,mins)
			if data.max() > 300:
				cnt = 0
				for x in data:
					if x > 300:
						cnt += 1
				p = round(cnt/mins*100)
				msg = '24hr water heating (min): '+str(p)+'%'
				send_email(msg)
#				say_msg(msg)
				logger.info(msg)
	except:
		logger.exception('24hr water heating time')