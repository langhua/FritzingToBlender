bl_info = {
    "name": "Generate PCB Model",
    "author": "Christopher S. Francis",
    "version": (1, 0),
    "blender": (2, 80, 3),
    "location": "",
    "description": "Imports layers from a Gerber file package in SVG form and generates a model of the given PCB to allow for 3D inspection before ordering",
    "warning": "",
    "wiki_url": "",
    "category": "Add PCB Object",
}


##
# @mainpage
# @section description Description
# This module contains methods to import svg file exports from a collection of Gerber files and automatically turns the imports into a 3D model of the PCB in Blender.\n
# For putting it together and only testing so far, the PCB was designed using EasyEDA online circuit editing software. The exported Gerber files were opened in gerbv Gerber Viewer software, from which the SVG files were exported. The components of the model will be named identical to the SVG files.
# @section Author
# Developed By: Christopher S. Francis 25 June 2020 to ...


import bpy
import math
from mathutils import Vector
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty


##
# The ImportPCB class is actually just the file dialog box which has to be an object in the current API when this was written (bpy 2.8.3)\n
class ImportPCB(Operator, ImportHelper):
    bl_idname = "pcb.import_svg"
    bl_label = "Import PCB Folder"
    
    filename_ext = "."
    use_filter_folder = True
    
    
    def execute(self, context):
        filenames = []
        directory = self.properties.filepath
        cut = directory.rindex("\\")
        directory = directory[0:cut]        
        with open(directory + "\\filenames.txt", mode="r") as file:
            for line in file:
               filenames.append(line[0:-1])
                      
        for file in filenames:
            import_svg(directory, file)
        
        bpy.ops.object.select_all(action="SELECT")
        for layer in bpy.context.selected_objects:
            if layer.name != "board_outline":
                removeExtraVerts(layer)
                removeOutline(layer)
            else:
                removeExtraVerts(layer)


        extrudeLayers()
        
        apply_materials()
        
        solidify()
        
        drill()
        
        harden()

        return {"FINISHED"}


    
##
# Adds this class to the list the bpy module knows about, necessary to run it\n
# in later versions register it to whichever menu or panel it will be called from
def register():
    bpy.utils.register_class(ImportPCB)
    

##
# Removes this class from the list the bpy module knows about 
def unregister():
    bpy.utils.unregister_class(ImportPCB)
    
    

if __name__ == "__main__":
    register()
    bpy.ops.pcb.import_svg("INVOKE_DEFAULT")







##
# Turns visibility off for all objects           
def hideAll():
    for layer in bpy.data.objects:
        layer.select_set(False)
        layer.hide_set(True) 





##
# Turns on all objects which are part of the PCB, this excludes the drill_holes tool object
def revealAll():
    for layer in bpy.data.objects:
        layer.select_set(False)
        if layer.name == "drill_holes":
            layer.hide_set(True)
        else:
            layer.hide_set(False)





##
# Brings in the SVG file, applies the x and y orientation, converts the curves to meshes, scales it to 1 meter in blender equals 1 millimeter in the real world, and places the objects into a collection ... \(still to come: extrusions, height placement, cut the holes, and join a copy into a completed version\)\n
# Uses Blender 2.8.2 or higher API
# @param dir -the directory where the files are located
# @param file -the list of SVG files representing the Gerber Files / PCB
def import_svg(dir, file):
    bpy.ops.import_curve.svg(filepath=(dir + "/" + file))


    context = bpy.context
    scene = context.scene

    col = bpy.data.collections.get(file)
    if col:
        for obj in col.objects:    
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
            obj.to_mesh(preserve_all_data_layers=True)
            

    
    bpy.ops.object.join()
    layer = bpy.context.selected_objects[0]
    layer.name = file[0:-4]
    layer.scale = (2814.5, 2814.5, 2814.5)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    bpy.ops.object.convert(target="MESH") 

    
    if "layers" not in bpy.data.collections:
        bpy.ops.object.move_to_collection(collection_index = 0, is_new = True, new_collection_name="layers")
    else:
        bpy.data.collections["layers"].objects.link(layer)

    col = bpy.data.collections.get(file)
    if col:
        bpy.data.collections.remove(col)
    
    
    col = bpy.data.collections.get("layers")
    if col:
        for obj in col.objects:
            obj.select_set(False)
			


