import thread
import actionlab.models
import socket
import sys
import time, datetime
import logging
logger = logging.getLogger('actionlab_usermodule.'+__name__)
logger.info('loaded usermodule '+__name__)
from actionlab.actionlabengine import get_data_from_dataid, send_socket

def ComputeAndAct(dictTable):
	try:
#		import pdb;pdb.set_trace()
		dt = datetime.datetime.now()
		#define data variables and query data
		PorchTemp = get_data_from_dataid(27)
#		DayroomTemp = get_data_from_dataid(39)
#		DryerExhaustHumidity = get_data_from_dataid(50)
		logger.debug('ID 48 '+str(PorchTemp))
#		print 'ID 49 '+str(DayroomTemp)
		
		#calculate result	
		ampm = 'AM'
		if dt.hour > 11:
			ampm = 'PM'
		wd = ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[dt.weekday()]
		fdt = wd+' '+dt.strftime('%m/%d %H:%M')
		if (PorchTemp < 32):
			msg = "Porch %s degrees.  It's freezing outside."%(PorchTemp)
			logger.info(msg)
			send_socket(msg,fdt,"192.168.1.100", 247)
	
		if dt.hour > 7 and dt.hour < 12:
			if get_numpy_data_from_dataid(18,'minutes',dt,10).max() == 1:
				msg = 'Baby awake'
				send_email(msg+' '+fdt)
	except:
		logger.exception()
		
