import bpy
from .report import importdata
from bpy.types import Operator
from .remove_extra_verts import removeExtraVerts

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
                    objects_to_keep = drillHoles(joined_layer, drill_layer=drill_layer, algorithm=algorithm)
                    if objects_to_keep is not None:
                        importdata.objects_to_keep = objects_to_keep
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
    objects_to_keep = []
    if bpy.context is None:
        return
    for area in bpy.context.screen.areas: 
        if area.type == "VIEW_3D":
            for space in area.spaces: 
                if space.type == "VIEW_3D":
                    setattr(getattr(space, 'shading'), 'type', "SOLID")

    if layer and drill_layer:
        vert_count_before = len(layer.data.vertices)
        if algorithm == 'AutoBoolean':
            # apply bool tool
            bpy.ops.object.select_all(action='DESELECT')
            layer.select_set(True)
            for obj in drill_layer.objects:
                obj.select_set(True)
                vert_count_before += len(obj.data.vertices)
            bpy.context.view_layer.objects.active = layer
            getattr(getattr(bpy.ops, 'object'), 'boolean_auto_difference')()
            vert_count_after = len(layer.data.vertices)
            print(f'--DrillHoles: AutoBoolean vert count before: {vert_count_before}, after: {vert_count_after}, removed: {vert_count_before - vert_count_after}')
        else:
            for obj in drill_layer.objects:
                obj_origin_dims = obj.dimensions.copy()
                try:
                    modifier = layer.modifiers.new(name="Boolean", type="BOOLEAN")
                    modifier.object = obj
                    bpy.context.view_layer.objects.active = layer
                    bpy.ops.object.modifier_apply(modifier="Boolean")
                
                    if modifier.name in obj.modifiers:
                        print(f"--DrillHoles: BooleanModifier failed on object {obj.name}")
                        objects_to_keep.append(obj)
                    elif obj_origin_dims != obj.dimensions:
                        print(f"--DrillHoles: BooleanModifier error on object {obj.name}:{obj_origin_dims} != {obj.dimensions}")
                        objects_to_keep.append(obj)

                except Exception as e:
                    print(f'--DrillHoles: BooleanModifier failed on object {obj.name} with error: {str(e)}')
                    if str(e).find("'utf-8' codec can't decode byte") != -1:
                        # 修复对象编码问题
                        fix_object_encoding(obj)
                        try:
                            modifier = layer.modifiers.new(name="Boolean", type="BOOLEAN")
                            modifier.object = obj
                            bpy.context.view_layer.objects.active = layer
                            bpy.ops.object.modifier_apply(modifier="Boolean")
                        
                            if modifier.name in obj.modifiers:
                                print(f"--DrillHoles: BooleanModifier failed on object {obj.name}")
                                objects_to_keep.append(obj)
                            elif obj_origin_dims != obj.dimensions:
                                print(f"--DrillHoles: BooleanModifier error on object {obj.name}:{obj_origin_dims} != {obj.dimensions}")
                                objects_to_keep.append(obj)
                        except Exception as e2:
                            print(f'--DrillHoles: BooleanModifier retry failed on object {obj.name} with error: {str(e2)}')
                            objects_to_keep.append(obj)
                    else:
                        objects_to_keep.append(obj)
                        continue

                vert_count_after = len(layer.data.vertices)
                obj_size = max(obj.dimensions.x, obj.dimensions.y, obj.dimensions.z)
                # print(f"{obj.name}: x={obj.dimensions.x}, y={obj.dimensions.y}, z={obj.dimensions.z}, size={obj_size}")
                if vert_count_before - vert_count_after >= 0:
                    print(f'--DrillHoles: BooleanModifier vert count difference: {vert_count_before - vert_count_after}, keeping hole: {obj.name}')
                    objects_to_keep.append(obj)
                # elif obj_size > 0.002: # 2mm hole
                #     print(f'--DrillHoles: Large hole found: {obj.name} with size {obj_size}, keeping it.')
                #     objects_to_keep.append(obj)
    print(f'--DrillHoles complete: Total objects to keep: {len(objects_to_keep)}')
    return objects_to_keep

def fix_object_encoding(obj):
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
    
    # 3. 对于曲线对象，检查并修复控制点
    # if obj.type == 'CURVE':
    #     curve = obj.data
        
    #     # 进入编辑模式清理曲线
    #     bpy.context.view_layer.objects.active = obj
    #     bpy.ops.object.mode_set(mode='EDIT')
        
    #     # 选择所有控制点
    #     bpy.ops.curve.select_all(action='SELECT')
        
    #     # 清理曲线
    #     bpy.ops.curve.delete(type='VERT')
        
    #     # 返回对象模式
    #     bpy.ops.object.mode_set(mode='OBJECT')
    
    return obj
