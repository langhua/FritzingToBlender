import bpy
from .report import importdata
from bpy.types import Operator

class CleanDrillHoles(Operator):
    bl_idname = "fritzing.clean_drill_holes"
    bl_label = "Fritzing post import: clean drill holes"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            if svgLayers and svgLayers['drill']:
                drill_layer = svgLayers['drill']
                for obj in drill_layer.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.collections.remove(drill_layer)
                svgLayers.pop('drill')
        except Exception as e:
            print('--exception: ' + str(e))
            importdata.error_msg = str(e)
            bpy.ops.fritzing.import_error("INVOKE_DEFAULT")

        importdata.step_name = 'POST_MERGE_LAYERS'
        return {"FINISHED"}
