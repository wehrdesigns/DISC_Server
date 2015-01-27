{'application':{'type':'Application',
          'name':'Template',
    'backgrounds': [
    {'type':'Background',
          'name':'jsonconfigguiBackground',
          'title':u'JSON Configuration GUI',
          'size':(531, 497),
          'statusBar':1,
          'style':['resizeable'],

        'menubar': {'type':'MenuBar',
         'menus': [
             {'type':'Menu',
             'name':'menuFile',
             'label':'&File',
             'items': [
                  {'type':'MenuItem',
                   'name':'menuFileOpen',
                   'label':u'Open',
                  },
                  {'type':'MenuItem',
                   'name':'menuFileSave',
                   'label':u'Save\tCtrl+S',
                  },
                  {'type':'MenuItem',
                   'name':'menuFileArchive',
                   'label':u'Create Archive Copy',
                  },
                  {'type':'MenuItem',
                   'name':'',
                   'label':'E&xit',
                   'command':'exit',
                  },
              ]
             },
             {'type':'Menu',
             'name':'menuEdit',
             'label':u'&Edit',
             'items': [
                  {'type':'MenuItem',
                   'name':'menuEditAddCurrentValuetoOptions',
                   'label':u'Add Current Value to Options',
                  },
                  {'type':'MenuItem',
                   'name':'menuEditDeleteSelectedOption',
                   'label':u'Delete Selected Option',
                  },
              ]
             },
             {'type':'Menu',
             'name':'menuHelp',
             'label':u'&Help',
             'items': [
                  {'type':'MenuItem',
                   'name':'menuHelpAbout',
                   'label':u'About',
                  },
                  {'type':'MenuItem',
                   'name':'menuHelpNotes',
                   'label':u'Notes',
                  },
              ]
             },
         ]
     },
         'components': [

{'type':'TextField', 
    'name':'valueText', 
    'position':(70, 193), 
    'size':(445, -1), 
    },

{'type':'StaticText', 
    'name':'StaticText4', 
    'position':(13, 309), 
    'text':u'Description', 
    },

{'type':'StaticText', 
    'name':'StaticText3', 
    'position':(3, 0), 
    'text':u'Configuration', 
    },

{'type':'StaticText', 
    'name':'StaticText2', 
    'position':(29, 218), 
    'text':u'Options', 
    },

{'type':'StaticText', 
    'name':'StaticText1', 
    'position':(40, 194), 
    'text':u'Value', 
    },

{'type':'TextArea', 
    'name':'descriptionText', 
    'position':(70, 308), 
    'size':(445, 107), 
    'editable':False, 
    },

{'type':'List', 
    'name':'optionList', 
    'position':(70, 217), 
    'size':(445, 90), 
    'items':[], 
    },

{'type':'List', 
    'name':'configList', 
    'position':(70, 0), 
    'size':(445, 191), 
    'items':[], 
    },

] # end components
} # end background
] # end backgrounds
} }
