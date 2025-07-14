from bpy.types import Context, Operator
from .report import importdata
import winsound
import os

##
# Dialog box to handle error messages
class ErrorDialog(Operator):
    bl_idname = "fritzing.import_error"
    bl_label = "Fritzing Import Error"

    def draw(self, context: Context | None):
        layout = self.layout
        box = layout.box()
        box.alert = True
        box.row()
        row = box.row()
        text = 'Import error happened.'
        if importdata.error_msg != None:
            text = importdata.error_msg
        row.label(icon='ERROR', text=text)
        box.row()
    
    def execute(self, context):
        context.scene.progress_indicator = 101
        importdata.step_name = 'FINISHED'
        if os.name == 'nt':
            frequency = 1500
            # Set Duration To 1000 ms == 1 second
            duration = 1000
            winsound.Beep(frequency, duration)
        return {"FINISHED"}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


