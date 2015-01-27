from django.db import models
from django.contrib.auth.models import Group
from env.models import *

class Master(models.Model):
	'''The serial adapter between an RS232 and the Samewire network.  Provides power and comm.'''
	Controller = models.ForeignKey(Controller)#v1.3 , on_delete=models.SET_NULL
	Name = models.CharField(max_length=40)
	CommPort = models.CharField(max_length=50)
	Baudrate = models.CharField(max_length=10, default = '9600')
	
	def __unicode__(self):
		return self.Name

class Serf(models.Model):
	'''A circuit to which multiple sensors are attached.  Addressed by a character over the samewire network.'''
	Master = models.ForeignKey(Master)
	Address = models.CharField(max_length=1)
	Address.help_text = 'Each samewire module has a single character address.  Each command begins with this address.'
	
	def __unicode__(self):
		return self.Address+'_'+str(self.Master.Name)
	
class Sensor(models.Model):
	'''Linked to a DataID.  Provides the read command and parameters for the sensor on a Serf.'''
	Serf = models.ForeignKey(Serf)#v1.3 , on_delete=models.SET_NULL
	Serf.help_text='Link this sensor (which is on a Samewire Serf) to a Samewire Master.'
	DataID = models.ForeignKey(Data,related_name='DataID-samewire')
	DataID.help_text = 'Link the sensor to a DataID.  Example: The sensor is in Room A and linked to DataID:0 which is defined for Room A, later the sensor is moved to Room B and defined for DataID:1 which is defined for Room B. The Data is defined by its location while the sensor can be moved without erasing the context of historical data.'
	Command = models.CharField(max_length=10, null=True)
		#Prevent a DataID from being linked to while it is active or linked to another sensor
	ScaleFactors = models.CharField(max_length=200, null=True, blank=True, default = '')
	ScaleFactors.help_text = 'Leave blank for raw data or enter a formula that contains the character "?" (? is the raw sensor data point).  The formula will be passed to the Python "eval()" statement.  See Python help for "eval()".'
	CreationDate = models.DateTimeField('CreationDate',auto_now_add=True)
	Notes = models.TextField(max_length=1000, null=True, blank=True)

	def __unicode__(self):
		return str(self.id)

class Backup(models.Model):
	'''Backup firmware configuration and parameters.'''
	Serf = models.ForeignKey(Serf)
	CreationDate = models.DateTimeField('CreationDate',auto_now_add=True)
	FirmwareVersion = models.CharField(max_length=10)
	PinFunction = models.CharField(max_length=16)
	
class BackupDetail(models.Model):
	'''Backup firmware configuration and parameters.'''
	Backup = models.ForeignKey(Backup)
	CreationDate = models.DateTimeField('CreationDate') #Set this equal to the CreationDate in Backup
	Parameter = models.CharField(max_length=10)
	Value = models.CharField(max_length=20)

class Command(models.Model):
	'''Defines a command that can be sent to a Serf.  Can accept user input.'''
	Serf = models.ForeignKey(Serf)
	Name = models.CharField(max_length=40)
	Group = models.ManyToManyField(Group)
	Group.help_text = "Use to restrict access to a command by setting it to restricted group(s)."
	Command = models.CharField(max_length=40, null=True, blank=True)
	Command.help_text = 'Enter command string as expected by the Serf.  Insert a ? as a variable that will be replaced by a value from the caller.'
	ValidationRegex = models.CharField(max_length=40, null=True, blank=True)
	ValidationRegex.help_text = 'If validation is desired, enter a regular expression that must match the parameter before the command will be accepted and sent.'
	Notes = models.TextField(max_length=1000, null=True, blank=True)
