from django.db import models
from django.contrib.auth.models import Group

"""

"""

#Data *****************************
#DATA_TYPE_CHOICES = (
#	('Temperature', 'Temperature'),
#	('Humidity', 'Humidity'),
#	('Light Level', 'Light Level'),
#	('Wind Speed', 'Wind Speed'),
#	('Wind Direction', 'Wind Direction'),
#	('Rainfall', 'Rainfall'),
#	('Barometric Pressure', 'Barometric Pressure'),
#	('Thermostat Setpoint', 'Thermostat Setpoint'),
#	('Heat On', 'Heat On'),
#	('Air Conditioner On', 'Air Conditioner On'),
#)

BASIC_COLOR_CHOICES = (
    ('AliceBlue', 'AliceBlue'),
    ('AntiqueWhite', 'AntiqueWhite'),
    ('Aqua', 'Aqua'),
    ('Aquamarine', 'Aquamarine'),
    ('Azure', 'Azure'),
    ('Beige', 'Beige'),
    ('Bisque', 'Bisque'),
    ('Black', 'Black'),
    ('BlanchedAlmond', 'BlanchedAlmond'),
    ('Blue', 'Blue'),
    ('BlueViolet', 'BlueViolet'),
    ('Brown', 'Brown'),
    ('BurlyWood', 'BurlyWood'),
    ('CadetBlue', 'CadetBlue'),
    ('Chartreuse', 'Chartreuse'),
    ('Chocolate', 'Chocolate'),
    ('Coral', 'Coral'),
    ('CornflowerBlue', 'CornflowerBlue'),
    ('Cornsilk', 'Cornsilk'),
    ('Crimson', 'Crimson'),
    ('Cyan', 'Cyan'),
    ('DarkBlue', 'DarkBlue'),
    ('DarkCyan', 'DarkCyan'),
    ('DarkGoldenRod', 'DarkGoldenRod'),
    ('DarkGray', 'DarkGray'),
    ('DarkGrey', 'DarkGrey'),
    ('DarkGreen', 'DarkGreen'),
    ('DarkKhaki', 'DarkKhaki'),
    ('DarkMagenta', 'DarkMagenta'),
    ('DarkOliveGreen', 'DarkOliveGreen'),
    ('Darkorange', 'Darkorange'),
    ('DarkOrchid', 'DarkOrchid'),
    ('DarkRed', 'DarkRed'),
    ('DarkSalmon', 'DarkSalmon'),
    ('DarkSeaGreen', 'DarkSeaGreen'),
    ('DarkSlateBlue', 'DarkSlateBlue'),
    ('DarkSlateGray', 'DarkSlateGray'),
    ('DarkSlateGrey', 'DarkSlateGrey'),
    ('DarkTurquoise', 'DarkTurquoise'),
    ('DarkViolet', 'DarkViolet'),
    ('DeepPink', 'DeepPink'),
    ('DeepSkyBlue', 'DeepSkyBlue'),
    ('DimGray', 'DimGray'),
    ('DimGrey', 'DimGrey'),
    ('DodgerBlue', 'DodgerBlue'),
    ('FireBrick', 'FireBrick'),
    ('FloralWhite', 'FloralWhite'),
    ('ForestGreen', 'ForestGreen'),
    ('Fuchsia', 'Fuchsia'),
    ('Gainsboro', 'Gainsboro'),
    ('GhostWhite', 'GhostWhite'),
    ('Gold', 'Gold'),
    ('GoldenRod', 'GoldenRod'),
    ('Gray', 'Gray'),
    ('Grey', 'Grey'),
    ('Green', 'Green'),
    ('GreenYellow', 'GreenYellow'),
    ('HoneyDew', 'HoneyDew'),
    ('HotPink', 'HotPink'),
    ('IndianRed', 'IndianRed'),
    ('Indigo', 'Indigo'),
    ('Ivory', 'Ivory'),
    ('Khaki', 'Khaki'),
    ('Lavender', 'Lavender'),
    ('LavenderBlush', 'LavenderBlush'),
    ('LawnGreen', 'LawnGreen'),
    ('LemonChiffon', 'LemonChiffon'),
    ('LightBlue', 'LightBlue'),
    ('LightCoral', 'LightCoral'),
    ('LightCyan', 'LightCyan'),
    ('LightGoldenRodYellow', 'LightGoldenRodYellow'),
    ('LightGray', 'LightGray'),
    ('LightGrey', 'LightGrey'),
    ('LightGreen', 'LightGreen'),
    ('LightPink', 'LightPink'),
    ('LightSalmon', 'LightSalmon'),
    ('LightSeaGreen', 'LightSeaGreen'),
    ('LightSkyBlue', 'LightSkyBlue'),
    ('LightSlateGray', 'LightSlateGray'),
    ('LightSlateGrey', 'LightSlateGrey'),
    ('LightSteelBlue', 'LightSteelBlue'),
    ('LightYellow', 'LightYellow'),
    ('Lime', 'Lime'),
    ('LimeGreen', 'LimeGreen'),
    ('Linen', 'Linen'),
    ('Magenta', 'Magenta'),
    ('Maroon', 'Maroon'),
    ('MediumAquaMarine', 'MediumAquaMarine'),
    ('MediumBlue', 'MediumBlue'),
    ('MediumOrchid', 'MediumOrchid'),
    ('MediumPurple', 'MediumPurple'),
    ('MediumSeaGreen', 'MediumSeaGreen'),
    ('MediumSlateBlue', 'MediumSlateBlue'),
    ('MediumSpringGreen', 'MediumSpringGreen'),
    ('MediumTurquoise', 'MediumTurquoise'),
    ('MediumVioletRed', 'MediumVioletRed'),
    ('MidnightBlue', 'MidnightBlue'),
    ('MintCream', 'MintCream'),
    ('MistyRose', 'MistyRose'),
    ('Moccasin', 'Moccasin'),
    ('NavajoWhite', 'NavajoWhite'),
    ('Navy', 'Navy'),
    ('OldLace', 'OldLace'),
    ('Olive', 'Olive'),
    ('OliveDrab', 'OliveDrab'),
    ('Orange', 'Orange'),
    ('OrangeRed', 'OrangeRed'),
    ('Orchid', 'Orchid'),
    ('PaleGoldenRod', 'PaleGoldenRod'),
    ('PaleGreen', 'PaleGreen'),
    ('PaleTurquoise', 'PaleTurquoise'),
    ('PaleVioletRed', 'PaleVioletRed'),
    ('PapayaWhip', 'PapayaWhip'),
    ('PeachPuff', 'PeachPuff'),
    ('Peru', 'Peru'),
    ('Pink', 'Pink'),
    ('Plum', 'Plum'),
    ('PowderBlue', 'PowderBlue'),
    ('Purple', 'Purple'),
    ('Red', 'Red'),
    ('RosyBrown', 'RosyBrown'),
    ('RoyalBlue', 'RoyalBlue'),
    ('SaddleBrown', 'SaddleBrown'),
    ('Salmon', 'Salmon'),
    ('SandyBrown', 'SandyBrown'),
    ('SeaGreen', 'SeaGreen'),
    ('SeaShell', 'SeaShell'),
    ('Sienna', 'Sienna'),
    ('Silver', 'Silver'),
    ('SkyBlue', 'SkyBlue'),
    ('SlateBlue', 'SlateBlue'),
    ('SlateGray', 'SlateGray'),
    ('SlateGrey', 'SlateGrey'),
    ('Snow', 'Snow'),
    ('SpringGreen', 'SpringGreen'),
    ('SteelBlue', 'SteelBlue'),
    ('Tan', 'Tan'),
    ('Teal', 'Teal'),
    ('Thistle', 'Thistle'),
    ('Tomato', 'Tomato'),
    ('Turquoise', 'Turquoise'),
    ('Violet', 'Violet'),
    ('Wheat', 'Wheat'),
    ('White', 'White'),
    ('WhiteSmoke', 'WhiteSmoke'),
    ('Yellow', 'Yellow'),
    ('YellowGreen', 'YellowGreen'),
)

