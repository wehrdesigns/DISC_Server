from django.db import models
from django.contrib.auth.models import Group
from env.models import *

class Thermostat(models.Model):
	'''Defines the serial connection to a thermostat and which Controller drives this thermostat.'''
	Controller = models.ForeignKey(Controller)#v1.3 , on_delete=models.SET_NULL
	Name = models.CharField(max_length=40)
	CommPort = models.CharField(max_length=50)
	Baudrate = models.CharField(max_length=10, default='9600')

	def __unicode__(self):
		return self.Name
				
class Sensor(models.Model):
	'''Linked to a DataID.  Provides the read command and parameters for the sensor on a Thermostat.'''
	Thermostat = models.ForeignKey(Thermostat)# , on_delete=models.SET_NULL
	DataID = models.ForeignKey(Data,related_name='DataID-thermostat')
	DataID.help_text = 'Link the sensor to a DataID.  Example: The sensor is in Room A and linked to DataID:0 which is defined for Room A, later the sensor is moved to Room B and defined for DataID:1 which is defined for Room B. The Data is defined by its location while the sensor can be moved without erasing the context of historical data.'
	Command = models.CharField(max_length=40)
	Command.help_text = 'Include Carriage Return \r and New Line \n as expected by the thermostat'
	ResponseTermination = models.CharField(max_length=10, null=True, blank=True)
	ResponseTermination.help_text = 'Termination characters from the thermostat --None, Carriage Return \r, New Line \n, etc'
	Slice = models.CharField(max_length=10, null=True, blank=True)
	Slice.help_text = 'Parse data by Python slice notation -- example: 2:5 which will slice two characters starting at the third character (the first character is index zero)'
	RegularExpression = models.CharField(max_length=40, null=True, blank=True)
	ScaleFactors = models.CharField(max_length=80, null=True, blank=True, default='?')
	ScaleFactors.help_text = 'Enter a formula that contains the character "?" (? is the raw sensor data point).  The formula will be passed to the Python "eval()" statement.  See Python help for "eval()".  Will be ignored if blank.'
	Notes = models.TextField(max_length=1000, null=True, blank=True)
	
	def __unicode__(self):
		return str(self.id)

class Action(models.Model):
	'''Defines an action command that can be sent to a Thermostat.  Can accept user input.'''
	Thermostat = models.ForeignKey(Thermostat)
	Name = models.CharField(max_length=40)
	Command = models.CharField(max_length=40, null=True, blank=True)
	Command.help_text = 'Enter command string as expected by the thermostat.  Insert a ? as a variable that will be replaced by a value from the caller.'
	ValidationRegex = models.CharField(max_length=40, null=True, blank=True)
	ValidationRegex.help_text = 'If validation is desired, enter a regular expression that must match the parameter before the command will be accepted and sent.'
