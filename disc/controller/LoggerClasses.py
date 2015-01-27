#!/usr/bin/python
__version__ = "1.0.0"

__all__ = ["SensorList","MyHTMLTableParser","PostFromQuery","TemporaryData"]

from HTMLParser import HTMLParser
import csv, threading, time, os, urllib, httplib
import logging
logger = logging.getLogger(__name__)

class SensorList():
	__ID_List = []
	__table = [[]]
	def __init__(self):
		self.reset()
		self.logger = logging.getLogger(__name__+'.SensorList')
	def reset(self):
		self.__table = [[]]
		self.ID_List = []
	def load_table(self, table):
		self.__table = table
		#Create a list of ID's
		col = self.__table[0].index('SensorID')
		self.__ID_List = [self.__table[i][col] for i in range(len(self.__table))]
	def get(self,ID,ParameterName):
		value = ''
		try:
			col = self.__table[0].index(ParameterName)
			row = self.__ID_List.index(ID)
			value = self.__table[row][col]
		except:
			self.logger.exception('{} {} {} {} {}'.format(ID, ParameterName, row, col, value))
		finally:
			return value
	def get_id_list(self):
		return self.__ID_List
	def get_table(self):
		return self.__table
	def get_table_header(self):
		return self.__table[0]

class MyHTMLTableParser(HTMLParser):
	def __init__(self, IndexOfTable=0):
		self.logger = logging.getLogger(__name__+'.MyHTMLTableParser')
		self.__debug=False
		self.reset()
		self.my_reset()
		self.IndexOfTable = IndexOfTable
#		print 'IndexOfTable',IndexOfTable
	def my_reset(self):
		self.__table = []
		self.__Col = -1
		self.__Row = -1
		self.__Data = ''
		self.__endtag = ''
		self.__starttag = ''
		self.__NumTables = -1
		self.__data_in_first_cell = []
		self.LoadData = True

	def row(self):
		return self.__Row
	def col(self):
		return self.__Col
	def table(self):
		return self.__table

	def cell(self,row=0,col=0):
		return self.__table[row][col]
	
	def number_of_tables(self):
		return self.__NumTables

	def data_in_first_cell(self):
		return self.__data_in_first_cell
	
	def handle_starttag(self, tag, attrs):
		self.__starttag = tag
		self.__endtag = ''
#		print 'starttag ',tag
		if tag == 'table':
			if self.__NumTables == self.IndexOfTable:
				self.LoadData = False
			if self.LoadData:
				self.__Col = -1
				self.__Row = -1
				self.__table = []
				self.__NumTables += 1
				self.__data_in_first_cell.append('')
#				print 'LoadingData from table ',self.__NumTables
		if (tag == 'tr') and self.LoadData == True:
			self.__Row += 1
			self.__Col = -1
#			print 'Row counter ', self.__Row
		if (tag == 'td' or tag == 'th') and self.LoadData == True:
			self.__Col += 1
			if self.__Col == 0:
				self.__table.append([])
				if self.__debug:print 'Append Row ', self.__Row
			try:
				self.__table[self.__Row].append('')
			except:
				pass
	def handle_endtag(self, tag):
		if self.__debug:print 'stoptag ',tag
		self.__endtag = tag
		if tag == 'table':
			self.LoadData == False

	def handle_data(self, data):
		if self.LoadData:
			if self.__debug:print 'Load Data: ',self.__starttag,self.__Row,self.__Col,data
			if self.__Col > -1 and self.__endtag == '':
				self.__table[self.__Row][self.__Col] = data
				if self.__Col == 0 and self.__Row == 0:
					self.__data_in_first_cell[self.__NumTables] = data


class TemporaryData():
	def __init__(self, mainThread):
		csv.register_dialect('csv',delimiter=',')
		self.MT = mainThread
		self.__FileName = self.MT.settings.TEMORARY_DATA_STORAGE_PATH+'/DataStorageFromPOSTFailure.csv'
		self.logger = logging.getLogger(__name__+'.TemporaryData')

	def file_exists(self):
		try:
			f = open(self.__FileName,'rb')
			f.close()
		except:
			return ''
		return '1'
		
	def save_data(self,Data):
		try:
			f = open(self.__FileName,'ab')#w to replace contents, a to append
			writer = csv.writer(f,'csv')
			writer.writerow(Data)
			f.close()
			self.print2('Data written to file')
		except IOError:
			self.logger.warning('IO Error while writing temporary data')
		except:
			self.logger.warning('Error while writing temporary data')
			
	def get_data(self):
		Data = []
		try:
			f = open(self.__FileName,'rb')
			reader = csv.reader(f,'csv')
			for row in reader:
				try:
					a,b,c,d = row
					if a <> '' and b <> '' and c <> '' and d <> '':
						Data.append(row)
				except:
					self.logger.debug('continuing with next row')
			f.close()
		except IOError:
			self.logger.warning('IO Error while reading temporary data')
		except:
			self.logger.warning('Error while reading temporary data')
		return Data
		
	def clear_data(self):
		try:
			f = open(self.__FileName,'wb')
			writer = csv.writer(f,'csv')
			writer.writerow([])
			f.close()
		except IOError:
			self.logger.warning('IO Error while trying to clear temporary data')
		except:
			self.logger.warning('Error clearing temporary data')


