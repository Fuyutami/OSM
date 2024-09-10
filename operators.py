import bpy
import blf
import bgl
import uuid
import gpu
from gpu_extras.batch import batch_for_shader


def get_collection(obj_name):
    obj_collection_name = obj_name + " (backup)"
    if "BACKUP" not in bpy.data.collections:
        new_collection = bpy.data.collections.new("BACKUP")
        new_collection.color_tag = "COLOR_05"
        bpy.context.scene.collection.children.link(new_collection)
        
        
    if obj_collection_name not in bpy.data.collections["BACKUP"].children:
        new_collection = bpy.data.collections.new(obj_collection_name)
        new_collection.color_tag = "COLOR_05"
        bpy.data.collections.get("BACKUP").children.link(new_collection)
    return bpy.data.collections["BACKUP"].children[obj_collection_name]


def generate_ID():
    return str(uuid.uuid4())

def draw_callback_px(self, context):
    obj = context.active_object
    font_id = 0
    # Draw rectangle
     # Enable blending using the new `gpu.state` API
    gpu.state.blend_set('ALPHA')

    # Create the shader
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    
    # Define the vertices and indices for a rectangle
    vertices = [(50, 150), (200, 150), (200, 30), (50, 30)]
    indices = [(0, 1, 2), (2, 3, 0)]
    
    # Create a batch for the shader
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)

    # Bind the shader and set the color with alpha (transparency)
    shader.bind()
    shader.uniform_float("color", (0.0, 0.0, 0.0, 0.5))  # Red with 50% transparency
    
    # Draw the batch (the rectangle)
    batch.draw(shader)
    
    # Reset blending to default
    gpu.state.blend_set('NONE')

    # Set the color (white)
    blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
    # Set the size
    blf.size(font_id, 15)

    # Enable shadow
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 3, 0, 0, 0, 0.7)
    blf.shadow_offset(font_id, 2, -2)

    # Set the position
    blf.position(font_id, 70, 120, 0)
    # Draw the text
    blf.draw(font_id, "INFO")

    # draw vertices
    vertices = len(obj.data.vertices)
    evaluated_object = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    vertices_after_mods = len(evaluated_object.data.vertices)
    blf.position(font_id, 70, 90, 0)
    blf.draw(font_id, "Vertices:    " + str(vertices) + " (" + str(vertices_after_mods) + ")")
    # draw number of ngons
    # polygons = obj.data.polygons
    # ngon_count = sum(1 for poly in polygons if len(poly.vertices) > 4)
    # blf.position(font_id, 70, 60, 0)
    # blf.draw(font_id, "Ngons:   " + str(ngon_count))
    #draw modifiers info
    modifiers_list = ""
    for mod in obj.modifiers:
        if mod.show_viewport:
            if mod.type == "BEVEL":
                modifiers_list += mod.name + "[s" + str(mod.segments) + "]  "
            elif mod.type == "SUBSURF":
                modifiers_list += mod.name + "[lv" + str(mod.levels) + "]  "
            else:
                modifiers_list += mod.name + "  "
    
    blf.position(font_id, 70, 60, 0)
    blf.draw(font_id, "Mods:    " + str(modifiers_list))


    # draw controls
    lines = ["CONTROLS", "Scroll:    Switch between states", "Left Click:    Recall object", "Right Click:    Cancel", "X: Delete visible state", "Delete: Delete all states"]
    longest_line = max(lines, key=len)
    width, height = blf.dimensions(font_id, longest_line)

    # Get the width and height of the 3D Viewport region
    area = next(area for area in bpy.context.screen.areas if area.type == 'VIEW_3D')
    width_3d_viewport = area.width

    # Calculate the X-coordinate from the right side of the 3D Viewport
    x_coordinate = width_3d_viewport - width - 30

    # Set the position of the text
    y_offset = 15  # Initial y-coordinate
    line_spacing = 30  # Adjust as needed

    # Reverse the order of lines
    lines.reverse()

     # Draw the text
    for line in lines:
        y_coordinate = y_offset
        blf.position(font_id, x_coordinate, y_coordinate, 0)
        blf.draw(font_id, line)
        y_offset += line_spacing

    



        


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
            self.report({'INFO'}, f"Scrolled up to state {self.current_state_index}")

        if event.type == 'WHEELDOWNMOUSE':
            self.scroll(context, "DOWN")
            self.report({'INFO'}, f"Scrolled down to state {self.current_state_index}")
         

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.report({'INFO'}, f"number of states: {len(self.states)}")

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
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            args = (self, context)
            self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_callback_px, args, 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)

            if(self.osm_id == None):
                self.selected_object["osm_id"] = generate_ID()
                self.selected_object["stateID"] = 0
                self.osm_id = self.selected_object["osm_id"]
                self.states = sorted(
                    [obj for obj in bpy.data.objects if "osm_id" in obj and obj["osm_id"] == self.osm_id],
                    key=lambda x: x["stateID"]
                )

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
    
        

        

        

def register():
    bpy.utils.register_class(BackupObject)
    bpy.utils.register_class(StateScroll)


def unregister():
    bpy.utils.unregister_class(BackupObject)
    bpy.utils.unregister_class(StateScroll)