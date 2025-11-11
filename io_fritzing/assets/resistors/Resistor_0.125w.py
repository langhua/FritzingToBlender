import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# 清理默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# 定义 1/8W 碳膜电阻标准尺寸（单位：毫米）
body_length = 3.5    # 圆柱主体长度
body_diameter = 1.8  # 圆柱主体直径

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

def add_final_color_bands(collection, body_length, body_diameter):
    """添加最终版色环（增大间距）"""
    # 色环颜色映射
    color_map = {
        'brown': (0.4, 0.2, 0.1),   # 棕色 - 第一环
        'black': (0.15, 0.15, 0.15), # 黑色 - 第二环
        'red': (0.7, 0.1, 0.1),     # 红色 - 第三环
        'gold': (0.8, 0.6, 0.1)     # 金色 - 容差环
    }
    
    # 1kΩ电阻的色环顺序
    band_colors = ['brown', 'black', 'red', 'gold']
    
    # 调整后的色环参数（增大间距）
    band_width = 0.25      # 色环宽度保持不变
    band_gap = 0.18        # 增大色环间距（从0.12增加到0.18）
    band_diameter = body_diameter * 1.01  # 色环直径略大于电阻体
    start_offset = 0.4     # 起始边距
    
    # 计算起始位置（从电阻体左端开始）
    start_x = -body_length / 2 + start_offset
    
    for i, color_name in enumerate(band_colors):
        # 创建色环材质
        color_rgb = color_map[color_name]
        band_mat = create_resistor_material(f"Band_{color_name}", color_rgb, metallic=0.0, roughness=0.95)
        
        # 创建色环几何体
        bm_band = bmesh.new()
        bmesh.ops.create_cone(
            bm_band,
            radius1=band_diameter/2,
            radius2=band_diameter/2,
            depth=band_width,
            segments=32,
            cap_ends=True
        )
        
        # 旋转色环使其沿X轴方向
        bmesh.ops.rotate(
            bm_band,
            verts=bm_band.verts,
            cent=(0, 0, 0),
            matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
        )
        
        # 计算色环位置（使用增大的间距）
        band_x = start_x + i * (band_width + band_gap) + band_width / 2
        for v in bm_band.verts:
            v.co.x += band_x
        
        # 创建网格和对象
        mesh_band = bpy.data.meshes.new(f"Color_Band_{i+1}_{color_name}")
        bm_band.to_mesh(mesh_band)
        obj_band = bpy.data.objects.new(f"Color_Band_{i+1}_{color_name}", mesh_band)
        collection.objects.link(obj_band)
        obj_band.data.materials.append(band_mat)
        
        bm_band.free()

# 创建集合
collection = bpy.data.collections.new("Carbon_Film_Resistor_Final")
bpy.context.scene.collection.children.link(collection)

# 创建材质
body_mat = create_resistor_material("Resistor_Body", (0.9, 0.7, 0.4), metallic=0.0, roughness=0.7)
end_cap_mat = create_resistor_material("End_Cap", (0.7, 0.7, 0.7), metallic=0.9, roughness=0.2)

# 1. 创建圆柱形电阻体（主体）
bm_body = bmesh.new()
bmesh.ops.create_cone(
    bm_body,
    radius1=body_diameter/2,
    radius2=body_diameter/2,
    depth=body_length,
    segments=32,
    cap_ends=True
)

# 旋转圆柱体使其沿X轴方向
bmesh.ops.rotate(
    bm_body,
    verts=bm_body.verts,
    cent=(0, 0, 0),
    matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
)

mesh_body = bpy.data.meshes.new("Resistor_Cylinder_Body")
bm_body.to_mesh(mesh_body)
obj_body = bpy.data.objects.new("Resistor_Cylinder_Body", mesh_body)
collection.objects.link(obj_body)
obj_body.data.materials.append(body_mat)

