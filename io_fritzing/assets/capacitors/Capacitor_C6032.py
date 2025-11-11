import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# 清理默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# 获取当前场景
scene = bpy.context.scene
# 设置单位系统为公制
scene.unit_settings.system = 'METRIC'
# 设置长度单位为毫米
scene.unit_settings.length_unit = 'MILLIMETERS'
# 确保缩放比例为 1（1米 = 1000毫米）
scene.unit_settings.scale_length = 0.001

# 定义常见贴片钽电容封装尺寸（单位：毫米）
TANTALUM_SIZES = {
    'A3216': {'length': 3.2, 'width': 1.6, 'height': 1.6, 'terminal_width': 1.2, 'extension_length': 0.8},
    'B3528': {'length': 3.5, 'width': 2.8, 'height': 1.9, 'terminal_width': 2.2, 'extension_length': 0.8},
    'C6032': {'length': 6.0, 'width': 3.2, 'height': 2.2, 'terminal_width': 2.2, 'extension_length': 1.3},
    'D7343': {'length': 7.3, 'width': 4.3, 'height': 2.5, 'terminal_width': 2.4, 'extension_length': 1.3},
    'E7343H': {'length': 7.3, 'width': 4.3, 'height': 4.0, 'terminal_width': 2.4, 'extension_length': 1.3},
    'V7343': {'length': 7.3, 'width': 4.3, 'height': 2.5, 'terminal_width': 3.1, 'extension_length': 1.4}
}

