import bpy
from .report import importdata
from bpy.types import Operator

class RemoveExtraVerts(Operator):
    bl_idname = "fritzing.remove_extra_verts"
    bl_label = "Fritzing post import: remove extra verts"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            bpy.ops.object.select_all(action="SELECT")
            for layerClass, layer in svgLayers.items():
                if layerClass != 'drill':
                    removeExtraVerts(layer)
        except Exception as e:
            print('--RemoveExtraVerts exception: ' + str(e))
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")

        importdata.step_name = 'POST_EXTRUDE'
        return {"FINISHED"}
        

##
# Removes the overlapping vertices on all layers
def removeExtraVerts(layer):
    if bpy.context:
        bpy.context.view_layer.objects.active = layer
        bpy.ops.object.editmode_toggle()
        bpy.ops.mesh.select_mode(type="VERT")
        bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.mesh.remove_doubles()
        bpy.ops.mesh.select_all(action="DESELECT")
        bpy.ops.object.editmode_toggle()
