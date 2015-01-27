#! /usr/bin/env python
import os
import sys
import json
import signal
import time

import tornado.httpserver
import tornado.ioloop
import tornado.wsgi
import tornado.web

import django.core.handlers.wsgi

os.environ.setdefault('LANG','en_US')

admin_wsgi_app = tornado.wsgi.WSGIContainer(django.core.handlers.wsgi.WSGIHandler())

import logging

class BufferSizeHandler(logging.Handler):
	def __init__(self, capacity):
		logging.Handler.__init__(self)
		self.capacity = capacity
		self.buffer = []
		self.formatter = logging.Formatter('<td>%(name)-40s</td><td>%(levelname)-8s</td><td>%(message)s</td>')
		
	def flush(self):
		self.buffer = self.buffer[self.capacity:]

	def gethtml(self):
		s = '<table>'
		for r in self.buffer:
			s += '<tr>' + self.formatter.format(r) + '</tr>'
		return s+'</table>'

	def shouldFlush(self, record):
		return (len(self.buffer) >= self.capacity)

	def emit(self, record):
		self.buffer.append(record)
		if self.shouldFlush(record):
			self.flush()

	def close(self):
		self.buffer = []
		logging.Handler.close(self)

class ServerStatusLoggingHandler(tornado.web.RequestHandler):
	def initialize(self):
		pass
		
	def get(self):
		self.write('<html><title>DISC Server Status Logging</title>'
				+'<script type="text/javascript">'
				+'location.hash = "bottomofpage";'
				+'</script>'
				+'<body>'
				+'<BR>'+htmlloggingbuffer.gethtml()
				+'<div id="bottomofpage"></div>'
				+'</body></html>')

class MainHandler(tornado.web.RequestHandler):
	def initialize(self):
		pass
		
	def get(self):
		self.write('<html><title>DISC Server</title><body>'
				+'<BR><a href="/'+HTTP_PROXY_PATH+'/login">DISC Server Login</a>'
				+'<BR><BR><a href="/'+HTTP_PROXY_PATH+'/env/">DISC Server Index</a>'
				+'</body></html>')

def stop_server():
	tornadoserver.stop()

def handleSigTERM(signum,stackframe):
	from discengines import START_ACTIONLABENGINE, USE_SQLITE_QUEUED_MEMORY_MANAGER
	if START_ACTIONLABENGINE:
		from discengines import ALE
		logger.critical('stopping actionlab engine...')
		ALE.quit()
		logging.info('Action Lab Engine Stopped')
	if USE_SQLITE_QUEUED_MEMORY_MANAGER:
		#this will save data to file for all timebases
		logger.critical('stopping sqlite engine...')
		discengines.datatable.stop_sqlite_engine()
	else:
		import os
		time.sleep(1)
		os._exit(os.R_OK)

if __name__ == "__main__":

	logger = logging.getLogger()
	#logger.setLevel(logging.DEBUG)
	logger.setLevel(logging.INFO)
	console = logging.StreamHandler(stream=sys.stdout)
	#console.setLevel(logging.DEBUG)
	console.setLevel(logging.WARNING)
	formatter = logging.Formatter('%(name)-40s: %(levelname)-8s %(message)s')
	console.setFormatter(formatter)
	
	#if len(sys.argv) > 1:
	#    if 'console' in sys.argv[1]:
	#        logger.addHandler(console)
	#memoryhandler = logging.handlers.MemoryHandler(1024*10, logging.DEBUG, ch)
	#logger.addHandler(memoryhandler)
	logger.debug('started logger')

	htmlloggingbuffer = BufferSizeHandler(500)
	logger.addHandler(htmlloggingbuffer)

#    import pdb;pdb.set_trace()
	sys.path.append(os.path.join(os.path.abspath('.'),'djangosite'))
	os.environ['DJANGO_SETTINGS_MODULE'] = 'djangosite.settings'
	
	APP_BASE_PATH = os.path.abspath('.')
	jsondict = json.load(open(os.path.join(os.path.join(APP_BASE_PATH,'user'),'config.json'),'r'))
	HTTP_PORT = int(jsondict['HTTP_PORT']['value'])
	HTTP_PROXY_PATH = jsondict['HTTP_PROXY_PATH']['value']
	
	settings = {
		"static_path": "static",
		#"static_path": os.path.join(os.path.dirname(__file__), "static"),
		#"static_path": os.path.join(os.path.dirname(os.path.abspath(__file__)),'static'),
		#"cookie_secret": "61oETzKXQAGaYdkL5gEmGeJJFuYh7EQnp2XdTP1o/Vo=",
		"login_url": "/"+HTTP_PROXY_PATH+"/admin/login/",
		"xsrf_cookies": False,
	}
	application = tornado.web.Application([
		(r"/",MainHandler),
		('/'+HTTP_PROXY_PATH+r"/",MainHandler),
		('/'+HTTP_PROXY_PATH+r"/static/(.*)",tornado.web.StaticFileHandler,dict(path=settings['static_path'])),
#		('/'+HTTP_PROXY_PATH+r"/logging",ServerStatusLoggingHandler),
	#    (r"/login", LoginHandler),
		('/'+HTTP_PROXY_PATH+r"/(apple-touch-icon\.png)",tornado.web.StaticFileHandler,dict(path=settings['static_path'])),
		('/'+HTTP_PROXY_PATH+r"/(favicon\.ico)",tornado.web.StaticFileHandler,dict(path=settings['static_path'])),
		(r".*",tornado.web.FallbackHandler,dict(fallback=admin_wsgi_app)),
	], **settings)

	try:
		import discengines
	except:
		print 'error importing discengines'
		logger.exception('Error importing discengines')

	discengines.htmlloggingbuffer = htmlloggingbuffer

#    access_log = logging.getLogger("tornado.access")
#    access_log.addHandler(console)
#    app_log = logging.getLogger("tornado.application")
#    app_log.addHandler(console)
#    gen_log = logging.getLogger("tornado.general")
#    gen_log.addHandler(console)

	try:
		from postdataserver import PostDataServer
		pds = PostDataServer()
		pds.start()
	except:
		logger.exception('starting post data server')

	import platform
	if platform.system() == 'Linux':		
		for i in [x for x in dir(signal) if x.startswith("SIG")]:
			try:
				signum = getattr(signal,i)
				if signum > 0:
					signal.signal(signum,handleSigTERM)
			except RuntimeError,m:
				logger.debug("Skipping %s"%i)

	logger.info('Starting DISC server on port '+str(HTTP_PORT))
	server = tornado.httpserver.HTTPServer(application)
	server.listen(int(HTTP_PORT))
	tornadoserver = tornado.ioloop.IOLoop.instance()
	tornadoserver.start()
	
