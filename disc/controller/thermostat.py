import logging
import httplib, urllib, serial, time, csv, sys, threading, re, datetime
from LoggerClasses import *
from math import *
from string import *
import tornado.web
import settings

ID_LENGTH = 1
SECONDS_BETWEEN_QUERY = 0

LastValue = {} # initialize a dictionary of last value for each ID
LastUpdate = {} # initalize a dictionary of last time increment for each ID in (increment might be second, minute, hour, day)

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
		self.print1('*** Stopping Thermostat thread ***')
		self.qprint1()
		self.__active = False
		while not self.__complete:
			time.sleep(1)
			self.print1('*** waiting to stop Thermostat thread ***')
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
		self.print1("Thermostat interface started.")
#		try:
		url_table = 'http://'+settings.HTTP_HOST+':'+settings.HTTP_PORT+'/'+settings.HTTP_PROXY_PATH+'/thermostat/active_sensors'
		strdata = self.load_sensor_table_url(url_table)
		if not strdata:
			self.print1('Unable to load Sensor Table from URL: '+url_table)
			self.MT.quit()
			
		p = MyHTMLTableParser(0)
		p.feed(strdata)
		p.close()
		print p.table()
		index = p.table()[0].index('thermostat')
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
					LastValue[ID] = float(0)
					LastUpdate[ID] = datetime.datetime.now()
					CP = s.get(ID,'Thermostat.CommPort')
					self.print1 (ID + ', ' + CP)
					if sp.has_key(CP):
						self.print1 ('Re-using comm port: ' + CP)
					else:
						self.print1 ('Initializing Comm Port ' + CP + ' for ID ' + ID)
						sp[CP]=serial.Serial()
						sp[CP].port = CP
						sp[CP].baudrate = s.get(ID,'Thermostat.Baudrate')
						
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
				for ID in s.get_id_list():
					if s.get(ID,'Active') == 'True' and s.get(ID,'Controller.Name') == settings.CONTROLLER_NAME:
						CP = s.get(ID,'Thermostat.CommPort')
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
								self.qprint1()
						except KeyboardInterrupt:
							raise KeyboardInterrupt
						except:
							self.print1 ('Error while servicing ID '+ID)
						finally:
							if self.logger.isEnabledFor(logging.DEBUG):
								self.print1 (ID+' query complete')
							if QueryNow:
								self.qprint1()

				while datetime.datetime.now().second == LastSecond and self.__active:
					if not self.MT.CmdQ['thermostat'].empty():
						self.process_cmd(sp[CP])#This assumes that only one active thermostat is being used
					time.sleep(0.5)
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		finally:
			self.close_comm_ports(sp)
			self.__complete = True

	def process_cmd(self, sp):
		msg = ''
		cmd = ''
		q_ticket = datetime.datetime.now()
		try:
			q_ticket,cmd = self.MT.CmdQ['thermostat'].get()
			if cmd == 'status':
				resp = self.get_response(sp,'A=1 R=1\r')
				if resp:
					msg += 'Temperature: '+str(re.search('T=[0-9]+\s',resp).group(0)[2:-1])+'\n'
					msg += 'Setpoint Heat: '+str(re.search('SPH=[0-9]+\s',resp).group(0)[4:-1])+'\n'
					msg += 'Setpoint Cool: '+str(re.search('SPC=[0-9]+\s',resp).group(0)[4:-1])+'\n'
					msg += 'HVAC Mode: '+str(re.search('M=[A-Z]\s',resp).group(0)[2:-1])+'\n'
					msg += 'Fan Status: '+str(re.search('FM=[0-1]',resp).group(0)[3:])+'\n'
				else:
					resp = 'No response from thermostat on serial port: '+str(sp.port)
				resp = self.get_response(sp,'A=1 SC=?\r')
				if resp:
					msg += 'Run=1/Hold=0: '+str(re.search('SC=[0-1]',resp).group(0)[3:])+'\n'
			if cmd == 'SP_plus':
				msg = 'Processed command: '+'SP&#43;'
				sp.write('A=1 SP+\r')
			if cmd == 'SP-':
				msg = 'Processed command: '+cmd
				sp.write('A=1 SP-\r')
			if re.search('SPH=',cmd) != None:
				msg = 'Processed command: '+cmd
				sp.write('A=1 '+cmd+'\r')
			if re.search('SPC=',cmd) != None:
				msg = 'Processed command: '+cmd
				sp.write('A=1 '+cmd+'\r')
			if cmd == 'Run':
				msg = 'Processed command: '+cmd
				sp.write('A=1 SC=1\r')
			if cmd == 'Hold':
				msg = 'Processed command: '+cmd
				sp.write('A=1 SC=0\r')
			if cmd == 'Off':
				msg = 'Processed command: '+cmd
				sp.write('A=1 M=O\r')
			if cmd == 'Heat':
				msg = 'Processed command: '+cmd
				sp.write('A=1 M=H\r')
			if cmd == 'Cool':
				msg = 'Processed command: '+cmd
				sp.write('A=1 M=C\r')
		finally:
			self.MT.RespQ['thermostat'].put([q_ticket,cmd,msg])

	def get_response(self,sp,cmd):
		cmd = str(cmd) #serial port does not accept unicode so force all to string
		resp = ''
		try:
			sp.write(cmd)
			print 'the command written was: '+cmd
			time.sleep(0.05)
			c = 0
			while resp.find('\r') == -1 and c < 20:
				resp += sp.read(sp.inWaiting())
				time.sleep(0.05)
				c = c + 1
		except:
			self.logger.exception('processing get_response')
			return 'error'
		finally:
			print 'the comm response: '+resp
			return resp

	def log_error(strError):
		f=open('..\datastore\EnvironmentErrorLog.txt','a')
		f.write(time.strftime("%m/%d/%Y %H:%M:%S",time.localtime()) + ',  ' + strError + '\n')
		f.close
			
	def query_and_log(self, ID, sp, SList):
		s = SList
		SensorGroup = s.get(ID,'Group')
		Cmd = s.get(ID,'Command').replace('\\r','\r').replace('\\n','\n')
