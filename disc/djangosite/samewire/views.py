import logging
logger = logging.getLogger(__name__)
import datetime
import re
import urllib
import httplib
import sys
import time
from django.http import HttpResponse
from django.template import Context, loader

from django import forms
from django.shortcuts import render_to_response
from django.template import Context, loader, RequestContext, Template
from django.forms.fields import DateField, ChoiceField, MultipleChoiceField
from django.forms.widgets import RadioSelect, CheckboxSelectMultiple
#from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.decorators import login_required, user_passes_test
import django.contrib.auth
from django.contrib import messages

from samewire.models import *
from env.models import *
from djangosite.settings import HTTP_PROXY_PATH, APP_BASE_PATH
from discengines import datatable

def all_sensors(request):
	'''An HTML Table of parameters for the Controller.'''
	TableIndex = ['this_table','samewire']
	qsSamewire = Sensor.objects.all()
	t = loader.get_template('samewire/sensors.html')
	c = Context({'TableIndex':TableIndex,'qsSamewire':qsSamewire})
	return HttpResponse(t.render(c))

def active_sensors(request):
	'''An HTML Table of parameters for the Controller.'''
	TableIndex = ['this_table','samewire']
	#exclude inactive sensors
	qsSamewire = Sensor.objects.exclude(DataID__Active=False)
	t = loader.get_template('samewire/sensors.html')
	c = Context({'TableIndex':TableIndex,'qsSamewire':qsSamewire})
	return HttpResponse(t.render(c))

def data_id_owners(self,ID):
	return Sensor.objects.filter(DataID=ID)


'''
Create Env Items
	Data Types (Temperature, Humidity, Light, PIR Motion)
	Group (Create or choose from a list)
	Controller (Create or choose from a list)
	Samewire
		Master (Create or choose from a list)
			Link Controller
		Serf Address (Create)
			Loop for Defined Serf (Temperature, Hummidity, Light, Motion)
				Data
					Location Name  (same name used for each)
					Link Type (Temp, Hum, Light, Motion)
					Link Group (same for all)
					Color (choose from a list with a default)
						Temp = Green
						Hum = Blue
						Light = Yellow
						Motion = Black
					Activate (1)
					Timebase (Minute) (choose from a list with a default)
					Period (1)
					Copy (-10)
					Purge (Never)
				Sensor
					Command
						Temp (TV)
						Hum (PV:15)
						Light (PV:16)
						Motion (PV:22)
						
Set
	PID:
	PRC:0
	PRE:SET0
	PRE:SET1
	PRE:SET2
	PRE:SET3
	PCS:R
	
Test
	TV
	PV:15
	PV:16
	PV:22
'''
class Form_load_serf(forms.Form):
	Group = forms.MultipleChoiceField(required=True, widget=CheckboxSelectMultiple)
	Controller = forms.ChoiceField(required=True, widget=RadioSelect)
	Master = forms.ChoiceField(required=True, widget=RadioSelect)
	Serf_Address = forms.CharField(max_length=5,required=True)
	Data_Name = forms.CharField(max_length=50,required=True)
	Color = forms.ChoiceField(required=True, choices=BASIC_COLOR_CHOICES)

@user_passes_test(lambda u: u.is_superuser)
@login_required()
def load_serf(request):
	'''*SuperUser* Load the database configuration and program firmware parameters for a serf to measure temperature, humidity, light and PIR motion.'''
	g=[]
	controllers=[]
	masters=[]
	try:
		for x in request.user.groups.all():
			o = Group.objects.get(name=x)
			g.append((o.id,o.name))
		for x in Controller.objects.all():
			o = Controller.objects.get(Name=x)
			controllers.append((o.id,o.Name))
		for x in Master.objects.all():
			o = Master.objects.get(Name=x)
			masters.append((o.id,o.Name))
	except:
		messages.error(request,'Application error loading data.')
	
	if request.method == 'POST':
		form = Form_load_serf(request.POST)
		form.fields['Group'].choices = tuple(g)
		form.fields['Controller'].choices = tuple(controllers)
		form.fields['Master'].choices = tuple(masters)
		if form.is_valid():
