import bpy
import bmesh
from mathutils import Vector, Matrix
import math

# 清理默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# 设置场景单位
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.unit_settings.scale_length = 0.001

# 根据图片中的表格定义W值映射表（根据直径ΦD）
W_VALUE_MAP = {
    3.0: (0.45, 0.75),      # ΦD=3: W=0.45~0.75
    4.0: (0.5, 0.8),        # ΦD=4: W=0.5~0.8
    5.0: (0.5, 0.8),        # ΦD=5: W=0.5~0.8
    6.3: (0.5, 0.8),        # ΦD=6.3: W=0.5~0.8
    8.0: (0.7, 1.1),        # ΦD=8: W=0.7~1.1
    10.0: (0.7, 1.1),       # ΦD=10: W=0.7~1.1
    12.5: (1.1, 1.4),       # ΦD=12.5: W=1.1~1.4
    16.0: (1.1, 1.4)        # ΦD=16: W=1.1~1.4
}

# 定义常见贴片电解电容封装尺寸（单位：毫米），恢复之前的参数
ELECTROLYTIC_SIZES = {
    '3x5.3mm': {'diameter': 3.0, 'height': 5.3, 'lead_spacing': 0.8, 'horizontal_exposed_type': 1},
    '4x5.3mm': {'diameter': 4.0, 'height': 5.3, 'lead_spacing': 1.0, 'horizontal_exposed_type': 1},
    '5x5.3mm': {'diameter': 5.0, 'height': 5.3, 'lead_spacing': 1.5, 'horizontal_exposed_type': 1},
    '6.3x5.3mm': {'diameter': 6.3, 'height': 5.3, 'lead_spacing': 2.0, 'horizontal_exposed_type': 1},
    '6.3x7.7mm': {'diameter': 6.3, 'height': 7.7, 'lead_spacing': 2.0, 'horizontal_exposed_type': 1},
    '8x10mm': {'diameter': 8.0, 'height': 10.0, 'lead_spacing': 3.1, 'horizontal_exposed_type': 2},
    '8x10.3mm': {'diameter': 8.0, 'height': 10.3, 'lead_spacing': 3.1, 'horizontal_exposed_type': 2},
    '10x10mm': {'diameter': 10.0, 'height': 10.0, 'lead_spacing': 4.7, 'horizontal_exposed_type': 2},
    '10x10.3mm': {'diameter': 10.0, 'height': 10.3, 'lead_spacing': 4.7, 'horizontal_exposed_type': 2},
    '12.5x13.5mm': {'diameter': 12.5, 'height': 13.5, 'lead_spacing': 4.4, 'horizontal_exposed_type': 2},
    '12.5x16mm': {'diameter': 12.5, 'height': 16.0, 'lead_spacing': 4.4, 'horizontal_exposed_type': 2},
    '16x16.5mm': {'diameter': 16.0, 'height': 16.5, 'lead_spacing': 6.4, 'horizontal_exposed_type': 2}
}

def get_w_value(diameter):
    """根据直径获取对应的W值（取范围中间值）"""
    # 找到最接近的标准直径
    closest_diameter = min(W_VALUE_MAP.keys(), key=lambda x: abs(x - diameter))
    w_range = W_VALUE_MAP[closest_diameter]
    # 返回范围中间值
    return (w_range[0] + w_range[1]) / 2

def create_electrolytic_material(name, base_color, metallic=0.0, roughness=0.8):
    """创建电解电容材质"""
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

def get_horizontal_exposed_length(horizontal_exposed_type):
    """根据水平露出长度类型返回对应的露出长度"""
    if horizontal_exposed_type == 1:
        return 0.4  # 类型1：水平露出0.4mm
    elif horizontal_exposed_type == 2:
        return 1.0  # 类型2：水平露出1.0mm
    else:
        return 0.4  # 默认值