class PostFromQuery(threading.Thread):
	def __init__(self, mainThread):
		threading.Thread.__init__(self)
		self.__myThread = threading.Thread
		self.MT = mainThread
		self.tempdata = TemporaryData(self.MT)
		self.CheckTemporaryData = True
		self.msg = ''
		self.__active = True
		self.__complete = False
		self.logger = logging.getLogger(__name__+'.PostFromQuery')

	def quit(self):
		self.print2('*** Stopping PostFromQuery thread ***')
		self.qprint2()
		self.__active = False
		while not self.__complete:
			time.sleep(1)
			self.print2('*** waiting to stop PostFromQuery thread ***')
		self.__myThread._Thread__stop
		self.__myThread._Thread__delete

	def print2(self,text):
#		self.MT.addText2END(text+"\n")
#		self.MT.scrollToEndText2()
		#print text
		self.msg += text+'\n'

	def qprint2(self):
		self.MT.printQ.put(self.msg)
		self.msg = ''

	def run(self):
		try:
			while self.__active:
			#			if LastMinute == '0' or LastMinute == '30': # try to upload the temporary data every hour
				time.sleep(1)
				while not self.MT.Q.empty():
					try:
						if self.CheckTemporaryData:
							if self.send_temp_data():
								self.CheckTemporaryData = False
						if self.CheckTemporaryData:
							print 'Not posting new data until temporary data has been uploaded...'
							d = self.MT.Q.get()
							ID,Value,RecordDateTime,Timebase = d
							self.tempdata.save_data(d)
							self.CheckTemporaryData = True
						else:
							d = self.MT.Q.get()
							ID,Value,RecordDateTime,Timebase = d
							self.http_post_data(ID,Value,RecordDateTime,Timebase)
							try:
	#							self.http_post_data_development_server(ID,Value,RecordDateTime,Timebase)
								pass
							except:
								pass
							qs = self.MT.Q.qsize()
							if qs > 2:
								self.print2('Queue Size: '+str(qs)+'  *** the server is not accepting the data fast enough ***')
							
					except KeyboardInterrupt:
						raise KeyboardInterrupt
					except:
						self.print2 ('Store data in file')
						self.tempdata.save_data(d)
						self.CheckTemporaryData = True
					finally:
						self.qprint2()
		finally:
			self.__complete = True			

	def http_post_data(self,ID,Value,RecordDateTime,Timebase):
		try:
			params = urllib.urlencode({'ID': ID, 'RecordDateTime': RecordDateTime, 'Value': Value, 'Timebase': Timebase, 'AccessCode': self.MT.settings.POST_ACCESSCODE})
			headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
			conn = httplib.HTTPConnection(self.MT.settings.HTTP_POST_HOST, self.MT.settings.HTTP_POST_PORT, timeout=self.MT.settings.HTTP_POST_TIMEOUT)
			if conn:
				conn.request("POST", self.MT.settings.URL_POST_SENSOR_DATA, params, headers)
				response = conn.getresponse()
				body = response.read()
				if response.status == 200 and body == 'OK':
					self.print2 ('Successful POST: '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase)
				else:
					self.print2 ('*Failed* POST: '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase)
					self.print2 ('HTTP RESPONSE: '+str(response.status)+' '+str(response.reason))
					raise
				data = response.read()
				conn.close()
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		except:
			self.print2 ('Unable to POST data '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase)
			raise

	#for development testing
	def http_post_data_development_server(self,ID,Value,RecordDateTime,Timebase):
		'''The development server must have the same Data ID list as the primary server'''
		DEVHOST = 'localhost'
		DEVPORT = 8002
		DEVPROXY = 'disc2'
		DEV_URL_POST_SENSOR_DATA = '/'+DEVPROXY+'/env/post_data'
		try:
			params = urllib.urlencode({'ID': ID, 'RecordDateTime': RecordDateTime, 'Value': Value, 'Timebase': Timebase, 'AccessCode': self.MT.settings.POST_ACCESSCODE})
			headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
			conn = httplib.HTTPConnection(DEVHOST, DEVPORT, timeout=5)
			if conn:
				conn.request("POST", DEV_URL_POST_SENSOR_DATA, params, headers)
				response = conn.getresponse()
				self.print2 (str(response.status)+' '+str(response.reason))
				body = response.read()
				if response.status == 200 and body == 'OK':
					self.print2 ('DEVELOPMENT: Successful POST: '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase)
				else:
					self.print2 ('DEVELOPMENT: *Failed* POST: '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase)
					raise
				data = response.read()
				conn.close()
		except KeyboardInterrupt:
			raise KeyboardInterrupt
		except:
			self.print2 ('DEVELOPMENT: Unable to POST data '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase)
			raise

	def send_temp_data(self):
		try:
			if self.tempdata.file_exists():
				d = self.tempdata.get_data()
				if d:
					self.print2 ('***Attempting to upload temporary data***')
					for row in d:
						ID,Value,RecordDateTime,Timebase = row
						self.http_post_data(ID,Value,RecordDateTime,Timebase)
					self.tempdata.clear_data()
			return True
		except KeyboardInterrupt:
			raise KeyfboardInterrupt
		except:
			self.print2 ("Error trying to upload temporary data")
			return False


