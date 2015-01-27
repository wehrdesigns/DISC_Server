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
		roomname = 					['bathroom',	'garage',	'little room',	'master bedroom',	'nursery',	'downstairs']
		id_ll = 					[97,			29,			41,				25,					17,			37]
		id_motion = 				[98,			38,			22,				26,					18,			38]
		period_light_on_inform = 	[20,			20,			20,				20,					20,			20]
		period_light_on_warn = 		[30,			30,			30,				30,					30,			30]
		#disable check by setting a large light level
		lightlevel = 				[99,			99,			10,				10,					99,			99]
		outside_id_ll = 			[29,			29,			29,				29,					29,			29]
		#disable the outside light level check by setting a large negative number
		outside_ll = 				[-100,			-100,			0,				0,					0,			0]
		
		for i in range(len(roomname)):
			try:
				#is the light on?
				if float(get_data_from_dataid(id_ll[i])) > lightlevel[i]:
					#is it the outside light instead?
					if float(get_data_from_dataid(outside_id_ll[i])) < outside_ll[i]:
						#has the light been on long enough to that we care to tell someone?
						if get_numpy_data_from_dataid(id_ll[i],'minutes',dt,period_light_on_inform[i]).min() < lightlevel[i]:
							#has there been any motion while the light has been on?
							if get_numpy_data_from_dataid(id_motion[i],'minutes',dt,period_light_on_inform[i]).max() == 0:
								msg = 'Light on in the '+roomname[i]+' and no motion for {} minutes.'.format(period_light_on_inform[i])
					#			send_socket(msg,'',"192.168.1.101", 247)
								say_msg(msg)
								logger.info(msg)
								#has there been no motion for such a long time that we should warn someone?
								if get_numpy_data_from_dataid(id_motion[i],'minutes',dt,period_light_on_warn[i]).max() == 0:
									msg = 'Light on in the '+roomname[i]+' and no motion for {} minutes.'.format(period_light_on_warn[i])
									send_email(msg+' '+fdt)
			except:
				logger.exception('checking the '+roomname[i]+' light')
	except:
		logger.exception('checking the '+roomname[i]+' light')
