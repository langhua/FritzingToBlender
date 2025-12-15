import bpy
import bmesh
from mathutils import Vector
from io_fritzing.assets.commons.rounded_rect import create_rounded_rectangle
import math

def clear_scene():
    context = bpy.context
    if context is not None and hasattr(context, 'mode') and context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    scene = getattr(context, 'scene', None)
    if scene is not None:
        scene.unit_settings.system = 'METRIC'
        scene.unit_settings.length_unit = 'MILLIMETERS'

pin_width = 0.3
pin_length = 0.5
pin_height = 0.2
pin_spacing = 0.5

def create_vqfn_hr_12():
    """创建VQFN-HR-12封装模型"""
    # 创建专用集合来组织对象
    main_collection = bpy.data.collections.new("VQFN-HR-12_Components")
    scene = getattr(bpy.context, 'scene', None)
    if scene and hasattr(scene, 'collection') and hasattr(scene.collection, 'children'):
        scene.collection.children.link(main_collection)
    
    # 芯片本体尺寸 (单位: mm)
    body_length = 2.6
    body_width = 2.4
    body_height = 0.95
    
    # 创建芯片本体
    chip_body = create_chip_body(body_length, body_width, body_height)
    
    # 创建引脚（正确布局）
    pins = create_pins(body_length, body_width, body_height)
    
    # 创建表面文字标记
    text_obj = create_surface_text(body_length, body_width, body_height)

    # 创建引脚1标记
    pin1_marker_obj = create_surface_marker(Vector((-body_length/2 + pin_length/2, pin_spacing * 1.5, body_height + 0.01)))
    
    # 将所有对象添加到专用集合
    for obj in [chip_body, text_obj, pin1_marker_obj] + pins:
        if obj is not None and hasattr(obj, 'name'):
            scene = getattr(bpy.context, 'scene', None)
            if scene and hasattr(scene, 'collection') and hasattr(scene.collection, 'objects'):
                if obj.name in scene.collection.objects:
                    scene.collection.objects.unlink(obj)
            if hasattr(main_collection, 'objects'):
                main_collection.objects.link(obj)
    
    print("VQFN-HR-12封装模型创建完成！")

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
    material = create_black_plastic_material()
    if hasattr(body, 'data') and hasattr(body.data, 'materials'):
        if body.data.materials:
            body.data.materials[0] = material
        else:
            body.data.materials.append(material)
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
            material = create_metal_material()
            if hasattr(pin, 'data') and hasattr(pin.data, 'materials'):
                if pin.data.__getattribute__('materials'):
                    pin.data.__setattr__('materials', [material])
                else:
                    pin.data.__getattribute__('materials').append(material)

    return pin

def create_surface_text(length, width, height):
    """创建表面文字标记"""
    bpy.ops.object.text_add(location=(0, 0, height + 0.01))
    text_obj = getattr(bpy.context, 'active_object', None)
    if text_obj is None:
        raise RuntimeError("无法获取文字对象")
    text_obj.name = "Chip_Text"
    if hasattr(text_obj, 'data'):
        if hasattr(text_obj.data, 'body'):
            text_obj.data.body = "VQFN-HR-12"
        if hasattr(text_obj.data, 'align_x'):
            text_obj.data.align_x = 'CENTER'
        if hasattr(text_obj.data, 'align_y'):
            text_obj.data.align_y = 'CENTER'
        if hasattr(text_obj.data, 'size'):
            text_obj.data.size = 0.5
    text_obj.scale = (0.8, 0.8, 0.1)
    text_obj.rotation_euler = (0, 0, -math.pi / 2)
    # 将文字转换为网格
    bpy.ops.object.select_all(action='DESELECT')
    if hasattr(text_obj, 'select_set'):
        text_obj.select_set(True)
    view_layer = getattr(bpy.context, 'view_layer', None)
    if view_layer and hasattr(view_layer, 'objects'):
        view_layer.objects.active = text_obj
    bpy.ops.object.convert(target='MESH')
    # 设置文字材质
    material = create_white_material()
    if hasattr(text_obj, 'data') and hasattr(text_obj.data, 'materials'):
        if text_obj.data.materials:
            text_obj.data.materials[0] = material
        else:
            text_obj.data.materials.append(material)
    return text_obj

