import bpy
from bpy.types import Context, Operator
from .report import importdata
import winsound
import os

##
# Dialog box to handle error messages
class GerberErrorDialog(Operator):
    bl_idname = "fritzing.gerber_import_error"
    bl_label = "Fritzing Gerber Import Error"

    def draw(self, context: Context | None):
        layout = self.layout
        box = layout.box()
        box.alert = True
        box.row()
        row = box.row()
        text = 'Gerber import error happened.'
        if importdata.error_msg != None:
            text = importdata.error_msg
        row.label(icon='ERROR', text=text)
        box.row()
    
    def execute(self, context):
        if context and hasattr(context.scene, 'gerber_progress_indicator'):
            setattr(context.scene, 'gerber_progress_indicator', 101)
        importdata.step_name = 'FINISHED'
        if os.name == 'nt':
            frequency = 1500
            # Set Duration To 1000 ms == 1 second
            duration = 1000
            winsound.Beep(frequency, duration)
        return {"FINISHED"}
    
    def invoke(self, context, event):
        area_3d = None
        if bpy.context is None or context is None:
            return
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area_3d = area
                break
        if area_3d:
            screen_width = area_3d.width
            screen_height = area_3d.height
            center_x = int(screen_width / 2)
            center_y = int(screen_height / 2)
            # Warp the cursor to the center of the 3D Viewport
            context.window.cursor_warp(center_x, center_y)
        return context.window_manager.invoke_props_dialog(self)


