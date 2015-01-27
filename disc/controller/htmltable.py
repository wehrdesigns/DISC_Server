import logging
import httplib, urllib2, serial, time, csv, sys, threading, datetime
from LoggerClasses import *
from math import *
from string import *
import tornado.web
import settings
import subprocess

SECONDS_BETWEEN_QUERY = 0

LastValue = {} # initialize a dictionary of last value for each ID
LastUpdate = {} # initalize a dictionary of last time increment for each ID in (increment might be second, minute, hour, day)

dictTimeDelta = {}
dictTimeDelta['seconds'] = datetime.timedelta(seconds=1)
dictTimeDelta['minutes'] = datetime.timedelta(seconds=60)
dictTimeDelta['hours'] = datetime.timedelta(seconds=3600)
dictTimeDelta['days'] = datetime.timedelta(days=1)


class Logger(threading.Thread):
	def __init__(self, mainThread):
		threading.Thread.__init__(self)
		self.__myThread = threading.Thread
		self.MT = mainThread
		self.msg = ''
		self.__active = True
		self.__complete = False
		self.logger = logging.getLogger(__name__+'.Logger')

	def quit(self):
		self.print1('*** Stopping HTMLTable thread ***')
		self.qprint1()
		self.__active = False
		while not self.__complete:
			time.sleep(1)
			self.print1('*** waiting to stop HTMLTable thread ***')
		self.__myThread._Thread__stop
		self.__myThread._Thread__delete

	def print1(self,text):
		self.msg += text+'\n'

	def qprint1(self):
		self.MT.printQ.put(self.msg)
		self.msg = ''

        def subprocess_load_sensor_table_url(self, script):
                output = ''
                try:
                        output = subprocess.check_output(['python',script])
                except:
                        print 'subprocess error'
                return output
        
	def load_sensor_table_url(self, strURL):
		try:
                        if strURL[-3:].lower() == '.py':
                                script = strURL.replace('http://www.myscript.com/','')
                                self.print1('Executing script: '+script)
                                strPage = self.subprocess_load_sensor_table_url(script)
                        else:
                                self.print1('Loading URL '+strURL)
                                try:
                                        f = urllib2.urlopen(strURL,)
#                                        print 'Server returned code '+str(f.code)
                                        if f.code == 200 and f.info() != '':
#                                                print 'Read URL...'
                                                strPage = ''.join(f.readlines())
#                                                print 'Read URL '+str(len(strPage))+' characters'
                #				#print 'HTML Content: ' + strPage
                                        else:
                                                strPage = None
                                except urllib2.URLError as e:
                                        print 'urllib2 URLError'
                                        strPage = None
                                except socket.timeout as e:
                                        print 'socket timeout'
                                        strPage = None
                                except KeyboardInterrupt:
                                        print 'caught keyboard interrupt'
                                except:
                                        print 'caught an error'
                                finally:
                                        try:
                                                f.close()
                                        except:
                                                pass
		except:
			self.logger.exception('Reading url')
			print 'Error reading url'
			self.print1('Error reading url '+strURL)
			strPage = None
		finally:
			if strPage == None:
				self.print1 ('Unable to connect or read from URL '+strURL)
			return strPage
				
	strdata = r"""<html><head>my head</head><body><table><tr><td>ID</td><td>Name</td><td>Desc</td></tr><tr><td>0</td><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td><td>5</td></tr></table></body></html>"""

	def run(self):
		self.print1("HTMLTable interface started.")
#		try:
		url_table = 'http://'+settings.HTTP_HOST+':'+settings.HTTP_PORT+'/'+settings.HTTP_PROXY_PATH+'/htmltable/active_sensors'
		strdata = self.load_sensor_table_url(url_table)
		if not strdata:
			self.print1('Unable to load Sensor Table from URL: '+url_table)
			self.MT.quit()
		
		p = MyHTMLTableParser(0)
		p.feed(strdata)
		p.close()
		
		index = p.table()[0].index('htmltable')
		p = MyHTMLTableParser(index)
		p.feed(strdata)
		p.close()

		s = SensorList()
		s.load_table(p.table())

		dictTable = {} # initialize a dictionary for the table data
		dictTableLoadTime = {}

		if self.logger.isEnabledFor(logging.DEBUG):
			self.logger.debug(str(s.get_table_header()))
