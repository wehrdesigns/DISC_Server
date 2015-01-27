import thread
import socket
import sys
import time, datetime
import logging
logger = logging.getLogger('actionlab_usermodule.'+__name__)
logger.info('loaded usermodule '+__name__)
import actionlab.models
from actionlab.actionlabengine import get_data_from_dataid, send_socket, get_numpy_data_from_dataid

from utilities import send_email, say_msg

def ComputeAndAct(dictTable):
	dt = datetime.datetime.now()
	ampm = 'AM'
	if dt.hour > 11:
		ampm = 'PM'
	wd = ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[dt.weekday()]
	fdt = wd+' '+dt.strftime('%m/%d %H:%M')
	
	if dt.hour == 9:
		try:
	#		import pdb;pdb.set_trace()
			#define data variables and query data
			#use 24hr format
			light_on_level = 0
			sleephr = 21		#earliest hour of sleeping
			wakehr = 6			#latest hour of sleeping
			sleepperiod = 24 - (sleephr - wakehr)
			if sleephr < wakehr:
				sleepperiod = wakehr - sleephr
			stoptime = dt.replace(hour=wakehr,minute=0,second=0,microsecond=0)
			points = sleepperiod*60
			starttime = stoptime - datetime.timedelta(minutes=points)
			light = get_numpy_data_from_dataid(25,'minutes',stoptime,points)
			motion = get_numpy_data_from_dataid(26,'minutes',stoptime,points)
			
			#define the start of the sleep period
				#lights out in bedroom
			#search until the middle of the array (the sleep period) to find the last time the light was turned on
			iLightOff = 0
			i = 0
			for l in light[:int(points/2)]:
				if l > light_on_level:
					iLightOff = i
				i += 1
			
			#define the stop of the sleep period
				#light on in bedroom
			#search from the middle of the array until the light is turned on
			iLightOn = points
			i = 0
			for l in light[int(points/2):]:
				if l > light_on_level:
					iLightOn = i + int(points/2)
					break
				i += 1
				
			#find longest interval of no motion during sleep
			max_no_motion_index = iLightOff
			max_no_motion = 0
			i = 0
			m = 0
			for v in motion[iLightOff:iLightOn]:
				if v == 0:
					m += 1
					if m > max_no_motion:
						max_no_motion = m
						max_no_motion_index = iLightOff + i - int(m/2)
				else:
					m = 0
				i += 1
			dt_no_motion = starttime + datetime.timedelta(minutes=max_no_motion_index)
			
#			print points
#			print stoptime
#			print dt_no_motion
#			print max_no_motion
#			print max_no_motion_index
			msg = 'Activity: '+str(motion.sum())+'/'+str(points)
			msg += '. Stillness: '+str(max_no_motion)+' min. @ '+dt_no_motion.strftime('%m/%d %H:%M')
			msg += '.  Light off: '+(starttime+datetime.timedelta(minutes=iLightOff)).strftime('%m/%d %H:%M')
			msg += '.  Light on: '+(starttime+datetime.timedelta(minutes=iLightOn)).strftime('%m/%d %H:%M')
#			send_socket(msg,fdt,"192.168.1.101", 247)
			logger.info(msg)
			send_email(msg)
	
		except:
			logger.exception('error executing test')
		
