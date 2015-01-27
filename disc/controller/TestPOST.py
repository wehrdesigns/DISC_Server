import httplib, urllib

class TestPOST():
    def __init__(self,Host,Port,URL):
        self.Host = Host
        self.Port = Port
        self.URL = URL
        
    def http_post_data(self,ID,Value,RecordDateTime):
            try:
                    params = urllib.urlencode({'ID': ID, 'RecordDateTime': RecordDateTime, 'Value': Value})
                    headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
                    conn = httplib.HTTPConnection(self.Host+':'+self.Port)
                    if conn:
                            conn.request("POST", self.URL, params, headers)
                            response = conn.getresponse()
                            print (str(response.status)+' '+str(response.reason))
                            if response.status == 200:
                                    print ('Successful POST: '+ID+', '+str(Value)+', '+RecordDateTime)
                            else:
                                    raise
                            data = response.read()
                            conn.close()
            except KeyboardInterrupt:
                    raise KeyboardInterrupt
            except:
                    print ('Unable to POST data '+ID+', '+str(Value)+', '+RecordDateTime)
                    raise