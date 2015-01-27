import logging
logger = logging.getLogger(__name__)
from env.models import *

from django.http import HttpResponse, HttpRequest, HttpResponseRedirect
from django.template import Context, loader, RequestContext, Template
from django.views.decorators.http import require_http_methods, require_POST, require_GET
from django import forms
from django.shortcuts import render_to_response
from django.forms.fields import DateField, ChoiceField, MultipleChoiceField
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
#from django.forms.extras.widgets import SelectDateWidget
import time, urllib
from django.contrib.auth.decorators import login_required, user_passes_test
#from django.forms import ModelForm
from django.contrib import messages

import djangosite.settings
import sys
from decimal import Decimal

from threading import Lock

import datetime, time
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
font = {'family' : 'Bitstream Vera Sans',
		'weight' : 'normal',
		'size'   : 12}
matplotlib.rc('font', **font)
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
from matplotlib import ticker
import numpy as np

#def AutoLocatorInit(self):
#	ticker.MaxNLocator.__init__(self, nbins=9, steps=[1, 2, 5, 10])
#ticker.AutoLocator.__init__ = AutoLocatorInit
matplotlib.ticker.MultipleLocator(base=10.0)
import discengines
import json

listTimebase = ['seconds','minutes','hours','days']

def post_data(request):
	'''By POST, accepts ID, RecordDateTime, Value, timebase to filter, aggregate and store with the time series engine.
		
		ID (also known as DataID) is a unique integer that specifies item of the env.model.Data
		RecordDateTime is date and time stamp corresponding to server time with format %Y-%m-%d %H:%M:%S
		Value is coerced to a floating point value, but is stored in the database as a string
		timebase is one of: seconds, minutes, hours, days
		
	'''
	if request.method == 'POST':
		try:
			if request.POST['AccessCode'] == discengines.POST_ACCESSCODE:
				datatable = discengines.datatable
				ID = request.POST['ID']
				RecordDateTime = request.POST['RecordDateTime']
				Value = request.POST['Value']
				timebase = request.POST['Timebase']
				if not listTimebase.__contains__(timebase):
					logger.exception('invalid timebase')
					return HttpResponse("ERROR")
		#		print 'params: ',ID, Value, timebase, RecordDateTime
				datatable.update_record(ID,RecordDateTime,Value,timebase,None,None,True)	
				discengines.dictValues[ID] = Value
				discengines.dictDateTime[ID] = RecordDateTime
				return HttpResponse("OK")
			else:
				logger.warning('Access denied for post data')
				return HttpResponse("Access denied.")
		except:
			logger.exception("Unexpected error during post_data")
			if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
				try:
					datatable.db_close(ID)
				except:
					logger.exception('Error closing sqlite db for ID:'+str(ID))
			return HttpResponse("ERROR")
	return HttpResponse("Post data here")

@user_passes_test(lambda u: u.is_staff)
@login_required()
def serverlog(request,arg=''):
	'''Return the server log buffer.
		
		Append "auto" to auto refresh.  The refresh period can be any number of seconds.  Specify it with "auto5". (for 5 seconds)
	'''
	auto = ''
	try:
		if 'auto' in arg:
			period = 10
			try:
				period = int(''.join(ele for ele in arg[4:12] if ele.isdigit()))
			except:
				pass
			auto = '<meta http-equiv="refresh" content="'+str(period)+';URL=/'+djangosite.settings.HTTP_PROXY_PATH+'/env/serverlog/auto'+str(period)+'?'+str(datetime.datetime.now().microsecond)+'#bottomofpage">'
	except:
		logger.exception('parsing auto period')
#	t = loader.get_template('env/serverlog.html')
#	c = Context({'serverlog':discengines.htmlloggingbuffer.gethtml(),'auto':auto})
#	return HttpResponse(t.render(c))
	return render_to_response('env/serverlog.html',
							  {'serverlog':discengines.htmlloggingbuffer.gethtml(),'auto':auto},
							  context_instance=RequestContext(request))

def testvalue(request):
	'''Returns a table with the value hour + minute + (second*0.01)'''
	s = datetime.datetime.now().hour + datetime.datetime.now().minute + datetime.datetime.now().second*0.01
	return HttpResponse('<table><tr><td>'+str(s)+'</td></tr></table>')

def randomvalue(request):
	'''Returns a table with the value int(100*random)'''
	import random
	s = int(100*random.random())
	return HttpResponse('<table><tr><td>'+str(s)+'</td></tr></table>')

def sawtoothvalue(request):
	'''Returns a table with the value day + hour + minute + second'''
	s = datetime.datetime.now().day + datetime.datetime.now().hour + datetime.datetime.now().minute + datetime.datetime.now().second
	return HttpResponse('<table><tr><td>'+str(s)+'</td></tr></table>')

def logvalue(request):
	'''Returns a table with the value 40*log10(day + hour + minute + second)'''
	from decimal import Decimal as Dec
	s = datetime.datetime.now().day + datetime.datetime.now().hour + datetime.datetime.now().minute + datetime.datetime.now().second
	l = round(40*Dec.log10(Dec(s)),3)
	return HttpResponse('<table><tr><td>'+str(l)+'</td></tr></table>')

def sinevalue(request):
	'''Returns a table with the value a sum of sine waves seeded from the time'''
	from math import sin,pi
	from decimal import Decimal as Dec
	#import pdb;pdb.set_trace()
	dt = datetime.datetime.now()
	s = round(100*sin(Dec(dt.hour)/Dec(24)*2*Dec(pi)) + 10*sin(Dec(dt.minute)/Dec(60)*2*Dec(pi)) + sin(Dec(dt.second)/Dec(60)*2*Dec(pi)),2)
	return HttpResponse('<table><tr><td>'+str(s)+'</td></tr></table>')

def copyright_license(request):
	t = loader.get_template('env/copyright_license.html')
	c = Context({'indexbody':''})
	return HttpResponse(t.render(c))

@login_required()
def index(request):
	'''Returns a few useful links to get started'''
	return render_to_response('env/index.html',
							  {'proxy_path':djangosite.settings.HTTP_PROXY_PATH},
							  context_instance=RequestContext(request))


