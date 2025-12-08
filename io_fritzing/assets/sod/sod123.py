import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# 清理场景
def clear_scene():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'

# 根据设计图定义SOD-123参数（取中值）
dimensions = {
    # 本体尺寸
    'body_length': 2.7,       # 本体长度: 2.7±0.2 → 2.7mm
    'body_width': 1.8,        # 本体宽度: 1.8±0.2 → 1.8mm
    'body_height': 1.1,       # 本体高度: 1.1±0.25 → 1.1mm
    
    # 引脚尺寸
    'pin_length': 0.6,        # 引脚长度（X方向）: 0.6±0.25 → 0.6mm
    'pin_width': 1.0,         # 引脚宽度（Y方向）: 1.0±0.2 → 1.0mm
    'pin_thickness': 0.2,     # 引脚厚度（Z方向）: 0.1-0.3mm，取中值0.2mm
    
    # 总长度
    'total_length': 3.7,       # 总长度: 3.7±0.2 → 3.7mm
    
    # 倒角参数
    'chamfer_size': 0.05,
    'chamfer_segments': 8,
}

def apply_all_modifiers(obj=None):
    """应用所有修改器"""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    if obj:
        objects = [obj]
    else:
        objects = bpy.context.scene.objects
    
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        for modifier in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except:
                obj.modifiers.remove(modifier)

def create_sod123_model():
    """创建SOD-123完整模型"""
    # 创建芯片主体
    body = create_chip_body()
    
    # 创建2个引脚
    pins = create_pins()
    
    # 创建白色标记
    marker = create_marking(body)
    
    # 确保所有修改器都被应用
    apply_all_modifiers()
    
    # 将所有对象组织到一个组合中
    collection = create_collection_and_organize(body, pins, marker)
    
    return body, pins, collection

def create_chip_body():
    """创建芯片主体"""
    length = dimensions['body_length']  # 2.7mm
    width = dimensions['body_width']    # 1.0mm
    height = dimensions['body_height']  # 1.8mm
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2)
    )
    body = bpy.context.active_object
    body.name = "SOD-123_Body"
    
    # 设置尺寸
    body.scale = (length, width, height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 添加倒角修改器
    bevel_mod = body.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = dimensions['chamfer_size']
    bevel_mod.segments = dimensions['chamfer_segments']
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 应用修改器
    apply_all_modifiers(body)
    
    # 设置材质
    body.data.materials.clear()
    mat_body = create_plastic_material("Plastic_Black")
    body.data.materials.append(mat_body)
    
    return body

def create_plastic_material(name):
    """创建塑料材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = (0.05, 0.05, 0.05, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_metal_material(name):
    """创建金属材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = (0.8, 0.8, 0.85, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.85, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.2
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_white_material(name):
    """创建白色标记材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.6
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_pins():
    """创建2个对称引脚"""
    pins = []
    
    # 创建左侧引脚
    pin_left = create_single_pin(side='left')
    pins.append(pin_left)
    
    # 创建右侧引脚
    pin_right = create_single_pin(side='right')
    pins.append(pin_right)
    
    return pins

def create_single_pin(side='left'):
    """创建单个引脚"""
    # 引脚尺寸
    pin_length = dimensions['pin_length']
    pin_width = dimensions['pin_width']
    pin_thickness = dimensions['pin_thickness']
    
    pin_x = dimensions['total_length'] / 2 - pin_length / 2
    if side == 'left':
        pin_x = -pin_x

    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(pin_x, 0, pin_thickness/2)
    )
    pin = bpy.context.active_object
    if side == 'left':
        pin.name = "Pin_Cathode"
    elif side == 'right':
        pin.name = "Pin_Anode"
    else:
        pin.name = "Pin_Unknown"
    
    # 设置尺寸
    pin.scale = (pin_length, pin_width, pin_thickness)
    bpy.ops.object.transform_apply(scale=True)
    
    # bpy.context.collection.objects.link(pin)
    
    # 为引脚添加倒角
    bevel_mod = pin.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = 0.02
    bevel_mod.segments = 4
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 应用修改器
    bpy.ops.object.select_all(action='DESELECT')
    pin.select_set(True)
    bpy.context.view_layer.objects.active = pin
    bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    
    # 设置材质
    pin.data.materials.clear()
    mat_pin = create_metal_material("Metal_Silver")
    pin.data.materials.append(mat_pin)
    
    return pin

def create_marking(body):
    """在主体上创建白色极性标记"""
    # 标记尺寸
    mark_length = dimensions['body_length'] * 0.2
    mark_width = dimensions['body_width'] - dimensions['chamfer_size'] * 2
    
    # 位置（在主体顶部中心）
    mark_x = -dimensions['body_length'] / 2 + mark_length / 2 + 0.1
    mark_y = 0
    mark_z = dimensions['body_height'] - 0.01
    
    # 创建标记平面
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(mark_x, mark_y, mark_z)
    )
    marking = bpy.context.active_object
    marking.name = "SOD-123_Marking"
    
    # 缩放标记
    marking.scale = (mark_length, mark_width, 0.035)
    bpy.ops.object.transform_apply(scale=True)
    
    # 旋转标记使其与主体顶部平行
    marking.rotation_euler = (0, 0, 0)
    
    # 设置材质
    marking.data.materials.clear()
    mat_marking = create_white_material("Marking_White")
    marking.data.materials.append(mat_marking)
    
    return marking

def create_collection_and_organize(body, pins, marker):
    """将所有对象组织到一个组合中"""
    # 创建新的组合
    collection = bpy.data.collections.new("SOD-123_Package")
    bpy.context.scene.collection.children.link(collection)
    
    # 收集所有对象
    objects_to_move = [body]
    objects_to_move.extend(pins)
    objects_to_move.append(marker)
    
    # 从主场景移除并添加到新组合
    for obj in objects_to_move:
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
        collection.objects.link(obj)
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects_to_move:
        obj.select_set(True)
    
    return collection

def main():
    """主函数"""
    # 清理场景
    clear_scene()
    
    # 创建SOD-123封装模型
    body, pins, collection = create_sod123_model()
    
    # 打印尺寸信息
    print("SOD-123封装模型创建完成！")
    print(f"主体尺寸: {dimensions['body_length']} x {dimensions['body_width']} x {dimensions['body_height']} mm")
    print(f"总长度: {dimensions['total_length']} mm")
    print(f"引脚宽度: {dimensions['pin_width']} mm")
    print(f"引脚厚度: {dimensions['pin_thickness']} mm")
    print("模型包含白色标记，符合实物特征")
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].shading.type = 'MATERIAL'
    
    return collection

if __name__ == "__main__":
    main()