##
# Removes the overlapping vertices on all layers
def removeExtraVerts(layer):
    bpy.context.view_layer.objects.active = layer
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_mode(type="VERT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.remove_doubles()
    bpy.ops.mesh.select_all(action="DESELECT")
    bpy.ops.object.editmode_toggle()



##
# Finds the vertex closest to the origin \(that has to be in the board outline\) and removes all the vertices connected to it.
def removeOutline(layer):
    bpy.context.view_layer.objects.active = layer
    min = layer.data.vertices[0]
    minDistance = math.sqrt(min.co[0] **2 + min.co[1]**2)
    for vert in layer.data.vertices:
        vertDistance = math.sqrt(vert.co[0] **2 + vert.co[1]**2)
        if(vertDistance < minDistance):
            min = vert
            minDistance = vertDistance       
    min.select = True
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.select_linked()
    bpy.ops.mesh.delete(type="VERT")
    bpy.ops.object.editmode_toggle()
    


##
# extrudes all components and sets the vertical position of each layer
def extrudeLayers():
    bpy.ops.object.select_all(action="DESELECT")
    for layer in bpy.data.objects:
        if layer.name == "board_outline":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((0, 0, 2.4))})
            bpy.ops.object.editmode_toggle()
        elif layer.name == "bottom_solder":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.edge_face_add()
            bpy.ops.object.editmode_toggle()
            layer.location.z = -0.01
        elif layer.name == "bottom_layer":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((0, 0, 0.8))})
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.edge_face_add()
            bpy.ops.object.editmode_toggle()
            layer.location.z = 0.2
        elif layer.name == "top_layer":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((0, 0, 0.8))})
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.edge_face_add()
            bpy.ops.object.editmode_toggle()
            layer.location.z = 1.4
        elif layer.name == "top_solder":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.flip_normals()
            bpy.ops.object.editmode_toggle()
            layer.location.z = 2.41
        elif layer.name == "silk_screen":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((0.1, 0.1, 0))})
            bpy.ops.object.editmode_toggle()
            layer.location.z = 2.41
        elif layer.name == "drill_holes":
            bpy.context.view_layer.objects.active = layer
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.edge_face_add()
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.extrude_region_move(MESH_OT_extrude_region={"use_normal_flip":False, "mirror":False}, TRANSFORM_OT_translate={"value":Vector((0, 0, 2.8))})
            bpy.ops.object.editmode_toggle()
            layer.location.z = -0.2





##
# Generates a starting material \(base-color, mettalic, specular_intensity, and roughness\) for each of the layers of the PCB and applies said material\n
# Final version of project will probably have this overloaded to accept rgba values for the base colorings and tint of the metal, for now it's:\n
# green circuit board\n
# metallic trace layers and outside solder masks\n
# off-white silk-screen\n
def apply_materials():
    context = bpy.context
    scene = context.scene

    # make sure computer thinks the mouse is in the right location, avoid ...poll() errors.
    # this isn't working in a method with the enum passed in???
    for area in context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"

    
    hideAll()
        

    # loop through all objects and apply the material
    for layer in bpy.data.objects:
        if layer.name == "board_outline":
            layer.hide_set(False)
            layer.select_set(True)
            object = bpy.context.selected_objects[0]
            data = object.data
            material = bpy.data.materials.new("board")
            material.diffuse_color = (0.062, 0.296, 0.020, 0.99)
            data.materials.append(material)
            object.active_material.metallic = 0.234
            object.active_material.roughness = 0.20
            layer.select_set(False)
            layer.hide_set(True)
            
            
        elif layer.name == "bottom_solder":
            layer.hide_set(False)
            layer.select_set(True)
            object = bpy.context.selected_objects[0]
            data = object.data
            material = bpy.data.materials.new("metal")
            material.diffuse_color = (0.391, 0.521, 0.627, 1.0)
            data.materials.append(material)
            object.active_material.metallic = 0.849
            object.active_material.specular_intensity = 0.279
            object.active_material.roughness = 0.245
            layer.select_set(False)
            layer.hide_set(True)
            
            
        elif layer.name == "bottom_layer":
            layer.hide_set(False)
            layer.select_set(True)
            object = bpy.context.selected_objects[0]
            data = object.data
            material = bpy.data.materials.new("metal")
            material.diffuse_color = (0.391, 0.521, 0.627, 1.0)
            data.materials.append(material)
            object.active_material.metallic = 0.849
            object.active_material.specular_intensity = 0.279
            object.active_material.roughness = 0.245
            layer.select_set(False)
            layer.hide_set(True)
            
            
        elif layer.name == "top_layer":
            layer.hide_set(False)
            layer.select_set(True)
            object = bpy.context.selected_objects[0]
            data = object.data
            material = bpy.data.materials.new("metal")
            material.diffuse_color = (0.391, 0.521, 0.627, 1.0)
            data.materials.append(material)
            object.active_material.metallic = 0.849
            object.active_material.specular_intensity = 0.279
            object.active_material.roughness = 0.245
            layer.select_set(False)
            layer.hide_set(True)
            
            
        elif layer.name == "top_solder":
            layer.hide_set(False)
            layer.select_set(True)
            object = bpy.context.selected_objects[0]
            data = object.data
            material = bpy.data.materials.new("metal")
            material.diffuse_color = (0.391, 0.521, 0.627, 1.0)
            data.materials.append(material)
            object.active_material.metallic = 0.849
            object.active_material.specular_intensity = 0.279
            object.active_material.roughness = 0.245
            layer.select_set(False)
            layer.hide_set(True)
            
            
        elif layer.name == "silk_screen":
            layer.hide_set(False)
            layer.select_set(True)
            object = bpy.context.selected_objects[0]
            data = object.data
            material = bpy.data.materials.new("silk_screen")
            material.diffuse_color = (0.513, 0.627, 0.552, 1.0)
            data.materials.append(material)
            object.active_material.metallic = 0.234
            object.active_material.roughness = 0.20
            layer.select_set(False)
            layer.hide_set(True)
        
        
    revealAll()





