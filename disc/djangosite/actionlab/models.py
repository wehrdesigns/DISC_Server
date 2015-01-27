from django.db import models
from env.models import Data,TIMEBASE_CHOICES
from django.contrib.auth.models import User

TIMEBASE_CHOICES = (
	('Second', 'Second'),
	('Minute', 'Minute'),
	('Hour', 'Hour'),
	('Day', 'Day'),
)

class ActionLab(models.Model):
	'''Specifies a code module and the frequency that the module should be executed.'''
	Active = models.BooleanField()
	Name = models.CharField(max_length=200)
	Module = models.CharField(max_length=100)
	Module.help_text = 'Name of a python module stored in the folder actionlabmodules. DO NOT include .py extension because that is interpreted as a py module!!!'
	Timebase = models.CharField(max_length=10, choices = TIMEBASE_CHOICES, default = 'Minute')
	Period = models.CharField(max_length=30, default = '1')
	Period.help_text = 'update every N units of the timebase, default = 1 (may not be used by all)'
	CreationDate = models.DateTimeField('CreationDate',auto_now_add=True)
	Notes = models.TextField(max_length=1000, null=True, blank=True)

	def __unicode__(self):
		return str(self.id)

#class ActionLabData(models.Model):
#	ActionLab = models.ForeignKey(ActionLab)
#	DataID = models.ForeignKey(Data,related_name='DataID-actionlab')

#class ActionLabUser(models.Model):
#	ActionLab = models.ForeignKey(ActionLab)
#	User = models.ManyToManyField(User)
	