TIMEBASE_CHOICES = (
	('seconds', 'seconds'),
	('minutes', 'minutes'),
	('hours', 'hours'),
	('days', 'days'),
)

class DataType(models.Model):
	'''Provides a way to categorize data
	
		DefaultValue is used by the data filtering system.
		Also, if no data is recorded, this value is displayed.
		The default value could be set to make it obvious that no data was collected
		or it could be set to a common value so that it is difficult to tell that data was not collected.
		You decide based on how the data is used.
	'''
	Type = models.CharField(max_length=40, default='Other')
#	Color = models.CharField(max_length=20, choices = BASIC_COLOR_CHOICES, default = 'Black')
#	Color.help_text = "The default color for this data type."
	DecimalPlaces = models.DecimalField(max_digits=1,decimal_places=0, default = 0)
	Units = models.CharField(max_length=20, null=True, blank=True)
	DefaultValue = models.CharField(max_length=20, default='0')
	PlotYmax = models.DecimalField(max_digits=20,decimal_places=10, default = 100)
	PlotYmin = models.DecimalField(max_digits=20,decimal_places=10, default = 0)
	Boolean = models.BooleanField()
	Boolean.help_text = "This data plot will be filled in for True values. Averaged data will show a count of the timebase (rather than an average which will always be between 0 and 1."
	def __unicode__(self):
		return str(self.Type)