@login_required()
def urls(request):
	'''Tries to import all the installed apps and then reads their url patterns to generate a list of urls'''
	html = '<a href="/'+djangosite.settings.HTTP_PROXY_PATH+'/admin/">DISC Admin Home</a>'
	html += '<BR><a href="/'+djangosite.settings.HTTP_PROXY_PATH+'/servertime">Server Time</a>'
	html += '<BR><a href="/'+djangosite.settings.HTTP_PROXY_PATH+'/">DISC Index</a>'
	html += '<BR>'
	for m in djangosite.settings.INSTALLED_APPS:
		htmlrows = ''
		if m.rfind('django.contrib') == -1:
			try:
				im = __import__(m)
	#			import pdb;pdb.set_trace()
				for u in im.urls.urlpatterns:
					htmlc0 = '<td></td>'
					htmlc1 = '<td></td>'
					htmlc2 = '<td></td>'
					href = u._regex.replace('^','').replace('/(.+)','').replace('/$','/')
					htmlc0 = '<td><a href="/'+djangosite.settings.HTTP_PROXY_PATH+'/'+m+'/'+href+'">'+m+'/'+href+'</a></td>'
					try:
						lst = u._callback_str.split('.')
	#					if lst[0] == 'samewire':import pdb;pdb.set_trace()
						mf = __import__(lst[0]+'.'+lst[1])
						htmlc2 = '<td>'+eval('mf.'+lst[1]+'.'+lst[2]+'.__doc__').split('\n')[0].replace('\n','<BR>').replace('\t','    ')+'</td>'
						htmlc1 = '<td><a href="/'+djangosite.settings.HTTP_PROXY_PATH+'/env/docstring/'+lst[0]+'__'+lst[1]+'__'+lst[2]+'">full doc</a></td>'
					except:
						pass
					newrow = '<tr>'+htmlc0+htmlc1+htmlc2+'</tr>'
					if newrow not in htmlrows:
						htmlrows += newrow
			except:
				pass
			html += '<BR><table>'+htmlrows+'</table>'
	return render_to_response('env/urls.html',
							  {'urlsbody':html},
							  context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
@login_required()
def docstring(request, arg1=''):
	'''Create a help window with the docstring of the given function.
		
		The function in the first argument. example: /env/docstring/given_function
		Provide a path to the function as follows: /env/docstring/path1__path2__given_function
	'''
#	import pdb;pdb.set_trace()
	try:
		lst = arg1.split('__')
		importobj = __import__(lst[0]+'.'+lst[1])
		callobj = arg1.replace(arg1.split('__')[0],'importobj').replace('__','.')
		html = eval(callobj+'.__doc__').replace('\n','<BR>').replace('\t','    ')+'</td>'
	except:
		html = 'Unable to load docstring for: '+arg1
	return render_to_response('env/docstring.html',
							  {'docstringbody':html},
							  context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_superuser)
@login_required()
def stop_sqlite_engine(request):
	'''*SuperUser* Stops the ActionLabEngine and if USE_SQLITE_QUEUED_MEMORY_MANAGER = true, writes memory data to file and stops the sqlite engine'''
	from discengines import START_ACTIONLABENGINE, USE_SQLITE_QUEUED_MEMORY_MANAGER
	if START_ACTIONLABENGINE:
		from discengines import ALE
		ALE.quit()
		logging.info('Action Lab Engine Stopped')
	if USE_SQLITE_QUEUED_MEMORY_MANAGER:
		#this will save data to file for all timebases
		discengines.datatable.stop_sqlite_engine()
	else:
		import os
		time.sleep(1)
		os._exit(os.R_OK)
	return HttpResponse("Sqlite Engine Stopped")

@user_passes_test(lambda u: u.is_superuser)
@login_required()
def sync_to_file(request):
	'''*SuperUser* If USE_SQLITE_QUEUED_MEMORY_MANAGER = true, write memory data to file'''
	from discengines import START_ACTIONLABENGINE, USE_SQLITE_QUEUED_MEMORY_MANAGER
	if USE_SQLITE_QUEUED_MEMORY_MANAGER:
		#this will save data to file for all timebases
		discengines.datatable.sync_to_file()
		return HttpResponse("Memory data synced to file")
	else:
		return HttpResponse("Nothing to do")

def active_interfaces(request):
	'''JSON list of all interfaces with active DataID's
	
		Tries to import all installed apps and if they have a Sensor model, read the active Sensors.  If an active sensor is found, add the interface to the list.
	'''
#	import pdb;pdb.set_trace()
	interfaces = []
	if request.method == 'GET':
		for m in djangosite.settings.INSTALLED_APPS:
			try:
				im = __import__(m)
				if im.models.Sensor.objects.exclude(DataID__Active=False):
					interfaces.append(str(m))
			except:
				pass
#	if request.method == 'POST':
#		name = request.POST['name']
#		if form.is_valid():
#			IDs = form.cleaned_data['Data_ID_To_Plot']
#			for m in djangosite.settings.INSTALLED_APPS:
#				try:
#					im = __import__(m)
#					if im.models.Master.objects.filter(Controller=name):
#						if im.models.Sensor.objects.exclude(DataID__Active=False):
#							interfaces.append(str(m))
#				except:
#					pass
	return HttpResponse(json.dumps(interfaces))

@login_required()
def env_data_table(request):
	'''Table of env.model.Data items'''
	EnvData = Data.objects.all()
	t = loader.get_template('env/env_data_table.html')
	c = Context({'EnvData':EnvData,})
	return HttpResponse(t.render(c))

@login_required()
def active_env_data_table(request):
	'''Table of only the active env.model.Data items'''
	EnvData = Data.objects.exclude(Active=False)
	return render_to_response('env/env_data_table.html',
							  {'EnvData':EnvData,},
							  context_instance=RequestContext(request))

@user_passes_test(lambda u: u.is_staff)
@login_required()
def controller_urls(request):
	'''A list of controller urls with links to the main url and the output url
	
		In addition to these urls, there may be specific urls for each interface running on the controller.
		The interfaces are loaded based on the sensors that are active.
		Example: the samewire interface will have a controller url such as: localhost:11111/controller/samewire
	'''
	controllers = Controller.objects.all()
	return render_to_response('env/controller_urls.html',
							  {'controllers':controllers},
							  context_instance=RequestContext(request))

TIMEBASE_CHOICES = (('seconds','seconds'),('minutes','minutes'),('hours','hours'),('days','days'))

class SmoothingForm(forms.Form):
	Timebase = forms.ChoiceField(choices=TIMEBASE_CHOICES,widget=RadioSelect,required=True,initial='minutes')
	Start_Time = forms.CharField(max_length=19,required=False)
	Stop_Time = forms.CharField(max_length=19,required=False)
	Data_ID_To_Smooth = forms.MultipleChoiceField(widget=CheckboxSelectMultiple, required=True)
	Smooth_all_active_data_id = forms.BooleanField(required=False)

@user_passes_test(lambda u: u.is_staff)
@login_required()
def smooth_missing_data(request):
	'''Used to smooth missing or erroneous data.
	
		Choose start and stop times that include a little time before and after the bad data.
		*** this function is NOT complete ***
	'''
	err = ''
	datatable = discengines.datatable
	PostPath = '/'+djangosite.settings.HTTP_PROXY_PATH+'/env/smooth_missing_data'
	g=[]
	[g.append(str(x)) for x in request.user.groups.all()]
	listID = []
	#, Timebase=timebase
	qs = Data.objects.all().filter(Active=True).order_by('Type','Name').filter(Group__name__in=g).distinct()
	for d in qs:
		o = Data.objects.get(ID=d.ID)
#		strColor = '<font color="'+str(d.Color)+'"><b>'+str(d.Color)+'</b></font>, '
		listID.append((o.ID,str(o.Name)+'_'*(30-len(o.Name))+str(o.Type)+'.'*(21-len(str(o.Type)))+str(d.Color)+', '+str(d.ID)))
	ID_CHOICES=tuple(listID)

	if request.method == 'POST':
		form = SmoothingForm(request.POST)
		form.fields['Data_ID_To_Smooth'].choices = ID_CHOICES
#		form.fields['Timebase'].choices = TIMEBASE_CHOICES
		if form.is_valid():
			#import pdb;pdb.set_trace()
			smoothID = form.cleaned_data['Data_ID_To_Smooth']
			starttime = form.cleaned_data['Start_Time']
			stoptime = form.cleaned_data['Stop_Time']
			smoothall = form.cleaned_data['Smooth_all_active_data_id']
			timebase = form.cleaned_data['Timebase']
			
			starttime_dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(starttime,'%Y-%m-%d_%H-%M-%S')))
			stoptime_dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(starttime,'%Y-%m-%d_%H-%M-%S')))
			
		if not smoothall:
			qs = Data.objects.get(ID=smoothID)
		
		for d in qs:
			lock = Lock()
			with lock:
				o = Data.objects.get(ID=d.ID)
	#			ts = dictTable.calculate_start_time(datetime.datetime.now(),1,'minutes')
				points = int(float(hours) * 60)
				timebase = o.Timebase
				if timebase == 'seconds':
					points = points * 60
				if timebase == 'hours':
					points = int(points / 60)
				if timebase == 'days':
					points = int(points / 1440)
				sts = datatable.calculate_start_time(ts,points,timebase)
				try:
					y = datatable.get_data_records_before_time(d.ID,ts,points,timebase)
					if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
						datatable.db_close(d.ID)
				except:
					y = range(points)
				try:
					n = np.array(y)
					nmin = str(Decimal(str(n.min())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nmean = str(Decimal(str(n.mean())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nmax = str(Decimal(str(n.max())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nstd = str(Decimal(str(n.std())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nptp = str(Decimal(str(n.ptp())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
				except:
					nmin = '-'
					nmean = '-'
					nmax = '-'
					nstd = '-'
					nptp = '-'
				l.append([datatable.get_data_record(d.ID,ts,timebase,int(o.Type.DecimalPlaces)),o.Name,o.Type,nmin,nmean,nmax,nstd,nptp])
				if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
					datatable.db_close(d.ID)
		l.sort(key=lambda x:int(float(x[0])))
		l.reverse()
		listRend += l
		if l:
			listTypesFiltered.append(t)
			
			
			
			
			
	else:
		ts = datatable.calculate_start_time(datetime.datetime.now(),0,'minutes')
		form = SmoothingForm()
		form.fields['Data_ID_To_Smooth'].choices = ID_CHOICES
		form.fields['Timebase'].choices = TIMEBASE_CHOICES
		form.fields['Start_Time'] = str(ts)
		form.fields['Stop_Time'] = str(ts)

	if len(form.errors) > 0:
		err = err + '; form errors: ' + str(form.errors)
	ts = datatable.calculate_start_time(datetime.datetime.now(),0,'minutes')
	return render_to_response('env/plot.html',
		{'timestamp':str(ts)+err,'form':form, 'PostPath':PostPath,'strTable':strTable},
		context_instance=RequestContext(request))


@login_required()
def values(request, arg1 = ''):
	'''Returns the latest value of all Data ID's for Groups accessible by the logged in user.
	
		If there are active DataIDs and no data values are listed,
		make sure the data items and the user are members of the same group.
		Accepts one argument with the following functions:
			1) Auto refresh: include the argument /autoN.  Example: /env/values/auto30 will refresh every 30 seconds
				(performed by including a meta refresh tag in the page header)
			2) To view all data for a specific group, use the url format /env/value/groupname
			3) To view data for a specific datetime, use the url format /env/value/%Y-%m-%d_%H-%M-%S (hours in 24 hour format)
	'''
	try:
		"""Filtering on Group
			Data.objects.filter(Group__name__in=['Group1',])	
		"""
		datatable = discengines.datatable	
		g=[]
		[g.append(str(x)) for x in request.user.groups.all()]
	#	import pdb;pdb.set_trace()
		ts = {}
		auto = ''
		period = 5 #seconds
		if arg1 != '':
			if arg1[:4] == 'auto':
				if arg1[4:].isdigit():
					period = int(arg1[4:])
					auto = '<meta http-equiv="refresh" content="'+str(period)+';URL=/'+djangosite.settings.HTTP_PROXY_PATH+'/env/values/auto'+str(period)+'?'+str(datetime.datetime.now().microsecond)+'">'
			else:
				if arg1 in g:
					g = [arg1]
				else:
					dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(arg1,'%Y-%m-%d_%H-%M-%S')))
					ts['seconds'] = dt
					dt = dt.replace(second = 0)
					ts['minutes'] = dt
					dt = dt.replace(minute = 0)
					ts['hours'] = dt
					dt = dt.replace(hour = 0)
					ts['days'] = dt
		
		listTypes = DataType.objects.all()
		listRend = []	
		listTypesFiltered = []
		allData = Data.objects.all()
		for t in listTypes:
			l = []
			qs = allData.filter(Active=True).filter(Type=t).filter(Group__name__in=g).distinct()
			for d in qs:
				o = Data.objects.get(ID=d.ID)
				if ts == {}:
					#calculate the time at which there should be data available
					cts = datatable.calculate_start_time(datetime.datetime.now(),int(o.Period),o.Timebase)
				else:
					#or get the specific time requested
					cts = ts[o.Timebase]
				try:
					if discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER and (arg1[:4] == 'auto' or arg1 == ''):
						#Get the last value stored in the Value dictionary rather than querying from memory based on a delayed timestamp
						#first check the age of the present data
						dtr = datatable.get_value_date_time(d.ID,o.Timebase)
						if dtr:#if there is data, use that time
							#if string formatted time
							#dt = datetime.datetime.fromtimestamp(time.mktime(time.strptime(dtr,'%Y-%m-%d %H:%M:%S')))
							dt = dtr
						else:
							dt = cts
						if cts <= dt:
							l.append([datatable.get_value(d.ID,o.Type.DecimalPlaces,o.Timebase),o.Name,o.Type,d.ID])
						else:
							try:
								l.append([datatable.get_value(d.ID,o.Type.DecimalPlaces,o.Timebase),o.Name+' ** Last Update: '+datatable.get_value_date_time(d.ID,o.Timebase).strftime('%Y-%m-%d_%H-%M-%S'),o.Type,d.ID])
							except:
								# check the LastUpdate in the status table before reporting no data
								l.append([0,o.Name+' * no new data *',o.Type])
#						print d.ID,'cts,dtr,dt',cts,dtr,dt
					else:
						#convert this to use the dictLatestValue and fall back to the last update in the status table before reporting no data
						l.append([datatable.get_data_record(d.ID,cts,o.Timebase,int(o.Type.DecimalPlaces)),o.Name,o.Type,d.ID])
						if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
							datatable.db_close(d)
				except:
					if datatable.get_value_date_time(d.ID,o.Timebase) == '':
						l.append([0,o.Name+' * no data loaded *',o.Type,d.ID])
					else:
						logger.exception('')
#						exc_type, exc_value, exc_traceback = sys.exc_info()
#						import traceback
#						traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
						l.append([0,o.Name+' * error reading data *',o.Type,d.ID])
			l.sort(key=lambda x:int(float(x[0])))
			l.reverse()
			listRend += l
			if l:
				listTypesFiltered.append(t)
		return render_to_response('env/values.html',
			{'auto':auto,
			 'listRend':listRend,
			 'listTypes':listTypesFiltered,
			 'proxy_path':djangosite.settings.HTTP_PROXY_PATH},
			context_instance=RequestContext(request))
	except:
		logger.exception('')
#		exc_type, exc_value, exc_traceback = sys.exc_info()
#		import traceback
#		traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		return HttpResponse("Error retrieving data")

@login_required()
def values_quick_from_db(request):
	'''Returns the latest value of all Data ID's for Groups accessible by the logged in user.
	
		If there are active DataIDs and no data values are listed,
		make sure the data items and the user are members of the same group.
		** Does not check date and time or notify is data is getting old.
	'''
	try:
		g=[]
		[g.append(str(x)) for x in request.user.groups.all()]
		listTypes = DataType.objects.all()
		listRend = []	
		listTypesFiltered = []
		allData = Data.objects.all()
		for t in listTypes:
			l = []
			qs = allData.filter(Active=True).filter(Type=t).filter(Group__name__in=g).distinct()
			for d in qs:
				o = Data.objects.get(ID=d.ID)
				#convert this to use the dictLatestValue and fall back to the last update in the status table before reporting no data
				dp = int(o.Type.DecimalPlaces)
				try:
					v = str(round(float(discengines.dictValues[str(d.ID)]),dp))
				except:
					v = str(o.Type.DefaultValue)
				if dp == 0:
					v = v[:-2]
				l.append([v,o.Name,o.Type])
#			l.sort(key=lambda x:int(float(x[0])))
#			l.reverse()
			listRend += l
			if l:
				listTypesFiltered.append(t)
		return render_to_response('env/values.html',
			{'auto':'',
			 'listRend':listRend,
			 'listTypes':listTypesFiltered},
			context_instance=RequestContext(request))
	except:
		logger.exception('')
#		exc_type, exc_value, exc_traceback = sys.exc_info()
#		import traceback
#		traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		return HttpResponse("Error retrieving data")

@login_required()
def values_quick(request):
	'''Returns the latest value of all Data ID's for Groups accessible by the logged in user.
	
		If there are active DataIDs and no data values are listed,
		make sure the data items and the user are members of the same group.
		** Does not check date and time or notify is data is getting old.
	'''
#	import pdb;pdb.set_trace()
	try:
		g=[]
		[g.append(str(x)) for x in request.user.groups.all()]
		listRend = []	
		listTypesFiltered = []
		for t in discengines.dictDataType:
			l = []
			for d in discengines.dictData:
				if discengines.dictData[d]['Type'] == t:
					if list(set(discengines.dictData[d]['GroupList']) & set(g)): #They have a common group
						try:
							v = str(round(float(discengines.dictValues[unicode(d)]),int(discengines.dictDataType[t]['DecimalPlaces'])))
						except:
							v = str(discengines.dictDataType[t]['DefaultValue'])
						if discengines.dictDataType[t]['DecimalPlaces'] == 0:
							v = v[:-2]
						l.append([v,discengines.dictData[d]['Name'],discengines.dictDataType[t]['Type']])
#			l.sort(key=lambda x:int(float(x[0])))
#			l.reverse()
			listRend += l
			if l:
				listTypesFiltered.append(discengines.dictDataType[t]['Type'])
#		print listRend
		return render_to_response('env/values.html',
			{'auto':'',
			 'timestamp':'',
			 'listRend':listRend,
			 'listTypes':listTypesFiltered},
			context_instance=RequestContext(request))
	except:
		logger.exception('')
#		exc_type, exc_value, exc_traceback = sys.exc_info()
#		import traceback
#		traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		return HttpResponse("Error retrieving data")

@login_required()
def stats(request, hours='24',stoptime=''):
	"""Statistics for all the active DataIDs of which the DataID and the user are members of the same Group.
	
		Accepts two optional arguments: hours and a datetime stamp (format %Y-%m-%d_%H-%M-%S) (hour in 24hr format)
		Statistics are calculated over the number of hours preceeding the datetime stamp
	"""
	"""
		Filtering on Group
		Data.objects.filter(Group__name__in=['Group1',])
		Statistics for 24 hour period
		Latest Value, Min/Average/Max/StdDev for Period
	"""
#	import pdb;pdb.set_trace()
	if hours.isdigit():
		hours = int(hours.replace('/','')) #if stoptime is blank, the '/' character is included with the hours variable
	else:
		messages.warning(request,'invalid value for hours argument.  Using 24 hours.')
		hours = 24
	datatable = discengines.datatable
	if stoptime == '':
		ts = datatable.calculate_start_time(datetime.datetime.now(),1,'minutes')
	else:
		try:
			ts = datetime.datetime.fromtimestamp(time.mktime(time.strptime(stoptime,'%Y-%m-%d_%H-%M-%S')))
			messages.debug(request,'Using timestamp '+stoptime)
		except:
			messages.warning(request,'INVALID TIME STAMP (use format %Y-%m-%d %H:%M:%S), *USING CURRENT TIME*')
			ts = datatable.calculate_start_time(datetime.datetime.now(),1,'minutes')
	g=[]
	[g.append(str(x)) for x in request.user.groups.all()]
	listTypes = DataType.objects.all()
	listRend = []	
	listTypesFiltered = []
	for t in listTypes:
		t_id = DataType.objects.get(Type=t).id
		l = []
		qs = Data.objects.all().filter(Active=True).filter(Type=t).filter(Group__name__in=g).distinct()
		for d in qs:
			lock = Lock()
			with lock:
				o = Data.objects.get(ID=d.ID)
	#			ts = dictTable.calculate_start_time(datetime.datetime.now(),1,'minutes')
				points = int(float(hours) * 60)
				timebase = o.Timebase
				if timebase == 'seconds':
					points = points * 60
				if timebase == 'hours':
					points = int(points / 60)
				if timebase == 'days':
					points = int(points / 1440)
				sts = datatable.calculate_start_time(ts,points,timebase)
				try:
					y = datatable.get_data_records_before_time(d.ID,ts,points,timebase)
					if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
						datatable.db_close(d.ID)
				except:
					y = range(points)
				try:
					n = np.array(y)
					nmin = str(Decimal(str(n.min())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nmean = str(Decimal(str(n.mean())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nmax = str(Decimal(str(n.max())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nstd = str(Decimal(str(n.std())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nptp = str(Decimal(str(n.ptp())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nsum = str(Decimal(str(n.sum())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					nmeanXhrs = str(Decimal(str(float(nmean)*int(hours))).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
					#need numpy v1.8 to add median
#					nmedian = str(Decimal(str(n.median())).quantize(Decimal(10) ** (-1*o.Type.DecimalPlaces)))
				except:
					logger.exception('error calculating statistics for ID {}'.format(d.ID))
					nmin = '-'
					nmean = '-'
					nmax = '-'
					nstd = '-'
					nptp = '-'
					nsum = '-'
					nmeanXhrs = '-'
#					nmedian = '-'
				
				try:
					dp = int(discengines.dictDataType[t_id]['DecimalPlaces'])
					if stoptime == '':
						dtr = datatable.get_value_date_time(d.ID,o.Timebase)
						if dtr:
							ts = dtr
						else:
							ts = datatable.calculate_start_time(datetime.datetime.now(),int(o.Period),o.Timebase)
					value = datatable.get_data_record(d.ID,ts,timebase,int(o.Type.DecimalPlaces))
					datavalue = str(round(float(value),dp))
					if dp == 0:
						datavalue = datavalue[:-2]
				except:
					datavalue = -999
					logger.exception('')
				finally:
					if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
						datatable.db_close(d.ID)
				l.append([datavalue,o.Name,o.Type,nmin,nmean,nmax,nstd,nptp,nsum,timebase,nmeanXhrs,d.ID])
		l.sort(key=lambda x:int(float(x[0])))
		l.reverse()
		listRend += l
		if l:
			listTypesFiltered.append(t)
	return render_to_response('env/stats.html',
							  {'listRend':listRend,'listTypes':listTypesFiltered,'proxy_path':djangosite.settings.HTTP_PROXY_PATH,'minutes':hours*60,'stoptime':stoptime},
							  context_instance=RequestContext(request))

@login_required()
def data_table(request,timebase='minutes',arg_points='60',arg_time=''):
	"""Data Table for all the active DataIDs of which the DataID and the user are members of the same Group.
	
		Accepts three optional arguments in the following order:
			timebase(seconds,minutes,hours,days), 
			number of points, 
			datetime stamp (format %Y-%m-%d_%H-%M-%S)
		Default is data_table/minutes/60/<time now>
	"""
	try:
		#if request.method == 'GET':
		#	try:
		#		print 'request:',request.session.get('timebase')
		#	except:
		#		print 'none found'
		datatable = discengines.datatable
		points = int(arg_points.replace('/',''))
		#argTime = ''
		#if arg1 <> '' and len(arg1) < 5:
		#	hours = arg1
		#	if arg2 <> '':
		#		argTime = arg2
		#if len(arg1) > 4:
		#	argTime = arg1
		#	if arg2 <> '':
		#		hours = arg2
		#points = int(float(hours) * 60)
	#	print 'points',points
		if arg_time == '':
			ts = datetime.datetime.now()#datatable.calculate_start_time(datetime.datetime.now(),1,timebase)
		else:
			ts = datetime.datetime.fromtimestamp(time.mktime(time.strptime(argTime,'%Y-%m-%d_%H-%M-%S')))
		sts = datatable.calculate_start_time(ts,points,timebase)
		listTS = eval('[ sts + datetime.timedelta('+timebase+'=x) for x in range('+str(points)+') ]')
	
		IDs = ['ID',]
		Names = ['Name',]
		Types = ['Type',]
		DataTable = [listTS,]
		for d in Data.objects.all().exclude(Active=False):
			o = Data.objects.get(ID=d.ID)
	
	#		timebase = o.Timebase
			#if timebase == 'seconds':
			#	points = points * 60
			#if timebase == 'hours':
			#	points = int(points / 60)
			#if timebase == 'days':
			#	points = int(points / 1440)
			IDs.append(d.ID)
			Names.append(o.Name)
			Types.append(o.Type)
			try:
	#			import pdb;pdb.set_trace()
				lst = datatable.get_data_records_before_time(d.ID,ts,points,timebase)
#				print d.ID,lst
				if lst:
					DataTable.append(lst)
				else:
					DataTable.append(range(points))
				if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
					datatable.db_close(d.ID)
			except:
				DataTable.append(range(points))
				logging.exception('error retrieving data for data_table view with d.ID: '+str(d.ID))
#				exc_type, exc_value, exc_traceback = sys.exc_info()
#				import traceback
#				traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		strTable = '<tr>'
		for c in IDs:
			strTable += '<td>'+str(c)+'</td>'
		strTable += '</tr>'
		for c in Names:
			strTable += '<td>'+str(c)+'</td>'
		strTable += '</tr>'
		for c in Types:
			strTable += '<td>'+str(c)+'</td>'
		strTable += '</tr>'
	
		for r in range(len(DataTable[0])):
	#		print 'r',r
			strTable += '<tr>'
			for c in range(len(DataTable)):
	#			print 'c',c,DataTable[c][r],type(DataTable[c][r])
				if c == 0:
					strTable += '<td>'+str(DataTable[c][r])+'</td>'
				else:
					try:
						strTable += '<td>'+'{:.2f}'.format(DataTable[c][r])+'</td>'
					except:
						strTable += '<td></td>'
			strTable += '</tr>'
		return render_to_response('env/data_table.html',
								{'strTable':strTable,},
								context_instance=RequestContext(request))
	except:
		logger.exception('')
#		exc_type, exc_value, exc_traceback = sys.exc_info()
#		import traceback
#		traceback.print_exception(exc_type,exc_value,exc_traceback,limit=10,file=sys.stdout)
		return HttpResponse("Error retrieving data")

POINT_CHOICES = (
('10','10 min'),
('60','1 hr'),
('180','3 hrs'),
('360','6 hrs'),
('720','12 hrs'),
('1440','1 day'),
('2880','2 days'),
('4320','3 days'),
('10080','7 days'),
('40320','28 days'),
('259200','180 days'),
('525600','365 days'))

class PlotForm(forms.Form):
	Timebase = forms.ChoiceField(choices=TIMEBASE_CHOICES,widget=RadioSelect,required=True,initial='minutes')
	Stop_Time = forms.CharField(max_length=19,required=False,initial='now') 
	Points_To_Plot = forms.ChoiceField(choices=POINT_CHOICES, required=True,initial=2880)
	Data_ID_To_Plot = forms.MultipleChoiceField(widget=CheckboxSelectMultiple, required=True)
	Auto_Scale_All = forms.BooleanField(required=False)
	Show_Data_Table = forms.BooleanField(required=False)

	#def __init__(self, *args, **kwargs):
	#	ID_CHOICES = kwargs.pop('ID_CHOICES')
	#	super(PlotForm, self).__init__(*args, **kwargs)
	#	self.fields['Points_To_Plot'] = forms.ChoiceField(required=True, widget=RadioSelect, choices=POINT_CHOICES, initial=2880)
	#	self.fields['Data_ID_To_Plot'] = forms.MultipleChoiceField(choices=ID_CHOICES, widget=CheckboxSelectMultiple, required=True)

@login_required()
def plot(request):
	'''Uses Matplotlib to plot data from active DataIDs of which the user and DataID are in the same group
		
		Data can be displayed in any timebase regardless of the timebase in which it was recorded
		Data is separtely plotted according to it's Type and the Y axis Max/Min settings of that Type
		Choosing autoscale forces all the data to the same plot and the Y axis is autoscaled to all the data.
	'''
	datatable = discengines.datatable
	PostPath = '/'+djangosite.settings.HTTP_PROXY_PATH+'/env/plot'
	g=[]
	[g.append(str(x)) for x in request.user.groups.all()]
	ImageName = str(datetime.datetime.now()).replace(':','-').replace(' ','_').replace('.','-')

	listID = []
	#, Timebase=timebase
	for d in Data.objects.all().filter(Active=True).order_by('Type','Name').filter(Group__name__in=g).distinct():
		o = Data.objects.get(ID=d.ID)
#		strColor = '<font color="'+str(d.Color)+'"><b>'+str(d.Color)+'</b></font>, '
		listID.append((o.ID,str(o.Name)+'_'*(30-len(o.Name))+str(o.Type)+'.'*(21-len(str(o.Type)))+str(d.Color)+', '+str(d.ID)))
		
	ID_CHOICES=tuple(listID)
	strTable = None
	
	if request.method == 'POST':
		form = PlotForm(request.POST)
		form.fields['Data_ID_To_Plot'].choices = ID_CHOICES
#		form.fields['Timebase'].choices = TIMEBASE_CHOICES
		if form.is_valid():
			#import pdb;pdb.set_trace()
			IDs = form.cleaned_data['Data_ID_To_Plot']
			points = int(form.cleaned_data['Points_To_Plot'])
			stoptime = form.cleaned_data['Stop_Time']
			autoscaleall = form.cleaned_data['Auto_Scale_All']
			timebase = form.cleaned_data['Timebase']
			if stoptime != '' and stoptime != 'now':
				try:
					ts = datetime.datetime.fromtimestamp(time.mktime(time.strptime(stoptime,'%Y-%m-%d %H:%M:%S')))
				except:
					ts = datatable.calculate_start_time(datetime.datetime.now(),0,timebase)
					messages.warning(request,'INVALID TIME STAMP (use format %Y-%m-%d %H:%M:%S), *USING CURRENT TIME*')
			else:
				ts = datatable.calculate_start_time(datetime.datetime.now(),0,timebase)
			#Justify time to the next hour
			#ts = ts + datetime.timedelta(minutes=(59-ts.minute),seconds=59-ts.second,microseconds=1000000-ts.microsecond)

			if timebase == 'seconds':
				points = points * 60
			if timebase == 'hours':
				points = int(points / 60)
			if timebase == 'days':
				points = int(points / 1440)
			lock = Lock()
			with lock:
				sts = datatable.calculate_start_time(ts,points,timebase)
				if timebase == 'seconds':
					listTS = [ sts + datetime.timedelta(seconds=x) for x in range(0,points) ]
				if timebase == 'minutes':
					listTS = [ sts + datetime.timedelta(minutes=x) for x in range(0,points) ]
				if timebase == 'hours':
					listTS = [ sts + datetime.timedelta(hours=x) for x in range(0,points) ]
				if timebase == 'days':
					listTS = [ sts + datetime.timedelta(days=x) for x in range(0,points) ]
				listTS = np.array(listTS)
				majorLocator = MultipleLocator(5)
				majorFormatter = FormatStrFormatter('%d')
				minorLocator = MultipleLocator(1)
				#ax.yaxis.set_major_locator(majorLocator)
				#ax.yaxis.set_major_formatter(majorFormatter)
				#ax.yaxis.set_minor_locator(minorLocator)			
				
				if timebase == 'seconds':
					majorFormatter = matplotlib.dates.DateFormatter('%H:%M:%S')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.SecondLocator(interval=30)
				if timebase == 'minutes':
					majorFormatter = matplotlib.dates.DateFormatter('%m/%d %H:%M')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.MinuteLocator(interval=15)
				if timebase == 'hours':
					majorFormatter = matplotlib.dates.DateFormatter('%m/%d %H:%M')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.HourLocator(interval=1)
				if timebase == 'days':
					majorFormatter = matplotlib.dates.DateFormatter('%m/%d')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.DayLocator(interval=1)
				
				if autoscaleall:
					listYaxis = ['']
				else:
					listYaxis = []
					for d in IDs:
						o = Data.objects.get(ID=d)
						T = DataType.objects.get(Type = o.Type)
						if (float(T.PlotYmin),float(T.PlotYmax)) not in listYaxis:
							listYaxis.append((float(T.PlotYmin),float(T.PlotYmax)))

				if form.cleaned_data['Show_Data_Table']:
					listIDs = ['ID',]
					Names = ['Name',]
					Types = ['Type',]
					DataTable = [listTS,]

				fig = plt.figure()
				listAxes = []
				listNumPlot = []
				for d in IDs:
					#fullID = Data.objects.get(ID=d)
					#import pdb;pdb.set_trace()
					try:
						y = datatable.get_data_records_before_time(d,ts,points,timebase)
						y = np.array(y)
					except:
						y = np.array(range(points))
					if len(y) == 0:
						y = np.array(range(points))
					if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
						datatable.db_close(d)
					o = Data.objects.get(ID=d)
					T = DataType.objects.get(Type = o.Type)
					if T.Boolean and timebase != o.Timebase:
						 m = {'seconds':60,'minutes':60,'hours':60,'days':24}[timebase]
						 y *= m
					
					if form.cleaned_data['Show_Data_Table']:
						DataTable.append(y.tolist())
						listIDs.append(d)
						Names.append(o.Name)
						Types.append(o.Type)
						
					if autoscaleall:
						i = 0
					else:
						i = listYaxis.index((float(T.PlotYmin),float(T.PlotYmax)))
					NumPlot = int(len(listYaxis)*100 + 10 + (1 + i))
					if NumPlot not in listNumPlot:
						listNumPlot.append(NumPlot)
						if len(listNumPlot) == 1:
							ax = fig.add_subplot(NumPlot)
							if not autoscaleall:
								ax.set_ylim(float(T.PlotYmin),float(T.PlotYmax))	
							ax.xaxis.set_minor_locator(minorLocator)
							ax.xaxis.set_major_formatter(majorFormatter)
							fig.autofmt_xdate()
						else:
							ax = fig.add_subplot(NumPlot, sharex=listAxes[0])
							ax.set_ylim(float(T.PlotYmin),float(T.PlotYmax))
						if T.Boolean:
							ax.fill_between(listTS,0,y,facecolor=str(o.Color))
						else:
							try:
								ax.plot(listTS,y,color=str(o.Color),label=str(o.Name))
							except:
								logger.exception('')
#								print 'error plotting'
#								import pdb;pdb.set_trace()
#								print len(listTS),len(y)
						listAxes.append(ax)
					else:
						listAxes[listNumPlot.index(NumPlot)].plot(listTS,y,color=str(o.Color),label=str(o.Name))

				fig.set_size_inches(12,9.6)
				#fig.savefig('../media/plots/'+ImageName+'.png',dbi=200)
				fig.savefig(djangosite.settings.APP_BASE_PATH+'/media/plots/'+ImageName+'.png',dbi=200)
				time.sleep(0.2)
				
			if form.cleaned_data['Show_Data_Table']:
				strTable = '<tr>'
				for c in listIDs:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'
				for c in Names:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'
				for c in Types:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'

				for r in range(len(DataTable[0])):
			#		print 'r',r
					strTable += '<tr>'
					for c in range(len(DataTable)):
			#			print 'c',c,DataTable[c][r],type(DataTable[c][r])
						if c == 0:
							strTable += '<td>'+str(DataTable[c][r])+'</td>'
						else:
							try:
								strTable += '<td>'+'{:.2f}'.format(DataTable[c][r])+'</td>'
							except:
								strTable += '<td></td>'
					strTable += '</tr>'


	else:
		form = PlotForm()
		form.fields['Data_ID_To_Plot'].choices = ID_CHOICES
		form.fields['Timebase'].choices = TIMEBASE_CHOICES
		ImageName = None

	MediaPath =djangosite.settings.MEDIA_URL
	return render_to_response('env/plot.html',
		{'form':form, 'MediaPath':MediaPath, 'ImageName':ImageName, 'PostPath':PostPath, 'strTable':strTable},
		context_instance=RequestContext(request))

class HighchartsForm(forms.Form):
	Timebase = forms.ChoiceField(choices=TIMEBASE_CHOICES,widget=RadioSelect,required=True,initial='minutes')
	Stop_Time = forms.CharField(max_length=19,required=False,initial='now') 
	Points_To_Plot = forms.ChoiceField(choices=POINT_CHOICES, required=True,initial=2880)
	Data_ID_To_Plot = forms.MultipleChoiceField(widget=CheckboxSelectMultiple, required=True)
#	Auto_Scale_All = forms.BooleanField(required=False)
	Show_Data_Table = forms.BooleanField(required=False)
	
@login_required()
def highcharts(request):
	'''Uses highcharts to plot data from active DataIDs of which the user and DataID are in the same group
		
		Data can be displayed in any timebase regardless of the timebase in which it was recorded
		All data is displayed on the same plot and the Y axis is autoscaled
	'''
	PostPath = '/'+djangosite.settings.HTTP_PROXY_PATH+'/env/highcharts'
	ProxyPath = djangosite.settings.HTTP_PROXY_PATH
	datatable = discengines.datatable
	g=[]
	[g.append(str(x)) for x in request.user.groups.all()]

	listID = []
	#, Timebase=timebase
	for d in Data.objects.all().filter(Active=True).order_by('Type','Name').filter(Group__name__in=g).distinct():
		o = Data.objects.get(ID=d.ID)
#		strColor = '<font color="'+str(d.Color)+'"><b>'+str(d.Color)+'</b></font>, '
		listID.append((o.ID,str(o.Name)+'_'*(30-len(o.Name))+str(o.Type)+'.'*(21-len(str(o.Type)))+str(d.Color)+', '+str(d.ID)))
		
	ID_CHOICES=tuple(listID)
	strTable = None

	series = []
	xAxis_categories = {}
	series_colors = []
	
	if request.method == 'POST':
		form = HighchartsForm(request.POST)
		form.fields['Data_ID_To_Plot'].choices = ID_CHOICES
#		form.fields['Timebase'].choices = TIMEBASE_CHOICES
		if form.is_valid():
#			import pdb;pdb.set_trace()
			IDs = form.cleaned_data['Data_ID_To_Plot']
			points = int(form.cleaned_data['Points_To_Plot'])
			stoptime = form.cleaned_data['Stop_Time']
			autoscaleall = False#form.cleaned_data['Auto_Scale_All']
			timebase = form.cleaned_data['Timebase']
			if stoptime != '' and stoptime != 'now':
				try:
					ts = datetime.datetime.fromtimestamp(time.mktime(time.strptime(stoptime,'%Y-%m-%d %H:%M:%S')))
				except:
					ts = datatable.calculate_start_time(datetime.datetime.now(),0,timebase)
					messages.warning(request,'INVALID TIME STAMP (use format %Y-%m-%d %H:%M:%S), *USING CURRENT TIME*')
			else:
				ts = datatable.calculate_start_time(datetime.datetime.now(),0,timebase)
			#Justify time to the next hour
			#ts = ts + datetime.timedelta(minutes=(59-ts.minute),seconds=59-ts.second,microseconds=1000000-ts.microsecond)
						
			if timebase == 'seconds':
				points = points * 60
			if timebase == 'hours':
				points = int(points / 60)
			if timebase == 'days':
				points = int(points / 1440)
			lock = Lock()
			with lock:
				sts = datatable.calculate_start_time(ts,points,timebase)
				if timebase == 'seconds':
					listTS = [ (sts + datetime.timedelta(seconds=x)).strftime('%H:%M:%S') for x in range(0,points) ]
					pointInterval = 1000
				if timebase == 'minutes':
					listTS = [ (sts + datetime.timedelta(minutes=x)).strftime('%d_%H:%M') for x in range(0,points) ]
					pointInterval = 60000
				if timebase == 'hours':
					listTS = [ (sts + datetime.timedelta(hours=x)).strftime('%d_%H') for x in range(0,points) ]
					pointInterval = 3600000
				if timebase == 'days':
					listTS = [ (sts + datetime.timedelta(days=x)).strftime('%m-%d') for x in range(0,points) ]
					pointInterval = 24*3600000
				#listTS = np.array(listTS)
				xAxis_categories['categories'] = json.dumps(listTS)
				
				if autoscaleall:
					listYaxis = ['']
				else:
					listYaxis = []
					for d in IDs:
						o = Data.objects.get(ID=d)
						T = DataType.objects.get(Type = o.Type)
						if (float(T.PlotYmin),float(T.PlotYmax)) not in listYaxis:
							listYaxis.append((float(T.PlotYmin),float(T.PlotYmax)))

				if form.cleaned_data['Show_Data_Table']:
					listIDs = ['ID',]
					Names = ['Name',]
					Types = ['Type',]
					DataTable = [listTS,]
				
				listAxes = []
				listNumPlot = []
				for d in IDs:
					#fullID = Data.objects.get(ID=d)
					#import pdb;pdb.set_trace()
					try:
						y = datatable.get_data_records_before_time(d,ts,points,timebase)
						y = np.array(y)
					except:
						y = np.array(range(points))
					if len(y) == 0:
						y = np.array(range(points))
						logger.debug('no data found for ID: '+str(d))
					if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
						datatable.db_close(d)
					o = Data.objects.get(ID=d)
					#T = DataType.objects.get(Type = o.Type)
					#if T.Boolean and timebase != o.Timebase:
					#	 m = {'Second':60,'Minute':60,'Hour':60,'Day':24}[timebase]
					#	 y *= m
					
					if form.cleaned_data['Show_Data_Table']:
						DataTable.append(y.tolist())
						listIDs.append(d)
						Names.append(o.Name)
						Types.append(o.Type)
						
					if autoscaleall:
						i = 0
					else:
						i = listYaxis.index((float(T.PlotYmin),float(T.PlotYmax)))
					series_y = {}
					series_y['name'] = '\''+str(o.Name)+'\''
					series_y['data'] = y.tolist()
					sts_minusmonth = str(int(sts.strftime('%m'))-1)
					series_y['pointStart'] = sts.strftime('Date.UTC(%Y, month, %d, %H, %M, %S)').replace('month',sts_minusmonth)
					series_y['pointInterval'] = pointInterval
					series.append(series_y)
					series_colors.append(o.Color)
					
			if form.cleaned_data['Show_Data_Table']:
				strTable = '<tr>'
				for c in listIDs:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'
				for c in Names:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'
				for c in Types:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'

				for r in range(len(DataTable[0])):
			#		print 'r',r
					strTable += '<tr>'
					for c in range(len(DataTable)):
			#			print 'c',c,DataTable[c][r],type(DataTable[c][r])
						if c == 0:
							strTable += '<td>'+str(DataTable[c][r])+'</td>'
						else:
							try:
								strTable += '<td>'+'{:.2f}'.format(DataTable[c][r])+'</td>'
							except:
								strTable += '<td></td>'
					strTable += '</tr>'
		jsonseries = json.dumps(series)
		json_series_colors = json.dumps(series_colors)
		
	else:
		form = HighchartsForm()
		form.fields['Data_ID_To_Plot'].choices = ID_CHOICES
		form.fields['Timebase'].choices = TIMEBASE_CHOICES
		jsonseries = ''
		xAxis_categories = ''
		json_series_colors = ''
		
	if len(form.errors) > 0:
		err = err + '; form errors: ' + str(form.errors)
	ts = datatable.calculate_start_time(datetime.datetime.now(),0,'minutes')
	return render_to_response('env/highcharts.html',
		{'form':form, 'PostPath':PostPath, 'ProxyPath':ProxyPath, 'series_colors':json_series_colors, 'xAxis_categories':xAxis_categories, 'series':jsonseries, 'strTable':strTable},
		context_instance=RequestContext(request))


def checkdata_id_owners(self, ID):
	#ID = id that is being checked for duplicate links (from different models)
	listOwners = []
	for m in djangosite.settings.INSTALLED_APPS:
		try:
			listSensors = sys.modules[m].views.data_id_owners(ID)
			if listSensors:
				for s in listSensors:
					listOwners.append(s)
		except:
			pass
	return listOwners

MINUTE_CHOICES = tuple([(str(x),str(x)) for x in range(0,61)])
HOUR_CHOICES = tuple([(str(x),str(x)) for x in range(0,25)])
DAY_CHOICES = tuple([(str(x),str(x)) for x in range(0,8)])
WEEK_CHOICES = tuple([(str(x),str(x)) for x in range(0,105)])

class DifferenceForm(forms.Form):
	Timebase = forms.ChoiceField(choices=TIMEBASE_CHOICES,widget=RadioSelect,required=True,initial='minutes')
	Stop_Time = forms.CharField(max_length=19,required=False,initial='now')
	Minutes_To_Plot = forms.ChoiceField(choices=MINUTE_CHOICES,required=True,initial=0)
	Hours_To_Plot = forms.ChoiceField(choices=HOUR_CHOICES,required=True,initial=0)
	Days_To_Plot = forms.ChoiceField(choices=DAY_CHOICES,required=True,initial=2)
	Weeks_To_Plot = forms.ChoiceField(choices=WEEK_CHOICES,required=True,initial=0)
	Minuend = forms.ChoiceField(required=True)
	Subtrahend = forms.ChoiceField(required=True)
	Minutes_to_shift_Subtrahend = forms.ChoiceField(choices=MINUTE_CHOICES,required=True,initial=0)
	Hours_to_shift_Subtrahend = forms.ChoiceField(choices=HOUR_CHOICES,required=True,initial=0)
	Days_to_shift_Subtrahend = forms.ChoiceField(choices=DAY_CHOICES,required=True,initial=0)
	Weeks_to_shift_Subtrahend = forms.ChoiceField(choices=WEEK_CHOICES,required=True,initial=0)
#	Auto_Scale_All = forms.BooleanField(required=False)
	Show_Data_Table = forms.BooleanField(required=False)

@login_required()
def difference(request):
	'''Uses highcharts to plot the difference between two DataIDs of which the user and DataID are in the same group
		
		Data can be displayed in any timebase regardless of the timebase in which it was recorded
		All data is displayed on the same plot and the Y axis is autoscaled
	'''
	PostPath = '/'+djangosite.settings.HTTP_PROXY_PATH+'/env/difference'
	ProxyPath = djangosite.settings.HTTP_PROXY_PATH
	datatable = discengines.datatable
	g=[]
	[g.append(str(x)) for x in request.user.groups.all()]

	listID = []
	#, Timebase=timebase
	for d in Data.objects.all().filter(Active=True).order_by('Type','Name').filter(Group__name__in=g).distinct():
		o = Data.objects.get(ID=d.ID)
#		strColor = '<font color="'+str(d.Color)+'"><b>'+str(d.Color)+'</b></font>, '
		listID.append((o.ID,str(o.Name)+'_'*(30-len(o.Name))+str(o.Type)+'.'*(21-len(str(o.Type)))+str(d.Color)+', '+str(d.ID)))
		
	ID_CHOICES=tuple(listID)
	strTable = None

	series = []
	xAxis_categories = {}
	series_colors = []
	
	if request.method == 'POST':
		form = DifferenceForm(request.POST)
		form.fields['Minuend'].choices = ID_CHOICES
		form.fields['Subtrahend'].choices = ID_CHOICES
		if form.is_valid():
			
			minuend = form.cleaned_data['Minuend']
			subtrahend = form.cleaned_data['Subtrahend']
			minutes = int(form.cleaned_data['Minutes_To_Plot'])
			hours = int(form.cleaned_data['Hours_To_Plot'])
			days = int(form.cleaned_data['Days_To_Plot'])
			weeks = int(form.cleaned_data['Weeks_To_Plot'])
			stoptime = form.cleaned_data['Stop_Time']
			autoscaleall = False#form.cleaned_data['Auto_Scale_All']
			timebase = form.cleaned_data['Timebase']
			shiftminutes = int(form.cleaned_data['Minutes_to_shift_Subtrahend'])
			shifthours = int(form.cleaned_data['Hours_to_shift_Subtrahend'])
			shiftdays = int(form.cleaned_data['Days_to_shift_Subtrahend'])
			shiftweeks = int(form.cleaned_data['Weeks_to_shift_Subtrahend'])
			
			IDs = [minuend,subtrahend]
			
			if stoptime != '' and stoptime != 'now':
				try:
					ts = datetime.datetime.fromtimestamp(time.mktime(time.strptime(stoptime,'%Y-%m-%d %H:%M:%S')))
				except:
					ts = datatable.calculate_start_time(datetime.datetime.now(),0,timebase)
					messages.warning(request,'INVALID TIME STAMP (use format %Y-%m-%d %H:%M:%S), *USING CURRENT TIME*')
			else:
				ts = datatable.calculate_start_time(datetime.datetime.now(),0,timebase)
			#Justify time to the next hour
			#ts = ts + datetime.timedelta(minutes=(59-ts.minute),seconds=59-ts.second,microseconds=1000000-ts.microsecond)
			
			if timebase == 'seconds':
				points = minutes * 60
				points += hours * 60 * 60
				points += days * 60 * 60 * 24
				
				shiftpoints = shiftminutes * 60
				shiftpoints += shifthours * 60 * 60
				shiftpoints += shiftdays * 60 * 60 * 24
				shiftdelta = datetime.timedelta(seconds=shiftpoints)
#Uncomment if it is okay to wait forever for this much data
#				points += weeks * 60 * 60 * 24 *7
			if timebase == 'minutes':
				points = minutes
				points += hours * 60
				points += days * 60 * 24
				points += weeks * 60 * 24 * 7
				
				shiftpoints = shiftminutes
				shiftpoints += shifthours * 60
				shiftpoints += shiftdays * 60 * 24
				shiftpoints += shiftweeks * 60 * 24 * 7
				shiftdelta = datetime.timedelta(minutes=shiftpoints)
			if timebase == 'hours':
				points = int(minutes / 60)
				points += hours
				points += days * 24
				points += weeks * 24 * 7
				
				shiftpoints = int(shiftminutes / 60)
				shiftpoints += shifthours
				shiftpoints += shiftdays * 24
				shiftpoints += shiftweeks * 24 * 7
				shiftdelta = datetime.timedelta(hours=shiftpoints)
			if timebase == 'days':
				points = int(minutes / 1440)
				points += int(hours / 24)
				points += days
				points += weeks * 7
				
				shiftpoints = int(shiftminutes / 1440)
				shiftpoints += int(shifthours / 24)
				shiftpoints += shiftdays
				shiftpoints += shiftweeks * 7
				shiftdelta = datetime.timedelta(days=shiftpoints)
			lock = Lock()
			with lock:
				sts = datatable.calculate_start_time(ts,points,timebase)
				if timebase == 'seconds':
					listTS = [ (sts + datetime.timedelta(seconds=x)).strftime('%H:%M:%S') for x in range(0,points) ]
					pointInterval = 1000
				if timebase == 'minutes':
					listTS = [ (sts + datetime.timedelta(minutes=x)).strftime('%d_%H:%M') for x in range(0,points) ]
					pointInterval = 60000
				if timebase == 'hours':
					listTS = [ (sts + datetime.timedelta(hours=x)).strftime('%d_%H') for x in range(0,points) ]
					pointInterval = 3600000
				if timebase == 'days':
					listTS = [ (sts + datetime.timedelta(days=x)).strftime('%m-%d') for x in range(0,points) ]
					pointInterval = 24*3600000
				#listTS = np.array(listTS)
				xAxis_categories['categories'] = json.dumps(listTS)
				
				if autoscaleall:
					listYaxis = ['']
				else:
					listYaxis = []
					for d in IDs:
						o = Data.objects.get(ID=d)
						T = DataType.objects.get(Type = o.Type)
						if (float(T.PlotYmin),float(T.PlotYmax)) not in listYaxis:
							listYaxis.append((float(T.PlotYmin),float(T.PlotYmax)))

				if form.cleaned_data['Show_Data_Table']:
					listIDs = ['ID',]
					Names = ['Name',]
					Types = ['Type',]
					DataTable = [listTS,]
				
				listAxes = []
				listNumPlot = []
				ydata = []
				cnt = 1
#				import pdb;pdb.set_trace()
				for d in IDs:
					#fullID = Data.objects.get(ID=d)
					if cnt == 2:
						ts -= shiftdelta
					try:
						y = datatable.get_data_records_before_time(d,ts,points,timebase)
						y = np.array(y)
					except:
						y = np.array(range(points))
					if len(y) == 0:
						y = np.array(range(points))
						messages.warning(request,'no data found for ID: '+str(d))
					if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
						datatable.db_close(d)
					o = Data.objects.get(ID=d)
					#T = DataType.objects.get(Type = o.Type)
					#if T.Boolean and timebase != o.Timebase:
					#	 m = {'Second':60,'Minute':60,'Hour':60,'Day':24}[timebase]
					#	 y *= m
					ydata.append(y)					
					
					if form.cleaned_data['Show_Data_Table']:
						DataTable.append(y.tolist())
						listIDs.append(d)
						Names.append(o.Name)
						Types.append(o.Type)
						
					if autoscaleall:
						i = 0
					else:
						i = listYaxis.index((float(T.PlotYmin),float(T.PlotYmax)))
					series_y = {}
					series_y['name'] = '\''+str(o.Name)+'\''
					series_y['data'] = y.tolist()
					sts_minusmonth = str(int(sts.strftime('%m'))-1)
					series_y['pointStart'] = sts.strftime('Date.UTC(%Y, month, %d, %H, %M, %S)').replace('month',sts_minusmonth)
					series_y['pointInterval'] = pointInterval
					series.append(series_y)
					series_colors.append(o.Color)
					cnt += 1

#				import pdb;pdb.set_trace()
				#Calculate Difference
				ydiff = []
				for x in range(len(ydata[0])):
					ydiff.append(ydata[0][x] - ydata[1][x])
				
				if form.cleaned_data['Show_Data_Table']:
					DataTable.append(ydiff)
					listIDs.append('-1')
					Names.append('Difference')
					Types.append(o.Type)
					
				if autoscaleall:
					i = 0
				else:
					i = listYaxis.index((float(T.PlotYmin),float(T.PlotYmax)))
				series_y = {}
				series_y['name'] = '\''+'Difference'+'\''
				series_y['data'] = ydiff
				sts_minusmonth = str(int(sts.strftime('%m'))-1)
				series_y['pointStart'] = sts.strftime('Date.UTC(%Y, month, %d, %H, %M, %S)').replace('month',sts_minusmonth)
				series_y['pointInterval'] = pointInterval
				series.append(series_y)
				series_colors.append('Black')


			if form.cleaned_data['Show_Data_Table']:
				strTable = '<tr>'
				for c in listIDs:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'
				for c in Names:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'
				for c in Types:
					strTable += '<td>'+str(c)+'</td>'
				strTable += '</tr>'

				for r in range(len(DataTable[0])):
			#		print 'r',r
					strTable += '<tr>'
					for c in range(len(DataTable)):
			#			print 'c',c,DataTable[c][r],type(DataTable[c][r])
						if c == 0:
							strTable += '<td>'+str(DataTable[c][r])+'</td>'
						else:
							try:
								strTable += '<td>'+'{:.2f}'.format(DataTable[c][r])+'</td>'
							except:
								strTable += '<td></td>'
					strTable += '</tr>'
		jsonseries = json.dumps(series)
		json_series_colors = json.dumps(series_colors)
		
	else:
		form = DifferenceForm()
		form.fields['Minuend'].choices = ID_CHOICES
		form.fields['Subtrahend'].choices = ID_CHOICES
		jsonseries = ''
		xAxis_categories = ''
		json_series_colors = ''
		
	ts = datatable.calculate_start_time(datetime.datetime.now(),0,'minutes')
	return render_to_response('env/difference.html',
		{'form':form, 'PostPath':PostPath, 'ProxyPath':ProxyPath, 'series_colors':json_series_colors, 'xAxis_categories':xAxis_categories, 'series':jsonseries, 'strTable':strTable},
		context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
@login_required()	
def load_initial_data(request):
	'''*SuperUser* Load the system with useful settings.
	
	Can be executed repeatedly to load deleted or missing items.
	'''
	try:
		import django.contrib.auth
		SuperUser = django.contrib.auth.models.User.objects.get(id=1)
		#add default Groups to django auth system
		#link to super user (assumes that a super user was created)
		lstGroup = ['all','guest','restricted']
		for g in lstGroup:
			if not django.contrib.auth.models.Group.objects.filter(name=g):
				grp = django.contrib.auth.models.Group(name=g)
				grp.save()
				grp.user_set.add(SuperUser)
				messages.info(request,'--'+g)
		messages.info(request,'Loaded Groups')
		
		#add controller
		controller = ('LocalController','localhost','11111','/controller')
		if not Controller.objects.filter(Name = controller[0]):
			name,host,port,path = controller
			c = Controller(Name=name,Host=host,Port=port,Path=path)
			c.save()
			messages.info(request,'--'+name)
		messages.info(request,'Loaded Controller')
		
		#add test DataTypes
		datatype = [('Other',0,'','0',100,0,0),
				('Temperature',0,'F','-50',100,0,0),
				('Humidity',0,'%','-10',100,0,0),
				('Light Level',0,'','1',100,-50,0),
				('PIR Motion',0,'','-1',1,-1,0),
				('Thermostat Setpoint',0,'F','-50',100,0,0),
				('Thermostat Status',0,'','-1',1,-1,0),
				('Wind Speed',0,'','-1',50,0,0),
				('Barometric Pressure',2,'inHg','20',33,27,0),
				('Samewire Voltage',2,'V','-1',14,10,0),
				('AC Voltage',2,'V','-1',140,100,0),
				('AC Power',0,'W','-1',1000,0,0)]
		for Type,DecimalPlaces,Units,DefaultValue,PlotYmax,PlotYmin,Boolean in datatype:
			if not DataType.objects.filter(Type=Type):
				DataType(Type=Type,DecimalPlaces=DecimalPlaces,Units=Units,DefaultValue=DefaultValue,PlotYmax=PlotYmax,PlotYmin=PlotYmin,Boolean=Boolean).save()
				messages.info(request,'--'+Type)
		messages.info(request,'Loaded DataTypes')
		
		#add test data ID's			
		data = [(1,'Other','test 1','Black',0,'Minute',1,0,''),
				(2,'Other','test 2','Black',0,'Minute',1,0,''),
				(3,'Other','test 3','Black',0,'Minute',1,0,''),
				(4,'Other','test 4','Black',0,'Minute',1,0,''),
				(5,'Other','test 5','Black',0,'Minute',1,0,''),
				(6,'Other','test 6','Black',0,'Minute',1,0,''),
				(7,'Other','test 7','Black',0,'Minute',1,0,''),
				(8,'Other','test 8','Black',0,'Minute',1,0,''),
				(9,'Other','test 9','Black',0,'Minute',1,0,''),
				(10,'Other','test 10','Black',0,'Minute',1,0,'')]
		for ID,Type,Name,Color,Active,Timebase,Period,Copy,Notes in data:
			if not Data.objects.filter(ID=ID):
				Type_id = DataType.objects.get(Type=Type).id
				Data(ID=ID,Type_id=Type_id,Name=Name,Color=Color,Active=Active,Timebase=Timebase,Period=Period,Copy=Copy,Notes=Notes).save()
				messages.info(request,'--'+Name)
		messages.info(request,'Loaded Data ID\'s')
		
		messages.info(request,'Initial data loading complete.')
	except:
		logging.exception('')
		messages.error(request,'Initial data loading error: '+str(sys.exc_type)+'; '+str(sys.exc_value))
	finally:
		return render_to_response('env/show_messages.html',
			{},
			context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
@login_required()
def load_test_cases(request):
	'''*SuperUser* Load the system with settings useful for testing and experimenting. See full doc.
	
	This expects that initial data was loaded.
	It will overwrite DataID's 1-5 (in the data table).
	Can be executed repeatedly to load missing or deleted items.
	This is a good example of how to use the htmltable app.
	It provides data useful for development testing.
	'''
	try:
#		import pdb;pdb.set_trace()
		import django.contrib.auth
		#Load HTMLTable
		from htmltable.models import  HTMLTable as HTMLTable
		from htmltable.models import  Sensor as HTMLTableSensor
		newhtmltable_sensors = [(1,'LocalController','testvalue','http://localhost:8000/'+djangosite.settings.HTTP_PROXY_PATH+'/env/testvalue',('1',1,0,0,'?')),
						(2,'LocalController','randomvalue','http://localhost:8000/'+djangosite.settings.HTTP_PROXY_PATH+'/env/randomvalue',('2',1,0,0,'?')),
						(3,'LocalController','sawtoothvalue','http://localhost:8000/'+djangosite.settings.HTTP_PROXY_PATH+'/env/sawtoothvalue',('3',1,0,0,'?')),
						(4,'LocalController','logvalue','http://localhost:8000/'+djangosite.settings.HTTP_PROXY_PATH+'/env/logvalue',('4',1,0,0,'?')),
						(5,'LocalController','sinevalue','http://localhost:8000/'+djangosite.settings.HTTP_PROXY_PATH+'/env/sinevalue',('5',1,0,0,'?'))]
		for tableid,controller,tablename,tableurl,sensor in newhtmltable_sensors:
			if not HTMLTable.objects.filter(id=tableid):
				controller_id = Controller.objects.get(Name=controller).id
				t = HTMLTable(id=tableid,Controller_id=controller_id,Name=tablename,URL=tableurl)
				t.save()
				s = HTMLTableSensor(DataID=Data.objects.get(ID=sensor[0]),HTMLTable=t,TableIndex=sensor[1],Row=sensor[2],Column=sensor[3],ScaleFactors=sensor[4])
				s.save()
				d = Data.objects.get(ID=sensor[0])
				d.Active = True
				grp = django.contrib.auth.models.Group.objects.get(name='Restricted')
				d.Group.add(grp)
				d.save()
		messages.info(request,'Loaded testcase htmltables and sensor')
		
	except:
		logging.exception('')
		messages.error(request,'Load test cases error: '+str(sys.exc_type)+'; '+str(sys.exc_value))
	finally:
		return render_to_response('env/show_messages.html',
			{},
			context_instance=RequestContext(request))
	

@login_required()
def id_plot(request,dataid='1',timebase='minutes',points='60',stoptime=''):
	'''Uses Matplotlib to plot data from a DataID provided as an argument.
		
		Provide four arguments in this order:
			dataid
			timebase ('seconds','minutes','hours','days')
			points
			stoptime in the format %Y-%m-%d_%H-%M-%S (hour in 24hr format)
				if stoptime is left blank, then the current time is used
		example:
			/env/plot_id/1/minutes/60/
			/env/plot_id/1/minutes/1440/2000-1-1_00-00-00
	'''
#	import pdb;pdb.set_trace()
	try:
		dataid = int(dataid.replace('/',''))
		if timebase in ('seconds','minutes','hours','days'):
			timebase = str(timebase.replace('/',''))
		else:
			timebase = 'minutes'
		points = int(points.replace('/','')) #if not stoptime is given, a '/' is passed to the points variable
		datatable = discengines.datatable
		g=[]
		[g.append(str(x)) for x in request.user.groups.all()]
		ImageName = str(datetime.datetime.now()).replace(':','-').replace(' ','_').replace('.','-')
	
		o = Data.objects.all().filter(Group__name__in=g).distinct().get(ID=dataid)
		if o:
			if len(stoptime) > 4:
				try:
					ts = datetime.datetime.fromtimestamp(time.mktime(time.strptime(stoptime,'%Y-%m-%d_%H-%M-%S')))
				except:
					ts = datatable.calculate_start_time(datetime.datetime.now(),0,timebase)
					messages.warning(request,'INVALID TIME STAMP (use format %Y-%m-%d_%H-%M-%S), *USING CURRENT TIME*')
			else:
				ts = datatable.calculate_start_time(datetime.datetime.now(),int(o.Period),timebase)
			#Justify time to the next hour
			#ts = ts + datetime.timedelta(minutes=(59-ts.minute),seconds=59-ts.second,microseconds=1000000-ts.microsecond)

			lock = Lock()
			with lock:
				sts = datatable.calculate_start_time(ts,points,timebase)
				if timebase == 'seconds':
					listTS = [ sts + datetime.timedelta(seconds=x) for x in range(0,points) ]
				if timebase == 'minutes':
					listTS = [ sts + datetime.timedelta(minutes=x) for x in range(0,points) ]
				if timebase == 'hours':
					listTS = [ sts + datetime.timedelta(hours=x) for x in range(0,points) ]
				if timebase == 'days':
					listTS = [ sts + datetime.timedelta(days=x) for x in range(0,points) ]
				listTS = np.array(listTS)
				majorLocator = MultipleLocator(5)
				majorFormatter = FormatStrFormatter('%d')
				minorLocator = MultipleLocator(1)
				#ax.yaxis.set_major_locator(majorLocator)
				#ax.yaxis.set_major_formatter(majorFormatter)
				#ax.yaxis.set_minor_locator(minorLocator)			
				
				if timebase == 'seconds':
					majorFormatter = matplotlib.dates.DateFormatter('%H:%M:%S')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.SecondLocator(interval=30)
				if timebase == 'minutes':
					majorFormatter = matplotlib.dates.DateFormatter('%m/%d %H:%M')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.MinuteLocator(interval=15)
				if timebase == 'hours':
					majorFormatter = matplotlib.dates.DateFormatter('%m/%d %H:%M')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.HourLocator(interval=1)
				if timebase == 'days':
					majorFormatter = matplotlib.dates.DateFormatter('%m/%d')#'%Y-%m-%d %H:%M:%S'
					minorLocator = matplotlib.dates.DayLocator(interval=1)
				
				fig = plt.figure()
				d = dataid
					#import pdb;pdb.set_trace()
				try:
					y = datatable.get_data_records_before_time(d,ts,points,timebase)
					y = np.array(y)
				except:
					y = np.array(range(points))
				if len(y) == 0:
					y = np.array(range(points))
				if not discengines.USE_SQLITE_QUEUED_MEMORY_MANAGER:
					datatable.db_close(d)
				T = DataType.objects.get(Type = o.Type)
#				if T.Boolean and timebase != o.Timebase:
#					 m = {'seconds':60,'minutes':60,'hours':60,'days':24}[timebase]
#					 y *= m
			
				i = 0
				NumPlot = 111
				ax = fig.add_subplot(NumPlot)
#				ax.set_ylim(float(T.PlotYmin),float(T.PlotYmax))	
				ax.xaxis.set_minor_locator(minorLocator)
				ax.xaxis.set_major_formatter(majorFormatter)
				fig.autofmt_xdate()
				if T.Boolean:
					ax.fill_between(listTS,0,y,facecolor=str(o.Color))
				else:
					try:
						ax.plot(listTS,y,color=str(o.Color),label=str(o.Name))
					except:
						logger.exception('')

				fig.set_size_inches(12,9.6)
				#fig.savefig('../media/plots/'+ImageName+'.png',dbi=200)
				fig.savefig(djangosite.settings.APP_BASE_PATH+'/media/plots/'+ImageName+'.png',dbi=200)
				time.sleep(0.2)
	except:
		logger.exception('')
		messages.error(request,'error creating plot')

	MediaPath = djangosite.settings.MEDIA_URL
	return render_to_response('env/id_plot.html',
		{'MediaPath':MediaPath, 'ImageName':ImageName},
		context_instance=RequestContext(request))