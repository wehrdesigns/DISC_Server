from django.db import models
from django.contrib.auth.models import Group
from env.models import *

class HTMLTable(models.Model):
	'''Defines the URL from with to get table data.  This software is operated in the Controller.'''
	Controller = models.ForeignKey(Controller)#v1.3 , on_delete=models.SET_NULL
	Name = models.CharField(max_length=40)
	URL = models.URLField(max_length=400, null=True)#verify_exists is false because of a problem reading demo data from the server while the model data is being updated
	
	def __unicode__(self):
		return self.Name

class Sensor(models.Model):
	'''Linked to a DataID.  Provides the table index and the row and column index of the desired data.
		Data can be scaled if desired.
	'''
	DataID = models.ForeignKey(Data,related_name='DataID-htmltable')
	DataID.help_text = 'Link the sensor to a DataID.  Example: The sensor is in Room A and linked to DataID:0 which is defined for Room A, later the sensor is moved to Room B and defined for DataID:1 which is defined for Room B. The Data is defined by its location while the sensor can be moved without erasing the context of historical data.'
		#Prevent a DataID from being linked to, while it is active or linked to another sensor
	HTMLTable = models.ForeignKey(HTMLTable)#v1.3 , on_delete=models.SET_NULL
	TableIndex = models.DecimalField(max_digits=10, decimal_places=0, default=1)
	Row = models.DecimalField(max_digits=10, decimal_places=0)
	Column = models.DecimalField(max_digits=10, decimal_places=0)
	ScaleFactors = models.CharField(max_length=200, null=True, default='?')
	ScaleFactors.help_text = 'Enter a formula that contains the character "?".  The formula will be passed to the Python "eval()" statement.  See Python help for "eval()".'
	CreationDate = models.DateTimeField('CreationDate',auto_now_add=True)
	Notes = models.TextField(max_length=1000, null=True, blank=True)

	def __unicode__(self):
		return str(self.id)
