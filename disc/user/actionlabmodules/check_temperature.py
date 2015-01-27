import socket
import sys
import time, datetime
import logging
logger = logging.getLogger('actionlab_usermodule.'+__name__)
logger.info('loaded usermodule '+__name__)
from actionlab.actionlabengine import get_data_from_dataid, send_socket, get_numpy_data_from_dataid

from utilities import send_email, say_msg

def ComputeAndAct(dictTable):
	dt = datetime.datetime.now()
	ampm = 'AM'
	if dt.hour > 11:
		ampm = 'PM'
	wd = ('Mon','Tue','Wed','Thu','Fri','Sat','Sun')[dt.weekday()]
	fdt = wd+' '+dt.strftime('%m/%d %H:%M')
	thishour = dt.strftime('%H '+ampm)

	try:
		roomname = 					['Green Room',		'Little Room', 'Master Bed']
		id_temp = 					[15,			39,				23]
		notify_max_temp =	 		[70,			99,				57]
		notify_min_temp = 			[63,			0,				47]

		warn_max_temp =				[75,			78,				70]
		warn_min_temp =			 	[65,			60,				50]
		start_hour =				[0,				21,				21]
		stop_hour = 				[23,			9,				9]			
		
		for i in range(len(roomname)):
			try:
				temp = float(get_data_from_dataid(id_temp[i]))
				#should we warn anyone?
#				if (warn_min_temp[i] >= temp) or (temp >= warn_max_temp[i]):
#					msg = 'Warning:' + roomname[i]+' temperature {} degrees ({}, {}).'.format(temp,warn_max_temp[i],warn_min_temp[i])
#					send_email(msg+' '+fdt)
#					say_msg(msg)
#				else:
				#should we notify anyone?
				if (notify_min_temp[i] >= temp) or (temp >= notify_max_temp[i]):
					#this needs to be fixed for ranges that don't go over midnight
#					if dt.hour >= start_hour[i] or dt.hour <= stop_hour[i]:
					msg = roomname[i]+' temperature {} degrees.'.format(temp)
					#send_socket(msg,'',"192.168.1.101", 247)
					say_msg(msg)
					send_email(msg+' '+fdt)
					logger.info(msg)
					
			except:
				logger.exception('checking the '+roomname[i]+' temperature')
	except:
		logger.exception('checking the '+roomname[i]+' temperature')
