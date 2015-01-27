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
		test1 = get_data_from_dataid(1)
		test2 = get_data_from_dataid(2)
		test3 = get_data_from_dataid(3)
		logger.info('ID 1 '+str(test1))
		logger.info('ID 2 '+str(test2))
		logger.info('ID 3 '+str(test3))
				
		#verify that this data is valid
		#the data should be set to None if it was invalid or if it is equal to the default value
		#then check for none here and skip the calculations using that value
		if test1 and test2 and test3:
			msg = 'test1 %s; test2 %s; test3 %s'%(test1,test2,test3)
#			send_socket(msg,'',"192.168.1.101", 247)
			logger.info(msg)
		
	except:
		logger.exception('')