#		if s.get(ID,'SendCR') == '1':
#		Cmd = Cmd + '\r'
#		if s.get(ID,'SendLF') == '1':
#			Cmd = Cmd + '\n'
#		RespTerm = ''
#		if s.get(ID,'ResponseCR') == '1':
		RespTerm = s.get(ID,'ResponseTermination').replace('\\r','\r').replace('\\n','\n')
		SensorName = s.get(ID,'Type').lstrip(' ').rstrip(' ') + ', ' + s.get(ID,'Description').lstrip(' ').rstrip(' ')
		#Invert = s.get(ID,'Invert')
		ScaleFactors = str(s.get(ID,'ScaleFactors'))
		respSlice = s.get(ID,'Slice')
		Timebase = s.get(ID,'Timebase')
		ReExp = s.get(ID,'RegularExpression')
		
		#Test comm port
#		if not sp.isOpen():
#			print 'Re-initializing Comm Port '+sp.port
		
		try:
			self.print1 ('\n'+ID+', '+SensorName)
			self.print1 ('Cmd: '+Cmd)
			if self.logger.isEnabledFor(logging.DEBUG):
				self.print1 ('SensorName: '+str(SensorName))
				self.print1 ('Comm Port: '+str(sp.port))
				self.print1 ('Scale Factors: '+str(ScaleFactors))
			retry = 0
			resp = ''
			RcvValue = ''
			Value = 0
			default = 0
			time.sleep(0.7)
			self.print1 ('LastValue: '+str(LastValue[ID])+'\n')
			while (resp.find(RespTerm) == -1 and retry < 3):# or ((abs(LastValue[ID] - Value) > 0.1 * LastValue[ID]) and retry < 2 and LastValue[ID] != 0):
#				sp.flushInput()
				sp.write(Cmd)
