from htmltable.models import *
from django.http import HttpResponse
from django.template import Context, loader, RequestContext, Template
from django import forms
import urllib
from HTMLParser import HTMLParser
import djangosite.settings

def all_sensors(request):
	'''An HTML Table of parameters for the Controller.'''
	TableIndex = ['this_table','htmltable']
	qsHTMLTable = Sensor.objects.all()
	t = loader.get_template('htmltable/sensors.html')
	c = Context({'TableIndex':TableIndex,'qsHTMLTable':qsHTMLTable})
	return HttpResponse(t.render(c))

def active_sensors(request):
	'''An HTML Table of parameters for the Controller.'''
	TableIndex = ['this_table','htmltable']
	#exclude inactive sensors
	qsHTMLTable = Sensor.objects.all().exclude(DataID__Active=False)
	t = loader.get_template('htmltable/sensors.html')
	c = Context({'TableIndex':TableIndex,'qsHTMLTable':qsHTMLTable})
	return HttpResponse(t.render(c))


class Formparse_and_index_htmltable(forms.Form):
	URL_to_index = forms.CharField()

def parse_and_index_htmltable(request):
	'''For HTML Table data.  Used to obtain the table index and the row and column index of data on a webpage that you specify.
	
		The top corner of each table contains the index of the table.  Tables are indexed 1 to N.
		The column index is listed across the top of each table from 0 to N.
		The row index is listed down the left side of each table from 0 to N.
	'''
	if request.method == 'POST':
		form = Formparse_and_index_htmltable(request.POST)
		URL = ''
		if form.is_valid():
			URL = form.cleaned_data['URL_to_index']
			
		if URL:
			f = urllib.urlopen(URL)
			strPage = f.read()
			p = MyHTMLTableParseAndIndex()
			p.feed(strPage)
			p.close()
			Tables = p.tables
		else:
			Tables = [[]]
		t = Template('{% for table in Tables %}'+
					 '<table border="1">'+
					 '{% for row in table %}'+
					 '</tr>'+
					 '{% for data in row %}'+
					 '<td>{{ data }}</td>'+
					 '{% endfor %}</tr>'+
					 '{% endfor %}</table>'+
					 '{% endfor %}')
		c = Context({'Tables':Tables,})
		return HttpResponse(t.render(c))

	else:
		form = Formparse_and_index_htmltable()
		t = Template('<form action="/'+djangosite.settings.HTTP_PROXY_PATH+'/htmltable/parse_and_index_htmltable/" method="post"> {{ form.as_p }} <input type="submit" value="Submit" /> </form>')
		c = Context({'form':form})
		return HttpResponse(t.render(c))
	
class MyHTMLTableParseAndIndex(HTMLParser):
		def __init__(self):
			self.__debug=False
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
			self.__TableOpen = False

		def row(self):
			return self.__Row
		def col(self):
			return self.__Col
		def table(self,TableIndex):
			return self.__listTables[TableIndex]
		def tables(self):
			return self.__listTables
		
		def cell(self,TableIndex=0,row=0,col=0):
			return self.__listTables[TableIndex][row][col]
		
		def number_of_tables(self):
			return self.__NumTables

		def data_in_first_cell(self):
			return self.__data_in_first_cell
		
		def handle_starttag(self, tag, attrs):
			self.__starttag = tag
			self.__endtag = ''
			if self.__debug:print 'starttag ',tag,'     row,col:',self.__Row,self.__Col
			if tag == 'table':
				self.__Col = -1
				self.__Row = 0
				#if there was no end tag 'table', then save this table and initialize the next
				if self.__table <> [[]]:
					self.close_table()
				self.__TableOpen = True
				self.__MaxCol = -1
				self.__NumTables += 1
				if self.__debug:print 'LoadingData from table ',self.__NumTables
			if (tag == 'tr') and self.__TableOpen == True:
				self.__Row += 1
				self.__Col = 0
				self.__MaxCol = 0
				self.__table.append([])
				self.__table[self.__Row].append('')
				if self.__debug:print 'Append Row ', self.__Row
				self.__table[self.__Row][0] = self.__Row - 1
				if self.__debug:print 'Row counter ', self.__Row
			if (tag == 'td' or tag == 'th') and self.__TableOpen == True:
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
			self.__table[0][0] = self.__NumTables
			self.__listTables.append(self.__table)
			if self.__debug:print 'saved table:',self.__listTables[self.__NumTables]
			self.__table = [[]]
			self.__TableOpen = False
		
		def handle_data(self, data):
			if self.__TableOpen:
				if self.__debug:print 'Load Data: ',self.__starttag,self.__Row,self.__Col,data
				if self.__Col > 0 and self.__endtag == '':
					self.__table[self.__Row][self.__Col] = data

def test_MyHTMLTableParseAndIndex():
	'''Test Parese and Index'''
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