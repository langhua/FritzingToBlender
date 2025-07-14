import bpy
from .report import importdata
from bpy.types import Operator
from mathutils import Vector

class Extrude(Operator):
    bl_idname = "fritzing.extrude"
    bl_label = "Fritzing post import: extrude"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            extrudeLayers(svgLayers, None, None, None, None)
        except Exception as e:
            print('--exception: ' + str(e))
            importdata.error_msg = str(e)
            bpy.ops.fritzing.import_error("INVOKE_DEFAULT")

        importdata.step_name = 'POST_CREATE_MATERIAL'
        return {"FINISHED"}

##
# extrudes all components and sets the vertical position of each layer
def extrudeLayers(svgLayers, boardThickness, copperThickness, solderMaskThickness, silkscreenThickness):
    if not boardThickness or boardThickness < 4e-4:
        boardThickness = 0.0016         # 1.6mm
    if not copperThickness or copperThickness < 2.54e-5:
        # 1oz
        copperThickness = 2.54e-5
    if not solderMaskThickness or solderMaskThickness < 2e-5:
        # 0.8mils
        solderMaskThickness = 2e-5
    if not silkscreenThickness or silkscreenThickness < 2.54e-5:
        silkscreenThickness = 2.54e-5
    silkscreenLineWidth = 5 * silkscreenThickness
    bpy.ops.object.select_all(action="DESELECT")
    for layerClass, layer in svgLayers.items():
        if layerClass == "outline":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((0, 0, boardThickness))})
            bpy.ops.object.editmode_toggle()
            layer.location.z = 0
        elif layerClass == 'bottomsilk':
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((silkscreenLineWidth, silkscreenLineWidth, silkscreenThickness))})
            bpy.ops.object.editmode_toggle()
            layer.location.z = -silkscreenThickness/2
        elif layerClass == "bottom":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((copperThickness, copperThickness, copperThickness/5))})
            bpy.ops.object.editmode_toggle()
            layer.location.z = - copperThickness/3
        elif layerClass == "top":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((copperThickness, copperThickness, copperThickness/5))})
            bpy.ops.object.editmode_toggle()
            layer.location.z = boardThickness - 2 * copperThickness / 3
        elif layerClass == "topsilk":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((silkscreenLineWidth, silkscreenLineWidth, silkscreenThickness))})
            bpy.ops.object.editmode_toggle()
            layer.location.z = boardThickness - silkscreenThickness/2
        elif layerClass == "drill":
            for obj in layer.objects:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.editmode_toggle()
                bpy.ops.mesh.select_all(action="SELECT")
                bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((0, 0, boardThickness + 2e-3))})
                bpy.ops.object.editmode_toggle()
                obj.location.z = -1e-3   # -1mm to 2.6mm if board thinkness is 1.6mm

