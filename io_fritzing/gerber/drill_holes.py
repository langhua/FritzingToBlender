import bpy
from io_fritzing.gerber.report import importdata
from bpy.types import Operator
import time
import bmesh
import gc


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
                if context and hasattr(context.scene, 'drill_algorithm_setting'):
                    algorithm = str(getattr(context.scene, 'drill_algorithm_setting'))
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
    # creates a drill hole through an individual layer of the pcb
    # @param layer_name -the layer to drill the holes in
    def drillHoles(self, context, layer, drill_layer, algorithm):
        if context is None:
            return
        
        self.refresh_3d(context)

        time_start = time.time()
        if layer and drill_layer:
            if algorithm == 'AutoBoolean':
                # apply bool tool
                bpy.ops.object.select_all(action='DESELECT')
                layer.select_set(True)
                i = 0
                for obj in drill_layer.objects:
                    if obj.type == 'MESH' and obj.dimensions.x > 0.001:
                        print(f'----{obj.name}')
                        obj.select_set(True)
                        i += 1
                        if i % 10 == 0:
                            i = 0
                            context.view_layer.objects.active = layer
                            bpy.ops.object.boolean_auto_difference()
                            self.refresh_3d(context)
                            # 强制垃圾回收
                            gc.collect()
                if i > 0:
                    context.view_layer.objects.active = layer
                    bpy.ops.object.boolean_auto_difference()
                    self.refresh_3d(context)
                    # 强制垃圾回收
                    gc.collect()
                print(f'📊 AutoBoolean done in {time.time() - time_start:.2f}s')
            else:
                i = 0
                for obj in drill_layer.objects:
                    if obj.type == 'MESH' and obj.dimensions.x > 0.001:
                        print(f'----{obj.name}')
                        modifier = layer.modifiers.new(name="Drill_Boolean", type="BOOLEAN")
                        modifier.object = obj
                        bpy.ops.object.modifier_apply(modifier=modifier.name)
                        i += 1
                        if i % 10 == 0:
                            self.refresh_3d(context)
                            # 强制垃圾回收
                            gc.collect()
                            i = 0

                if i > 0:
                    # 强制垃圾回收
                    gc.collect()

                bpy.ops.object.select_all(action='DESELECT')

                    # try:
                    # except Exception as e:
                        # print(f'--DrillHoles: BooleanModifier failed on object {obj.name} with error: {str(e)}')
                        # if str(e).find("'utf-8' codec can't decode byte") != -1:
                        #     # 修复对象编码问题
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
        """修复对象的编码问题"""
        # 1. 重命名对象（清除非法字符）
        safe_name = obj.name.encode('ascii', 'ignore').decode('ascii')
        if safe_name and safe_name != obj.name:
            print(f"重命名对象: {obj.name} -> {safe_name}")
            obj.name = safe_name
        
        # 2. 重命名数据块
        if obj.data:
            safe_data_name = obj.data.name.encode('ascii', 'ignore').decode('ascii')
            if safe_data_name != obj.data.name:
                print(f"重命名数据块: {obj.data.name} -> {safe_data_name}")
                obj.data.name = safe_data_name
        
        return obj

    def refresh_3d(self, context):
        areas = context.window.screen.areas
        for area in areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
