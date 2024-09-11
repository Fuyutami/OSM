import bpy
import os
from bpy.types import Menu
import bpy.utils.previews

preview_collections = {}

class SelectPieMenu(Menu):
    bl_idname = "OBJECT_MT_select_pie_menu"
    bl_label = "O.S.DM."

    def draw(self, context):
        layout = self.layout
        pcoll = preview_collections["main"]
        icon_backup = pcoll["icon_backup"]
        icon_scroll = pcoll["icon_scroll"]
        pie = layout.menu_pie()
        pie.operator("wm.save_mainfile", text="Save", icon='FILE_TICK')


        if bpy.context.selected_objects and bpy.context.mode == 'OBJECT':
            if len(bpy.context.selected_objects) == 1:
                pie.operator("object.backup_object", text="Backup Object", icon_value=icon_backup.icon_id)
                pie.operator("object.state_scroll", text="State Scroll", icon_value=icon_scroll.icon_id)
                

def register():
    bpy.utils.register_class(SelectPieMenu)
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name="Window", space_type="EMPTY")

    for kmi in km.keymap_items:
        if kmi.idname == 'wm.save_mainfile' and kmi.properties.name == "Save":
            km.keymap_items.remove(kmi)
            break
    kmi = km.keymap_items.new("wm.call_menu_pie", "S", "PRESS", ctrl=True)
    kmi.properties.name = "OBJECT_MT_select_pie_menu"

     # custom icons
    pcoll = bpy.utils.previews.new()
    my_icons_dir = os.path.join(os.path.dirname(__file__), "icons")
    pcoll.load("icon_backup", os.path.join(my_icons_dir, "icon_backup.png"), 'IMAGE')
    pcoll.load("icon_scroll", os.path.join(my_icons_dir, "icon_scroll.png"), 'IMAGE')
    preview_collections["main"] = pcoll

def unregister():
    bpy.utils.unregister_class(SelectPieMenu)
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps['Window']
        for kmi in km.keymap_items:
            if kmi.idname == 'wm.call_menu_pie' and kmi.properties.name == "OBJECT_MT_select_pie_menu":
                km.keymap_items.remove(kmi)
                break
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()