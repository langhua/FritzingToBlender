import bpy

# 清理场景
def clear_scene(center_x_offset=0, center_y_offset=0):
    if bpy.context is not None and bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False, confirm=False)
            
        scene = bpy.context.scene
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.length_unit = 'MILLIMETERS'
        scene.unit_settings.scale_length = 0.001

        area_3d = None
        for area in bpy.context.screen.areas:
            if area.type == "VIEW_3D":
                area_3d = area
                break
        if area_3d:
            screen_width = area_3d.width
            screen_height = area_3d.height
            center_x = int(screen_width / 2) + center_x_offset
            center_y = int(screen_height / 2) + center_y_offset
            # Warp the cursor to the center of the 3D Viewport
            bpy.context.window.cursor_warp(center_x, center_y)

def create_lighting():
    """创建照明"""
    if bpy.context is not None:
        # 主光源
        bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
        sun = bpy.context.active_object
        if sun is not None:
            setattr(sun.data, "energy", 2.0)
        setattr(sun, "name", "Main_Sun_Light")
        
        # 填充光
        bpy.ops.object.light_add(type='AREA', location=(-10, -10, 15))
        fill_light = bpy.context.active_object
        if fill_light is not None:
            setattr(fill_light.data, "energy", 1.0)
            setattr(fill_light.data, "size", 5.0)
            fill_light.name = "Fill_Light"
    
    return sun, fill_light

def create_camera():
    """创建相机"""
    if bpy.context is not None:
        bpy.ops.object.camera_add(location=(15, -15, 10))
        camera = bpy.context.active_object
        setattr(camera, "name", "Main_Camera")
        
        # 指向场景中心
        setattr(camera, "rotation_euler", (1.047, 0, 0.785))  # 约60度俯角，45度方位角
        
        # 设置活动相机
        bpy.context.scene.camera = camera
    
    return camera
