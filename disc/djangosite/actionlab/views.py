import datetime, sys, time, os, shutil
import logging
logger = logging.getLogger(__name__)
from django.http import HttpResponse
from django.template import Context, loader
import djangosite.settings

from django.http import HttpResponse
from django.template import Context, loader
from django import forms
from django.shortcuts import render_to_response
from django.template import Context, loader, RequestContext, Template
from django.forms.fields import DateField, ChoiceField, CharField
from django.forms.widgets import Textarea
#from django.forms.extras.widgets import SelectDateWidget
from django.contrib.auth.decorators import login_required, user_passes_test
import django.contrib.auth
from django.contrib import messages
#from epiceditor.widgets import AdminEpicEditorWidget

@user_passes_test(lambda u: u.is_staff)
@login_required()
def output(request):
	'''Get HTML from actionlab print queue'''
	from discengines import ALE, START_ACTIONLABENGINE
	if START_ACTIONLABENGINE:
		msg = ALE.msg.replace('\n','<BR>')
	else:
		msg = 'actionlab engine not running'
	t = loader.get_template('actionlab/output.html')
	c = Context({'msg':msg,})
	return HttpResponse(t.render(c))

class EditModuleForm(forms.Form): 
	Action_Lab_Module = forms.ChoiceField(required=True)
	Module_Text = forms.CharField(required=False, widget=Textarea)#AdminEpicEditorWidget())
	Save = forms.BooleanField(required=False)

@user_passes_test(lambda u: u.is_superuser)
@login_required()
def edit_module(request):
	'''Loads an actionlab module from file into a form for editing.'''
	path = os.path.join(djangosite.settings.APP_BASE_PATH,'user','actionlabmodules')
	ld = os.listdir(path)
#	print ld
	modules = []
	for x in ld:
		if x[len(x)-3:] == '.py' and x != '__init__.py':
			modules.append((x,x))
			
	if request.method == 'POST':
		#import pdb;pdb.set_trace()
		form = EditModuleForm(request.POST)
		form.fields['Action_Lab_Module'].choices = modules
		
		if form.is_valid():
			form2 = {}
			for k,v in form.cleaned_data.iteritems():
				form2[k] = v
			
			Action_Lab_Module = form.cleaned_data['Action_Lab_Module']
			Module_Text = form.cleaned_data['Module_Text']
			Save = form.cleaned_data['Save']
			
			ALMname = Action_Lab_Module[:-3]
			
			if Save:
				try:
					if not os.listdir(path).__contains__('archive'):
						os.mkdir(os.path.join(path,'archive'))
					if not os.listdir(os.path.join(path,'archive')).__contains__(ALMname):
						os.mkdir(os.path.join(path,'archive',ALMname))
						msg += '  Created archive folder for module.'
					shutil.copy(os.path.join(path,Action_Lab_Module),os.path.join(path,'archive',ALMname,ALMname+'_'+datetime.datetime.now().strftime('%Y_%m_%d_%H-%M-%S')+'.py'))
					messages.success(request,'Created archive copy of module.')
					with open(os.path.join(path,Action_Lab_Module),'w') as f:
						#it appears the the form data converts \n to \r, then python adds \r\n
						#replacing \r with '' handles input files with EOL \n and \r\n and \r.
						f.write(Module_Text.replace('\r',''))
					messages.success(request,'Saved module.')
				except:
					messages.error(request,'Error saving module.')
			else:
				#read module
				with open(os.path.join(path,Action_Lab_Module),'r') as f:
					c = f.read()
				form2['Module_Text'] = c
				form2['Save'] = True
			
		form = EditModuleForm(form2)
		
	else:
		form = EditModuleForm()
	form.fields['Action_Lab_Module'].choices = modules
#	import pdb;pdb.set_trace()
	PostPath = '/'+djangosite.settings.HTTP_PROXY_PATH+'/actionlab/edit_module'
	return render_to_response('actionlab/edit_module.html',{'PostPath':PostPath,'form':form},context_instance=RequestContext(request))