PURGE_CHOICES = (
	('Never', 'Never'),
	('Hour','Hour'),
	('Day', 'Day'),
	('Week', 'Week'),
	('Month', 'Month'),
	('Year', 'Year'),
	('Decade', 'Decade')
)

class Data(models.Model):
	'''All data is defined here.  Sources of data are defined in other django apps.
		
		Data is categorized by Type and the Name serves as a description.
		Color also helps to categorize data.
		Group is used to authorize and categorize data.
		Active status is used by the presentation, collection and application software.
		Timebase, Period and Copy work together and are used by the filter in the time series engine.
		A fixed quantity of data is recorded for each timebase. This provides a consistent format for using the data.
		The number of values recorded in a day for each timebase: days=1, hours=24, minutes=1440, seconds=86400
		The timebase defines how often the data is measured, but it might be desired to collect data at a slower rate.
		The period allows for a slower data collection rate.
			(e.g. to collect every 5 minutes, use timebase minutes and period 5)
		Copy is used to fill in the timebase interval when the collection interval is irregular.
		There are many reasons why data might not be collected exactly on the timebase interval (such as every minute).
		Copy is the maximum number of points that data can be copied (for the given timebase).
		Copy new data backward by specifying a negative integer and copy the previous data forward by specifying a positive integer.
				
		This data is defined by its location and application.  This allows the source of the data to change (e.g. a different sensor might be installed).
		For example, the living room temperature might come from a samewire temperature sensor
		but, later be changed to a thermostat temperature sensor.  This disconnects the source of the data (the sensor) from applications that use the data.
	'''
	ID = models.AutoField(primary_key=True)
	Type = models.ForeignKey(DataType)
	Name = models.CharField(max_length=40)
	Color = models.CharField(max_length=20, choices = BASIC_COLOR_CHOICES, default = 'Black')
	Active = models.BooleanField()
	Timebase = models.CharField(max_length=10, choices = TIMEBASE_CHOICES, default = 'minutes')
	Period = models.CharField(max_length=5, default = '1')
	Period.help_text = 'update every N units of the timebase, default = 1 (may not be used by all)'
	Copy = models.CharField(max_length=5, default = '0')
	Copy.help_text = 'If data is missed, copy a new value up to this number of timebase units.  Positive values copy forward and negative values copy backward.'
	Group = models.ManyToManyField(Group)
	Group.help_text = "Use this field to organize sensors into groups that you create."
	Notes = models.TextField(max_length=320, null=True, blank=True)
	
	def __unicode__(self):
		return str(self.ID)+'_'+str(self.Type)+'_'+str(self.Name)
#		return str(self.ID)

class Controller(models.Model):
	'''A remote software manager for data providers and action consumers.
	
		At a minimum, a name is required.
		A controller can link instances from different django apps and their associated software and hardware.
		Connection information is stored here so that django apps can access the resources on a remote controller.
		A controller might manage a samewire network as well as a thermostat.
		The controller might collect data from these data providers as well as transfer commands, such as updating the thermostat setpoint.
	'''
	Name = models.CharField(max_length=40)
	Host = models.CharField(max_length=100)
	Port = models.CharField(max_length=5)
	Path = models.CharField(max_length=100)
	
	def __unicode__(self):
		return self.Name

#To Reset this model in the database
	#python manage.py sqlclear env
		#copy the SQL
	#sqlite3 ../Environment.db
		#paste the SQL
	#python manage.py syncdb
	#python manage.py runserver

#To Use South to update/alter the database
#  After south is configured for the application
#   Save the new model
#   python manage.py schemamigration env --auto
#   python manage.py migrate env