##
# Applies a thickness to the 2d \(extruded along z by this point\) curves representing the traces for the top and bottom layer in the PCB
def solidify():
    context = bpy.context
    scene = context.scene

    for area in context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    space.shading.type = "SOLID"
    hideAll()


    bottom = bpy.data.objects["bottom_layer"]
    modifier = bottom.modifiers.new(name="Solidify", type="SOLIDIFY")
    modifier.thickness = 0.254
    context.view_layer.objects.active = bottom
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Solidify")
    bottom.select_set(False)



    top = bpy.data.objects["top_layer"]
    modifier = top.modifiers.new(name="Solidify", type="SOLIDIFY")
    modifier.thickness = 0.254
    context.view_layer.objects.active = top
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Solidify")
    top.select_set(False)


        
    revealAll()



##
# Creates the connection holes through the layers in the PCB
def drill():
    context = bpy.context
    scene = context.scene


    for area in context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    space.shading.type = "SOLID"



    hideAll()

    board = bpy.data.objects["board_outline"]
    modifier = board.modifiers.new(name="Boolean", type="BOOLEAN")
    modifier.object = bpy.data.objects["drill_holes"]
    context.view_layer.objects.active = board
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
    board.select_set(False)

    bSolder = bpy.data.objects["bottom_solder"]
    modifier = bSolder.modifiers.new(name="Boolean", type="BOOLEAN")
    modifier.object = bpy.data.objects["drill_holes"]
    context.view_layer.objects.active = bSolder
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
    bSolder.select_set(False)


    bottom = bpy.data.objects["bottom_layer"]
    modifier = bottom.modifiers.new(name="Boolean", type="BOOLEAN")
    modifier.object = bpy.data.objects["drill_holes"]
    context.view_layer.objects.active = bottom
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
    bottom.select_set(False)


    top = bpy.data.objects["top_layer"]
    modifier = top.modifiers.new(name="Boolean", type="BOOLEAN")
    modifier.object = bpy.data.objects["drill_holes"]
    context.view_layer.objects.active = top
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
    top.select_set(False)

    tSolder = bpy.data.objects["top_solder"]
    modifier = tSolder.modifiers.new(name="Boolean", type="BOOLEAN")
    modifier.object = bpy.data.objects["drill_holes"]
    context.view_layer.objects.active = tSolder
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
    tSolder.select_set(False)


    silk = bpy.data.objects["silk_screen"]
    modifier = silk.modifiers.new(name="Boolean", type="BOOLEAN")
    modifier.object = bpy.data.objects["drill_holes"]
    context.view_layer.objects.active = silk
    bpy.ops.object.modifier_apply(apply_as="DATA", modifier="Boolean")
    silk.select_set(False)


        
    revealAll()





##
# Duplicates all component layers in the pcb and joins them into a single object. It then moves this object out of the layers collection and into the primary collection. The single board is placed at the origin with a geometry-centralized local origin and the layered board is moved off to the side
def harden():
    context = bpy.context
    scene = context.scene

    revealAll()

    for area in context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    space.shading.type = "MATERIAL"

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.duplicate_move()
    bpy.ops.object.join()
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="MEDIAN")
    board = context.selected_objects[0]
    board.name = "PCB"
    bpy.data.collections["Collection"].objects.link(board)
    board.location = (0, 0, 0)
    bpy.ops.collection.objects_remove_active(collection="layers")
    for layer in bpy.data.objects:
        if layer.name != "PCB":
            layer.location.x += 100

