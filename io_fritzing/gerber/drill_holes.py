import bpy
from io_fritzing.gerber.report import importdata
from bpy.types import Operator
import time
import bmesh


class GerberDrillHoles(Operator):
    bl_idname = "fritzing.gerber_drill_holes"
    bl_label = "Fritzing Gerber post import: drill holes"
    
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
                if context and hasattr(context.scene, 'gerber_drill_algorithm_setting'):
                    algorithm = str(getattr(context.scene, 'gerber_drill_algorithm_setting'))
                if algorithm == 'AutoBoolean' and not hasattr(bpy.ops.object, 'boolean_auto_difference'):
                    raise Exception('Auto Boolean requires the "Bool Tool" addon.')
                if algorithm == 'NonDestructiveDifference' and not hasattr(bpy.ops.object, 'booltron_nondestructive_difference'):
                    raise Exception('Non Destructive Difference requires the "Booltron" addon.')
                if drill_layer and joined_layer:
                    self.drillHoles(context, joined_layer, drill_layer=drill_layer, algorithm=algorithm)
        except Exception as e:
            print('--DrillHoles exception: ' + str(e))
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'gerber_import_error')("INVOKE_DEFAULT")

        # importdata.step_name = 'POST_GERBER_CLEAN_DRILL'
        importdata.step_name = 'FINISHED'
        return {"FINISHED"}


    ##
    # Creates a drill hole through an individual layer of the PCB
    # @param layer_name -the layer to drill holes in
    def drillHoles(self, context, layer, drill_layer, algorithm):
        if context is None:
            return
        
        self.refresh_3d(context)

        time_start = time.time()

        cylinder_filter_setting = float(context.scene.gerber_cylinder_filter_setting)
        if cylinder_filter_setting == None:
            cylinder_filter_setting = 0.0
        
        if layer and drill_layer:
            if algorithm == 'AutoBoolean':
                # apply bool tool
                bpy.ops.object.select_all(action='DESELECT')
                layer.select_set(True)
                for obj in drill_layer.objects:
                    if obj.type == 'MESH' and pass_filtered(obj, cylinder_filter_setting):
                        print(f'Drilling hole: {obj.name}')
                        obj.select_set(True)
                        context.view_layer.objects.active = layer
                        getattr(bpy.ops.object, 'boolean_auto_difference')("INVOKE_DEFAULT")
                        self.refresh_3d(context)
                print(f'📊 AutoBoolean done in {time.time() - time_start:.2f}s')
            elif algorithm == 'NonDestructiveDifference':
                # apply bool tool
                bpy.ops.object.select_all(action='DESELECT')
                layer.select_set(True)
                if bpy.context:
                    setattr(getattr(context.window_manager, 'booltron'), 'non_destructive.solver', 'EXACT')
                for obj in drill_layer.objects:
                    if obj.type == 'MESH' and pass_filtered(obj, cylinder_filter_setting):
                        print(f'Drilling hole: {obj.name}')
                        obj.select_set(True)
                        layer.select_set(True)
                        context.view_layer.objects.active = layer
                        getattr(bpy.ops.object, 'booltron_nondestructive_difference')()
                        self.refresh_3d(context)
                print(f'📊 NonDestructiveDifference done in {time.time() - time_start:.2f}s')
            elif algorithm == 'BooleanModifier':
                objects_to_remove = []
                for obj in drill_layer.objects:
                    if obj.type == 'MESH' and pass_filtered(obj, cylinder_filter_setting):
                        bpy.ops.object.select_all(action='DESELECT')
                        print(f'Drilling hole: {obj.name}')
                        modifier = layer.modifiers.new(name="Drill_Boolean", type="BOOLEAN")
                        modifier.object = obj
                        context.view_layer.objects.active = layer
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                        self.refresh_3d(context)
                        objects_to_remove.append(obj)

                bpy.ops.object.select_all(action='DESELECT')
                for obj in objects_to_remove:
                    bpy.data.objects.remove(obj, do_unlink=True)

                    # try:
                    # except Exception as e:
                        # print(f'--DrillHoles: BooleanModifier failed on object {obj.name} with error: {str(e)}')
                        # if str(e).find("'utf-8' codec can't decode byte") != -1:
                        #     # Fix object encoding issue
                        #     self.fix_object_encoding(obj)
                        #     try:
                        #         modifier = layer.modifiers.new(name="Boolean", type="BOOLEAN")
                        #         modifier.object = obj
                        #         bpy.context.view_layer.objects.active = layer
                        #         bpy.ops.object.modifier_apply(modifier=modifier.name)
                        #     except Exception as e2:
                        #         print(f'--DrillHoles: BooleanModifier retry failed on object {obj.name} with error: {str(e2)}')
                        #         objects_to_keep.append(obj)
                        # else:
                        #     objects_to_keep.append(obj)
                        # pass
                print(f'📊 BooleanModifier done in {time.time() - time_start:.2f}s')


    def fix_object_encoding(self, obj):
        """Fix object encoding issues"""
        # 1. Rename the object (remove illegal characters)
        safe_name = obj.name.encode('ascii', 'ignore').decode('ascii')
        if safe_name and safe_name != obj.name:
            print(f"Renaming object: {obj.name} -> {safe_name}")
            obj.name = safe_name
        
        # 2. Rename the data block
        if obj.data:
            safe_data_name = obj.data.name.encode('ascii', 'ignore').decode('ascii')
            if safe_data_name != obj.data.name:
                print(f"Renaming data block: {obj.data.name} -> {safe_data_name}")
                obj.data.name = safe_data_name
        
        return obj

    def refresh_3d(self, context):
        areas = context.window.screen.areas
        for area in areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

def pass_filtered(obj, cylinder_filter_setting):
    if len(importdata.diameter_summary) == 0:
        if obj.dimensions.x >= cylinder_filter_setting:
            return True
    elif importdata.diameter_summary[obj.name]['diameter'] >= cylinder_filter_setting:
        return True
    return False
