import bpy
import bmesh
from mathutils import Vector
from commons.rounded_rect import create_rounded_rectangle
import math
from ..utils.material import create_material
from ..utils.scene import clear_scene

pin_width = 0.3
pin_length = 0.5
pin_height = 0.2
pin_spacing = 0.5

def create_vqfn_hr_12(chip_name = 'VQFN-HR-12'):
    """创建VQFN-HR-12封装模型"""
    # 芯片本体尺寸 (单位: mm)
    body_length = 2.6
    body_width = 2.4
    body_height = 0.95
    
    # 创建芯片本体
    chip_body = create_chip_body(body_length, body_width, body_height)
    
    # 创建引脚（正确布局）
    pins = create_pins(body_length, body_width, body_height)
    
    # 创建表面文字标记
    text_obj = create_surface_text(chip_name, body_width, body_height)

    # 创建引脚1标记
    pin1_marker_obj = create_pin1_marker(Vector((-body_length/2 + pin_length/2, pin_spacing * 1.5, body_height + 0.01)))
    
    if chip_body is not None:
        bpy.ops.object.select_all(action='DESELECT')
        chip_body.select_set(True)
        text_obj.select_set(True)
        pin1_marker_obj.select_set(True)
        for obj in pins:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = chip_body
        bpy.ops.object.join()
        chip_body.name = 'VQFN-HR-12_Package'
    
    # print("VQFN-HR-12封装模型创建完成！")
    return chip_body

def create_chip_body(length, width, height):
    """创建芯片本体"""
    bpy.ops.mesh.primitive_cube_add(location=(0, 0, height/2))
    body = getattr(bpy.context, 'active_object', None)
    if body is None:
        raise RuntimeError("无法获取芯片本体对象")
    body.name = "VQFN-HR-12_Package"
    body.scale = (length/2, width/2, height/2)
    # 添加圆角效果
    if hasattr(body, 'modifiers'):
        bevel_modifier = body.modifiers.new(name="Bevel", type='BEVEL')
        if hasattr(bevel_modifier, 'width'):
            bevel_modifier.width = 0.04
        if hasattr(bevel_modifier, 'segments'):
            bevel_modifier.segments = 10
        # 应用修改器
        bpy.ops.object.select_all(action='DESELECT')
        if hasattr(body, 'select_set'):
            body.select_set(True)
        view_layer = getattr(bpy.context, 'view_layer', None)
        if view_layer and hasattr(view_layer, 'objects'):
            view_layer.objects.active = body
        bpy.ops.object.modifier_apply(modifier=bevel_modifier.name)
        
    # 设置材质
    material = create_material(name = "VQFN-HR-12_Chip_Body", base_color = (0.05, 0.05, 0.05, 1.0), metallic = 0.0, roughness = 0.8)
    getattr(body.data, "materials").clear()
    getattr(body.data, "materials").append(material)
    return body

def create_pins(length, width, height):
    """创建引脚（修正布局，避免重复）"""
    pins = []
    
    # 左侧引脚 (4个) - 引脚1, 2, 3, 4
    left_x = -length/2 + pin_length/2
    for i in range(4):
        y_pos = (1.5 - i) * pin_spacing
        pin = create_pin((left_x - 0.01, y_pos, pin_height/2), pin_length, pin_width, pin_height, i+1, 'bottom')
        if pin is not None:  # 添加空值检查
            pin.rotation_euler = (0, 0, math.pi/2)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            pins.append(pin)

    # 底边引脚 (2个) - 引脚5, 6
    bottom_y = - width/2 + pin_length/2
    pin5 = create_pin((-pin_spacing/2, bottom_y - 0.01, pin_height/2), pin_length, pin_width, pin_height, 5, 'top')
    pin6 = create_pin((pin_spacing/2, bottom_y - 0.01, pin_height/2), pin_length, pin_width, pin_height, 6, 'top')
    if pin5 is not None:  # 添加空值检查
        pins.append(pin5)
    if pin6 is not None:  # 添加空值检查
        pins.append(pin6)
    
    # 右侧引脚 (4个) - 引脚7, 8, 9, 10
    right_x = length/2 - pin_length/2
    for i in range(4):
        y_pos = (-1.5 + i) * pin_spacing
        pin = create_pin((right_x + 0.01, y_pos, pin_height/2), pin_length, pin_width, pin_height, i+7, 'top')
        if pin is not None:  # 添加空值检查
            pin.rotation_euler = (0, 0, math.pi/2)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            pins.append(pin)

    # 顶边引脚 (2个) - 引脚11, 12（修复：确保有引脚12）
    top_y = width/2 - pin_length/2
    pin11 = create_pin((pin_spacing/2, top_y + 0.01, pin_height/2), pin_length, pin_width, pin_height, 11, 'bottom')
    pin12 = create_pin((-pin_spacing/2, top_y + 0.01, pin_height/2), pin_length, pin_width, pin_height, 12, 'bottom')
    if pin11 is not None:  # 添加空值检查
        pins.append(pin11)
    if pin12 is not None:  # 添加空值检查
        pins.append(pin12)
    
    return pins