#		except:
#			print "Failed to start logger"
			
#	def LoggerLoop(self):
		#Initialize HTMLTables
		self.print1 ('Initializing sensors for Controller: '+settings.CONTROLLER_NAME+' (if this controller name does not match a name on the disc server, then nothing will happen...')
		try:
			for ID in s.get_id_list():
#				print ID,s.get(ID,'Active'), s.get(ID,'DataID'),s.get(ID,'Controller.Name'),settings.CONTROLLER_NAME
				if s.get(ID,'Active') == 'True' and s.get(ID,'Controller.Name') == settings.CONTROLLER_NAME:
					LastValue[ID] = 0
					LastUpdate[ID] = datetime.datetime.now()
					URL = urllib2.unquote(s.get(ID,'HTMLTable.URL'))
					tableid = s.get(ID,'HTMLTable.id')
					TableIndex = s.get(ID,'TableIndex')
					self.print1 (ID + ', ' + TableIndex + ', ' + URL + ', ' + tableid)
					if dictTable.has_key(str(tableid)+str(TableIndex)):
						self.print1 ('Re-using URL: ' + URL)
					else:
						self.print1 ('Initializing URL ' + URL + ' with ID ' + ID)
						#Load URL here to verify connection
						try:
#							if urllib2.urlopen(URL):
#								self.print1 (URL+' is accessible')
							strdata = self.load_sensor_table_url(URL)
							if strdata == '':
								self.print1('No data found at URL: '+URL)
								#try again once
								time.sleep(3)
								strdata = self.load_sensor_table_url(URL)
#								self.MT.quit()
							p = MyHTMLTableParser(int(TableIndex) - 1)
							p.feed(strdata)
							p.close()
			
							dictTable[str(tableid)+str(TableIndex)] = p.table()
							dictTableLoadTime[str(tableid)+str(TableIndex)] = datetime.datetime.now()

						except KeyboardInterrupt:
							raise KeyboardInterrupt
						except:
							self.print1 ('Unable to read and parse URL: '+URL)
							self.logger.exception('Unable to read and parse URL: '+URL)
						finally:
							pass
				else:
					if s.get(ID,'Active') == 'True':
						self.print1('ignore controller: '+s.get(ID,'Controller.Name')+' for id '+str(ID))
				self.qprint1()

		except KeyboardInterrupt:
			raise KeyboardInterrupt
		except:
			self.logger.exception('')

		try:
			while self.__active:
				#time.sleep(5)
				LastSecond = datetime.datetime.now().second
#				if settings.CLEAR_TEXT_BOXES:
#					self.MT.deleteText()
#					self.MT.deleteText2()
				#Parse data from table
				for ID in s.get_id_list():
					if s.get(ID,'Active') == 'True' and s.get(ID,'Controller.Name') == settings.CONTROLLER_NAME and self.__active:
						try:
#							print str(LastUpdate[ID]),' --- ',str(datetime.datetime.now())
							QueryNow = False
							Timebase = s.get(ID,'Timebase')
							Period = int(s.get(ID,'Period'))
							if Timebase == 'seconds':
								if LastUpdate[ID] <= datetime.datetime.now():
									QueryNow = True
									LastUpdate[ID] = (datetime.datetime.now() + datetime.timedelta(seconds=Period)).replace(microsecond=0)
							elif Timebase == 'minutes':
								if LastUpdate[ID] <= datetime.datetime.now():
									QueryNow = True
									LastUpdate[ID] = (datetime.datetime.now() + datetime.timedelta(minutes=Period)).replace(second=0,microsecond=0)
							elif Timebase == 'hours':
								if LastUpdate[ID] <= datetime.datetime.now():
									QueryNow = True
									LastUpdate[ID] = (datetime.datetime.now() + datetime.timedelta(hours=Period)).replace(minute=0,second=0,microsecond=0)
							elif Timebase == 'days':
								if LastUpdate[ID] <= datetime.datetime.now():
									QueryNow = True
									LastUpdate[ID] = (datetime.datetime.now() + datetime.timedelta(days=Period)).replace(hour=0,minute=0,second=0,microsecond=0)

							if QueryNow:
								self.query_and_log(ID, dictTable, dictTableLoadTime, s)
								if self.logger.isEnabledFor(logging.DEBUG):
									self.print1 (ID+' query complete')
						except KeyboardInterrupt:
							raise KeyboardInterrupt
						except:
							self.print1 ('Error while evaluating when to query ID '+ID)
							self.logger.exception('Error while evaluating when to query ID '+ID)
						finally:
							pass
