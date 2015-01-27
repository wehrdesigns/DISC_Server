import urllib, httplib
from HTMLParser import HTMLParser

class GetHTMLTable():
        def __init__(self, URL):
                self.URL = URL
        
        def get_html(self):
                f = urllib.urlopen(self.URL)
                strdata = f.read()
                if not strdata:
                        print('Unable to load Table from URL: '+self.URL)
                        raise
                return strdata
        
        def load_table(self,IndexOfTable = 0):
                strdata = self.get_html()
                p = MyHTMLTableParser_IndexTables(IndexOfTable)
                p.feed(strdata)
                p.close()
                self.table = p.table()

        def table(self):
                return self.table

        def cell(self,row=0,col=0):
                return self.table[row][col]        

class MyHTMLTableParser_IndexTables(HTMLParser):
        def __init__(self, IndexOfTable):
                self.reset()
                self.my_reset()
                self.IndexOfTable = IndexOfTable
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
#                print "Encountered the beginning of a %s tag" % tag
                if tag == 'table':
                        if self.__NumTables == self.IndexOfTable:
                                self.LoadData = False
                        if self.LoadData:
                                self.__Col = -1
                                self.__Row = -1
                                self.__table = []
                                self.__NumTables += 1
                                self.__data_in_first_cell.append('')
                if tag == 'tr':
                        if self.LoadData:
                                self.__Row += 1
                                self.__Col = -1
                if tag == 'td':
                        if self.LoadData:
                                self.__Col += 1
                                if self.__Col == 0:
                                        self.__table.append([])
                                self.__table[self.__Row].append('')

        def handle_endtag(self, tag):
#                print "Encountered the end of a %s tag" % tag
                self.__endtag = tag

        def handle_data(self, data):
                if self.LoadData:
#                        print self.__starttag,self.__Row,',',self.__Col, data
                        if self.__Col > -1 and self.__endtag == '':
                                self.__table[self.__Row][self.__Col] = data
                                if self.__Col == 0 and self.__Row == 0:
                                        self.__data_in_first_cell[self.__NumTables] = data

def test():
        dTable = GetHTMLTable('http://forecast.weather.gov/MapClick.php?lat=39.79340&lon=-76.73050&unit=0&lg=english&FcstType=digital')
        dTable.load_table(7)
        
#        print dTable.get_html()
#        print ''
        print 'The Table:'
        t = dTable.table
        print t
        print ''
        print 'Table by row'
        for row in t:
                print row
        print ''
        print 'Cell 3,5',dTable.cell(3,5)


#test()