def create_pin(position, width, length, height, pin_number, rounded_corners):
    """创建单个引脚"""
    x, y, z = position

    if pin_number == 1:
        bpy.ops.mesh.primitive_cube_add(location=(x, y, z - 0.05))
        pin = getattr(bpy.context, 'active_object', None)
        if pin is None:
            raise RuntimeError(f"无法获取引脚{pin_number}对象")
        pin.scale = (length/2, width/2, height/2)
        pin.location = (x, y, z - 0.05)
    else:
        # 引脚1为长方体，其他为圆角矩形
        pin = create_rounded_rectangle(pin_number, length, width, height, length * 0.45, 16, rounded_corners)
        if pin is not None:
            pin.location = (x, y, z - 0.15)
    if pin is not None:
        pin.name = f"Pin_{pin_number}"
        # 设置材质
        if pin.type == 'MESH':  # 添加类型检查
            material = create_material(name="Metal", base_color = (0.8, 0.8, 0.85, 1.0), metallic = 1.0, roughness = 0.2)
            getattr(pin.data, "materials").clear()
            getattr(pin.data, "materials").append(material)

    return pin

def create_surface_text(chip_name, chip_width, height):
    """创建表面文字标记"""
    bpy.ops.object.text_add(location=(0, 0, height + 0.01))
    text_obj = getattr(bpy.context, 'active_object', None)
    if text_obj is None:
        raise RuntimeError("无法获取文字对象")
    text_obj.name = "Chip_Text"
    if hasattr(text_obj, 'data'):
        if hasattr(text_obj.data, 'body'):
            text_obj.data.body = chip_name
        if hasattr(text_obj.data, 'align_x'):
            text_obj.data.align_x = 'CENTER'
        if hasattr(text_obj.data, 'align_y'):
            text_obj.data.align_y = 'CENTER'
        if hasattr(text_obj.data, 'size'):
            text_obj.data.size = 0.5
    # 转换为网格
    bpy.ops.object.convert(target='MESH')
    
    # 缩放文本以适应主体
    if text_obj.dimensions.x > chip_width:
        
        text_obj.scale = (chip_width / text_obj.dimensions.x * 0.8, 0.8, 0.1)
    else:
        text_obj.scale = (0.8, 0.8, 0.1)
    bpy.ops.object.transform_apply(scale=True)
        
    # text_obj.rotation_euler = (0, 0, -math.pi / 2)
    # 将文字转换为网格
    bpy.ops.object.select_all(action='DESELECT')
    if hasattr(text_obj, 'select_set'):
        text_obj.select_set(True)
    view_layer = getattr(bpy.context, 'view_layer', None)
    if view_layer and hasattr(view_layer, 'objects'):
        view_layer.objects.active = text_obj
    bpy.ops.object.convert(target='MESH')

    # 设置文字材质
    material = create_material(name="White", base_color = (0.9, 0.9, 0.9, 1.0), metallic = 0.0, roughness = 0.2)
    getattr(text_obj.data, "materials").clear()
    getattr(text_obj.data, "materials").append(material)

    return text_obj

def create_pin1_marker(location):
    """创建引脚1标记"""
    bpy.ops.object.text_add(location=location)
    pin1_marker_obj = getattr(bpy.context, 'active_object', None)
    if pin1_marker_obj is None:
        raise RuntimeError("无法获取文字对象")
    pin1_marker_obj.name = "Pin1_Marker"
    if hasattr(pin1_marker_obj, 'data'):
        if hasattr(pin1_marker_obj.data, 'body'):
            pin1_marker_obj.data.body = "●"
        if hasattr(pin1_marker_obj.data, 'align_x'):
            pin1_marker_obj.data.align_x = 'CENTER'
        if hasattr(pin1_marker_obj.data, 'align_y'):
            pin1_marker_obj.data.align_y = 'CENTER'
        if hasattr(pin1_marker_obj.data, 'size'):
            pin1_marker_obj.data.size = 0.3
    pin1_marker_obj.scale = (0.8, 0.8, 0.1)

    # 将标记转换为网格
    bpy.ops.object.select_all(action='DESELECT')
    if hasattr(pin1_marker_obj, 'select_set'):
        pin1_marker_obj.select_set(True)
    view_layer = getattr(bpy.context, 'view_layer', None)
    if view_layer and hasattr(view_layer, 'objects'):
        view_layer.objects.active = pin1_marker_obj
    bpy.ops.object.convert(target='MESH')

    # 设置标记材质
    material = create_material(name="White", base_color = (0.9, 0.9, 0.9, 1.0), metallic = 0.0, roughness = 0.2)
    getattr(pin1_marker_obj.data, "materials").clear()
    getattr(pin1_marker_obj.data, "materials").append(material)

    return pin1_marker_obj

# 执行创建函数
if __name__ == "__main__":
    context = bpy.context
    if context is not None:  # 添加上下文检查
        active_object = getattr(context, 'active_object', None)
        if active_object is not None and hasattr(active_object, 'mode') and active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    
    create_vqfn_hr_12()

def main():
    # 清理场景
    clear_scene()
    
    # 创建模型
    create_vqfn_hr_12()
    
    print("VQFN-HR-12模型创建完成！")

if __name__ == "__main__":
    main()