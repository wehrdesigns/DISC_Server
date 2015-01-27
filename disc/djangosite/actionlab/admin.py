from actionlab.models import *
from django.contrib import admin

#class ActionLabDataInline(admin.StackedInline):
#        model = ActionLabData

#class ActionLabUserInline(admin.StackedInline):
#        model = ActionLabUser

class ActionLabAdmin(admin.ModelAdmin):
        list_display = ('id', 'Name', 'Module', 'Timebase', 'Period', 'Active')
        list_diplay_links = ('id', 'Name', 'Module', 'Timebase', 'Period', 'Active')
        list_editable = ('Module', 'Timebase', 'Period', 'Active')
 #       inlines = [ActionLabUserInline,ActionLabDataInline]

admin.site.register(ActionLab, ActionLabAdmin)