def create_tantalum_material(name, base_color, metallic=0.0, roughness=0.8):
    """创建钽电容材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    rgba_color = (*base_color, 1.0)
    mat.diffuse_color = rgba_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = rgba_color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_extension_fixed_tantalum_capacitor(size_name='C6032'):
    """创建延伸板长度修正的贴片钽电容3D模型"""
    if size_name not in TANTALUM_SIZES:
        size_name = 'C6032'
    
    dimensions = TANTALUM_SIZES[size_name]
    length = dimensions['length']
    width = dimensions['width']
    height = dimensions['height']
    terminal_width = dimensions['terminal_width']
    extension_length = dimensions['extension_length']  # 延伸板长度从字典获取
    
    print(f"调试信息：延伸板长度 = {extension_length}mm")  # 添加调试信息
    
    # 焊端参数
    terminal_length = length * 0.02
    terminal_thickness = 0.1
    
    # 电容体参数
    body_length = length * 0.98
    body_width = width * 0.9
    body_height = height * 0.9
    
    # 创建集合
    collection_name = f"Tantalum_Capacitor_{size_name}_Extension_Fixed"
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    
    # 创建材质
    body_mat = create_tantalum_material("Tantalum_Body", (0.6, 0.5, 0.3), metallic=0.0, roughness=0.8)
    terminal_mat = create_tantalum_material("Terminal_Metal", (0.9, 0.9, 0.92), metallic=0.9, roughness=0.2)
    marking_mat = create_tantalum_material("Polarity_Marking", (0.9, 0.9, 0.9), metallic=0.0, roughness=0.9)
    
    # 1. 创建钽电容体
    bm_body = bmesh.new()
    body_size = Vector((body_length, body_width, body_height))
    bmesh.ops.create_cube(bm_body, size=1.0)
    for v in bm_body.verts:
        v.co = v.co * body_size
    
    mesh_body = bpy.data.meshes.new("Tantalum_Body")
    bm_body.to_mesh(mesh_body)
    obj_body = bpy.data.objects.new("Tantalum_Body", mesh_body)
    collection.objects.link(obj_body)
    obj_body.data.materials.append(body_mat)
    
    # 2. 创建正极焊端
    bm_positive_terminal = bmesh.new()
    terminal_height = body_height / 2
    positive_terminal_size = Vector((terminal_length, terminal_width, terminal_height))
    bmesh.ops.create_cube(bm_positive_terminal, size=1.0)
    for v in bm_positive_terminal.verts:
        v.co = v.co * positive_terminal_size
        v.co.x -= (body_length + terminal_length) / 2
        v.co.z -= (body_height / 2 - terminal_height / 2)
    
    mesh_positive_terminal = bpy.data.meshes.new("Positive_Terminal")
    bm_positive_terminal.to_mesh(mesh_positive_terminal)
    obj_positive_terminal = bpy.data.objects.new("Positive_Terminal", mesh_positive_terminal)
    collection.objects.link(obj_positive_terminal)
    obj_positive_terminal.data.materials.append(terminal_mat)
    
    # 3. 创建负极焊端
    bm_negative_terminal = bmesh.new()
    negative_terminal_size = Vector((terminal_length, terminal_width, terminal_height))
    bmesh.ops.create_cube(bm_negative_terminal, size=1.0)
    for v in bm_negative_terminal.verts:
        v.co = v.co * negative_terminal_size
        v.co.x += (body_length + terminal_length) / 2
        v.co.z -= (body_height / 2 - terminal_height / 2)
    
    mesh_negative_terminal = bpy.data.meshes.new("Negative_Terminal")
    bm_negative_terminal.to_mesh(mesh_negative_terminal)
    obj_negative_terminal = bpy.data.objects.new("Negative_Terminal", mesh_negative_terminal)
    collection.objects.link(obj_negative_terminal)
    obj_negative_terminal.data.materials.append(terminal_mat)
    
    # 4. 创建极性标记
    bm_marking = bmesh.new()
    marking_length = body_width * 1  # 极性标记长度
    marking_width = body_length * 0.1
    marking_height = body_height * 0.08
    marking_size = Vector((marking_width, marking_length, marking_height))
    bmesh.ops.create_cube(bm_marking, size=1.0)
    for v in bm_marking.verts:
        v.co = v.co * marking_size
        v.co.x -= body_length * 0.5 - marking_width / 2
        v.co.z += body_height / 2 - marking_height / 2.1

    mesh_marking = bpy.data.meshes.new("Polarity_Marking")
    bm_marking.to_mesh(mesh_marking)
    obj_marking = bpy.data.objects.new("Polarity_Marking", mesh_marking)
    collection.objects.link(obj_marking)
    obj_marking.data.materials.append(marking_mat)
    
    # 5. 创建焊端延伸板
    # 正极延伸板
    bm_positive_extension = bmesh.new()
    extension_width = terminal_width
    extension_height = terminal_thickness
    positive_extension_size = Vector((extension_length, extension_width, extension_height))
    bmesh.ops.create_cube(bm_positive_extension, size=1.0)
    for v in bm_positive_extension.verts:
        v.co = v.co * positive_extension_size
        # 计算正极焊端左边缘位置
        v.co.x -= body_length / 2 - extension_length / 2 + terminal_length
        v.co.z -= (body_height / 2 + extension_height / 2)
    
    mesh_positive_extension = bpy.data.meshes.new("Positive_Extension")
    bm_positive_extension.to_mesh(mesh_positive_extension)
    obj_positive_extension = bpy.data.objects.new("Positive_Extension", mesh_positive_extension)
    collection.objects.link(obj_positive_extension)
    obj_positive_extension.data.materials.append(terminal_mat)
    
    # 负极延伸板
    bm_negative_extension = bmesh.new()
    negative_extension_size = Vector((extension_length, extension_width, extension_height))
    bmesh.ops.create_cube(bm_negative_extension, size=1.0)
    for v in bm_negative_extension.verts:
        v.co = v.co * negative_extension_size
        # 计算负极焊端右边缘位置
        v.co.x += body_length / 2 - extension_length / 2 + terminal_length
        v.co.z -= (body_height / 2 + extension_height / 2)

    
    mesh_negative_extension = bpy.data.meshes.new("Negative_Extension")
    bm_negative_extension.to_mesh(mesh_negative_extension)
    obj_negative_extension = bpy.data.objects.new("Negative_Extension", mesh_negative_extension)
    collection.objects.link(obj_negative_extension)
    obj_negative_extension.data.materials.append(terminal_mat)
    
    # 清理bmesh
    bm_body.free()
    bm_positive_terminal.free()
    bm_negative_terminal.free()
    bm_marking.free()
    bm_positive_extension.free()
    bm_negative_extension.free()
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
    
    bpy.context.view_layer.objects.active = obj_body
    
    return collection, dimensions

# 创建延伸板长度修正的C6032贴片钽电容
collection, dimensions = create_extension_fixed_tantalum_capacitor('C6032')

print("贴片钽电容3D模型生成完毕！")
