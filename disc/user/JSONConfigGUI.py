import PythonCard
from PythonCard import configuration, dialog, model
import wx
import json
import sys
import os
import datetime
from collections import OrderedDict
from shutil import copy2

class ConfigGUI(model.Background):

	def on_menuHelpAbout_select(self,event):
		aboutstr = 'Copyright 2014, Nathan A. Wehr.  Released under MIT License.'
		result = dialog.messageDialog(self, aboutstr, 'JSON Config GUI')

	def on_menuHelpNotes_select(self,event):
		helpstr = '''The intent is that the initial json config file be created in a text editor.
This gui makes it easier for the end user to modify the configuration file.
It ties description and help information as well as a developer supplied option list to the configuration variables name and value.

The value does not have to be one of the options.
Create Archive Copy - creates an Archive folder at the location of the source configuration file and places a datetime stamped copy of the file in that location. (the copy is of the file not of data in memory)
The option list in the json file must have all items in double quotes.
		'''
		result = dialog.messageDialog(self, helpstr, 'Notes for JSON Config GUI')

	def initialize_form(self):
		self.components.configList.clear()
		self.components.optionList.clear()
		self.components.valueText.text = ""
		self.components.descriptionText.text = ""
		if self.configDict:
			for k in self.configDict:
				self.components.configList.append(k)
		self.Show()

	def on_initialize(self,event):
		try:
#			import pdb;pdb.set_trace()
			self.config_file = 'config.json'
			if len(sys.argv) > 1:
				self.config_file = sys.argv[1]
			self.configDict = self.load_config(self.config_file)
			self.initialize_form()
		except:
			self.statusBar.text = 'Failed to load config file.'

	def load_config(self,config_file):
#		import pdb;pdb.set_trace()
		if os.path.isfile(config_file):
			f = open(config_file,'r')
			configDict = json.load(f,object_pairs_hook=OrderedDict)
			f.close()
			self.statusBar.text = 'Loaded config file: '+str(config_file)
			return configDict
		else:
			self.statusBar.text = 'File not found: '+str(config_file)
			return {}

	def on_configList_select(self,event):
#		import pdb;pdb.set_trace()
		configitem = self.components.configList.getString(event.target.selection)
		self.components.valueText.text = str(self.configDict[configitem]['value'])
		lst = self.configDict[configitem]['options']
		if type(lst) == type([]):
			self.components.optionList.clear()
			self.components.optionList.insertItems(lst,0)
		else:
			self.components.optionList.clear()
		self.components.descriptionText.text = str(self.configDict[configitem]['description'])

	def on_optionList_select(self,event):
		optionitem = str(self.components.optionList.getString(event.target.selection))
		self.components.valueText.text = optionitem
		configitem = self.components.configList.getString(self.components.configList.selection)
		self.configDict[configitem]['value'] = optionitem

	def on_menuFileOpen_select(self,event):
		wildcard = "JSON files (*.json)|*.json|All Files (*.*)|*.*"
		result = dialog.openFileDialog(wildcard=wildcard)
		if result.accepted:
			self.config_file = result.paths[0]
			self.configDict = self.load_config(self.config_file)
			self.initialize_form()
			self.statusBar.text = 'Loaded config file: '+str(self.config_file)

	def on_menuFileSave_select(self,event):
		self.statusBar.text = 'Saving File ... '+str(self.config_file)
		try:
			f = open(self.config_file,'w')
			json.dump(self.configDict,f,indent=4)
			f.close()
			self.statusBar.text = 'Saved file: '+str(self.config_file)
		except:
			self.statusBar.text = 'Error while trying to save: '+str(self.config_file)

	def on_menuFileArchive_select(self,event):
		try:
			path,fileonly = os.path.split(self.config_file)
			dt_fileonly = datetime.datetime.now().strftime('%Y_%m_%d_%H-%M-%S_')+fileonly
			if path == '':
				path = 'Archive'
			else:
				path = os.path.join(path,'Archive')
			if not os.path.isdir(path):
				os.mkdir(path)
			copy2(self.config_file,os.path.join(path,dt_fileonly))
			self.statusBar.text = 'Archived file: '+str(self.config_file)
		except:
			self.statusBar.text = 'Error while archiving file: '+str(self.config_file)

	def on_menuEditAddCurrentValuetoOptions_select(self,event):
#		import pdb;pdb.set_trace()
		configitem = self.components.configList.getString(self.components.configList.selection)
		lst = self.configDict[configitem]['options']
		if type(lst) != type([]):
			lst = []
		lst.append(self.components.valueText.text)
		self.configDict[configitem]['options'] = lst
		self.components.optionList.clear()
		self.components.optionList.insertItems(lst,0)

	def on_menuEditDeleteSelectedOption_select(self,event):
		result = dialog.messageDialog(self, 'Are you sure?', 'Delete Selected Option.',wx.ICON_EXCLAMATION | wx.YES_NO | wx.NO_DEFAULT)
		if result.accepted:
			configitem = self.components.configList.getString(self.components.configList.selection)
			lst = self.configDict[configitem]['options']
			optionitem = str(self.components.optionList.getString(self.components.optionList.selection))
			lst.remove(optionitem)
			self.configDict[configitem]['options'] = lst
			self.components.optionList.clear()
			self.components.optionList.insertItems(lst,0)

if __name__ == '__main__':
    app = model.Application(ConfigGUI)
    app.MainLoop()