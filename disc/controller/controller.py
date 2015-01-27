#!/usr/bin/python
__version__ = "1.0.0"
import threading
import os
import sys
import time
import datetime
from LoggerClasses import *
from Queue import Queue
import tornado.ioloop
import tornado.web
import settings
import json
import urllib
import httplib

import logging
logger = logging.getLogger()
logger.setLevel(settings.LOGGING_LEVEL)
console = logging.StreamHandler(stream=sys.stdout)
console.setLevel(settings.LOGGING_LEVEL)
formatter = logging.Formatter('%(name)-20s: %(levelname)-8s %(message)s')
console.setFormatter(formatter)
logger.addHandler(console)
#memoryhandler = logging.handlers.MemoryHandler(1024*10, logging.DEBUG, ch)
#logger.addHandler(memoryhandler)
logger.debug('started logger')

def get_interfaces():
#	import pdb;pdb.set_trace()
	interfaces = []
	if settings.INTERFACES:
		interfaces = settings.INTERFACES
	else:
		#get them from the disc server
		try:
			url = 'http://'+settings.HTTP_HOST+':'+settings.HTTP_PORT+'/'+settings.HTTP_PROXY_PATH+'/env/active_interfaces'
			logger.info('Downloading interfaces from: '+url)
			interfaces = json.loads(urllib.urlopen(url).read())
			logger.info('Downloaded active interfaces from the DISC Server: '+str(interfaces))
		except:
			logger.exception('unable to load active_interfaces from disc server')
	imported_interfaces = []
	if interfaces != []:
		for interface in interfaces:
			try:
				__import__(interface)
				logger.info("Imported interface: {}".format(i))
				imported_interfaces.append(interface)
			except:
				logger.exception('Error importing interface {}'.format(interface))
	return imported_interfaces

class Controller(threading.Thread):
	settings = settings
	ServerTimedelta = datetime.timedelta()
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.Q = Queue()
		self.printQ = Queue()
		self.activeflag = False
		self.restartflag = False
		self.CmdQ = {}
		self.RespQ = {}
		self.InterfaceThread = {}
		self.interfaces = []
		self.logger = logging.getLogger('root.Controller')

	def quit(self):
		self.updatetimeflag = False
		for interface in self.interfaces:
			self.InterfaceThread[interface].quit()
			self.logger.info(interface+' stopped')
		time.sleep(0.5)
		self.PFQ.quit()
		self.activeflag = False

	def restart(self):
		self.restartflag = True

	def run(self):
		#checking the server time keeps the controller from running until the server is ready
		#if the controller interfaces were set up to load sensor lists from an archive file, then it would not be necessary to wait for the controller.
		self.updatetimeflag = True
		boolUpdateTime = False
		while not boolUpdateTime and self.updatetimeflag:
			self.logger.info('Update timedelta from DISC server')
			boolUpdateTime = self.update_server_timedelta()
			if not boolUpdateTime:
				time.sleep(5)
		if not self.updatetimeflag:
			os._exit(os.R_OK)
		self.TimeUpdated = datetime.datetime.now().day
		if not settings.USE_DISC_SERVER_TIME_OFFSET:
			self.ServerTimedelta = datetime.timedelta() 
		self.interfaces = get_interfaces()
		if self.interfaces:
			for name in self.interfaces:
				self.CmdQ[name] = Queue()
				self.RespQ[name] = Queue()
		else:
			self.logger.warning('No interfaces.  Exiting.')
			os._exit(os.R_OK)
		self.PFQ = PostFromQuery(self)
		self.PFQ.start()
		for interface in self.interfaces:
			self.InterfaceThread[interface] = sys.modules[interface].Logger(self)
			self.InterfaceThread[interface].start()
			self.logger.info('Started interface: {}'.format(interface))
			
		self.activeflag = True
		self.Output = ''
		while self.activeflag:
			if self.restartflag:
				for interface in self.interfaces:
					self.InterfaceThread[interface].quit()
					self.logger.info(interface+' stopped')
					time.sleep(0.5)