#			import pdb;pdb.set_trace()
			fgroup = form.cleaned_data['Group']
			fcontroller = form.cleaned_data['Controller']
			fmaster = form.cleaned_data['Master']
			faddress = form.cleaned_data['Serf_Address']
			fname = form.cleaned_data['Data_Name']
			color = form.cleaned_data['Color']
			
			#Create Serf
			serf = Serf(Master=Master.objects.get(id=fmaster),Address=faddress)
			serf.save()
			
			#Create DataID and Sensor
#			listColor = ['Green','Blue','Yellow','Black']
			listType = ['Temperature','Humidity','Light Level','PIR Motion']
			listCommand = ['TV','PV:15','PV:16','PV:22']
			listScaleFactors = ['','','round(-10*log(-1*?)+110,2)','']
			for i in range(len(listType)):
				d = Data(Type=DataType.objects.get(Type=listType[i]), Name=fname, Color=color, Active=1, Timebase= 'minutes', Period='1', Copy='1440')
				d.save()
				for f in fgroup:
					group=Group.objects.get(id=f)
					d.Group.add(group)
				sensor = Sensor(Serf=serf,DataID=d,Command=listCommand[i],ScaleFactors=listScaleFactors[i])
				sensor.save()
			messages.success(request,'Serf and Data ID\'s and Sensor created successfully.')
	else:
		form = Form_load_serf()
		form.fields['Group'].choices = tuple(g)
		form.fields['Controller'].choices = tuple(controllers)
		form.fields['Master'].choices = tuple(masters)
		messages.info(request,'Fill in form and click load to create a Serf and Data ID\'s and Sensors (Temperature, Humidity, Light Level, PIR Motion)')
	
	ts = datetime.datetime.now()
	PostPath = '/'+HTTP_PROXY_PATH+'/samewire/load_serf'
	return render_to_response('samewire/load_serf.html',
		{'form':form,'PostPath':PostPath},
		context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
@login_required()
def load_serf_power_monitor_db_configuration(request):
	'''*SuperUser* Load the database configuration for a serf to measure voltage and power on 5 channels.'''
	g=[]
	controllers=[]
	masters=[]
	try:
		for x in request.user.groups.all():
			o = Group.objects.get(name=x)
			g.append((o.id,o.name))
		for x in Controller.objects.all():
			o = Controller.objects.get(Name=x)
			controllers.append((o.id,o.Name))
		for x in Master.objects.all():
			o = Master.objects.get(Name=x)
			masters.append((o.id,o.Name))
	except:
		messages.error(request,'Application error loading data.')
	if request.method == 'POST':
		form = Form_load_serf(request.POST)
		form.fields['Group'].choices = tuple(g)
		form.fields['Controller'].choices = tuple(controllers)
		form.fields['Master'].choices = tuple(masters)
		if form.is_valid():
			#import pdb;pdb.set_trace()
			fgroup = form.cleaned_data['Group']
			fcontroller = form.cleaned_data['Controller']
			fmaster = form.cleaned_data['Master']
			faddress = form.cleaned_data['Serf_Address']
			fname = form.cleaned_data['Data_Name']
			color = form.cleaned_data['Color']
			try:
				serf = Serf.objects.get(Master=Master.objects.get(id=fmaster),Address=faddress)
				messages.warning(request,'A Serf already exists with this address.')
			except:
				#Create Serf
				serf = Serf(Master=Master.objects.get(id=fmaster),Address=faddress)
				serf.save()
				messages.success(request,'Serf created.')
			
			#Create DataID and Sensor
#			listColor = ['Green','Blue','Yellow','Black']
			listType = ['Voltage','Power','Power','Power','Power','Power']
			listCommand = ['PV:10','CW:13','CW:14','CW:15','CW:16','CW:17']
			for i in range(len(listType)):
				sname = fname+listCommand[i][-1:]
				try:
					d = Data.objects.get(Type=DataType.objects.get(Type=listType[i]), Name=sname, Color=color, Timebase= 'minutes', Period='1', Copy='-60',group=Group.objects.get(id=fgroup))
				except:
					d = Data(Type=DataType.objects.get(Type=listType[i]), Name=sname, Color=color, Active=1, Timebase= 'minutes', Period='1', Copy='-60')
					d.save()
				try:
					sensor = Sensor.objects.get(Serf=serf,DataID=d,Command=listCommand[i])
				except:
					for f in fgroup:
						group=Group.objects.get(id=f)
						d.Group.add(group)
					sensor = Sensor(Serf=serf,DataID=d,Command=listCommand[i])
					sensor.save()
				else:
					messages.warning(request,'This configuration already exists: ('+listType[i]+','+listCommand[i]+').')
			messages.success(request,'Serf and Data ID\'s and Sensor created successfully.')
	else:
		form = Form_load_serf()
		form.fields['Group'].choices = tuple(g)
		form.fields['Controller'].choices = tuple(controllers)
		form.fields['Master'].choices = tuple(masters)
		messages.info(request,'Fill in form and click load to create a Serf and Data ID\'s and Sensors (one voltage and five power sensors)')

	ts = datetime.datetime.now()
	PostPath = '/'+HTTP_PROXY_PATH+'/samewire/load_serf_power_monitor_db_configuration'
	return render_to_response('samewire/load_serf.html',
		{'form':form,'PostPath':PostPath},
		context_instance=RequestContext(request))


@user_passes_test(lambda u: u.is_superuser)
@login_required()
def load_serf_power_monitor_firmware_configuration(request):
	'''*SuperUser* Program firmware parameters for a serf to measure voltage and power on 5 channels.'''
	g=[]
	controllers=[]
	masters=[]
	try:
		for x in request.user.groups.all():
			o = Group.objects.get(name=x)
			g.append((o.id,o.name))
		for x in Controller.objects.all():
			o = Controller.objects.get(Name=x)
			controllers.append((o.id,o.Name))
		for x in Master.objects.all():
			o = Master.objects.get(Name=x)
			masters.append((o.id,o.Name))
	except:
		messages.error(request,'Application error loading data.')
	if request.method == 'POST':
		form = Form_load_serf(request.POST)
		form.fields['Group'].choices = tuple(g)
		form.fields['Controller'].choices = tuple(controllers)
		form.fields['Master'].choices = tuple(masters)
		if form.is_valid():
			#import pdb;pdb.set_trace()
			fgroup = form.cleaned_data['Group']
			fcontroller = form.cleaned_data['Controller']
			fmaster = form.cleaned_data['Master']
			faddress = form.cleaned_data['Serf_Address']
			fname = form.cleaned_data['Data_Name']
			color = form.cleaned_data['Color']

			#program sensors for serf
			controller = Master.objects.get(id=fmaster).Controller
			Chost = Controller.objects.get(Name=controller).Host
			Cport = Controller.objects.get(Name=controller).Port
			Cpath = Controller.objects.get(Name=controller).Path
			
			#Verify Communication
			FV = http_post_cmdresp(serf.Address,'FV',Chost,Cport,Cpath)
			if len(FV) >= 4 and FV[2:4].isdigit():
				#stop serf
				resp = http_post_cmdresp(serf.Address,'PCS:S',Chost,Cport,Cpath)
				time.sleep(3)
				resp = http_post_cmdresp(serf.Address,'FV',Chost,Cport,Cpath)
				if resp.find('STOP') > -1:
					#disable redundant communication
					resp = http_post_cmdresp(serf.Address,'PRC:0',Chost,Cport,Cpath)
					time.sleep(3)
					lstCmd =  ['PPF:10,4','CPP:100520041001','PPP:10,30','PA1:0,3','PM1:0,0.0381','PO1:0,-0.04']
					lstCmd += ['PPF:13,4','CPP:130520041100','PPP:13,30','PA1:3,3','PM1:3,0.0049','PO1:3,-0.08']
					lstCmd += ['PPF:14,4','CPP:140520041100','PPP:14,30','PA1:4,3','PM1:4,0.0049','PO1:4,-0.08']
					lstCmd += ['PPF:15,4','CPP:150520041100','PPP:15,30','PA1:5,3','PM1:5,0.0049','PO1:5,-0.08']
					lstCmd += ['PPF:16,4','CPP:160520041100','PPP:16,30','PA1:6,3','PM1:6,0.0049','PO1:6,-0.08']
					lstCmd += ['PPF:17,4','CPP:170520041100','PPP:17,30','PA1:7,3','PM1:7,0.0049','PO1:7,-0.08']
					for cmd in lstCmd:
						try:
							resp = http_post_cmdresp(serf.Address,cmd,Chost,Cport,Cpath)
#							print serf.Address,cmd,resp
#							if resp.find('OK') == -1:
#								messages.info(request,'Check response for cmd: '+cmd+' ,resp: '+resp)
							for i in range(3):
								time.sleep(3)
								FV = http_post_cmdresp(serf.Address,'FV',Chost,Cport,Cpath)
								#print serf.Address,FV
								if len(FV) >= 4 and FV[2:4].isdigit(): # a Firmware Version example is: DD15
									break
						except:
							messages.error(request,'Error sending cmd '+cmd)
					
					#run serf
					resp = http_post_cmdresp(serf.Address,'PCS:R',Chost,Cport,Cpath)
				else:
					messages.warning(request,'Unable to put serf in STOP mode.')
			else:
				messages.error(request,'Error communicating with Serf.')
	else:
		form = Form_load_serf()
		form.fields['Group'].choices = tuple(g)
		form.fields['Controller'].choices = tuple(controllers)
		form.fields['Master'].choices = tuple(masters)
		messages.info(request,'Fill in form and click load to program the serf sensors (one voltage and five power sensors)')

	PostPath = '/'+HTTP_PROXY_PATH+'/samewire/load_serf_power_monitor_firmware_configuration'
	return render_to_response('samewire/load_serf.html',
		{'form':form,'PostPath':PostPath},
		context_instance=RequestContext(request))


class calibrate_sensorForm(forms.Form):
	Source_Of_Data = forms.ChoiceField(required=True, widget=RadioSelect, choices=(('Datetime Lookup','Datetime Lookup'),('Point Data','Point Data')))
	Point_1_Datetime = forms.CharField(max_length=50, required=True, initial=str(datetime.datetime.now())[:-9]+'00')
	Point_2_Datetime = forms.CharField(max_length=50, required=True, initial=str(datetime.datetime.now())[:-9]+'00')
	Calibration_Source = forms.ChoiceField(required=True, widget=forms.Select)
	Source_Point_High = forms.CharField(max_length=20, required=True, initial='1')
	Source_Point_Low = forms.CharField(max_length=20, required=True, initial='1')
	Calibration_Target = forms.ChoiceField(required=True, widget=forms.Select)
	Target_Point_High = forms.CharField(max_length=20, required=True, initial='1')
	Target_Point_Low = forms.CharField(max_length=20, required=True, initial='1')
	Old_Multiplier = forms.CharField(max_length=10, required=True, initial='1')
	Old_Offset = forms.CharField(max_length=10, required=True, initial='0')
	New_Multiplier = forms.CharField(max_length=10, required=True, initial='1')
	New_Offset = forms.CharField(max_length=10, required=True, initial='0')
	Port = forms.CharField(max_length=1, required=True, initial='0')
	Pin = forms.CharField(max_length=1, required=True, initial='0')
	Program_new_values = forms.BooleanField(required=False)

@user_passes_test(lambda u: u.is_superuser)
@login_required()
def calibrate_sensor(request):
	'''*SuperUser* Calculate the multiplier and offset and program them to a serf for a sensor.'''
	messages.info(request,'Fill in form and click Calculate to generate the calibration constants (a line equation with multiplier and offset)')
	DataIDs=[]
	try:
		for o in Data.objects.all():
			DataIDs.append((o.ID,str(o.ID)+'_'+str(o.Type)+'_'+str(o.Name)))
	except:
		messages.error(request,'Failed to create list of DataIDs')
#	import pdb;pdb.set_trace()
	if request.method == 'POST':
		form = calibrate_sensorForm(request.POST)
		form.fields['Calibration_Target'].choices = tuple(DataIDs)
		form.fields['Calibration_Source'].choices = tuple(DataIDs)
		if form.is_valid():
			form2 = {}
			for k,v in form.cleaned_data.iteritems():
				form2[k] = v
			
			Calibration_Target = form.cleaned_data['Calibration_Target']
			Calibration_Source = form.cleaned_data['Calibration_Source']
			Point_1_Datetime = form.cleaned_data['Point_1_Datetime']
			Point_2_Datetime = form.cleaned_data['Point_2_Datetime']
			Source_Of_Data = form.cleaned_data['Source_Of_Data']
#			import pdb;pdb.set_trace()
			#Reference the Serf/Sensor from the DataID
			sensor = Sensor.objects.get(DataID=Calibration_Target)
			serf = Serf.objects.get(id=sensor.Serf.id)
			controller = Master.objects.get(Name=Serf.objects.get(id=sensor.Serf.id).Master).Controller
			Chost = Controller.objects.get(Name=controller).Host
			Cport = Controller.objects.get(Name=controller).Port
			Cpath = Controller.objects.get(Name=controller).Path
			
			if form.cleaned_data['Program_new_values'] == False:
				try:
#					import pdb;pdb.set_trace()
					#get the present multiplier and offset from the target Serf/Sensor
					#get PortPin
					PortPin = sensor.Command
					Port = '0'
					Pin = '0'
					if PortPin[0:-2] == 'PV:':
						Port = PortPin[3:-1]
						Pin = PortPin[4:]
					if PortPin[0:-2] == 'PC:':
						Port = PortPin[3:-1]
						Pin = PortPin[4:]
					if PortPin == 'TV':
						Multiplier = http_post_cmdresp(serf.Address,'TM',Chost,Cport,Cpath)
						Multiplier1 = float(Multiplier)
						Offset = http_post_cmdresp(serf.Address,'TO',Chost,Cport,Cpath)
						Offset1 = float(Offset)
					else:
						if Port != '0' and Pin != '0':
							Multiplier = http_post_cmdresp(serf.Address,'PM:'+Port+Pin,Chost,Cport,Cpath)
							Multiplier1 = float(Multiplier)
						if Port != '0' and Pin != '0':
							Offset = http_post_cmdresp(serf.Address,'PO:'+Port+Pin,Chost,Cport,Cpath)
							Offset1 = float(Offset)
					
					if Source_Of_Data == 'Datetime Lookup':
						timebase = 'Minute'
#						import pdb;pdb.set_trace()
#						print str(dictTable[timebase].GetRecord(Calibration_Source,Point_1_Datetime,3))
						#Calculate new Multiplier and Offset
						#Vhs = 2 #Value High from Reference Sensor
						Vhs = float(datatable.get_data_record(Calibration_Source,Point_1_Datetime,timebase,3))
						#Vls = 1 #Value Low from Reference Sensor
						Vls = float(datatable.get_data_record(Calibration_Source,Point_2_Datetime,timebase,3))
						#Vht = 2 #Value High from the Sensor to be Calibrated
						Vht = float(datatable.get_data_record(Calibration_Target,Point_1_Datetime,timebase,3))
						#Vlt = 1 #Value Low from the Sensor to be Calibrated
						Vlt = float(datatable.get_data_record(Calibration_Target,Point_2_Datetime,timebase,3))
					
						#swap high and low points if necessary
						if Vhs < Vls and Vht < Vlt:
							t = Vls
							Vls = Vhs
							Vhs = t
							t = Vlt
							Vlt = Vht
							Vht = t
						
						form2['Source_Point_High'] = str(Vhs)
						form2['Source_Point_Low'] = str(Vls)
						form2['Target_Point_High'] = str(Vht)
						form2['Target_Point_Low'] = str(Vlt)
						
					if Source_Of_Data == 'Point Data':
						Vhs = float(form.cleaned_data['Source_Point_High'])
						Vls = float(form.cleaned_data['Source_Point_Low'])
						Vht = float(form.cleaned_data['Target_Point_High'])
						Vlt = float(form.cleaned_data['Target_Point_Low'])
					
					CalculateMessage = ''
					OffsetOnly = False
					if Point_1_Datetime == Point_2_Datetime:
						OffsetOnly = True					
					else:
						if Vhs < Vls and Vht > Vlt:
							CalculateMessage = 'Invalid Point Data: Reference high is less than the low, while the Calibrate high is more than the low'
						if Vhs > Vls and Vht < Vlt:
							CalculateMessage = 'Invalid Point Data: Reference high is more than the low, while the Calibrate high is less than the low'
						if Vht == Vlt:
							CalculateMessage = 'Divide by zero error: the Calibrate high and low data is equal'
					
					if CalculateMessage == '':
						if OffsetOnly:
							Multiplier2 = Multiplier1
							Offset2 = Offset1 + (Vhs - Vht)
						else:
							#Calculate Multiplier2 (the new, calibrated multiplier) for the Sensor to be Calibrated
							#Multiplier1 is the multiplier that was used for the source data from the sensor to be calibrated
							Multiplier2 = Multiplier1 * ((Vhs - Vls)/(Vht - Vlt))
							#Calculate Offset2 (the new, calibrated offset) for the Sensor to be Calibrated
							#Offset1 is the offset that was used for the source data from the sensor to be calibrated
							Offset2 = Vhs - Multiplier2/Multiplier1*(Vht - Offset1)
						
						#determine number of decimal places by analyzing multiplier and offset from serf
						md = 0
						if Multiplier.find('.') > -1:
							md = len(Multiplier[Multiplier.find('.')+1:])
						od = 0
						if Offset.find('.') > -1:
							od = len(Offset[Offset.find('.')+1:])

						from decimal import Decimal
						Multiplier2 = Decimal(str(Multiplier2)).quantize(Decimal(10) ** (-1*md))
						Offset2 = Decimal(str(Offset2)).quantize(Decimal(10) ** (-1*od))

						form2['Port'] = str(Port)
						form2['Pin'] = str(Pin)
						form2['Old_Multiplier'] = str(Multiplier)
						form2['Old_Offset'] = str(Offset)
						form2['New_Multiplier'] = str(Multiplier2)
						form2['New_Offset'] = str(Offset2)
						#First check if the calculated Multiplier and Offset is acceptable
						messages.success(request,'Calculated new calibration constants for serf address '+ str(serf.Address) + '. Click the check box to program the Multiplier and Offset to the Serf. '+'Using Controller: '+Chost+':'+Cport+Cpath+'/samewire')
					else:
						messages.warning(request,CalculateMessage)
				except:
					messages.error(request,'Application error')
					logger.exception('')
			else:
				try:
					#Save Multiplier and Offset to target and verify
					resp = str(http_post_cmdresp(serf.Address,'PCS:S',Chost,Cport,Cpath))
					time.sleep(3)
					if form.cleaned_data['Port'] == '0' and form.cleaned_data['Port'] == '0':
						resp += '; '+str(http_post_cmdresp(serf.Address,'PTM:'+str(form.cleaned_data['New_Multiplier']),Chost,Cport,Cpath))
						time.sleep(3)
						resp += '; '+str(http_post_cmdresp(serf.Address,'PTO:'+str(form.cleaned_data['New_Offset']),Chost,Cport,Cpath))
					else:
						resp += '; '+str(http_post_cmdresp(serf.Address,'PM'+str(form.cleaned_data['Port'])+':'+str(form.cleaned_data['Pin'])+','+str(form.cleaned_data['New_Multiplier']),Chost,Cport,Cpath))
						time.sleep(3)
						resp += '; '+str(http_post_cmdresp(serf.Address,'PO'+str(form.cleaned_data['Port'])+':'+str(form.cleaned_data['Pin'])+','+str(form.cleaned_data['New_Offset']),Chost,Cport,Cpath))
					time.sleep(3)
					resp += '; '+str(http_post_cmdresp(serf.Address,'PCS:R',Chost,Cport,Cpath))
					time.sleep(3)
					if form.cleaned_data['Port'] == '0' and form.cleaned_data['Port'] == '0':
						verifyMultiplier1 = float(http_post_cmdresp(serf.Address,'TM',Chost,Cport,Cpath))
						verifyOffset1 = float(http_post_cmdresp(serf.Address,'TO',Chost,Cport,Cpath))
					else:
						verifyMultiplier1 = float(http_post_cmdresp(serf.Address,'PM:'+str(form.cleaned_data['Port'])+str(form.cleaned_data['Pin']),Chost,Cport,Cpath))
						verifyOffset1 = float(http_post_cmdresp(serf.Address,'PO:'+str(form.cleaned_data['Port'])+str(form.cleaned_data['Pin']),Chost,Cport,Cpath))
					if verifyMultiplier1 == float(form.cleaned_data['New_Multiplier']) and verifyOffset1 == float(form.cleaned_data['New_Offset']):
						message.success(request,'Values programmed to the Serf Address: '+str(serf.Address))
					else:
						messages.warning(request,'Failed to program values to the Serf address '+ str(serf.Address) + '. Responses for Muliplier,Offset: '+str(verifyMultiplier1)+', '+str(verifyOffset1))
				except:
					messages.error(request,'Application error')
					logger.exception('')

			form = calibrate_sensorForm(form2)
		else:
			messages.warning(request,'Form data is not valid. '+str(form.errors))
	else:
		form = calibrate_sensorForm()

	form.fields['Calibration_Target'].choices = tuple(DataIDs)
	form.fields['Calibration_Source'].choices = tuple(DataIDs)

	PostPath = '/'+HTTP_PROXY_PATH+'/samewire/calibrate_sensor'
	return render_to_response('samewire/calibrate_sensor.html',
		{'form':form,'PostPath':PostPath},
		context_instance=RequestContext(request))


class backup_serfForm(forms.Form):
	Choose_Serf = forms.ChoiceField(required=True, widget=forms.Select)
#	Backup_All_Serfs = forms.BooleanField(required=False)

@user_passes_test(lambda u: u.is_superuser)
@login_required()
def backup_serf(request):
	'''*SuperUser* Read the firmware configuration and parameters of a serf and store them to a database.'''
	messages.info(request,'Select the Serf to Backup')
	Serfs=[]
	try:
		for o in Serf.objects.all():
			Serfs.append((o.id,str(o.Master)+'_'+str(o.Address)))
	except:
		messages.warning(request,'Failed to create list of Serfs.')
#	import pdb;pdb.set_trace()
	if request.method == 'POST':
		form = backup_serfForm(request.POST)
		form.fields['Choose_Serf'].choices = tuple(Serfs)
		if form.is_valid():
			form2 = {}
			for k,v in form.cleaned_data.iteritems():
				form2[k] = v
			
#			Backup_All_Serfs = form.cleaned_data['Backup_All_Serfs']
			Choose_Serf = form.cleaned_data['Choose_Serf']
			serf = Serf.objects.get(id=Choose_Serf)
			controller = Master.objects.get(Name=Serf.objects.get(id=serf.id).Master).Controller
			Chost = Controller.objects.get(Name=controller).Host
			Cport = Controller.objects.get(Name=controller).Port
			Cpath = Controller.objects.get(Name=controller).Path			
			
			#Verify Communication
			FV = http_post_cmdresp(serf.Address,'FV',Chost,Cport,Cpath)
			if len(FV) == 4:
				
				#Pin Function
				PF = http_post_cmdresp(serf.Address,'PF',Chost,Cport,Cpath)
				
				#Create a backup and get the Creation date to store with the detail records
				B = Backup(Serf=serf,FirmwareVersion=FV,PinFunction=PF)
				B.save()
				
				#Internal Temp
				lstCmd = ['TM','TO','TP','TA']
				for cmd in lstCmd:
					try:
						resp = http_post_cmdresp(serf.Address,cmd,Chost,Cport,Cpath)
						BD = BackupDetail(Backup=B,CreationDate=B.CreationDate,Parameter=cmd,Value=resp)
						BD.save()
					except:
						messages.warning(request,'Error @ param: '+cmd+', value: '+resp+'.')
								
				#Values for each Pin
				lstPF = [PF[0:1],PF[3:4],PF[4:5],PF[5:6],PF[6:7],PF[7:8],PF[8:9],PF[9:10],PF[10:11],PF[11:12],PF[12:13],PF[13:14],PF[14:15],PF[15:16]]
				lstPP = ['10','13','14','15','16','17','20','21','22','23','24','25','26','27']
				lstParamBase = ['PS','PP','PA']
				for i in range(14):
					lstParam = lstParamBase + ['PM','PO'] + ['UT','LT'] #if the Pin Function is not recognized, then backup everything
					if lstPF[i] == '2' or lstPF[i] == '3' or lstPF[i] == '4':
						lstParam = lstParamBase + ['PM','PO']
					elif lstPF[i] == '1':
						lstParam = lstParamBase + ['UT','LT']
					elif lstPF[i] == '0':
						lstParam = lstParamBase
					for P in lstParam:
						try:
							Ppp = P + ':' + lstPP[i]
							resp = http_post_cmdresp(serf.Address,Ppp,Chost,Cport,Cpath)
							BD = BackupDetail(Backup=B,CreationDate=B.CreationDate,Parameter=Ppp,Value=resp)
							BD.save()
						except:
							messages.warning(request,'Error @ param: '+Ppp+', value: '+resp+'.')
						if P == 'PS' and resp == 'ffffffff':
							break#don't backup parameters for pins that are not configured
				messages.success(request,'Completed backup up of serf address '+str(serf.Address)+'.  '+'Backup date: '+B.CreationDate.strftime('%Y-%m-%d %H:%M:%S')+'.')
			else:
				messages.warning(request,'No response for firmware version request.')
	else:
		form = backup_serfForm()
		form.fields['Choose_Serf'].choices = tuple(Serfs)
			
	PostPath = '/'+HTTP_PROXY_PATH+'/samewire/backup_serf'
	return render_to_response('samewire/backup_serf.html',
		{'form':form,'PostPath':PostPath},
		context_instance=RequestContext(request))


class SerfCommandForm(forms.Form):
	Select_Command = forms.ChoiceField(required=True, widget=forms.Select)
	Optional_Parameter = forms.CharField(max_length=40,required=False)

@user_passes_test(lambda u: u.is_staff)
@login_required()
def serf_command(request):
	'''*Staff* Commands to send to the serfs on the samewire network'''
	messages.info(request,'Select a command and click send.')
	resp = ''
	g=[]
	[g.append(str(x)) for x in request.user.groups.all()]
	lstCommands=[]
	try:
		for o in Command.objects.all().filter(Group__name__in=g).distinct():
			lstCommands.append((o.id,str(o.Name)))
	except:
		messages.error(request,'Unable to create a list of Commands.  Check that there are commands and that they are associated with the same group as your user login.')
#	import pdb;pdb.set_trace()
	if request.method == 'POST':
		form = SerfCommandForm(request.POST)
		form.fields['Select_Command'].choices = tuple(lstCommands)
		if form.is_valid():
			select_command = form.cleaned_data['Select_Command']
			optional_parameter = form.cleaned_data['Optional_Parameter']
			
			try:
				cmd = Command.objects.get(id=select_command)
				serf = Serf.objects.get(id=cmd.Serf.id)
				controller = Master.objects.get(id=serf.Master.id).Controller
				Chost = controller.Host
				Cport = controller.Port
				Cpath = controller.Path
				
				re = cmd.ValidationRegex
				if re != '':
					pass#add code to check the parameter with the validation regex
				
				messages.info(reqeust,'Response: '+http_post_cmdresp(serf.Address,cmd.Command,Chost,Cport,Cpath))
			except:
				messages.error(request,'Error sending command')

	else:
		form = SerfCommandForm()
		form.fields['Select_Command'].choices = tuple(lstCommands)
			
	PostPath = '/'+HTTP_PROXY_PATH+'/samewire/send_serf_command'
	return render_to_response('samewire/serf_command.html',
		{'form':form,'PostPath':PostPath},
		context_instance=RequestContext(request))



def http_post_cmdresp(Address,Command,Host,Port,Path):
	resp = ''
	logger.info(Address+Command)
	logger.info(Host+':'+Port+Path+'/samewire')
	Port = int(Port)
	try:
		params = urllib.urlencode({'address':Address,'manualcmd':Command})
		headers = {"Content-type": "application/x-www-form-urlencoded", "Accept": "text/plain"}
		conn = httplib.HTTPConnection(Host, Port, timeout=15)
		if conn:
			conn.request("POST", Path+'/samewire', params, headers)
			response = conn.getresponse()
			logger.debug(str(response.status)+' '+str(response.reason))
			body = response.read()
#			print 'Reponse: ',body
			if response.status == 200:
				logger.debug('POST Succeeded')
				try:
					m = re.search('<tr><td>Response</td><td>(.+)</td></tr></table><form',body)
#					print m.group(0)
					if m.group(0)[25:26] == Address:
						resp = m.group(0)[26:-23]
					else:
						logger.warn('No address character found')
						resp = 'AddressError'
					logger.debug('Response: {}'.format(resp))
				except:
					resp = '299792458' #send the speed of light
					logger.warning('Failed to parse response')
			else:
				logger.warning('POST Failed')
				raise
			conn.close()
	except KeyboardInterrupt:
		raise KeyboardInterrupt
	except:
		logger.exception('Failed to post')
		raise
	return str(resp)
