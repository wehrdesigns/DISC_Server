import urllib2

def load_sensor_table_url(strURL):
    try:
#        print 'Loading URL '+strURL
        timeout_time = 15
        try:
            f = urllib2.urlopen(strURL, timeout=timeout_time)
#            print 'Server returned code '+str(f.code)
            if f.code == 200 and f.info() != '':
#                print 'Read URL...'
                strPage = ''.join(f.readlines())
                f.close()
#                print 'Read URL '+str(len(strPage))+' characters'
            else:
                strPage = None
        except urllib2.URLError as e:
            print 'ERROR:urllib2 URLError'
#            print type(e)
#            print str(e)
            strPage = None
        except socket.timeout as e:
            print 'ERROR:socket timeout'
#            print type(e)
#            print str(e)
            strPage = None
        except KeyboardInterrupt:
            print 'ERROR:caught keyboard interrupt'
        except:
            print 'ERROR:caught an error'
        finally:
            pass
    except:
#    self.logger.exception('Reading url')
        print 'ERROR:Error reading url'
#    CallingThread.print1('Error reading url '+strURL)
        strPage = None
    finally:
        if strPage == None:
            print 'ERROR:Unable to connect or read from URL '+strURL
#    CallingThread.print1 ('Unable to connect or read from URL '+strURL)
        print strPage

import os
import sys

print >>sys.stdout, 400*''

load_sensor_table_url('http://192.168.254.12/')
    
