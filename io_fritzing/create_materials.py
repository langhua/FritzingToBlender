import bpy
from .report import importdata
from bpy.types import Operator

class CreateMaterials(Operator):
    bl_idname = "fritzing.create_materials"
    bl_label = "Fritzing post import: create materials"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            for layerClass, layer in svgLayers.items():
                if layerClass == "outline":
                    create_material(layer, layerClass, (0.062, 0.296, 0.020, 0.99), 0.234, 0.235, 0.202)
                elif layerClass == 'bottomsilk':
                    create_material(layer, layerClass, (100, 100, 100, 1.0), 1, 0.5, 0.2)
                elif layerClass == "bottom":
                    create_material(layer, layerClass, (255, 180, 0, 1.0), 1, 0.5, 0.2)
                elif layerClass == "top":
                    create_material(layer, layerClass, (255, 180, 0, 1.0), 1, 0.5, 0.2)
                elif layerClass == "topsilk":
                    create_material(layer, layerClass, (100, 100, 100, 1.0), 1, 0.5, 0.2)
        except Exception as e:
            print('--CreateMaterials exception: ' + str(e))
            importdata.error_msg = str(e)
            bpy.ops.fritzing.import_error("INVOKE_DEFAULT")

        importdata.step_name = 'POST_DRILL_HOLES'
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
    for area in bpy.context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"

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
                    space.shading.type = "SOLID"
