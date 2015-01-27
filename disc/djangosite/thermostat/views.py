from django.http import HttpResponse
from django.template import Context, loader
from thermostat.models import *

def all_sensors(request):
	'''An HTML Table of parameters for the Controller.'''
	TableIndex = ['this_table','thermostat']
	qsThermostat = Sensor.objects.all()
	t = loader.get_template('thermostat/sensors.html')
	c = Context({'TableIndex':TableIndex,'qsThermostat':qsThermostat})
	return HttpResponse(t.render(c))

def active_sensors(request):
	'''An HTML Table of parameters for the Controller.'''
	TableIndex = ['this_table','thermostat']
	#exclude inactive sensors
	qsThermostat = Sensor.objects.all().exclude(DataID__Active=False)
	t = loader.get_template('thermostat/sensors.html')
	c = Context({'TableIndex':TableIndex,'qsThermostat':qsThermostat})
	return HttpResponse(t.render(c))
