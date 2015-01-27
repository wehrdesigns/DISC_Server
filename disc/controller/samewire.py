import logging
import httplib, urllib, serial, time, csv, sys, threading, datetime
from LoggerClasses import *
from math import *
from string import *
import tornado.web
import settings

SECONDS_BETWEEN_QUERY = 0

LastValue = {} # initialize a dictionary of last value for each ID
LastUpdate = {} # initalize a dictionary of last time increment for each ID in (increment might be second, minute, hour, day)

Bluetooth = True
spError = {}; # initialize a dictionary that will count errors for an ID

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
		self.print1('*** Stopping Samewire thread ***')
		self.qprint1()
		self.__active = False
		while not self.__complete:
			time.sleep(1)
			self.print1('*** waiting to stop Samewire thread ***')
		self.__myThread._Thread__stop
		self.__myThread._Thread__delete

	def print1(self,text):
		self.msg += text+'\n'

	def qprint1(self):
		self.MT.printQ.put(self.msg)
		self.msg = ''

	def load_sensor_table_url(self, strURL):
		try:
			f = urllib.urlopen(strURL)
			strPage = f.read()
		except:
			strPage = None
		finally:
			if strPage == None:
				self.print1 ('Unable to connect')
			return strPage
				
	strdata = r"""<html><head>my head</head><body><table><tr><td>ID</td><td>Name</td><td>Desc</td></tr><tr><td>0</td><td>1</td><td>2</td></tr><tr><td>3</td><td>4</td><td>5</td></tr></table></body></html>"""

	def close_comm_ports(self, sp):
		for CP in sp:
			self.print1 ('Closing comm port: '+CP)
			sp[CP].close()
			if sp[CP].isOpen():
				self.print1 ('Unable to close: '+CP)
					
	def run(self):
		self.print1("Samewire interface started.")
#		try:
		url_table = 'http://'+settings.HTTP_HOST+':'+settings.HTTP_PORT+'/'+settings.HTTP_PROXY_PATH+'/samewire/active_sensors'
		strdata = self.load_sensor_table_url(url_table)
		if not strdata:
			self.print1('Unable to load Sensor Table from URL: '+url_table)
			self.MT.quit()
			
		p = MyHTMLTableParser(0)
		p.feed(strdata)
		p.close()

		index = p.table()[0].index('samewire')
		p = MyHTMLTableParser(index)
		p.feed(strdata)
		p.close()
		
		s = SensorList()
		s.load_table(p.table())

		sp = {} # initialize a dictionary for the serial ports

		if self.logger.isEnabledFor(logging.DEBUG):
			self.print1 (str(s.get_table_header()))
#		except:
#			print "Failed to start logger"
			
#	def LoggerLoop(self):
		#Initialize Comm Ports - because opening and closing them often can cause instability
		self.print1 ('Initializing sensors for Controller: '+settings.CONTROLLER_NAME+' (if this controller name does not match a name on the disc server, then nothing will happen...')
		self.qprint1()
		try:
			for ID in s.get_id_list():
