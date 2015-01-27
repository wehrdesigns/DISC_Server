#! /usr/bin/env python
import os
import sys
import json
import threading
import logging

import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
import tornado.web

listTimebase = ['seconds','minutes','hours','days']

APP_BASE_PATH = os.path.abspath('.')
jsondict = json.load(open(os.path.join(os.path.join(APP_BASE_PATH,'user'),'config.json'),'r'))
POST_DATA_HTTP_PORT = int(jsondict['POST_DATA_HTTP_PORT']['value'])
POST_DATA_HTTP_PROXY_PATH = jsondict['POST_DATA_HTTP_PROXY_PATH']['value']

if POST_DATA_HTTP_PORT > 0:
	try:
#        import pdb;pdb.set_trace()
		import discengines
	except:
		logger.exception('Error importing discengines')

class PostDataHandler(tornado.web.RequestHandler):
	def initialize(self):
		pass
	
	def get(self):
		self.write('<html><body>Post data here.</body></html>')
		
	def post(self):
		'''By POST, accepts ID, RecordDateTime, Value, timebase to filter, aggregate and store with the time series engine.
			
			ID (also known as DataID) is a unique integer that specifies item of the env.model.Data
			RecordDateTime is date and time stamp corresponding to server time with format %Y-%m-%d %H:%M:%S
			Value is coerced to a floating point value, but is stored in the database as a string
			timebase is one of: seconds, minutes, hours, days            
		'''
		try:
			if self.get_argument('AccessCode') == discengines.POST_ACCESSCODE:
				datatable = discengines.datatable
				ID = self.get_argument('ID')
				RecordDateTime = self.get_argument('RecordDateTime')
				Value = self.get_argument('Value')
				timebase = self.get_argument('Timebase')
				if not listTimebase.__contains__(timebase):
					logger.exception('invalid timebase')
					self.write("ERROR")
				datatable.update_record(ID,RecordDateTime,Value,timebase,None,None,True)	
				discengines.dictValues[ID] = Value
				discengines.dictDateTime[ID] = RecordDateTime
				self.write("OK")
			else:
				logger.warning('Access denied for post data')
				self.write("Access denied.")
		except:
			logger.exception('Unexpected error during post_data')
			if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
				try:
					datatable.db_close(ID)
				except:
					logger.exception('Error closing sqlite db for ID:'+str(ID))
			self.write("ERROR")

class PostDataServer(threading.Thread):
	def __init__(self,name='0',):
		threading.Thread.__init__(self)
		self.logger = logging.getLogger(__name__+'.'+name)
		self.tornadoserver = tornado.ioloop.IOLoop.instance()
		
	def quit(self):
		self.tornadoserver.stop()
		
	def run(self):

		if POST_DATA_HTTP_PORT > 0:
				
			post_settings = {
				"static_path": "static",
				#"static_path": os.path.join(os.path.dirname(__file__), "static"),
				#"static_path": os.path.join(os.path.dirname(os.path.abspath(__file__)),'static'),
				#"cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
				"login_url": "/"+POST_DATA_HTTP_PROXY_PATH+"/login/",
				"xsrf_cookies": False,
			}
			post_application = tornado.web.Application([
				(r"/post_data",PostDataHandler),
				('/'+POST_DATA_HTTP_PROXY_PATH+r"/post_data",PostDataHandler),
			], **post_settings)

			self.logger.info('Starting post data server on port '+str(POST_DATA_HTTP_PORT))
			server = tornado.httpserver.HTTPServer(post_application)
			server.listen(int(POST_DATA_HTTP_PORT))
			self.tornadoserver.start()
			
		else:
			self.logger.info('Post data server DISABLED.')

