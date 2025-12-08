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

# 根据图片说明修正蜂鸣器9042的尺寸
dimensions = {
    # 主体尺寸
    'diameter': 9.0,      # 直径: 9.0mm
    'height': 4.2,        # 高度: 4.2mm
    
    # 中心发声孔尺寸
    'hole_diameter': 1.6,  # 中心孔直径: 1.6±0.2mm → 1.6mm
    'hole_depth': 2.0,     # 中心孔深度: 2mm
    
    # 引脚尺寸
    'pin_diameter': 0.8,  # 引脚直径: 假设0.8mm
    'pin_1_length': 4.0,  # 引脚1长度: 4.0mm
    'pin_2_length': 5.5,  # 引脚2长度: 5.5mm
    'pin_spacing': 5.0,   # 引脚间距: 6.0mm
    
    # 十字正极标记尺寸
    'cross_width': 1.0,        # 十字宽度
    'cross_thickness': 0.035,  # 十字厚度
    'cross_height': 0.0175,    # 十字凸起高度
    'cross_offset': 2.5,       # 十字偏移中心距离
    
    # 倒角参数
    'chamfer_size': 0.2,
    'chamfer_segments': 4,
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

def create_buzzer_9042_model():
    """创建蜂鸣器9042完整模型"""
    # 创建蜂鸣器主体
    body = create_buzzer_body()
    
    # 创建2个引脚
    pins = create_pins()
    
    # 创建顶部中心发声孔
    create_sound_hole(body)
    
    # 创建十字正极标记
    marker = create_cross_marker(body)
    
    # 确保所有修改器都被应用
    apply_all_modifiers()
    
    # 将所有对象组织到一个组合中
    collection = create_collection_and_organize(body, pins, marker)
    
    return body, pins, collection

def create_buzzer_body():
    """创建蜂鸣器主体"""
    diameter = dimensions['diameter']
    height = dimensions['height']
    
    # 创建圆柱体
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=diameter/2,
        depth=height,
        location=(0, 0, height/2)  # 将主体放在z轴中心
    )
    body = bpy.context.active_object
    body.name = "Buzzer_9042_Body"
    
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
    """创建黑色塑料材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置基础颜色
    mat.diffuse_color = (0.1, 0.1, 0.1, 1.0)  # 黑色
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
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
    
    # 设置金属色
    mat.diffuse_color = (0.85, 0.85, 0.88, 1.0)  # 银色 nodes = mat.node_tree.nodes
    mat.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.85, 0.85, 0.88, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.3
    
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_white_material(name):
    """创建白色材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)  # 纯白色
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BS
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.6
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_sound_hole(body):
    """在蜂鸣器顶部创建中心发声孔"""
    hole_diameter = dimensions['hole_diameter']
    hole_depth = dimensions['hole_depth']
    body_height = dimensions['height']
    
    # 创建圆柱体作为切割工具
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=hole_diameter/2,
        depth=hole_depth + 0.1,  # 稍微超出深度
        location=(0, 0, body_height - hole_depth/2)  # 从顶部向下
    )
    hole_cutter = bpy.context.active_object
    hole_cutter.name = "Sound_Hole_Cutter"
    
    # 为蜂鸣器主体添加布尔修改器
    bool_mod = body.modifiers.new(name="Sound_Hole", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = hole_cutter
    
    # 应用布尔修改器
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    # 删除切割工具
    bpy.ops.object.select_all(action='DESELECT')
    hole_cutter.select_set(True)
    bpy.ops.object.delete(use_global=False)

def create_pins():
    """创建2个金属引脚"""
    pins = []
    
    # 引脚间距
    pin_spacing = dimensions['pin_spacing']
    body_height = dimensions['height']
    
    # 创建下方引脚
    pin_bottom = create_single_pin(
        y_pos=-pin_spacing/2,
        pin_number=1
    )
    pins.append(pin_bottom)
    
    # 创建上方引脚
    pin_top = create_single_pin(
        y_pos=pin_spacing/2,
        pin_number=2
    )
    pins.append(pin_top)
    
    return pins

def create_single_pin(y_pos, pin_number):
    """创建单个引脚"""
    # 引脚尺寸
    pin_diameter = dimensions['pin_diameter']
    pin_length = dimensions[f'pin_{pin_number}_length']
    
    # 创建引脚圆柱体
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=pin_diameter/2,
        depth=pin_length,
        location=(0, y_pos, -pin_length/2)  # 从底部中心开始
    )
    pin = bpy.context.active_object
    pin.name = f"Pin_{pin_number}"
    
    # 设置材质
    pin.data.materials.clear()
    mat_pin = create_metal_material("Metal_Silver")
    pin.data.materials.append(mat_pin)
    
    return pin

