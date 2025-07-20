import bpy
from .report import importdata
from bpy.types import Operator

class CleanDrillHoles(Operator):
    bl_idname = "fritzing.clean_drill_holes"
    bl_label = "Fritzing post import: clean drill holes"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            drill_layer = None
            try:
                drill_layer = svgLayers['drill']
            except:
                pass

            if svgLayers and drill_layer:
                for obj in drill_layer.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                bpy.data.collections.remove(drill_layer)

        except Exception as e:
            print('--CleanDrillHoles exception: ' + str(e))
            importdata.error_msg = str(e)
            bpy.ops.fritzing.import_error("INVOKE_DEFAULT")

        importdata.step_name = 'FINISHED'
        return {"FINISHED"}
