import bpy
from io_fritzing.svg.report import importdata
from bpy.types import Operator
from mathutils import Vector

class CleanDrillHoles(Operator):
    bl_idname = "fritzing.clean_drill_holes"
    bl_label = "Fritzing post import: clean drill holes"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            drill_layer = None
            try:
                drill_layer = svgLayers['drill']
            except:
                pass

            if svgLayers and drill_layer:
                for obj in drill_layer.objects:
                    if safe_object_check(obj) is not None and obj not in importdata.objects_to_keep:
                        bpy.data.objects.remove(obj, do_unlink=True)
                if safe_object_check(drill_layer) is not None and len(drill_layer.objects) == 0:
                    bpy.data.collections.remove(drill_layer)

                if len(importdata.objects_to_keep) == 0:
                    for layer in svgLayers.values():
                        if safe_object_check(layer) is not None:
                            # 获取物体边界框
                            bbox = [layer.matrix_world @ Vector(corner) for corner in layer.bound_box]
                            # x轴最小值
                            x_min = min(v.x for v in bbox)
                            y_min = min(v.y for v in bbox)
                            # 移动到原点
                            layer.location.x -= x_min
                            layer.location.y -= y_min
                            layer.lock_scale = (True, True, True)

        except Exception as e:
            print('--CleanDrillHoles exception: ' + str(e))
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")

        importdata.step_name = 'FINISHED'
        return {"FINISHED"}

def safe_object_check(obj_or_name):
    """
    安全地获取和检查对象
    支持对象实例或对象名称
    """
    if obj_or_name is None:
        return None
    
    if isinstance(obj_or_name, str):
        # 如果是字符串，按名称查找
        if obj_or_name in bpy.data.objects:
            return bpy.data.objects[obj_or_name]
        return None
    else:
        # 如果是对象实例，检查是否有效
        try:
            # 检查是否为有效对象
            if hasattr(obj_or_name, 'name'):
                # 确保对象在数据块中
                for obj in bpy.data.objects:
                    if obj.as_pointer() == obj_or_name.as_pointer():
                        return obj
        except (ReferenceError, RuntimeError) as e:
            if "has been removed" in str(e):
                return None
            raise
    
    return None