#				for c in Cmd:
#					sp.write(c)
#					time.sleep(0.01)
				time.sleep(0.5)
				time.sleep(0.01 * 20) #multiply by expected characters
				self.print1 ('Characters waiting: '+str(sp.inWaiting()))
				c = 0
				resp = ''
				while resp.find(RespTerm) == -1 and c < 100:
					resp = resp + sp.read(sp.inWaiting())
					time.sleep(0.01)
					c = c + 1
				if self.logger.isEnabledFor(logging.DEBUG):
					self.print1('C = '+str(c))
					self.print1 ('Response: '+resp)
					self.print1 ('Found Response Term: '+str(resp.find(RespTerm)))
					self.print1 ('Response Term: '+str(RespTerm))
				respMatch = ''
				if ReExp != '':
					if self.logger.isEnabledFor(logging.DEBUG):
						self.print1 ('Searching with Regular Expression: '+ReExp)
					m = re.search(ReExp,resp)
					if m:
						respMatch = m.group(0)
						if self.logger.isEnabledFor(logging.DEBUG):
							self.print1 ('Regular Expression Search Result for the first group: '+resp)
				if respSlice != '':
					RcvValue = eval('respMatch['+respSlice+']')
				else:
					RcvValue = resp[:resp.find(RespTerm)]#remove everything from the RespTerm on
				#calculate Value if using with LastValue to filter new data
#				Value = default
#				if RcvValue.isdigit():
#					Value = float(RcvValue)
				if self.logger.isEnabledFor(logging.DEBUG):
					self.print1 ('Slice: '+respSlice)
					self.print1 ('RcvValue: '+RcvValue)
				retry += 1
				time.sleep(0.5)
#				if resp.find(RespTerm) == -1:
#					time.sleep(0.05)
#				if resp.find(RespTerm) == -1:
#					self.log_error('No CR, '+str(ID)+', '+str(Cmd)+', '+str(resp))
				if self.logger.isEnabledFor(logging.DEBUG):
				    self.print1 ('retry: '+str(retry))

			if self.logger.isEnabledFor(logging.DEBUG):
				for x in RcvValue:
					self.print1 ("'"+str(x)+"' "+str(ord(x)))

			Value = default
			if RcvValue.isdigit():
				Value = float(RcvValue)
				LastValue[ID] = Value
				if s.get(ID,'ScaleFactors') != '':
					Value = eval(ScaleFactors.replace('?',str(Value)))
					self.print1 ('Scaled with ScaleFactor: ' + str(Value))
					
			RecordDateTime = (datetime.datetime.now() - self.MT.ServerTimedelta).strftime("%Y-%m-%d %H:%M:%S")
			self.print1 ('Value: '+str(Value)+'		'+RecordDateTime)

			if Value != '':
				#self.http_post_data(s.get(ID,'DataID'),Value,RecordDateTime)
				self.MT.Q.put((s.get(ID,'DataID'),Value,RecordDateTime,Timebase))
				
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		except:
			self.print1 ('Error while querying and logging ID '+ID)


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
		statusmsg = self.get_status()
		self.write('<html><body>'
			'Thermostat Status:<BR>'+statusmsg+'<BR>'+self.get_form()+
			'</body></html>')
		
	def post(self):
		#self.set_header("Content-Type", "text/plain")
		try:
			msg = ''
			resp = ''
			#check the key
			if True:#self.get_argument("key") == settings.WEB_ACCESS_CODE:
				cmd = str(self.get_argument("cmd"))
				self.logger.info('the cmd argument: '+cmd)
				if cmd != 'status':
					if cmd == 'SPC':
						cmd = 'SPC='+str(self.get_argument('value'))
					if cmd == 'SPH':
						cmd = 'SPH='+str(self.get_argument('value'))
					resp = self.execute_cmd(cmd)
				statusmsg = self.execute_cmd('status').replace('\n','<BR>')
				msg = '<html><body>'+resp+'<BR><BR>'+statusmsg+'<BR>'+self.get_form()+'</body></html>'
			else:
				msg = '<html><body>'+'password not valid<BR><BR>'+self.get_form()+'</body></html>'
		except:
			msg = 'Error communicating with Thermostat'
			self.logger.exception(str(msg))
		finally:
			self.write(tornado.escape.url_unescape(msg))

	def get_status(self):
		cmd = "status"
		q_ticket = datetime.datetime.now()
		self.C.CmdQ['thermostat'].put([q_ticket,cmd])
		msg = ''
		cnt = 100
		while not msg:
			time.sleep(0.1)
			cnt -= 1
			if not self.C.RespQ['thermostat'].empty():
				Qt,Qcmd,msg = self.C.RespQ['thermostat'].get()
				if q_ticket == Qt and Qcmd == cmd:
					if not msg:
						msg = "No Response"
					else:
						msg = tornado.escape.url_unescape(msg.replace('\n','<BR>'))
				else:
					# delete the queue item if it become too old -- we don't want the queue to fill up with orphans
					if (Qt + datetime.timedelta(minutes=5) > datetime.datetime.now()):
						self.C.RespQ['thermostat'].put([Qt,Qcmd,msg]) #put the queue item back in the queue because it doesn't match the cmd, it was generated by a different thread
					msg = 'No Response'
			if cnt == 0:
				msg = 'No response from thermostat for status request'
		return msg
		
	def execute_cmd(self,cmd):
		q_ticket = datetime.datetime.now()
		self.C.CmdQ['thermostat'].put([q_ticket,cmd])
		self.print1 ('Execute Command: '+cmd)
		msg = 'No Response'
		cnt = 100
		while msg == 'No Response':
			time.sleep(0.1)
			cnt -= 1
			if not self.C.RespQ['thermostat'].empty():
				Qt,Qcmd,msg = self.C.RespQ['thermostat'].get()
				if q_ticket == Qt and Qcmd == cmd:
#					if not msg:
#						msg = 'No Response'
#					else:
					msg = tornado.escape.url_unescape(msg.replace('\n','<BR>'))
				else:
					# delete the queue item if it become too old -- we don't want the queue to fill up with orphans
					if (Qt + datetime.timedelta(minutes=5) > datetime.datetime.now()):
						self.C.RespQ['thermostat'].put([Qt,Qcmd,msg]) #put the queue item back in the queue because it doesn't match the cmd, it was generated by a different thread
#					msg = 'No Response'
			if cnt == 0:
				msg = 'No response from thermostat for command: '+cmd
		self.print1 ('Response:'+msg)
		self.qprint1()
		return msg	

	def get_form(self):
		form = str('<form action="/'+settings.CONTROLLER_PROXY_PATH+'/thermostat" method="post">'
			'<input type="password" name="key">'
			'<p><label for="1">Select Command:</label> <ul>'
			'<li><label for="1"><input type="radio" id="1" value="status" name="cmd" />Update Status</label></li>'
			'<li><label for="2"><input type="radio" id="2" value="SP_plus" name="cmd" />Increment Setpoint 1 degree</label></li>'
			'<li><label for="3"><input type="radio" id="3" value="SP-" name="cmd" />Decrement Setpoint 1 degree</label></li>'
			'<li><label for="6"><input type="radio" id="6" value="Run" name="cmd" />Run Mode</label></li>'
			'<li><label for="7"><input type="radio" id="7" value="Hold" name="cmd" />Hold Mode</label></li>'
			'<li><label for="8"><input type="radio" id="8" value="Off" name="cmd" />HVAC OFF</label></li>'
			'<li><label for="9"><input type="radio" id="9" value="Heat" name="cmd" />Heat Mode</label></li>'
			'<li><label for="10"><input type="radio" id="10" value="Cool" name="cmd" />Cool Mode</label></li>'
			'<li><label for="4"><input type="radio" id="4" value="SPH" name="cmd" />Set Heat Setpoint to value</label></li>'
			'<li><label for="5"><input type="radio" id="5" value="SPC" name="cmd" />Set Cool Setpoint to value</label></li>'
			'</ul></p>'
			'Enter new setpoint here (for setpoing commands): <BR><input type="text" name="value"><BR>'
			'<input type="submit" value="Send Command">'
			'</form>')
		return form
