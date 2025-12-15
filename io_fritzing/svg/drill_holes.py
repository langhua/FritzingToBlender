import bpy
from io_fritzing.svg.report import importdata
from bpy.types import Operator
from io_fritzing.svg.remove_extra_verts import removeExtraVerts

class DrillHoles(Operator):
    bl_idname = "fritzing.drill_holes"
    bl_label = "Fritzing post import: drill holes"
    
    def execute(self, context):
        try:
            if bpy.context is not None:
                joined_layer = bpy.context.view_layer.objects['JoinedLayer']
                drill_layer = None
                try:
                    drill_layer = importdata.svgLayers['drill']
                except:
                    pass
                algorithm = 'BooleanModifier'
                if context and hasattr(context.scene, 'drill_algorithm_setting'):
                    algorithm = str(getattr(context.scene, 'drill_algorithm_setting'))
                if drill_layer and joined_layer:
                    drillHoles(joined_layer, drill_layer=drill_layer, algorithm=algorithm)
        except Exception as e:
            print('--DrillHoles exception: ' + str(e))
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")

        importdata.step_name = 'POST_CLEAN_DRILL'
        return {"FINISHED"}


##
# creates a drill hole through an individual layer of the pcb
# @param layer_name -the layer to drill the holes in
def drillHoles(layer, drill_layer, algorithm):
    if bpy.context is None:
        return
    for area in bpy.context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    setattr(getattr(space, 'shading'), 'type', "SOLID")

    if layer and drill_layer:
        if algorithm == 'AutoBoolean':
            # apply bool tool
            bpy.ops.object.select_all(action='DESELECT')
            layer.select_set(True)
            for obj in drill_layer.objects:
                obj.select_set(True)
            bpy.context.view_layer.objects.active = layer
            getattr(getattr(bpy.ops, 'object'), 'boolean_auto_difference')()
        else:
            for obj in drill_layer.objects:
                modifier = layer.modifiers.new(name="Boolean", type="BOOLEAN")
                modifier.object = obj
                bpy.context.view_layer.objects.active = layer
                bpy.ops.object.modifier_apply(modifier="Boolean")
