import bpy
from .report import importdata
from bpy.types import Operator

class DrillHoles(Operator):
    bl_idname = "fritzing.drill_holes"
    bl_label = "Fritzing post import: drill holes"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            drill_layer = None
            try:
                drill_layer = svgLayers['drill']
            except:
                pass
            if drill_layer and svgLayers:
                for layerClass, layer in svgLayers.items():
                    if layerClass != 'drill':
                        drillHoles(layer, drill_layer)
        except Exception as e:
            print('--DrillHoles exception: ' + str(e))
            importdata.error_msg = str(e)
            bpy.ops.fritzing.import_error("INVOKE_DEFAULT")

        importdata.step_name = 'POST_CLEAN_DRILL'
        return {"FINISHED"}


##
# creates a drill hole through an individual layer of the pcb
# @param layer_name -the layer to drill the holes in
def drillHoles(layer, drill_layer):
    for area in bpy.context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    space.shading.type = "SOLID"

    if layer and drill_layer:
        for obj in drill_layer.objects:
            modifier = layer.modifiers.new(name="Boolean", type="BOOLEAN")
            modifier.object = obj
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.modifier_apply(modifier="Boolean")