#				print ID,s.get(ID,'Active'), s.get(ID,'DataID'),s.get(ID,'ScaleFactors'),s.get(ID,'Scaling')
#				print s.get(ID,'Samewire_Master.CommPort'),s.get(ID,'Samewire_Master.Baudrate')
				if s.get(ID,'Active') == 'True' and s.get(ID,'Controller.Name') == settings.CONTROLLER_NAME:
					LastValue[ID] = 0
					LastUpdate[ID] = datetime.datetime.now()
					CP = s.get(ID,'Master.CommPort')
					self.print1 (ID + ', ' + CP)
					spError[ID] = 0
					if sp.has_key(CP):
						self.print1 ('Re-using comm port: ' + CP)
					else:
						self.print1 ('Initializing Comm Port ' + CP + ' for ID ' + ID)
						sp[CP]=serial.Serial()
						sp[CP].port = CP
						sp[CP].baudrate = s.get(ID,'Master.Baudrate')
						
						#if s.get(ID,'DataBitsParityStopBit') == '8N1':
						sp[CP].bytesize = serial.EIGHTBITS
						sp[CP].stopbits = serial.STOPBITS_ONE
						sp[CP].parity = serial.PARITY_NONE
						#elif s.get(ID,'DataBitsParityStopBit') == '7N1':
						#	sp[CP].bytesize = serial.SEVENBITS 
						#	sp[CP].stopbits = serial.STOPBITS_ONE
						#	sp[CP].parity = serial.PARITY_NONE
						#else:
						#	self.print1 ('DataBitsParityStopBit ' + s.get(ID,'DataBitsParityStopBit') + ' not supported')
						sp[CP].timeout = 1
						
						try:
							if sp[CP].isOpen():
								self.print1 (CP+' is already open')
							else:
								self.print1 ('Opening ' + CP)
								sp[CP].open()
						except KeyboardInterrupt:
							raise KeyboardInterrupt
						except:
							self.print1 ('Unable to open comm port: '+CP)
						finally:
							if sp[CP].isOpen():
								self.print1 (CP+' opened')
							else:
								self.print1 ('failed to open ' + CP)
							self.qprint1()
				else:
					if s.get(ID,'Active') == 'True':
						self.print1('ignore controller: '+s.get(ID,'Controller.Name')+' for id '+str(ID))
				self.qprint1()
				
		except KeyboardInterrupt:
			raise KeyboardInterrupt

		try:
			while self.__active:		
				LastSecond = datetime.datetime.now().second
#				if settings.CLEAR_TEXT_BOXES:
#					self.MT.deleteText()
#					self.MT.deleteText2()
				#Send CR to each comm port
#				for CP,v in sp.iteritems():
#					if sp[CP].isOpen():
#						self.print1 ('Send CR to: '+sp[CP].port)
#						sp[CP].write('\r')
#						time.sleep(0.01)
				#Query Data from Sensors
#				import pdb;pdb.set_trace()
				for ID in s.get_id_list():
					CP = s.get(ID,'Master.CommPort')
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
								if sp[CP].isOpen():
									if self.logger.isEnabledFor(logging.DEBUG):
										self.print1 ("ready to query "+ID)
									self.query_and_log(ID, sp[CP], s)
								else:
									self.print1 ('Comm port '+CP+' is not open for ID '+ID)
						except KeyboardInterrupt:
							raise KeyboardInterrupt
						except:
							self.print1 ('Error while servicing ID '+ID)
						finally:
							if self.logger.isEnabledFor(logging.DEBUG):
								self.print1 (ID+' query complete')
							if QueryNow:
								self.qprint1()
					#check for query from web interface before next ID is queried
					if not self.MT.CmdQ['samewire'].empty():
						self.process_cmd(sp, s)
				
				while datetime.datetime.now().second == LastSecond and self.__active:
					if not self.MT.CmdQ['samewire'].empty():
						self.process_cmd(sp, s)
					time.sleep(0.2)
				
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		finally:
			self.close_comm_ports(sp)
			self.__complete = True


	def log_error(strError):
		pass
#		f=open('..\datastore\EnvironmentErrorLog.txt','a')
#		f.write(time.strftime("%m/%d/%Y %H:%M:%S",time.localtime()) + ',  ' + strError + '\n')
#		f.close
			
	def query_and_log(self, ID, sp, SList):
		s = SList
		Address = s.get(ID,'Serf.Address')
		SensorGroup = s.get(ID,'Group')
		Cmd = s.get(ID,'Command')
		Cmd = Cmd + '\r'
		RespTerm = ''
		RespTerm = '\r'
		SensorName = s.get(ID,'Type').lstrip(' ').rstrip(' ') + ', ' + s.get(ID,'Name').lstrip(' ').rstrip(' ')
		ScaleFactors = str(s.get(ID,'ScaleFactors'))
		Timebase = s.get(ID,'Timebase')
		DelayBetweenCommands = 0.3
		DelayAfterFailedCommand = 1
		
		#Test comm port
