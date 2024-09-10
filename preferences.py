import bpy
from bpy.types import AddonPreferences

class Preferences(AddonPreferences):
    bl_idname = __package__
    
    save_state_on_revert: bpy.props.BoolProperty(
        name="Save state on revert",
        description="Save the current state to a new state before reverting to a previous state.",
        default=False,
    ) # type: ignore

    duplicate_reverted_state: bpy.props.BoolProperty(
        name="Duplicate reverted state",
        description="Duplicate the reverted state instead of restoring it.",
        default=True,
    ) # type: ignore
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "save_state_on_revert")
        layout.prop(self, "duplicate_reverted_state")


def register():
    bpy.utils.register_class(Preferences)

def unregister():
    bpy.utils.unregister_class(Preferences)