def create_electrolytic_capacitor_with_horizontal_exposed(size_name='4x5.3mm'):
    """创建水平露出长度修正的贴片电解电容3D模型"""
    if size_name not in ELECTROLYTIC_SIZES:
        size_name = '6.3x5.3mm'
    
    dimensions = ELECTROLYTIC_SIZES[size_name]
    diameter = dimensions['diameter']
    height = dimensions['height']
    lead_spacing = dimensions['lead_spacing']
    horizontal_exposed_type = dimensions['horizontal_exposed_type']
    
    # 根据直径获取W值（Extension宽度）
    w_value = get_w_value(diameter)
    
    # 获取水平露出长度
    horizontal_exposed_length = get_horizontal_exposed_length(horizontal_exposed_type)
    
    # 创建集合
    collection_name = f"Electrolytic_Capacitor_{size_name}"
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    
    # 创建材质
    body_mat = create_electrolytic_material("Capacitor_Body", (0.8, 0.8, 0.85), metallic=0.3, roughness=0.7)
    base_mat = create_electrolytic_material("Base_Plastic", (0.15, 0.15, 0.15), metallic=0.0, roughness=0.8)
    lead_mat = create_electrolytic_material("Lead_Metal", (0.9, 0.9, 0.92), metallic=0.9, roughness=0.2)
    polarity_mat = create_electrolytic_material("Polarity_Marking", (0.1, 0.1, 0.1), metallic=0.0, roughness=0.95)
    vent_mat = create_electrolytic_material("Vent_Marking", (0.9, 0.9, 0.9), metallic=0.0, roughness=0.9)
    
    # 1. 创建电解电容主体（圆柱体，银色）
    bm_body = bmesh.new()
    body_height = height * 0.95
    body_radius = diameter / 2
    bmesh.ops.create_cone(
        bm_body,
        radius1=body_radius,
        radius2=body_radius,
        depth=body_height,
        segments=32,
        cap_ends=True
    )
    
    mesh_body = bpy.data.meshes.new("Capacitor_Body")
    bm_body.to_mesh(mesh_body)
    obj_body = bpy.data.objects.new("Capacitor_Body", mesh_body)
    collection.objects.link(obj_body)
    obj_body.data.materials.append(body_mat)
    
    # 2. 创建底部塑料底座（带切角）- 恢复之前的计算方式
    bm_base = bmesh.new()
    base_height = height * 0.05
    base_size = diameter + 0.2
    
    # 创建正方形底座
    bmesh.ops.create_cube(bm_base, size=1.0)
    for v in bm_base.verts:
        v.co.x *= base_size
        v.co.y *= base_size
        v.co.z *= base_height
        v.co.z -= body_height / 2 + base_height / 2
    
    # 创建临时底座对象用于布尔运算
    mesh_base_temp = bpy.data.meshes.new("Base_Temp")
    bm_base.to_mesh(mesh_base_temp)
    obj_base_temp = bpy.data.objects.new("Base_Temp", mesh_base_temp)
    bpy.context.scene.collection.objects.link(obj_base_temp)
    
    # 创建两个旋转45度的正方体用于切角
    cut_size = base_size * 0.3
    
    # 创建右上角切角立方体
    bm_cut_ur = bmesh.new()
    bmesh.ops.create_cube(bm_cut_ur, size=1.0)
    for v in bm_cut_ur.verts:
        v.co.x *= cut_size
        v.co.y *= cut_size
        v.co.z *= base_height * 2
        rotation_matrix = Matrix.Rotation(math.radians(45), 4, 'Z')
        v.co = rotation_matrix @ v.co
        v.co.x += base_size / 2
        v.co.y += base_size / 2
        v.co.z -= height / 2
    
    mesh_cut_ur = bpy.data.meshes.new("Cut_UR")
    bm_cut_ur.to_mesh(mesh_cut_ur)
    obj_cut_ur = bpy.data.objects.new("Cut_UR", mesh_cut_ur)
    bpy.context.scene.collection.objects.link(obj_cut_ur)
    
    # 创建右下角切角立方体
    bm_cut_lr = bmesh.new()
    bmesh.ops.create_cube(bm_cut_lr, size=1.0)
    for v in bm_cut_lr.verts:
        v.co.x *= cut_size
        v.co.y *= cut_size
        v.co.z *= base_height * 2
        rotation_matrix = Matrix.Rotation(math.radians(45), 4, 'Z')
        v.co = rotation_matrix @ v.co
        v.co.x += base_size / 2
        v.co.y -= base_size / 2
        v.co.z -= height / 2
    
    mesh_cut_lr = bpy.data.meshes.new("Cut_LR")
    bm_cut_lr.to_mesh(mesh_cut_lr)
    obj_cut_lr = bpy.data.objects.new("Cut_LR", mesh_cut_lr)
    bpy.context.scene.collection.objects.link(obj_cut_lr)
    
    # 使用布尔修改器切除两个角
    bool_mod_ur = obj_base_temp.modifiers.new(name="Boolean_UR", type='BOOLEAN')
    bool_mod_ur.operation = 'DIFFERENCE'
    bool_mod_ur.object = obj_cut_ur
    
    bool_mod_lr = obj_base_temp.modifiers.new(name="Boolean_LR", type='BOOLEAN')
    bool_mod_lr.operation = 'DIFFERENCE'
    bool_mod_lr.object = obj_cut_lr
    
    # 应用修改器
    bpy.context.view_layer.objects.active = obj_base_temp
    bpy.ops.object.modifier_apply(modifier=bool_mod_ur.name)
    bpy.ops.object.modifier_apply(modifier=bool_mod_lr.name)
    
    # 将结果转换回bmesh
    bm_base_final = bmesh.new()
    bm_base_final.from_mesh(obj_base_temp.data)
    
    # 清理临时对象
    bpy.data.objects.remove(obj_cut_ur)
    bpy.data.objects.remove(obj_cut_lr)
    bpy.data.objects.remove(obj_base_temp)
    
    mesh_base = bpy.data.meshes.new("Base_Plastic")
    bm_base_final.to_mesh(mesh_base)
    obj_base = bpy.data.objects.new("Base_Plastic", mesh_base)
    collection.objects.link(obj_base)
    obj_base.data.materials.append(base_mat)
    
    # 3. 创建焊端延伸板（恢复之前的Extension位置计算方式）
    extension_height = 0.1
    extension_length = lead_spacing  # 延伸板总长度
    
    # 恢复之前的计算方式
    # 计算底座右侧边缘位置
    base_right_edge = base_size / 2
    # 计算延伸板右侧边缘位置（超出底座的水平露出长度）
    extension_right_edge = base_right_edge + horizontal_exposed_length
    # 计算延伸板中心点X坐标
    extension_center_x = extension_right_edge - extension_length / 2
    
    print(f"尺寸 {size_name}: 直径 = {diameter}mm, W值 = {w_value:.2f}mm")
    print(f"水平露出类型 = {horizontal_exposed_type}, 水平露出长度 = {horizontal_exposed_length}mm")
    print(f"底座尺寸: {base_size}mm, 延伸板总长度: {extension_length}mm")
    print(f"延伸板中心点X坐标: {extension_center_x}mm")
    
    # 正极延伸板（右侧）
    bm_positive_extension = bmesh.new()
    bmesh.ops.create_cube(bm_positive_extension, size=1.0)
    for v in bm_positive_extension.verts:
        v.co.x *= extension_length
        v.co.y *= w_value  # 使用W值作为延伸板宽度
        v.co.z *= extension_height
        # 定位到右侧，超出底座指定长度（恢复之前的计算方式）
        v.co.x += extension_center_x
        v.co.z -= (body_height / 2 - extension_height / 2.1 + base_height)
    
    mesh_positive_extension = bpy.data.meshes.new("Positive_Extension")
    bm_positive_extension.to_mesh(mesh_positive_extension)
    obj_positive_extension = bpy.data.objects.new("Positive_Extension", mesh_positive_extension)
    collection.objects.link(obj_positive_extension)
    obj_positive_extension.data.materials.append(lead_mat)
    
    # 负极延伸板（左侧）
    # 计算底座左侧边缘位置
    base_left_edge = -base_size / 2
    # 计算延伸板左侧边缘位置（超出底座的水平露出长度）
    extension_left_edge = base_left_edge - horizontal_exposed_length
    # 计算延伸板中心点X坐标
    extension_center_x_left = extension_left_edge + extension_length / 2
    
    bm_negative_extension = bmesh.new()
    bmesh.ops.create_cube(bm_negative_extension, size=1.0)
    for v in bm_negative_extension.verts:
        v.co.x *= extension_length
        v.co.y *= w_value  # 使用W值作为延伸板宽度
        v.co.z *= extension_height
        # 定位到左侧，超出底座指定长度（恢复之前的计算方式）
        v.co.x += extension_center_x_left
        v.co.z -= (body_height / 2 - extension_height / 2.1 + base_height)
    
    mesh_negative_extension = bpy.data.meshes.new("Negative_Extension")
    bm_negative_extension.to_mesh(mesh_negative_extension)
    obj_negative_extension = bpy.data.objects.new("Negative_Extension", mesh_negative_extension)
    collection.objects.link(obj_negative_extension)
    obj_negative_extension.data.materials.append(lead_mat)
    
    # 4. 创建弓形极性标记
    bm_polarity = bmesh.new()
    
    # 弓形参数
    arc_radius = body_radius
    arc_height = 0.01
    start_angle = math.radians(120)
    end_angle = math.radians(240)
    segments = 16
    delta_angle = math.radians(1)
    
    # 创建外弧顶点
    vertices_top = []
    vertices_bottom = []
    
    for i in range(segments + 1):
        angle = start_angle + (end_angle - start_angle) * (i / segments)
        x = math.cos(angle) * arc_radius
        y = math.sin(angle) * arc_radius
        vertices_top.append(bm_polarity.verts.new((x, y, arc_height/2)))
        vertices_bottom.append(bm_polarity.verts.new((x, y, -arc_height/2)))
    
    # 计算弦中点
    start_point = (math.cos(start_angle) * arc_radius, math.sin(start_angle) * arc_radius)
    end_point = (math.cos(end_angle) * arc_radius, math.sin(end_angle) * arc_radius)
    chord_midpoint = ((start_point[0] + end_point[0])/2, (start_point[1] + end_point[1])/2)
    mid_top = bm_polarity.verts.new((chord_midpoint[0], chord_midpoint[1], arc_height/2))
    mid_bottom = bm_polarity.verts.new((chord_midpoint[0], chord_midpoint[1], -arc_height/2))
    
    # 创建外弧面
    for i in range(segments):
        v1 = vertices_top[i]
        v2 = vertices_top[i+1]
        v3 = vertices_bottom[i+1]
        v4 = vertices_bottom[i]
        bm_polarity.faces.new([v1, v2, v3, v4])
    
    # 创建顶面
    for i in range(segments):
        v1 = mid_top
        v2 = vertices_top[i]
        v3 = vertices_top[i+1]
        bm_polarity.faces.new([v1, v2, v3])
    
    # 创建底面
    for i in range(segments):
        v1 = mid_bottom
        v2 = vertices_bottom[i]
        v3 = vertices_bottom[i+1]
        bm_polarity.faces.new([v1, v2, v3])
    
    # 创建起始端矩形面
    angle_start_delta = start_angle + delta_angle
    x_delta = math.cos(angle_start_delta) * arc_radius
    y_delta = math.sin(angle_start_delta) * arc_radius
    v3 = bm_polarity.verts.new((x_delta, y_delta, arc_height/2))
    v4 = bm_polarity.verts.new((x_delta, y_delta, -arc_height/2))
    bm_polarity.faces.new([vertices_top[0], vertices_bottom[0], v4, v3])
    
    # 创建结束端矩形面
    angle_end_delta = end_angle - delta_angle
    x_delta_end = math.cos(angle_end_delta) * arc_radius
    y_delta_end = math.sin(angle_end_delta) * arc_radius
    v7 = bm_polarity.verts.new((x_delta_end, y_delta_end, arc_height/2))
    v8 = bm_polarity.verts.new((x_delta_end, y_delta_end, -arc_height/2))
    bm_polarity.faces.new([vertices_top[-1], vertices_bottom[-1], v8, v7])
    
    # 定位到电容顶部
    for v in bm_polarity.verts:
        v.co.z += body_height / 2 + arc_height / 2
    
    mesh_polarity = bpy.data.meshes.new("Polarity_Marking")
    bm_polarity.to_mesh(mesh_polarity)
    obj_polarity = bpy.data.objects.new("Polarity_Marking", mesh_polarity)
    collection.objects.link(obj_polarity)
    obj_polarity.data.materials.append(polarity_mat)
    
    # 5. 创建顶部防爆阀标记
    bm_vent = bmesh.new()
    vent_size = diameter * 0.15
    vent_depth = 0.01
    bmesh.ops.create_cube(bm_vent, size=1.0)
    for v in bm_vent.verts:
        v.co.x *= vent_size
        v.co.y *= vent_size
        v.co.z *= vent_depth
        v.co.z += body_height / 2 + vent_depth / 2
    
    mesh_vent = bpy.data.meshes.new("Vent_Marking")
    bm_vent.to_mesh(mesh_vent)
    obj_vent = bpy.data.objects.new("Vent_Marking", mesh_vent)
    collection.objects.link(obj_vent)
    obj_vent.data.materials.append(vent_mat)
    
    # 清理bmesh
    bm_body.free()
    bm_base_final.free()
    bm_positive_extension.free()
    bm_negative_extension.free()
    bm_polarity.free()
    bm_vent.free()
    bm_cut_ur.free()
    bm_cut_lr.free()
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
    
    bpy.context.view_layer.objects.active = obj_body
    
    return collection, dimensions

# 创建4x5.3mm贴片电解电容
collection, dimensions = create_electrolytic_capacitor_with_horizontal_exposed('4x5.3mm')

print("贴片电解电容3D模型生成完毕！")
print(f"4x5.3mm规格参数：")
print(f"- 直径ΦD: {dimensions['diameter']}mm")
print(f"- 高度L: {dimensions['height']}mm") 
print(f"- 引脚间距P: {dimensions['lead_spacing']}mm")
print(f"- Extension宽度W: {get_w_value(6.3):.2f}mm (范围: 0.5~0.8mm)")
