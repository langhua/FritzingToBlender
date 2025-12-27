import bpy 
from bpy.types import Operator
from io_fritzing.svg.report import importdata, update as update_report
from lxml import etree # type: ignore
import os
from io_curve_svg.svg_util import units, read_float
from mathutils import Matrix
import time

fritzingPcbCollectionName = 'fritzing_pcb'

class ImportSingleSVG(Operator):
    bl_idname = "fritzing.import_single_svg"
    bl_label = "Import a single Fritzing Gerber svg file"
    
    def execute(self, context):
        try:
            layerClass = next(iter(importdata.filenames))
            filename = importdata.filenames[layerClass]
            importdata.current_file = filename
            if context and hasattr(context.scene, 'progress_indicator_text'):
                setattr(context.scene, 'progress_indicator_text', bpy.app.translations.pgettext('Importing ') + filename[filename.rindex(os.path.sep[0]) + 1 :])
            layer = import_svg(layerClass=layerClass, file=filename)
            if layer is not None:
                importdata.svgLayers[layerClass] = layer
            else:
                print(f"Error importing {layerClass}, try again...")

            # remove outline in drill
            if layerClass == 'drill':
                i = 0
                # generally, a rect outline has 4 curves(lines), so the last 4 curves are removed
                if layer:
                    total_obj = len(getattr(layer, 'all_objects')) - 4
                    bpy.ops.object.select_all(action='DESELECT')
                    for obj in getattr(layer, 'all_objects'):
                        if i >= total_obj:
                            obj.select_set(True)
                        i += 1
                    bpy.ops.object.delete()

                    # zoom in by drill layer seems more suitable than other layer
                    for obj in getattr(layer, 'all_objects'):
                        obj.select_set(True)
                    if bpy.context:
                        for area in bpy.context.screen.areas:
                            if area.type == 'VIEW_3D':
                                with bpy.context.temp_override(area=area, region=area.regions[-1]):
                                    bpy.ops.view3d.view_selected()
                        bpy.ops.object.select_all(action='DESELECT')

            importdata.filenames.pop(layerClass)
            importdata.current = importdata.current + 1
        except Exception as e:
            print('--ImportSingleSVG exception: ' + str(e))
            if str(e) != '':
                print('--ImportSingleSVG exception: ' + str(e))
                importdata.error_msg = str(e)
                getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")

            # all svg imported
            if len(importdata.filenames) == 0:
                importdata.step_name = 'POST_REMOVE_EXTRA_VERTS'

        return {"FINISHED"}


