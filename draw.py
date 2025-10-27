import bpy
import blf
import gpu
from gpu_extras.batch import batch_for_shader


def draw_object_info(self, context):
    obj = context.active_object
    modifiers_list_lines = [""]
    mod_count = 0
    for mod in obj.modifiers:
        mod_count += 1
        mod_str= ""
        if mod.show_viewport:
            if mod.type == "BEVEL":
                mod_str = mod.name + "[s" + str(mod.segments) + "]  "
            elif mod.type == "SUBSURF":
                mod_str += mod.name + "[lv" + str(mod.levels) + "]  "
            else:
                mod_str = mod.name + "  "
        
        if len(modifiers_list_lines[-1]) + len(mod_str) > 40:
            modifiers_list_lines.append(mod_str)
        else:
            modifiers_list_lines[-1] += mod_str
    
    total_lines = len(modifiers_list_lines) + 3 # 3 lines for the other info
    line_height = 30
    padding_L_R = 15
    padding_bottom = 20
    panel_min_width = 200
    panel_height = total_lines * line_height
    panel_width = mod_count > 0 and len(modifiers_list_lines[0]) * 10 + padding_L_R * 2 or panel_min_width
    panel_x = 50
    panel_y = 50
    header_margin = 10
    
    # DRAW PANEL
    header_corners = [(panel_x, panel_y + panel_height  +  padding_bottom - line_height), (panel_x + panel_width, panel_y + panel_height  +  padding_bottom - line_height), (panel_x + panel_width, panel_y + panel_height +  padding_bottom), (panel_x, panel_y + panel_height +  padding_bottom)]
    panel_corners = [(panel_x, panel_y), (panel_x + panel_width, panel_y ), (panel_x + panel_width, panel_y + panel_height  +  padding_bottom), (panel_x, panel_y + panel_height  +  padding_bottom)]
    gpu.state.blend_set('ALPHA')
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    
    # Panel header
    vertices = [(x, y) for x, y in header_corners]
    indices = [(0, 1, 2), (2, 3, 0)]
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", (0.0, 0.0, 0.0, 0.4))
    batch.draw(shader)
    
    # Panel
    vertices = [(x, y) for x, y in panel_corners]
    indices = [(0, 1, 2), (2, 3, 0)]
    batch = batch_for_shader(shader, 'TRIS', {"pos": vertices}, indices=indices)
    shader.bind()
    shader.uniform_float("color", (0.0, 0.0, 0.0, 0.4))
    batch.draw(shader)
    gpu.state.blend_set('NONE')
    
    # DRAW TEXT
    font_id = 0
    blf.size(font_id, 15)
    blf.enable(font_id, blf.SHADOW)
    blf.shadow(font_id, 3, 0, 0, 0, 0.7)
    blf.shadow_offset(font_id, 2, -2)
    
    # Header Title
    blf.position(font_id, panel_x + padding_L_R, panel_y + panel_height - line_height  +  padding_bottom + header_margin, 0)
    blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
    blf.draw(font_id, "OSM")

    # State ID
    blf.position(font_id, panel_x + padding_L_R, panel_y + panel_height - line_height * 2 +  padding_bottom, 0)
    blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
    blf.draw(font_id, "State ID: ")
    blf.position(font_id, panel_x + padding_L_R + 80, panel_y + panel_height - line_height * 2 +  padding_bottom, 0)
    blf.color(font_id, 1.0, 1.0, 1.0, 0.3)
    blf.draw(font_id, str(obj["stateID"]))

    # Vertices
    vertices = len(obj.data.vertices)
    evaluated_object = obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    vertices_after_mods = len(evaluated_object.data.vertices)
    blf.position(font_id, panel_x + padding_L_R, panel_y + panel_height - line_height * 3 +  padding_bottom, 0)
    blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
    blf.draw(font_id, "Vertices: ")
    blf.position(font_id, panel_x + padding_L_R + 80, panel_y + panel_height - line_height * 3 +  padding_bottom, 0)
    blf.color(font_id, 1.0, 1.0, 1.0, 0.3)
    blf.draw(font_id, str(vertices) + " (" + str(vertices_after_mods) + ")")

    # Modifiers
    for i, line in enumerate(modifiers_list_lines):
        
        if i == 0:
            blf.position(font_id, panel_x + padding_L_R, panel_y + panel_height - line_height * (i + 4) +  padding_bottom, 0)
            blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
            blf.draw(font_id, "Modifiers: ")
            blf.position(font_id, panel_x + padding_L_R + 80, panel_y + panel_height - line_height * (i + 4) +  padding_bottom, 0)
            blf.color(font_id, 1.0, 1.0, 1.0, 0.3)
            blf.draw(font_id, line)
        else:
            blf.position(font_id, panel_x + padding_L_R, panel_y + panel_height - line_height * (i + 4) +  padding_bottom, 0)
            blf.draw(font_id, line)
        
        
    
    