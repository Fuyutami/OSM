bl_info = {
    "name": "OSM",
    "author": "GC",
    "version": (1, 0),
    "blender": (2, 93, 0),
    "location": "",
    "description": "Object State Manager (OSM) lets you save and restore object states", 
    "category": "Object",
}

from . import preferences
from . import operators
from . import ui

def register():
    preferences.register()
    operators.register()
    ui.register()

def unregister():
    preferences.unregister()
    operators.unregister()
    ui.unregister()