##
# Brings in the SVG file, applies the x and y orientation, converts the curves to meshes, scales it to 1 millimeter in blender equals 1 millimeter in the real world, and places the objects into a collection ... \(still to come: extrusions, height placement, cut the holes, and join a copy into a completed version\)\n
# Uses Blender 4.2 or higher API
#
# @param layerClass - the layer class from pcb-tools
# @param dir - the directory where the files are located
# @param file - the list of SVG files representing the Gerber Files / PCB
#
# @return layer - the layer objct imported
#
def import_svg(layerClass: str, file: str):
    print(f'Importing svg file: layer[{layerClass}], file[{file}]')
    # 1. deselect all
    bpy.ops.object.select_all(action='DESELECT')
    if bpy.context is None:
        return None
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'

    # 2. import the svg file and get the new curves
    start_objs = bpy.data.objects[:]
    bpy.ops.import_curve.svg(filepath=file)
    collectionName = file[file.rindex(os.path.sep[0]) + 1 :]
    bpy.data.collections[collectionName].name = fritzingPcbCollectionName + '_' + layerClass
    collectionName = fritzingPcbCollectionName + '_' + layerClass
    new_curves = [o for o in bpy.data.objects if o not in start_objs]
    if not new_curves:
        return None

    # 3. transform new curves to mesh
    boardoutline = None
    for newCurve in new_curves:
        if bpy.data.curves[newCurve.name]:
            bpy.data.curves[newCurve.name].dimensions = '3D'
        if layerClass == 'outline':
            boardoutline = newCurve
        else:
            newCurve.select_set(True)

        if layerClass == 'drill':
            bpy.context.view_layer.objects.active = newCurve
            bpy.ops.object.convert(target="MESH")

    # 4. join the new curves into one by 2 steps
    if layerClass != 'drill':
        bpy.ops.object.select_all(action='DESELECT')
        objects = bpy.data.collections[collectionName].objects
        curves = []
        for obj in objects:
            bpy.context.view_layer.objects.active = obj
            active_object = bpy.context.active_object
            if obj != boardoutline and getattr(active_object, 'type') == 'CURVE':
                obj.select_set(True)
                curves.append(obj)

        if len(curves) > 0:
            bpy.context.view_layer.objects.active = curves[0]
            bpy.ops.object.join()
        if boardoutline:
            if layerClass == 'outline':
                boardoutline.select_set(True)
                bpy.context.view_layer.objects.active = boardoutline
                bpy.ops.object.join()
            else:
                bpy.ops.object.select_all(action='DESELECT')
                boardoutline.select_set(True)
                bpy.context.view_layer.objects.active = boardoutline
                bpy.ops.object.delete(use_global=True)
                

    # 5. parse the svg file again to get right unit scale number
    root = None
    with open(file) as f:
        tree = etree.parse(parser=None, source=f)
        root = tree.getroot()
    unitscale = 1.0
    unit = ''
    if root is not None and root.attrib['height'] is not None:
        raw_height = root.attrib['height']
        token, last_char = read_float(raw_height)
        unit = raw_height[last_char:].strip()

    if unit in ('cm', 'mm', 'in', 'pt', 'pc'):
        # convert units to BU:
        unitscale = units[unit] / 90 * 1000 / 39.3701
        # apply blender unit scale:
        unitscale = bpy.context.scene.unit_settings.scale_length / unitscale

    # 6. scale the new layer
    if unitscale != 1.0:
        mat_scale = Matrix.LocRotScale(None, None, (unitscale, unitscale, unitscale))
        if layerClass == 'drill':
            fileLayerObjects = bpy.data.collections[collectionName].objects
            for obj in  fileLayerObjects:
                if isinstance(obj.data, bpy.types.Mesh):
                    obj.data.transform(mat_scale)
                    obj.scale = 1, 1, 1
        else:
            bpy.context.view_layer.objects.active = bpy.data.collections[collectionName].objects[0]
            if bpy.context.object and isinstance(bpy.context.object.data, bpy.types.Curve):
                bpy.context.object.data.transform(mat_scale)
                bpy.context.object.scale = 1, 1, 1
    
    # 7. convert curves to MESH
    if layerClass != 'drill':
        objects = bpy.data.collections[collectionName].objects
        bpy.context.view_layer.objects.active = objects[0]
        for obj in objects:
            obj.select_set(True)
        bpy.ops.object.convert(target="MESH")
        # bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

    # 8. add the imported pcb board layer to fritzing pcb layer
    layer = None
    if layerClass == 'drill':
        layer = bpy.data.collections[collectionName]
    else:
        layer = bpy.context.selected_objects[0]
        layer.name = collectionName

    # 8.2 add layer to the top pcb collection
    if fritzingPcbCollectionName not in bpy.data.collections:
        if layerClass == 'drill':
            fritzingPcbCollection = bpy.data.collections.new(fritzingPcbCollectionName)
            if isinstance(layer, bpy.types.Collection):
                bpy.data.collections[fritzingPcbCollectionName].children.link(layer)
            elif isinstance(layer, bpy.types.Object):
                fritzingPcbCollection.objects.link(layer)
        else:
            bpy.ops.object.move_to_collection(collection_index = 0, is_new = True, new_collection_name=fritzingPcbCollectionName)
    else:
        if layerClass == 'drill':
            newLayer = bpy.data.collections.new('drill')
            for obj in getattr(layer, 'all_objects'):
                newLayer.objects.link(obj)
            bpy.data.collections[fritzingPcbCollectionName].children.link(newLayer)
            layer = newLayer
        else:
            if isinstance(layer, bpy.types.Object):
                bpy.data.collections[fritzingPcbCollectionName].objects.link(layer)
            elif isinstance(layer, bpy.types.Collection):
                bpy.data.collections[fritzingPcbCollectionName].children.link(layer)

    # 9. remove the orignal collection named by file
    col = bpy.data.collections[collectionName]
    if col:
        bpy.data.collections.remove(col)
    col = bpy.data.collections[fritzingPcbCollectionName]
    if col:
        for obj in col.objects:
            obj.select_set(False)
    
    # 10. return the layer
    print('  imported')
    return layer
