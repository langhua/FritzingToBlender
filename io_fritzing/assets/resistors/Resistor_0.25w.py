import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# 清理默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# 定义 1/4W 碳膜电阻标准尺寸（单位：毫米）
body_length = 6.5    # 圆柱主体长度
body_diameter = 2.5  # 圆柱主体直径
lead_length = 25.0    # 引线长度
lead_diameter = 0.6  # 引线直径

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

def add_color_bands(collection, body_length, body_diameter, resistance="1k"):
    """添加色环标记"""
    color_map = {
        'brown': (0.4, 0.2, 0.1),   # 棕色
        'black': (0.15, 0.15, 0.15), # 黑色
        'red': (0.7, 0.1, 0.1),     # 红色
        'gold': (0.8, 0.6, 0.1)     # 金色
    }
    
    band_colors = ['brown', 'black', 'red', 'gold']
    
    # 修改后的色环参数（宽度和间距增加50%）
    band_width = 0.45      # 色环宽度从0.3增加到0.45（增加50%）
    band_gap = 0.3        # 色环间距从0.2增加到0.3（增加50%）
    band_diameter = body_diameter * 1.01
    start_offset = 0.6
    
    start_x = -body_length / 2 + start_offset
    
    for i, color_name in enumerate(band_colors):
        color_rgb = color_map[color_name]
        band_mat = create_resistor_material(f"Band_{color_name}", color_rgb, metallic=0.0, roughness=0.95)
        
        bm_band = bmesh.new()
        bmesh.ops.create_cone(
            bm_band,
            radius1=band_diameter/2,
            radius2=band_diameter/2,
            depth=band_width,
            segments=32,
            cap_ends=True
        )
        
        bmesh.ops.rotate(
            bm_band,
            verts=bm_band.verts,
            cent=(0, 0, 0),
            matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
        )
        
        band_x = start_x + i * (band_width + band_gap) + band_width / 2
        for v in bm_band.verts:
            v.co.x += band_x
        
        mesh_band = bpy.data.meshes.new(f"Color_Band_{i+1}_{color_name}")
        bm_band.to_mesh(mesh_band)
        obj_band = bpy.data.objects.new(f"Color_Band_{i+1}_{color_name}", mesh_band)
        collection.objects.link(obj_band)
        obj_band.data.materials.append(band_mat)
        bm_band.free()

# 创建集合
collection = bpy.data.collections.new("Resistor_1_4W_Modified")
bpy.context.scene.collection.children.link(collection)

# 创建材质
body_mat = create_resistor_material("Resistor_Body", (0.9, 0.7, 0.4), metallic=0.0, roughness=0.7)
end_cap_mat = create_resistor_material("End_Cap", (0.7, 0.7, 0.7), metallic=0.9, roughness=0.2)

# 创建电阻体
bm_body = bmesh.new()
bmesh.ops.create_cone(
    bm_body,
    radius1=body_diameter/2,
    radius2=body_diameter/2,
    depth=body_length,
    segments=32,
    cap_ends=True
)

bmesh.ops.rotate(
    bm_body,
    verts=bm_body.verts,
    cent=(0, 0, 0),
    matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
)

mesh_body = bpy.data.meshes.new("Resistor_Body")
bm_body.to_mesh(mesh_body)
obj_body = bpy.data.objects.new("Resistor_Body", mesh_body)
collection.objects.link(obj_body)
obj_body.data.materials.append(body_mat)

# 创建端帽和引线
insertion_depth = 0.4

# 左侧端帽
bm_left_cap = bmesh.new()
bmesh.ops.create_uvsphere(
    bm_left_cap,
    u_segments=32,
    v_segments=16,
    radius=body_diameter/2
)

geom = bm_left_cap.verts[:] + bm_left_cap.edges[:] + bm_left_cap.faces[:]
bmesh.ops.bisect_plane(
    bm_left_cap,
    geom=geom,
    plane_co=(0, 0, 0),
    plane_no=(1, 0, 0),
    clear_outer=True
)

