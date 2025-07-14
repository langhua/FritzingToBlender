import bpy
from .report import importdata
from bpy.types import Operator

class MergeLayers(Operator):
    bl_idname = "fritzing.merge_layers"
    bl_label = "Fritzing post import: merge layers"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            joinedLayer = None
            if svgLayers:
                bpy.ops.object.select_all(action="DESELECT")
                for layerClass, layer in svgLayers.items():
                    layer.select_set(True)
                bpy.context.view_layer.objects.active = list(svgLayers.values())[0]
                bpy.ops.object.join()
                joinedLayer = bpy.context.view_layer.objects.active
                joinedLayer.name = 'JoinedLayer'
        except Exception as e:
            print('--MergeLayers exception: ' + str(e))
            importdata.error_msg = str(e)
            bpy.ops.fritzing.import_error("INVOKE_DEFAULT")

        importdata.step_name = 'FINISHED'
        return {"FINISHED"}