def create_surface_marker(location):
    """创建表面文字标记"""
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
    # 将文字转换为网格
    bpy.ops.object.select_all(action='DESELECT')
    if hasattr(pin1_marker_obj, 'select_set'):
        pin1_marker_obj.select_set(True)
    view_layer = getattr(bpy.context, 'view_layer', None)
    if view_layer and hasattr(view_layer, 'objects'):
        view_layer.objects.active = pin1_marker_obj
    bpy.ops.object.convert(target='MESH')
    # 设置文字材质
    material = create_white_material()
    if hasattr(pin1_marker_obj, 'data') and hasattr(pin1_marker_obj.data, 'materials'):
        if pin1_marker_obj.data.materials:
            pin1_marker_obj.data.materials[0] = material
        else:
            pin1_marker_obj.data.materials.append(material)
    return pin1_marker_obj

def create_black_plastic_material():
    """创建黑色塑料材质"""
    material = bpy.data.materials.new(name="Black_Plastic")
    material.diffuse_color = (0.05, 0.05, 0.05, 1.0)
    material.use_nodes = True
    if material.node_tree is not None and hasattr(material, 'node_tree') and hasattr(material.node_tree, 'nodes') and hasattr(material.node_tree, 'links'):
        material.node_tree.nodes.clear()
        # 添加原理化BSDF节点
        bsdf = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        # 设置塑料材质参数
        bsdf.inputs['Base Color'].__setattr__('default_value', (0.05, 0.05, 0.05, 1.0))  # 深黑色
        bsdf.inputs['Metallic'].__setattr__('default_value', 0.0)  # 非金属
        bsdf.inputs['Roughness'].__setattr__('default_value', 0.8)  # 高粗糙度，模拟塑料
        # 添加材质输出节点
        output = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)
        # 连接节点
        material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    return material

def create_metal_material():
    """创建金属材质"""
    material = bpy.data.materials.new(name="Metal")
    material.use_nodes = True

    # 设置diffuse_color，在实体模式下也能区分
    material.diffuse_color = (0.8, 0.8, 0.85, 1.0)  # 银白色

    # 清除默认节点
    if material.node_tree is not None and hasattr(material, 'node_tree') and hasattr(material.node_tree, 'nodes'):
        material.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    if material.node_tree is not None and hasattr(material, 'node_tree') and hasattr(material.node_tree, 'nodes'):
        bsdf = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
    
        # 设置金属材质参数
        bsdf.inputs['Base Color'].__setattr__('default_value', (0.8, 0.8, 0.85, 1.0))  # 银白色
        bsdf.inputs['Metallic'].__setattr__('default_value', 1.0)  # 金属材质
        bsdf.inputs['Roughness'].__setattr__('default_value', 0.2)  # 低粗糙度，光滑金属
    
        # 添加材质输出节点
        output = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)
    
        # 连接节点
        material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return material

def create_white_material():
    """创建白色材质"""
    material = bpy.data.materials.new(name="White")
    material.use_nodes = True
    
    # 设置diffuse_color，在实体模式下也能区分
    material.diffuse_color = (0.9, 0.9, 0.9, 1.0)  # 白色
    
    # 添加原理化BSDF节点
    if material.node_tree is not None and hasattr(material.node_tree, 'nodes'):  # 添加检查
        bsdf = material.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
    
        # 设置金属材质参数
        bsdf.inputs['Base Color'].__setattr__('default_value', (0.9, 0.9, 0.9, 1.0))  # 银白色
        bsdf.inputs['Roughness'].__setattr__('default_value', 0.2)  # 低粗糙度，光滑金属
        
        # 添加材质输出节点
        output = material.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (400, 0)
        
        # 连接节点
        material.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    return material

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