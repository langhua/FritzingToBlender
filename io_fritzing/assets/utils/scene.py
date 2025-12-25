import bpy

# 清理场景
def clear_scene():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
        
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001

def create_lighting():
    """创建照明"""
    # 主光源
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    sun.name = "Main_Sun_Light"
    
    # 填充光
    bpy.ops.object.light_add(type='AREA', location=(-10, -10, 15))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 1.0
    fill_light.data.size = 5.0
    fill_light.name = "Fill_Light"
    
    return sun, fill_light

def create_camera():
    """创建相机"""
    bpy.ops.object.camera_add(location=(15, -15, 10))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    
    # 指向场景中心
    camera.rotation_euler = (1.047, 0, 0.785)  # 约60度俯角，45度方位角
    
    # 设置活动相机
    bpy.context.scene.camera = camera
    
    return camera
