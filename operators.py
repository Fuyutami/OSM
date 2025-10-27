import bpy
from . utils import generate_ID
from . draw import draw_object_info


    
class BackupObject(bpy.types.Operator):
    """Backup the selected object"""
    bl_idname = "object.backup_object"
    bl_label = "Backup Object"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        selected_object = context.selected_objects[0]
        collection = selected_object.users_collection[0]
        name = selected_object.name

        # If the object is not already backed up
        if "osm_id" not in selected_object and "stateID" not in selected_object:
            selected_object["osm_id"] = generate_ID()
            selected_object["stateID"] = 0

        # Create a copy of the selected object
        new_object = selected_object.copy()
        new_object.data = selected_object.data.copy()
        new_object["osm_id"] = selected_object["osm_id"]
        new_object["stateID"] = selected_object["stateID"] + 1
        new_object.name = new_object['osm_id'] + " state " + str(selected_object["stateID"])

        # Link the new object to the same collection
        collection.objects.link(new_object)

        # Reparent children to the new object while preserving their world transforms
        for child in selected_object.children:
            matrix_world_copy = child.matrix_world.copy()
            child.parent = None
            child.matrix_world = matrix_world_copy
            child.parent = new_object
            child.matrix_world = matrix_world_copy
            # Clear the inverse matrix
            child.matrix_parent_inverse.identity()

        # Parent selected object to the new object
        selected_object_world_matrix = selected_object.matrix_world.copy()
        selected_object.parent = new_object
        selected_object.matrix_world = selected_object_world_matrix
        # Clear the parent inverse matrix
        selected_object.matrix_parent_inverse.identity()

        # Rename the selected object and the new object
        selected_object.name = f"OSM state ({new_object['osm_id']}) stateID ({selected_object['stateID']})"
        new_object.name = name

        # unlink the selected object from the collection
        collection.objects.unlink(selected_object)

        # Activate the new object
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = new_object
        new_object.select_set(True)

        self.report({'INFO'}, f"Backed up object!")

        return {'FINISHED'}

class StateScroll(bpy.types.Operator):
    """Scroll through the states of the selected object"""
    bl_idname = "object.state_scroll"
    bl_label = "State Scroll"
    bl_options = {'REGISTER', 'UNDO'}

    def __init__(self):
        self.selected_object = bpy.context.selected_objects[0]
        self.object_name = self.selected_object.name
        self.collection = self.selected_object.users_collection[0]
        self.osm_id = self.selected_object.get("osm_id", None)
        self.states = sorted(
            [obj for obj in bpy.data.objects if "osm_id" in obj and obj["osm_id"] == self.osm_id],
            key=lambda x: x["stateID"]
        )
        self.current_state_index = len(self.states) - 1

    def modal(self, context, event):
        context.area.tag_redraw()

        if event.type == 'WHEELUPMOUSE':
            self.scroll(context, "UP")
            

        if event.type == 'WHEELDOWNMOUSE':
            self.scroll(context, "DOWN")
           
         

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.revertState()
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.context.space_data.overlay.show_wireframes = False
            bpy.ops.object.select_all(action='DESELECT')
            self.collection.objects.unlink(self.states[self.current_state_index])
            self.collection.objects.link(self.states[len(self.states) - 1])
            bpy.context.view_layer.objects.active = self.states[len(self.states) - 1]
            self.states[len(self.states) - 1].select_set(True)
            return {'FINISHED'}

        # allow orbiting around the object
        if event.type == 'MIDDLEMOUSE':
            return {'PASS_THROUGH'}

        # cancel
        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.context.space_data.overlay.show_wireframes = False
            bpy.ops.object.select_all(action='DESELECT')
            self.collection.objects.unlink(self.states[self.current_state_index])
            self.collection.objects.link(self.states[len(self.states) - 1])
            bpy.context.view_layer.objects.active = self.states[len(self.states) - 1]
            self.states[len(self.states) - 1].select_set(True)
            
            
            # refresh status bar
            bpy.context.workspace.status_text_set("")
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_object_info, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)

            if(self.osm_id == None):
                self.selected_object["osm_id"] = generate_ID()
                self.selected_object["stateID"] = 0
                self.osm_id = self.selected_object["osm_id"]
                self.states = sorted(
                    [obj for obj in bpy.data.objects if "osm_id" in obj and obj["osm_id"] == self.osm_id],
                    key=lambda x: x["stateID"]
                )
            
            bpy.context.workspace.status_text_set("LMB - Recall state               SCROLL - Change state               RMB - Cancel                DEL - Delete state")    

            # Focus on the selected object
            bpy.ops.view3d.view_selected(use_all_regions=False)

            # show wireframe overlay
            bpy.context.space_data.overlay.show_wireframes = True

            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}
    
    def scroll(self, context, direction):
        prev_index = self.current_state_index

        if direction == "UP":
            self.current_state_index = (self.current_state_index + 1) % len(self.states)
        elif direction == "DOWN":
            self.current_state_index = (self.current_state_index - 1) % len(self.states)
        else:
            self.report({'ERROR'}, f"Invalid direction: {direction}")
            return {'CANCELLED'}

        bpy.ops.object.select_all(action='DESELECT')
        self.collection.objects.unlink(self.states[prev_index])
        self.collection.objects.link(self.states[self.current_state_index])
        bpy.context.view_layer.objects.active = self.states[self.current_state_index]
        self.states[self.current_state_index].select_set(True)
    
    def revertState(self):
        preferences = bpy.context.preferences.addons[__package__].preferences
        dublicate_reverted_state = preferences.duplicate_reverted_state
        save_state_on_revert = preferences.save_state_on_revert
        self.report({'INFO'}, f"Reverting to state {self.current_state_index}, duplicate_reverted_state: {dublicate_reverted_state}, save_state_on_revert: {save_state_on_revert}")
    
        

        

def register():
    bpy.utils.register_class(BackupObject)
    bpy.utils.register_class(StateScroll)


def unregister():
    bpy.utils.unregister_class(BackupObject)
    bpy.utils.unregister_class(StateScroll)