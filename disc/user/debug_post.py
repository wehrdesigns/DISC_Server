import urllib
import httplib
import datetime

def http_post_data(ID,Value,RecordDateTime,Timebase):
	try:
		params = urllib.urlencode({'ID': ID, 'RecordDateTime': RecordDateTime, 'Value': Value, 'Timebase': Timebase})
		headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
		conn = httplib.HTTPConnection('localhost', '8000', timeout=5)
		if conn:
			conn.request("POST", '/disc/env/post_data', params, headers)
			response = conn.getresponse()
			print str(response.status)+' '+str(response.reason)
			body = response.read()
			if response.status == 200 and body == 'OK':
				print 'Successful POST: '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase
			else:
				print '*Failed* POST: '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase
				raise
			data = response.read()
			conn.close()
	except KeyboardInterrupt:
		raise KeyboardInterrupt
	except:
		print 'Unable to POST data '+ID+', '+str(Value)+', '+RecordDateTime+', '+Timebase
		raise

def load_range_minutes():
        dt = datetime.datetime.now()
        points = 1440
        start = datetime.datetime.now() - datetime.timedelta(minutes=points)
        for i in range(0,points,1):
                ts = start + datetime.timedelta(minutes=i)
                http_post_data('2','30',ts.strftime('%Y-%m-%d %H:%M:%S'),'minutes')
        print dt,datetime.datetime.now()

def load_range_hours():
        dt = datetime.datetime.now()
        points = 100
        start = datetime.datetime.now() - datetime.timedelta(hours=points)
        for i in range(0,points,14):
                ts = start + datetime.timedelta(hours=i)
                http_post_data('2','1000',ts.strftime('%Y-%m-%d %H:%M:%S'),'hours')
        print dt,datetime.datetime.now()

		
#load_range_minutes()
load_range_hours()
#http_post_data('2','10','2014-1-10 23:59:00','hours')
