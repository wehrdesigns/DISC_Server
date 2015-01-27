import sys
import time, datetime
import logging
logger = logging.getLogger('actionlab_usermodule.'+__name__)
logger.info('loaded usermodule '+__name__)

import pyttsx

def ComputeAndAct(dictTable):
	pass

def send_email(message,address='me@emailserver.com'):
	try:
		import smtplib
		from email.mime.text import MIMEText
	
		msg = msg = MIMEText(message)
		me = 'me@emailserver.com'
		you = address
		msg['Subject'] = 'DISC Notification'
		msg['From'] = me
		msg['To'] = you
	
		s = smtplib.SMTP('smtp.emailserver.net',25)#465)
		#s.set_debuglevel(10)
#		s.ehlo()
#		s.starttls()
#		s.ehlo()
		s.login('user@emailserver.com','password')
		s.sendmail(me, [you], msg.as_string())
		s.quit()
	except:
		logger.exception('Error sending email')

def say_msg(msg):
	try:
		tts = pyttsx.init()
		rate = tts.getProperty('rate')
		tts.setProperty('rate', rate-40)
	#		voices = tts.getProperty('voices')
	#		for voice in voices:
	#			print 'voice id',voice.id
	#			tts.setProperty('voice',voice.id)
	#			tts.say(msg)
		
		tts.say(msg)
		tts.runAndWait()
	except:
		logger.exception('text to speech message')