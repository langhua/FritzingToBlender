import bpy
import bmesh
from mathutils import Vector

# 清理默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# 定义 0805 标准尺寸（单位：毫米）
length_mm = 2.0      # 陶瓷本体长度
width_mm = 1.25     # 陶瓷本体宽度
height_mm = 0.5     # 总高度
terminal_length_mm = 0.4  # 焊端延伸出本体的长度

# 计算总长
total_length = length_mm + 2 * terminal_length_mm

def create_resistor_material(name, base_color, metallic=0.0, roughness=0.8):
    """创建电阻材质"""
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

# 创建集合
collection = bpy.data.collections.new("Resistor_0805")
bpy.context.scene.collection.children.link(collection)

# 创建材质
metal_mat = create_resistor_material("0805_Metal", (0.92, 0.92, 0.92), metallic=0.9, roughness=0.15)
ceramic_mat = create_resistor_material("0805_Ceramic", (0.75, 0.75, 0.75), metallic=0.0, roughness=0.8)
coating_mat = create_resistor_material("0805_Coating", (0.12, 0.12, 0.12), metallic=0.0, roughness=0.95)

# 1. 创建陶瓷基体
bm_ceramic = bmesh.new()
ceramic_size = Vector((length_mm, width_mm, height_mm * 0.5))
bmesh.ops.create_cube(bm_ceramic, size=1.0)
for v in bm_ceramic.verts:
    v.co = v.co * ceramic_size
    v.co.z -= height_mm * 0.15

mesh_ceramic = bpy.data.meshes.new("0805_Ceramic_Base")
bm_ceramic.to_mesh(mesh_ceramic)
obj_ceramic = bpy.data.objects.new("0805_Ceramic_Base", mesh_ceramic)
collection.objects.link(obj_ceramic)
obj_ceramic.data.materials.append(ceramic_mat)

# 2. 创建左侧金属焊端
bm_left = bmesh.new()
left_terminal_size = Vector((terminal_length_mm, width_mm * 1.1, height_mm * 0.8))
bmesh.ops.create_cube(bm_left, size=1.0)
for v in bm_left.verts:
    v.co = v.co * left_terminal_size
    v.co.x -= length_mm / 2
    v.co.z += height_mm * 0.1

mesh_left = bpy.data.meshes.new("0805_Left_Terminal")
bm_left.to_mesh(mesh_left)
obj_left = bpy.data.objects.new("0805_Left_Terminal", mesh_left)
collection.objects.link(obj_left)
obj_left.data.materials.append(metal_mat)

# 3. 创建右侧金属焊端
bm_right = bmesh.new()
right_terminal_size = Vector((terminal_length_mm, width_mm * 1.1, height_mm * 0.8))
bmesh.ops.create_cube(bm_right, size=1.0)
for v in bm_right.verts:
    v.co = v.co * right_terminal_size
    v.co.x += length_mm / 2
    v.co.z += height_mm * 0.1

mesh_right = bpy.data.meshes.new("0805_Right_Terminal")
bm_right.to_mesh(mesh_right)
obj_right = bpy.data.objects.new("0805_Right_Terminal", mesh_right)
collection.objects.link(obj_right)
obj_right.data.materials.append(metal_mat)

# 4. 创建电阻涂层
bm_coating = bmesh.new()
coating_size = Vector((length_mm * 0.9, width_mm * 0.8, height_mm * 0.4))
bmesh.ops.create_cube(bm_coating, size=1.0)
for v in bm_coating.verts:
    v.co = v.co * coating_size
    v.co.z += height_mm * 0.25

mesh_coating = bpy.data.meshes.new("0805_Resistor_Coating")
bm_coating.to_mesh(mesh_coating)
obj_coating = bpy.data.objects.new("0805_Resistor_Coating", mesh_coating)
collection.objects.link(obj_coating)
obj_coating.data.materials.append(coating_mat)

# 清理bmesh
bm_ceramic.free()
bm_left.free()
bm_right.free()
bm_coating.free()

# 选择所有对象
bpy.ops.object.select_all(action='DESELECT')
for obj in collection.objects:
    obj.select_set(True)

bpy.context.view_layer.objects.active = obj_coating

print("简洁版0805贴片电阻3D模型生成完毕！")
print(f"标准尺寸：{total_length:.2f}mm × {width_mm:.2f}mm × {height_mm:.2f}mm")