class MyHTMLTableParseAndIndex(HTMLParser):
		def __init__(self):
			self.reset()
			self.my_reset()
		def my_reset(self):
			self.__table = [[]]	
			self.__Col = -1
			self.__Row = -1
			self.__Data = ''
			self.__endtag = ''
			self.__starttag = ''
			self.__NumTables = 0
			self.LoadData = True
			self.__listTables=[[]] # set table index 0 to an empty table
			self.__MaxCol = -1

		def row(self):
			return self.__Row
		def col(self):
			return self.__Col
		def table(self,TableIndex):
			return self.__listTables[TableIndex]

		def cell(self,TableIndex=0,row=0,col=0):
			return self.__listTables[TableIndex][row][col]
		
		def number_of_tables(self):
			return self.__NumTables

		def data_in_first_cell(self):
			return self.__data_in_first_cell
		
		def handle_starttag(self, tag, attrs):
			self.__starttag = tag
			self.__endtag = ''
			if tag == 'table':
				self.__Col = -1
				self.__Row = 0
				#if there was no end tag 'table', then save this table and initialize the next
				if self.__table <> [[]]:
					self.close_table()					
				self.__MaxCol = -1
				self.__NumTables += 1
			if tag == 'tr':
				self.__Row += 1
				self.__Col = 0
				self.__MaxCol = 0
				self.__table.append([])
				self.__table[self.__Row].append('')
				self.__table[self.__Row][0] = self.__Row - 1
			if tag == 'td' or tag == 'th':
				self.__Col += 1
				if self.__Col > self.__MaxCol:
					self.__MaxCol = self.__Col
				self.__table[self.__Row].append('')
				
		def handle_endtag(self, tag):
			if self.__debug:print 'stoptag ',tag
			self.__endtag = tag
			if tag == 'table':
				self.close_table()
		
		def close_table(self):
			if self.__debug:print 'closing table index',self.__NumTables
			self.__table[0] = range(-1,self.__MaxCol)
			self.__table[0][0] = ''
			self.__listTables.append(self.__table)
			if self.__debug:print 'saved table:',self.__listTables[self.__NumTables]
			self.__table = [[]]
		
		def handle_data(self, data):
			if self.__debug:print 'Load Data: ',self.__starttag,self.__Row,self.__Col,data
			if self.__Col > 0 and self.__endtag == '':
				self.__table[self.__Row][self.__Col] = data

def dev_test():
	'''Test Parse and Index'''
	#f = urlib.urlopen('file:\\c:\\users\\nwehr\\Downloads\table.html')
	#strPage = f.read()
	strPage = '<table>\r\n<tr>\r\n<td>one</td><td>two</td><td>one-two</td>\r\n</tr>\r\n<tr>\r\n<td>three</td><td>four</td><td>three-four</td>\r\n</tr>\r\n<tr>\r\n<td>five</td><td>six</td><td>five-six</td>\r\n</tr>\r\n</table>'
	strPage = strPage+'<table>\r\n<tr>\r\n<td>_one</td><td>two</td><td>one-two</td>\r\n</tr>\r\n<tr>\r\n<td>three</td><td>four</td><td>three-four</td>\r\n</tr>\r\n<tr>\r\n<td>five</td><td>six</td><td>five-six</td>\r\n</tr>\r\n</table>'
	strPage = strPage+'<table>\r\n<tr>\r\n<td>__one</td><td>two</td><td>one-two</td>\r\n</tr>\r\n<tr>\r\n<td>three</td><td>four</td><td>three-four</td>\r\n</tr>\r\n<tr>\r\n<td>five</td><td>six</td><td>five-six</td>\r\n</tr>\r\n</table>'
	strPage = strPage+'<table>\r\n<tr>\r\n<td>___one</td><td>two</td><td>one-two</td>\r\n</tr>\r\n<tr>\r\n<td>three</td><td>four</td><td>three-four</td>\r\n</tr>\r\n<tr>\r\n<td>five</td><td>six</td><td>five-six</td>\r\n</tr>\r\n</table>'

	p = MyHTMLTableParseAndIndex()
	p.feed(strPage)
	p.close()
	print ''
	print 'Number of Tables',p.number_of_tables()
	
	for i in range(1,p.number_of_tables() + 1):
		print p.table(i)
	