#		if not sp.isOpen():
#			print 'Re-initializing Comm Port '+sp.port
		
		try:
			self.print1 ('\n'+ID+', '+SensorName)
			self.print1 ('Cmd: '+Address+Cmd)
			if self.logger.isEnabledFor(logging.DEBUG):
				self.print1 ('SensorName '+str(SensorName))
				self.print1 ('Comm Port '+str(sp.port))
				self.print1 ('Scale Factors '+str(ScaleFactors))
			retry = 0
			resp = ''
			RcvID = ''
			RcvValue = ''
			Value = 0.0
			time.sleep(0.7)
			self.print1 ('LastValue'+str(LastValue[ID])+'\n')
			MissingAddress = True
			MissingRespTerm = True
			ValueBadRange = False
			
			#while (RcvID != Address and resp.find(RespTerm) == -1 and retry < 3) or ((abs(float(LastValue[ID]) - Value) > 0.1 * float(LastValue[ID])) and retry < 2 and LastValue[ID] != 0):
			while ((MissingAddress or MissingRespTerm or ValueBadRange) and retry < 4):
				sp.flushInput()
				for c in Address+Cmd:
					sp.write(c)
					time.sleep(0.01)
#				time.sleep(0.7)
#				time.sleep(0.01 * 10) #multiply by expected characters
				if self.logger.isEnabledFor(logging.DEBUG):
					self.print1 ('Characters waiting: '+str(sp.inWaiting()))
				i = 0
				resp = ''
				while resp.find(RespTerm) == -1 and i < 20:
					time.sleep(0.1)
					resp = resp + sp.read(sp.inWaiting())
					i = i + 1
				self.print1 ('Characters received: '+str(len(resp)))
				SendValue = True
				RcvID = resp[0:1]
				if RcvID == Address:
					self.print1 ('Response: '+resp)
					self.print1 ('')
					MissingAddress = False
				else:
					MissingAddress = True
					self.print1 ('Missing Address')
					SendValue = False
					RcvID = ''
#					self.print1 ('*No address found*')
#					for c in resp:  #remove non-alphanumeric characters because they cannot be displayed on a webpage by tornado (they choke the utf-8 encoder)
#						if c.isalnum():
#							respFilter +=c
#						else:
#							respFilter +='*'
#					self.print1 ('Alpha-Numeric characters: '+respFilter)
#					self.print1 ('')
				if self.logger.isEnabledFor(logging.DEBUG):
					self.print1 ('RcvID '+RcvID)
					
				if resp.find(RespTerm) > -1:
					RcvValue = resp[1:resp.find(RespTerm)]#remove ID and everything from the RespTerm on
					MissingRespTerm = False
				else:
					SendValue = False
					MissingRespTerm = True
					self.print1 ('Missing Response Termination')

				if self.logger.isEnabledFor(logging.DEBUG):
					self.print1 ('RcvValue '+RcvValue)
				retry += 1

				if MissingAddress or MissingRespTerm:
#					self.log_error(str('No CR, '+str(ID)+', '+str(Address+Cmd)+', '+str(resp)).replace('\r',';').replace('\n',';'))
					time.sleep(DelayAfterFailedCommand)
					self.print1 ('Delay after failed command')
				else:
					SendValue = True
					try:
						Value = float(RcvValue)
						LastValue[ID] = Value
						if s.get(ID,'ScaleFactors') != '':
							Value = eval(ScaleFactors.replace('?',str(Value)))
							self.print1 ('Scaled with ScaleFactor' + str(Value))
						ValueBadRange = False
					except:
						SendValue = False
						ValueBadRange = True

