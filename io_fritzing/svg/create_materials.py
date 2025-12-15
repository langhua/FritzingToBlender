import bpy
from io_fritzing.svg.report import importdata
from bpy.types import Operator
from io_fritzing.svg.commondata import Board_Black, Board_Blue, Board_Green, Board_Purple, Board_Red, Board_White, Board_Yellow
from io_fritzing.svg.commondata import Copper, Copper2, Silk_Black, Silk_White, Silk_White2

class CreateMaterials(Operator):
    bl_idname = "fritzing.create_materials"
    bl_label = "Fritzing post import: create materials"
    
    def execute(self, context):
        try:
            board_color = (0, 0.435, 0.282, 0.99)
            if context and hasattr(context.scene, 'board_color_setting'):
                board_colors = [Board_Black, Board_Blue, Board_Green, Board_Purple, Board_Red, Board_White, Board_Yellow]
                board_color_setting = str(getattr(context.scene, 'board_color_setting'))
                for color in board_colors:
                    if board_color_setting == color['name']:
                        board_color = color['rgba']

            silk_color = (0.918, 0.965, 0.961, 1.0)
            if context and hasattr(context.scene, 'silk_color_setting'):
                silk_colors = [Silk_Black, Silk_White, Silk_White2]
                silk_color_setting = str(getattr(context.scene, 'silk_color_setting'))
                for color in silk_colors:
                    if silk_color_setting == color['name']:
                        silk_color = color["rgba"]

            copper_color = (1, 0.706, 0, 1.0)
            if context and hasattr(context.scene, 'copper_color_setting'):
                copper_colors = [Copper, Copper2]
                copper_color_setting = str(getattr(context.scene, 'copper_color_setting'))
                for color in copper_colors:
                    if copper_color_setting == color['name']:
                        copper_color = color["rgba"]
            
            svgLayers = importdata.svgLayers
            for layerClass, layer in svgLayers.items():
                if layerClass == "outline":
                    create_material(layer, layerClass, board_color, 0.234, 0.235, 0.202)
                elif layerClass == "topsilk" or layerClass == 'bottomsilk':
                    create_material(layer, layerClass, silk_color, 1, 0.5, 0.2)
                elif layerClass == "top" or layerClass == "bottom":
                    create_material(layer, layerClass, copper_color, 1, 0.5, 0.2)
        except Exception as e:
            print('--CreateMaterials exception: ' + str(e))
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")

        importdata.step_name = 'POST_MERGE_LAYERS'
        return {"FINISHED"}


##
# Generates a starting material \(base-color, mettalic, specular_intensity, and roughness\) for each of the layers of the PCB and applies said material\n
# @param object -the object to which the material will be applied
# @param name -string of a unique name for the material
# @param rgba -a tuple of floats representing the red-green-blue-alpha value for the base coloring
# @param metallic -a float for the percentage of metallic texture
# @param specular -a float for the percentage of specular-intensity \(reflected light\)
# @param roughness -a float for the percentage of roughness in the texture \(surface divisions for specular intensity\)
def create_material(layer, name="material_name", rgba=(0.0, 0.0, 0.0, 1.0), metallic=0.5, specular=0.5, roughness=0.5):
    # make sure computer thinks the mouse is in the right location, avoid ...poll() errors.
    if bpy.context is None:
        return
    for area in bpy.context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D" and hasattr(space, 'shading.type'):
                    setattr(getattr(space, 'shading'), 'type', "MATERIAL")

    bpy.context.view_layer.objects.active = layer
    material = bpy.data.materials.new(name)
    material.diffuse_color = rgba
    material.metallic = metallic
    material.specular_intensity = specular
    material.roughness = roughness
    layer.data.materials.append(material)
                    
    for area in bpy.context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    setattr(getattr(space, 'shading'), 'type', "SOLID")