for v in bm_left_cap.verts:
    v.co.x -= body_length / 2

mesh_left_cap = bpy.data.meshes.new("Left_Cap")
bm_left_cap.to_mesh(mesh_left_cap)
obj_left_cap = bpy.data.objects.new("Left_Cap", mesh_left_cap)
collection.objects.link(obj_left_cap)
obj_left_cap.data.materials.append(end_cap_mat)

# 右侧端帽
bm_right_cap = bmesh.new()
bmesh.ops.create_uvsphere(
    bm_right_cap,
    u_segments=32,
    v_segments=16,
    radius=body_diameter/2
)

geom = bm_right_cap.verts[:] + bm_right_cap.edges[:] + bm_right_cap.faces[:]
bmesh.ops.bisect_plane(
    bm_right_cap,
    geom=geom,
    plane_co=(0, 0, 0),
    plane_no=(-1, 0, 0),
    clear_outer=True
)

for v in bm_right_cap.verts:
    v.co.x += body_length / 2

mesh_right_cap = bpy.data.meshes.new("Right_Cap")
bm_right_cap.to_mesh(mesh_right_cap)
obj_right_cap = bpy.data.objects.new("Right_Cap", mesh_right_cap)
collection.objects.link(obj_right_cap)
obj_right_cap.data.materials.append(end_cap_mat)

# 左侧引线
bm_left_lead = bmesh.new()
bmesh.ops.create_cone(
    bm_left_lead,
    radius1=lead_diameter/2,
    radius2=lead_diameter/2,
    depth=lead_length,
    segments=16,
    cap_ends=True
)

bmesh.ops.rotate(
    bm_left_lead,
    verts=bm_left_lead.verts,
    cent=(0, 0, 0),
    matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
)

left_lead_x = -body_length/2 - body_diameter/2 - lead_length/2 + insertion_depth
for v in bm_left_lead.verts:
    v.co.x += left_lead_x

mesh_left_lead = bpy.data.meshes.new("Left_Lead")
bm_left_lead.to_mesh(mesh_left_lead)
obj_left_lead = bpy.data.objects.new("Left_Lead", mesh_left_lead)
collection.objects.link(obj_left_lead)
obj_left_lead.data.materials.append(end_cap_mat)

# 右侧引线
bm_right_lead = bmesh.new()
bmesh.ops.create_cone(
    bm_right_lead,
    radius1=lead_diameter/2,
    radius2=lead_diameter/2,
    depth=lead_length,
    segments=16,
    cap_ends=True
)

bmesh.ops.rotate(
    bm_right_lead,
    verts=bm_right_lead.verts,
    cent=(0, 0, 0),
    matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
)

right_lead_x = body_length/2 + body_diameter/2 + lead_length/2 - insertion_depth
for v in bm_right_lead.verts:
    v.co.x += right_lead_x

mesh_right_lead = bpy.data.meshes.new("Right_Lead")
bm_right_lead.to_mesh(mesh_right_lead)
obj_right_lead = bpy.data.objects.new("Right_Lead", mesh_right_lead)
collection.objects.link(obj_right_lead)
obj_right_lead.data.materials.append(end_cap_mat)

# 添加修改后的色环
add_color_bands(collection, body_length, body_diameter)

# 清理
bm_body.free()
bm_left_cap.free()
bm_right_cap.free()
bm_left_lead.free()
bm_right_lead.free()

bpy.ops.object.select_all(action='DESELECT')
for obj in collection.objects:
    obj.select_set(True)

bpy.context.view_layer.objects.active = obj_body

print("修改后的1/4W碳膜电阻3D模型生成完毕！")
print("色环参数调整：")
print("- 色环宽度：0.3mm → 0.45mm（增加50%）")
print("- 色环间距：0.2mm → 0.3mm（增加50%）")
print(f"总尺寸：{body_length + body_diameter + 2 * lead_length:.1f}mm × {body_diameter:.1f}mm")