#				if LastValue[ID] > 1 and Value > 1:#ignore binary - also, some functions reset binary state to 0 when read so re-reading will always be 0
#					if (abs(Value) < 0.7 * abs(LastValue[ID]) or abs(Value) > 1.3 * abs(LastValue[ID])):
#						ValueBadRange = True
#						SendValue = False
#					else:
#						ValueBadRange = False
#				else:
#					ValueBadRange = False
				
			if self.logger.isEnabledFor(logging.DEBUG):
				for x in RcvValue:
					self.print1 ("'"+str(x)+"' "+str(ord(x)))
				self.print1 ('MissingAddress '+str(MissingAddress))
				self.print1 ('MissingRespTerm '+str(MissingRespTerm))
				self.print1 ('ValueBadRange '+str(ValueBadRange))

			RecordDateTime = (datetime.datetime.now() - self.MT.ServerTimedelta).strftime("%Y-%m-%d %H:%M:%S")
			self.print1 ('Value: '+str(Value)+'		'+RecordDateTime)

			if SendValue:
				#self.http_post_data(s.get(ID,'DataID'),Value,RecordDateTime)
				self.MT.Q.put((s.get(ID,'DataID'),Value,RecordDateTime,Timebase))
				if spError[ID] > 0:
					spError[ID] = 0
			else:
				spError[ID] += 1
				if spError[ID] > 3:
					spError[ID] = 0
					if Bluetooth:
						if sp.isOpen():
							sp.close()
						time.sleep(8)
						sp.open()
						time.sleep(0.5)
					
			time.sleep(DelayBetweenCommands)
			
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		except:
			self.print1 ('Error while querying and logging ID '+ID)

	def process_cmd(self, sp, s):
		msg = ''
		cmd = ''
		resp = 'error'
		q_ticket = datetime.datetime.now()
		CP = ''
		try:
			q_ticket,cmd = self.MT.CmdQ['samewire'].get()
			address = cmd[0:1]
			for ID in s.get_id_list():
				a = s.get(ID,'Serf.Address')
				if address == a:
					CP = s.get(ID,'Master.CommPort')
					break
			if sp.has_key(CP):
				resp = self.get_response(sp[CP],cmd)
			else:
				resp = 'Serial Port address not found for samewire address: '+address
		finally:
			self.MT.RespQ['samewire'].put([q_ticket,cmd,resp])

	def get_response(self,sp,cmd):
		cmd = str(cmd) #serial port does not accept unicode so force them to strings
		resp = ''
		cmd += '\r'
		i=5
		try:
			time.sleep(0.7)
			sp.flushInput()
#			sp.write(cmd)
			for c in cmd:
				sp.write(c)
				time.sleep(0.01)
			time.sleep(0.1)
			i = 0
			while resp.find('\r') == -1 and i < 20:
				time.sleep(0.1)
				resp += sp.read(sp.inWaiting())
				i = i + 1
		except:
			self.logger.exception('processing get_response')
			err_type, value, traceback = sys.exc_info()#[:2]
			resp = 'Unexpected error in get_response:<BR>Type:' + str(err_type)+'<BR>Value:'+str(value)+'<BR>Traceback:'+str(traceback)
		finally:
			return resp.replace('\r','').replace('\n','')


class WebHandler(tornado.web.RequestHandler):
	def initialize(self, C):
		self.C = C
		self.logger = logging.getLogger(__name__+'.WebHandler')
		self.msg = ''
		
	def print1(self,text):
		self.msg += text+'\n'

	def qprint1(self):
		self.C.printQ.put(self.msg)
		self.msg = ''

	def get(self):
		self.write('<html><body>'+self.get_form()+'</body></html>')