#				self.print1 ("Last Second "+LastSecond)
#				self.print1 ("Sleeping until next minute...")
				while datetime.datetime.now().second == LastSecond and self.__active:
					time.sleep(0.5)
				
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		except:
			self.logger.exception('')
		finally:
			self.__complete = True

	def log_error(strError):
		f=open('..\datastore\EnvironmentErrorLog.txt','a')
		f.write(time.strftime("%m/%d/%Y %H:%M:%S",time.localtime()) + ',  ' + strError + '\n')
		f.close

	def query_and_log(self, ID, dictTable, dictTableLoadTime, SList):
		s = SList
		SensorGroup = s.get(ID,'Group')
		Row = s.get(ID,'Row')
		Col = s.get(ID,'Column')
		TableIndex = s.get(ID,'TableIndex')
		SensorName = s.get(ID,'Type').lstrip(' ').rstrip(' ') + ', ' + s.get(ID,'Name').lstrip(' ').rstrip(' ')
		ScaleFactors = str(s.get(ID,'ScaleFactors'))
		URL = urllib2.unquote(s.get(ID,'HTMLTable.URL'))
		TableIndex = s.get(ID,'TableIndex')
		Timebase = s.get(ID,'Timebase')
		tableid = s.get(ID,'HTMLTable.id')
		t = []
		
		try:
			self.print1 ('\n'+ID+', '+SensorName+', '+Timebase)
			self.print1 ('TableIndex,Row,Col: '+str(TableIndex)+','+str(Row)+','+str(Col))
			if self.logger.isEnabledFor(logging.DEBUG):
				self.logger.debug('Scale Factors '+str(ScaleFactors))
				self.logger.debug('URL '+str(URL))
			Value = 0
			#import pdb;pdb.set_trace()
			if (datetime.datetime.now() - dictTableLoadTime[str(tableid)+str(TableIndex)]) > dictTimeDelta[Timebase]:
				strdata = self.load_sensor_table_url(URL)
				if not strdata:
					#try again once
					time.sleep(0.5)
					strdata = self.load_sensor_table_url(URL)
				if not strdata:
					self.print1('Unable to load Sensor Table from URL: '+URL)
#					self.MT.quit()
				else:
					p = MyHTMLTableParser(int(TableIndex) - 1)
					p.feed(strdata)
					p.close()

					dictTable[str(tableid)+str(TableIndex)] = p.table()
					dictTableLoadTime[str(tableid)+str(TableIndex)] = datetime.datetime.now()
					t = p.table()
			else:
				t = dictTable[str(tableid)+str(TableIndex)]
			if t:
				Value = t[int(Row)][int(Col)]

                                try:
					if ScaleFactors:
						Value = eval(ScaleFactors.replace('?',str(Value)))
						if self.logger.isEnabledFor(logging.DEBUG):
							self.print1 (dictTable[str(tableid)+str(TableIndex)][int(Row)][int(Col)]+' scaled to ' + str(Value))
                                except:
                                        pass
				RecordDateTime = (datetime.datetime.now() - self.MT.ServerTimedelta).strftime("%Y-%m-%d %H:%M:%S")
				self.print1 ('Value: '+str(Value)+'		'+RecordDateTime)

				if Value != '':
					#self.http_post_data(s.get(ID,'DataID'),Value,RecordDateTime)
					self.MT.Q.put((s.get(ID,'DataID'),Value,RecordDateTime,Timebase))
			else:
				self.print1 ('Error loading table for DataID '+str(ID))
				
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		except:
			self.print1 ('Error while querying and logging ID '+ID)
			self.logger.exception('Error while querying and logging ID '+ID)


class WebHandler(tornado.web.RequestHandler):
	def initialize(self, C):
		self.C = C
		self.logger = logging.getLogger(__name__+'.WebHandler')

	def get(self):
		self.write('<html><body>'
				   'Web Handler for HTML Table'
				   '</body></html>')

	def post(self):
		self.write('<html><body>'
				   'Web Handler for HTML Table'
				   '</body></html>')