#				self.PFQ.quit()
#				time.sleep(1)
#				self.PFQ.start()
				for interface in self.interfaces:
					self.InterfaceThread[interface] = sys.modules[interface].Logger(self)
					self.InterfaceThread[interface].start()
					self.logger.info(interface+' started')
				
				self.restartflag = False
			time.sleep(0.2)
			while not self.printQ.empty():
				try:
					msg = self.printQ.get()
					self.logger.info('******************\n'+msg)
					self.Output +=   '******************\n'+msg
					self.Output = self.Output[-10000:]
					
				except KeyboardInterrupt:
					self.quit()
			#check server time
			if settings.USE_DISC_SERVER_TIME_OFFSET:
				if datetime.datetime.now().day != self.TimeUpdated:
						if self.update_server_timedelta():
							self.TimeUpdated = datetime.datetime.now().day
	
	def update_server_timedelta(self):
		try:
			f = urllib.urlopen('http://'+settings.HTTP_HOST+':'+settings.HTTP_PORT+'/'+settings.HTTP_PROXY_PATH+'/servertime')
			strPage = f.read()
			#print 'HTML Content: ' + strPage
		except:
			strPage = None
		finally:
			if strPage == None:
				self.logger.warn('Unable to retrieve server time\n')
				return False
			else:
				try:
					#dt = re.search('<body>(.+?)</body>',strPage).group(0)[6:-7]
					self.ServerTimedelta = datetime.datetime.strptime(strPage,'%Y-%m-%d %H:%M:%S.%f') - datetime.datetime.now()
					self.logger.info('Updated ServerTimedelta (seconds delta = '+str(self.ServerTimedelta.total_seconds())+')\n')
				except:
					self.logger.exception('')
					self.ServerTimedelta = datetime.timedelta()
				return True


class MainHandler(tornado.web.RequestHandler):
	def initialize(self, C):
		self.C = C

	def get(self):
		self.write('<html><body><form action="/'+settings.CONTROLLER_PROXY_PATH+'/" method="post">'
			'<input type="password" name="key">'
			'<input type="checkbox" name="restart" value="1">Reload Sensor Tables'
			'<input type="submit" value="quit">'
			'</form></body></html>')
		
	def post(self):
		self.set_header("Content-Type", "text/plain")
		msg = '<html><body>indeterminate</body></html>'
		quitnow = False
		try:
			#check the key
			if self.get_argument("key") != settings.WEB_ACCESS_CODE:
				raise
			if self.get_argument("restart",default='') == '1':
				msg = '*** Restarting ...'
				C.restart()
			else:
				msg = '*** all threads have stopped ***   this server will self destruct in 2 seconds ...'
				C.quit()
				quitnow = True
			
		except:
			msg = '*** ERROR ***'
		finally:
			self.write(msg)
			if quitnow:
				time.sleep(2)
				tornado.ioloop.IOLoop.instance().stop()

class OutputHandler(tornado.web.RequestHandler):
	def initialize(self, C):
		self.C = C

	def get(self):
		self.write(tornado.escape.url_unescape(C.Output.replace('\n','<BR>')))


C=Controller()
C.start()
logger.info('Waiting for Controller to start...')
i = 100
while(not C.activeflag and --i > 1):
	time.sleep(0.1)
logger.info('Controller Started')

listURL = [
	(r"/"+settings.CONTROLLER_PROXY_PATH, MainHandler, dict(C=C)),
	(r"/"+settings.CONTROLLER_PROXY_PATH+r"/", MainHandler, dict(C=C)),
	(r"/"+settings.CONTROLLER_PROXY_PATH+r"/output", OutputHandler, dict(C=C))
]

for interface in C.interfaces:
	logger.info('Adding WebHandler for interface '+interface)
	t = (r"/"+settings.CONTROLLER_PROXY_PATH+r"/"+interface, sys.modules[interface].WebHandler, dict(C=C))
	listURL.append(t)

logger.info('Starting tornado web server')
tornadoApp = tornado.web.Application(listURL)
tornadoApp.listen(settings.CONTROLLER_PORT)
tornado.ioloop.IOLoop.instance().start()