#		self.write('<html><body>'
#				   '<form action="/'+settings.CONTROLLER_PROXY_PATH+'/samewire" method="post"><input type="password" name="key"></form>'
#				   '</body></html>')

	def post(self):
		#self.set_header("Content-Type", "text/plain")
		try:
			msg = ''
			resp = ''
			#check the key
			if True:#self.get_argument('key',default='') == settings.WEB_ACCESS_CODE:
				cmd = str(self.get_argument('cmd',default='FV'))
				port = self.get_argument('port',default='')
				pin = self.get_argument('pin',default='')
				address = str(self.get_argument('address',default=''))
				manualcmd = str(self.get_argument('manualcmd',default=''))
				sendcmd = address+cmd+port+pin #default command
				if manualcmd != '':
					sendcmd = address+manualcmd
				if len(cmd) == 4: #this will be the default for advanced commands
					sendcmd = address+cmd+pin+','+self.get_argument('programvalue',default='')
				if cmd == 'PTP:' or cmd == 'PTO:' or cmd == 'PTM:' or cmd == 'PID:' or cmd == 'PCS:' or cmd == 'PTA:':
					sendcmd = address+cmd+self.get_argument('programvalue',default='')
				if cmd == 'RST:' or cmd == 'SCI:':
					sendcmd = address+cmd+'  '
				if cmd == 'PPP:':
					sendcmd = address+cmd+port+pin+','+self.get_argument('programvalue',default='')
				if (cmd == 'PM1:') or (cmd == 'PO1:') or (cmd == 'PA1:'):
					sendcmd = address+cmd+pin+','+self.get_argument('programvalue',default='')
				if cmd != '' and address != '':
					resp = self.execute_cmd(sendcmd)
					import string
					f = lambda c: c in string.printable
					resp = filter(f, resp)
				else:
					resp = 'Invalid address or command'
				msg = '<html><body><table><tr><td>Command</td><td>'+sendcmd+'</td></tr><tr><td>Response</td><td>'+resp+'</td></tr></table>'+self.get_form()+'</body></html>'
			else:
				msg = '<html><body>'+'access code not valid<BR><BR>'+'<form action="/'+settings.CONTROLLER_PROXY_PATH+'/samewire" method="post"><input type="password" name="key"></form>'+'</body></html>'
		except:
			self.logger.exception('')
			err_type, value, traceback = sys.exc_info()#[:2]
			msg = 'Unexpected error while processing form post:<BR>Type:' + str(err_type)+'<BR>Value:'+str(value)+'<BR>Traceback:'+str(traceback)
		finally:
			self.write(tornado.escape.url_unescape(msg))

	def execute_cmd(self,cmd):
		q_ticket = datetime.datetime.now()
		self.C.CmdQ['samewire'].put([q_ticket,cmd])
		self.print1 ('Execute Command: '+cmd)
		msg = 'No Response'
		cnt = 100
		while msg == 'No Response':
			time.sleep(0.1)
			cnt -= 1
			if not self.C.RespQ['samewire'].empty():
				Qt,Qcmd,msg = self.C.RespQ['samewire'].get()
				if q_ticket == Qt and Qcmd == cmd:
					if not msg:
						msg = 'No Response'
				else:
					# delete the queue item if it become too old -- we don't want the queue to fill up with orphans
					if (Qt + datetime.timedelta(minutes=5) > datetime.datetime.now()):
						self.C.RespQ['samewire'].put([Qt,Qcmd,msg]) #put the queue item back in the queue because it doesn't match the cmd, it was generated by a different thread
					msg = 'No Response'
			if cnt == 0:
				msg = 'No response from samewire for command: '+cmd
		self.print1 ('Response:'+msg)
		self.qprint1()
		return msg

	def get_form(self):
		#'<input type="password" name="key">'
		return str('<form action="/'+settings.CONTROLLER_PROXY_PATH+'/samewire" method="post">'
			'<BR>Address: <input type="text" name="address"><BR>'
			'Select Command:'
			'<table border="1">'
			'<tr><td></td><td>Read Commands</td><td>Write Commands</td></tr>'
			'<tr><td></td><td><ul>'
			'<li><label for="2"><input type="radio" id="2" value="FV" name="cmd" />Firmware Version</label></li>'
			'<li><label for="3.6"><input type="radio" id="3.6" value="CS" name="cmd" />Configuration Status</label></li>'
			'<li><label for="3.7"><input type="radio" id="3.7" value="ID" name="cmd" />ID (if using universal address !)</label></li>'
			'<li><label for="3.8"><input type="radio" id="3.8" value="PF" name="cmd" />Pin Function code for all pins</label></li>'
			'</ul></td><td><ul>'
			'<li><label for="107"><input type="radio" id="107" value="SCI:" name="cmd" />Set all pin function to Input</label></li>'
			'<li><label for="108"><input type="radio" id="108" value="PCS:" name="cmd" />Set WDT Operation I | R | S (Initialize,Run,Stop)</label></li>'
			'<li><label for="109"><input type="radio" id="109" value="PID:" name="cmd" />Program ID</label></li>'
			'<li><label for="110"><input type="radio" id="110" value="RST:" name="cmd" />Reset</label></li>'
			'</ul></td></tr>'
			'<tr><td>Temperature</td><td>Read Commands</td><td>Write Commands</td></tr>'
			'<tr><td></td><td><ul>'
			'<li><label for="3"><input type="radio" id="3" value="TV" name="cmd" />A2D Value</label></li>'
			'<li><label for="3.2"><input type="radio" id="3.2" value="TC" name="cmd" />A2D Count</label></li>'
			'<li><label for="3.3"><input type="radio" id="3.3" value="TP" name="cmd" />Period</label></li>'
			'<li><label for="3.31"><input type="radio" id="3.31" value="TA" name="cmd" />Points Average</label></li>'
			'<li><label for="3.4"><input type="radio" id="3.4" value="TM" name="cmd" />Multiplier</label></li>'
			'<li><label for="3.5"><input type="radio" id="3.5" value="TO" name="cmd" />Offset</label></li>'
			'</ul></td><td><ul>'
			'<li><label for="104"><input type="radio" id="104" value="PTM:" name="cmd" />Multiplier in decimal</label></li>'
			'<li><label for="105"><input type="radio" id="105" value="PTO:" name="cmd" />Offset in decimal</label></li>'
			'<li><label for="106"><input type="radio" id="106" value="PTP:" name="cmd" />Period in decimal</label></li>'
			'<li><label for="106.1"><input type="radio" id="106.1" value="PTA:" name="cmd" />Points Average in decimal</label></li>'
			'</ul></td></tr>'			
			'<tr><td>'
			'<label for="1">Select Port:</label> <ul>'
			'<li><label for="500"><input type="radio" id="500" value="1" name="port" />1</label></li>'
			'<li><label for="501"><input type="radio" id="501" value="2" name="port" />2</label></li>'
			'</ul><label for="1">Select Pin:</label> <ul>'
			'<li><label for="502"><input type="radio" id="502" value="0" name="pin" />0</label></li>'
			'<li><label for="503"><input type="radio" id="503" value="1" name="pin" />1</label></li>'
			'<li><label for="504"><input type="radio" id="504" value="2" name="pin" />2</label></li>'
			'<li><label for="505"><input type="radio" id="505" value="3" name="pin" />3</label></li>'
			'<li><label for="506"><input type="radio" id="506" value="4" name="pin" />4</label></li>'
			'<li><label for="507"><input type="radio" id="507" value="5" name="pin" />5</label></li>'
			'<li><label for="508"><input type="radio" id="508" value="6" name="pin" />6</label></li>'
			'<li><label for="509"><input type="radio" id="509" value="7" name="pin" />7</label></li>'
			'</ul></td><td><ul>'
			'<li><label for="4"><input type="radio" id="4" value="PC:" name="cmd" />Count for Port.Pin</label></li>'
			'<li><label for="5"><input type="radio" id="5" value="PV:" name="cmd" />Value for Port.Pin</label></li>'
			'<li><label for="6"><input type="radio" id="6" value="PM:" name="cmd" />Multiplier for Port.Pin (port 1 only)</label></li>'
			'<li><label for="7"><input type="radio" id="7" value="PO:" name="cmd" />Offset for Port.Pin (port 1 only)</label></li>'
			'<li><label for="8"><input type="radio" id="8" value="PP:" name="cmd" />Period for Port.Pin</label></li>'
			'<li><label for="9"><input type="radio" id="9" value="PA:" name="cmd" />Points Average for Port.Pin</label></li>'
			'</ul></td><td><ul>'
			'<li><label for="100"><input type="radio" id="100" value="PPP:" name="cmd" />Pin Period ports 1,2(decimal)</label></li>'
			'<li><label for="101"><input type="radio" id="101" value="PM1:" name="cmd" />Multiplier port 1 (decimal)</label></li>'
			'<li><label for="102"><input type="radio" id="102" value="PO1:" name="cmd" />Offset port 1 (decimal)</label></li>'
			'<li><label for="103"><input type="radio" id="103" value="PA1:" name="cmd" />Points Averaging port 1 (decimal)</label></li>'
			'<ul></td></tr>'
			'</table>'
			'Value for Write commands: <input type "text" name="programvalue">'
			'<BR>Enter raw commands here: <input type="text" name="manualcmd">'
			'<BR><input type="submit" value="Send Command">'
			'</form>')
