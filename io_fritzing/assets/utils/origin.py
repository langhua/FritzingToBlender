import bpy
import bmesh
from mathutils import Vector

# 设置原点到几何中心
def set_origin_to_geometry(obj):
    """设置原点到物体的几何中心"""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    if bpy.context:
        bpy.context.view_layer.objects.active = obj
    
    # 设置原点到几何中心
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    
    return obj

# 设置原点到底部中心
def set_origin_to_bottom(obj):
    """设置原点到物体的底部中心"""
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    if bpy.context:
        bpy.context.view_layer.objects.active = obj
    
    # 获取物体边界框
    bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    
    # 计算底部中心
    z_min = min(v.z for v in bbox)
    bottom_center = Vector((
        sum(v.x for v in bbox) / 8,
        sum(v.y for v in bbox) / 8,
        z_min
    ))
    
    # 转换为局部坐标
    bottom_center_local = obj.matrix_world.inverted() @ bottom_center
    
    # 设置3D光标到底部中心
    if bpy.context:
        bpy.context.scene.cursor.location = obj.matrix_world @ bottom_center_local
    
    # 设置原点到3D光标
    bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    
    return obj

# 自定义原点位置
def set_custom_origin(obj, origin_point_local):
    """
    设置自定义原点位置（局部坐标）
    origin_point_local: Vector，相对于物体网格的局部坐标
    """
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    if bpy.context:
        bpy.context.view_layer.objects.active = obj
    
    # 切换到编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    
    # 选中所有顶点
    bpy.ops.mesh.select_all(action='SELECT')
    
    # 移动几何体
    bm = bmesh.from_edit_mesh(obj.data)
    for vert in bm.verts:
        vert.co -= origin_point_local
    
    bmesh.update_edit_mesh(obj.data)
    
    # 切换回物体模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 更新物体位置
    offset_world = obj.matrix_world @ origin_point_local
    obj.location = offset_world
    
    return obj