# 2. 创建左侧半球端帽
bm_left_hemisphere = bmesh.new()
bmesh.ops.create_uvsphere(
    bm_left_hemisphere,
    u_segments=32,
    v_segments=16,
    radius=body_diameter/2
)

# 切割球体为左半球
geom = bm_left_hemisphere.verts[:] + bm_left_hemisphere.edges[:] + bm_left_hemisphere.faces[:]
bmesh.ops.bisect_plane(
    bm_left_hemisphere,
    geom=geom,
    plane_co=(0, 0, 0),
    plane_no=(1, 0, 0),
    clear_outer=True
)

# 移动到圆柱体左端
for v in bm_left_hemisphere.verts:
    v.co.x -= body_length / 2

mesh_left_hemisphere = bpy.data.meshes.new("Left_Hemisphere_Cap")
bm_left_hemisphere.to_mesh(mesh_left_hemisphere)
obj_left_hemisphere = bpy.data.objects.new("Left_Hemisphere_Cap", mesh_left_hemisphere)
collection.objects.link(obj_left_hemisphere)
obj_left_hemisphere.data.materials.append(end_cap_mat)

# 3. 创建右侧半球端帽
bm_right_hemisphere = bmesh.new()
bmesh.ops.create_uvsphere(
    bm_right_hemisphere,
    u_segments=32,
    v_segments=16,
    radius=body_diameter/2
)

# 切割球体为右半球
geom = bm_right_hemisphere.verts[:] + bm_right_hemisphere.edges[:] + bm_right_hemisphere.faces[:]
bmesh.ops.bisect_plane(
    bm_right_hemisphere,
    geom=geom,
    plane_co=(0, 0, 0),
    plane_no=(-1, 0, 0),
    clear_outer=True
)

# 移动到圆柱体右端
for v in bm_right_hemisphere.verts:
    v.co.x += body_length / 2

mesh_right_hemisphere = bpy.data.meshes.new("Right_Hemisphere_Cap")
bm_right_hemisphere.to_mesh(mesh_right_hemisphere)
obj_right_hemisphere = bpy.data.objects.new("Right_Hemisphere_Cap", mesh_right_hemisphere)
collection.objects.link(obj_right_hemisphere)
obj_right_hemisphere.data.materials.append(end_cap_mat)

# 4. 创建金属引线（调整插入深度）
lead_length = 25.0
lead_diameter = 0.5
insertion_depth = 0.3  # 导线插入半球体的深度

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

# 调整左侧引线位置，使其插入半球体
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
    depth= lead_length,
    segments=16,
    cap_ends=True
)

bmesh.ops.rotate(
    bm_right_lead,
    verts=bm_right_lead.verts,
    cent=(0, 0, 0),
    matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
)

# 调整右侧引线位置，使其插入半球体
right_lead_x = body_length/2 + body_diameter/2 + lead_length/2 - insertion_depth
for v in bm_right_lead.verts:
    v.co.x += right_lead_x

mesh_right_lead = bpy.data.meshes.new("Right_Lead")
bm_right_lead.to_mesh(mesh_right_lead)
obj_right_lead = bpy.data.objects.new("Right_Lead", mesh_right_lead)
collection.objects.link(obj_right_lead)
obj_right_lead.data.materials.append(end_cap_mat)

# 5. 添加最终版色环（增大间距）
add_final_color_bands(collection, body_length, body_diameter)

# 清理bmesh
bm_body.free()
bm_left_hemisphere.free()
bm_right_hemisphere.free()
bm_left_lead.free()
bm_right_lead.free()

# 选择所有对象
bpy.ops.object.select_all(action='DESELECT')
for obj in collection.objects:
    obj.select_set(True)

bpy.context.view_layer.objects.active = obj_body

print("最终版碳膜电阻3D模型生成完毕！")
print("调整内容：")
print("- 色环间距从0.12mm增加到0.18mm")
print("- 导线插入半球体深度为0.3mm")
print("- 色环宽度保持0.25mm不变")
