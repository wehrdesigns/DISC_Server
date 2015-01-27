import thread
import socket
import sys
import time, datetime
import logging
logger = logging.getLogger('actionlab_usermodule.'+__name__)
logger.info('loaded usermodule '+__name__)
import actionlab.models
from actionlab.actionlabengine import get_data_from_dataid, send_socket

from utilities import send_email, say_msg

def ComputeAndAct(dictTable):
	try:
#		import pdb;pdb.set_trace()
		dt = datetime.datetime.now()
		#define data variables and query data
		LaundryRoomTemp = int(float(get_data_from_dataid(48)))
		DryerExhaustTemp = int(float(get_data_from_dataid(49)))
		DryerExhaustHumidity = int(float(get_data_from_dataid(50)))
		logger.info('ID 48 {}'.format(LaundryRoomTemp))
		logger.info('ID 49 {}'.format(DryerExhaustTemp))
		
		#verify that this data is valid
		#the data should be set to None if it was invalid or if it is equal to the default value
		#then check for none here and skip the calculations using that value
		if LaundryRoomTemp and DryerExhaustTemp and DryerExhaustHumidity:
			#calculate result	
			ampm = 'AM'
			if dt.hour > 11:
				ampm = 'PM'
			wd = ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[dt.weekday()]
			fdt = wd+' '+dt.strftime('%m/%d %H:%M')
			if (DryerExhaustTemp > LaundryRoomTemp + 20) or DryerExhaustTemp > 100:
				msg = 'Dryer {} degrees {} percent'.format(DryerExhaustTemp,DryerExhaustHumidity)
				logger.info(msg)
				send_socket(msg,fdt,"192.168.1.100", 247)
#				send_socket(msg,fdt,"192.168.1.101", 247)
				say_msg(msg)
			if DryerExhaustTemp > 120 and DryerExhaustHumidity < 25:
				msg = 'Check dryer'
				logger.info(msg)
				send_socket(msg,fdt,"192.168.1.100", 247)
#				send_socket(msg,fdt,"192.168.1.101", 247)
				say_msg(msg)
				
			msg = 'Dryer %s degrees %s percent'%(DryerExhaustTemp,DryerExhaustHumidity)
#			sendSocket(msg,fdt,"192.168.1.100", 247)
			logger.info(msg)
		
	except:
		logger.exception('error executing test')