def create_cross_marker(body):
    """在蜂鸣器顶部创建凸起的十字正极标记"""
    cross_width = dimensions['cross_width']
    cross_thickness = dimensions['cross_thickness']
    cross_height = dimensions['cross_height']
    cross_offset = dimensions['cross_offset']
    body_height = dimensions['height']
    
    # 十字标记位置（中心孔旁边）
    marker_x = 0
    marker_y = cross_offset
    marker_z = body_height  # 在顶部表面上
    
    # 创建水平条
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(marker_x, marker_y, marker_z + cross_height/2)
    )
    cross_h = bpy.context.active_object
    cross_h.name = "Cross_Marker_Horizontal"
    
    # 设置水平条尺寸
    cross_h.scale = (cross_width, cross_thickness, cross_height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 创建垂直条
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(marker_x, marker_y, marker_z + cross_height/2)
    )
    cross_v = bpy.context.active_object
    cross_v.name = "Cross_Marker_Vertical"
    
    # 设置垂直条尺寸
    cross_v.scale = (cross_thickness, cross_width, cross_height)
    bpy.ops.object.transform_apply(scale=True)

    # 创建圆环
    bpy.ops.mesh.primitive_torus_add(
        # align='WORLD',          # 对齐方式
        location=(marker_x, marker_y, marker_z + cross_height/2),
        major_radius=cross_width/2 + 0.15,
        minor_radius=cross_thickness/2,
        major_segments=48,
        minor_segments=16,
    )
    cross_circle = bpy.context.active_object
    cross_circle.name = "Cross_Marker_Circle"
    
    # 合并十字标记的两部分
    bpy.ops.object.select_all(action='DESELECT')
    cross_h.select_set(True)
    cross_v.select_set(True)
    cross_circle.select_set(True)
    bpy.context.view_layer.objects.active = cross_h
    bpy.ops.object.join()
    
    # 重命名合并后的对象
    cross_h.name = "Cross_Positive_Marker"
    
    # 设置十字标记材质
    cross_h.data.materials.clear()
    mat_cross = create_white_material("Cross_White")
    cross_h.data.materials.append(mat_cross)
    
    return cross_h

def create_collection_and_organize(body, pins, marker):
    """将所有对象组织到一个组合中"""
    # 创建新的组合
    collection = bpy.data.collections.new("Buzzer_9042")
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
    
    # 创建蜂鸣器9042模型
    body, pins, collection = create_buzzer_9042_model()
    
    # 打印规格信息
    print("蜂鸣器9042 3D模型创建完成！")
    print("=" * 60)
    print("产品信息:")
    print("  型号: 蜂鸣器9042")
    print("  类型: 无源直插式蜂鸣器")
    print("  工作频率: 2.7KHz")
    print("  尺寸规格: 9.0×4.2mm")
    print("")
    print("结构参数 (单位:mm):")
    print(f"  主体直径: {dimensions['diameter']}mm")
    print(f"  主体高度: {dimensions['height']}mm")
    print(f"  中心发声孔直径: {dimensions['hole_diameter']}mm")
    print(f"  中心发声孔深度: {dimensions['hole_depth']}mm")
    print(f"  引脚直径: {dimensions['pin_diameter']}mm")
    print(f"  引脚1长度: {dimensions['pin_1_length']}mm")
    print(f"  引脚2长度: {dimensions['pin_2_length']}mm")
    print(f"  引脚间距: {dimensions['pin_spacing']}mm")
    print(f"  十字标记宽度: {dimensions['cross_width']}mm")
    print(f"  十字标记厚度: {dimensions['cross_thickness']}mm")
    print(f"  十字标记凸起高度: {dimensions['cross_height']}mm")
    print(f"  十字标记偏移中心: {dimensions['cross_offset']}mm")
    print("")
    print("模型特性:")
    print("  - 黑色塑料主体")
    print("  - 银色金属引脚")
    print("  - 顶部中心有直径1.6mm、深2mm的发声孔")
    print("  - 顶部有凸起的白色十字正极标记")
    print("  - 符合无源直插式蜂鸣器结构")
    print("  - 工作频率: 2.7KHz")
    print("")
    print("引脚定义:")
    print("  引脚1: 左侧引脚")
    print("  引脚2: 右侧引脚")
    print("  注意: 顶部十字标记表示正极引脚位置")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用材质预览模式
            area.spaces[0].shading.type = 'MATERIAL'
            area.spaces[0].shading.light = 'MATCAP'
#            area.spaces[0].shading.studio_light = 'default'
            # 设置背景为浅色以便观察
            area.spaces[0].shading.background_type = 'VIEWPORT'
            area.spaces[0].shading.background_color = (0.9, 0.9, 0.9)
    
    return collection

if __name__ == "__main__":
    main()