import bpy
import bmesh
from mathutils import Vector
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

# 四棱台尺寸参数
frustum_dimensions = {
    'bottom_length': 4.0,     # 下底面长度
    'bottom_width': 3.0,      # 下底面宽度
    'top_length': 2.0,        # 上底面长度
    'top_width': 1.5,         # 上底面宽度
    'height': 3.0,            # 高度
    'location': (0, 0, 0),    # 位置
    'rotation': (0, 0, 0),    # 旋转
    'material_color': (0.7, 0.5, 0.3),  # 棕色材质，现在是3个值
}

def create_square_frustum():
    """创建一个正方形四棱台（上下底面都是正方形）"""
    bm = bmesh.new()
    
    # 使用正方形底面参数
    bottom_size = 4.0
    top_size = 2.0
    height = 3.0
    
    half_bottom = bottom_size / 2
    half_top = top_size / 2
    
    # 创建下底面四个顶点
    v1 = bm.verts.new((-half_bottom, -half_bottom, 0))  # 左后
    v2 = bm.verts.new((half_bottom, -half_bottom, 0))   # 右后
    v3 = bm.verts.new((half_bottom, half_bottom, 0))    # 右前
    v4 = bm.verts.new((-half_bottom, half_bottom, 0))   # 左前
    
    # 创建上底面四个顶点
    v5 = bm.verts.new((-half_top, -half_top, height))   # 左后
    v6 = bm.verts.new((half_top, -half_top, height))    # 右后
    v7 = bm.verts.new((half_top, half_top, height))     # 右前
    v8 = bm.verts.new((-half_top, half_top, height))    # 左前
    
    # 创建下底面
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建上底面
    bm.faces.new([v8, v7, v6, v5])  # 注意顶点顺序保证法线朝外
    
    # 创建四个侧面
    bm.faces.new([v1, v2, v6, v5])  # 后面
    bm.faces.new([v2, v3, v7, v6])  # 右面
    bm.faces.new([v3, v4, v8, v7])  # 前面
    bm.faces.new([v4, v1, v5, v8])  # 左面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Square_Frustum_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    frustum = bpy.data.objects.new("Square_Frustum", mesh)
    bpy.context.collection.objects.link(frustum)
    
    return frustum

def create_rectangular_frustum(bottom_length=4.0, bottom_width=3.0, 
                               top_length=2.0, top_width=1.5, height=3.0):
    """创建一个长方形四棱台（上下底面都是长方形）"""
    bm = bmesh.new()
    
    half_bottom_length = bottom_length / 2
    half_bottom_width = bottom_width / 2
    half_top_length = top_length / 2
    half_top_width = top_width / 2
    
    # 创建下底面四个顶点
    v1 = bm.verts.new((-half_bottom_length, -half_bottom_width, 0))  # 左后
    v2 = bm.verts.new((half_bottom_length, -half_bottom_width, 0))   # 右后
    v3 = bm.verts.new((half_bottom_length, half_bottom_width, 0))    # 右前
    v4 = bm.verts.new((-half_bottom_length, half_bottom_width, 0))   # 左前
    
    # 创建上底面四个顶点
    v5 = bm.verts.new((-half_top_length, -half_top_width, height))   # 左后
    v6 = bm.verts.new((half_top_length, -half_top_width, height))    # 右后
    v7 = bm.verts.new((half_top_length, half_top_width, height))     # 右前
    v8 = bm.verts.new((-half_top_length, half_top_width, height))    # 左前
    
    # 创建下底面
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建上底面
    bm.faces.new([v8, v7, v6, v5])  # 注意顶点顺序保证法线朝外
    
    # 创建四个侧面
    bm.faces.new([v1, v2, v6, v5])  # 后面
    bm.faces.new([v2, v3, v7, v6])  # 右面
    bm.faces.new([v3, v4, v8, v7])  # 前面
    bm.faces.new([v4, v1, v5, v8])  # 左面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Rectangular_Frustum_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    frustum = bpy.data.objects.new("Rectangular_Frustum", mesh)
    bpy.context.collection.objects.link(frustum)
    
    return frustum

def create_centered_frustum(bottom_size=4.0, top_size=2.0, height=3.0):
    """创建一个中心对齐的四棱台"""
    bm = bmesh.new()
    
    half_bottom = bottom_size / 2
    half_top = top_size / 2
    
    # 创建下底面顶点
    v1 = bm.verts.new((-half_bottom, -half_bottom, 0))
    v2 = bm.verts.new((half_bottom, -half_bottom, 0))
    v3 = bm.verts.new((half_bottom, half_bottom, 0))
    v4 = bm.verts.new((-half_bottom, half_bottom, 0))
    
    # 创建上底面顶点
    v5 = bm.verts.new((-half_top, -half_top, height))
    v6 = bm.verts.new((half_top, -half_top, height))
    v7 = bm.verts.new((half_top, half_top, height))
    v8 = bm.verts.new((-half_top, half_top, height))
    
    # 创建下底面
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建上底面
    bm.faces.new([v8, v7, v6, v5])
    
    # 创建侧面
    bm.faces.new([v1, v2, v6, v5])  # 后面
    bm.faces.new([v2, v3, v7, v6])  # 右面
    bm.faces.new([v3, v4, v8, v7])  # 前面
    bm.faces.new([v4, v1, v5, v8])  # 左面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Centered_Frustum_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    frustum = bpy.data.objects.new("Centered_Frustum", mesh)
    bpy.context.collection.objects.link(frustum)
    
    return frustum

def create_offset_frustum(bottom_size=4.0, top_size=2.0, height=3.0, 
                          offset_x=0.5, offset_y=0.3):
    """创建一个偏移的四棱台（上下底面中心不垂直对齐）"""
    bm = bmesh.new()
    
    half_bottom = bottom_size / 2
    half_top = top_size / 2
    
    # 创建下底面顶点
    v1 = bm.verts.new((-half_bottom, -half_bottom, 0))
    v2 = bm.verts.new((half_bottom, -half_bottom, 0))
    v3 = bm.verts.new((half_bottom, half_bottom, 0))
    v4 = bm.verts.new((-half_bottom, half_bottom, 0))
    
    # 创建上底面顶点（相对于中心偏移）
    v5 = bm.verts.new((-half_top + offset_x, -half_top + offset_y, height))
    v6 = bm.verts.new((half_top + offset_x, -half_top + offset_y, height))
    v7 = bm.verts.new((half_top + offset_x, half_top + offset_y, height))
    v8 = bm.verts.new((-half_top + offset_x, half_top + offset_y, height))
    
    # 创建下底面
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建上底面
    bm.faces.new([v8, v7, v6, v5])
    
    # 创建侧面
    bm.faces.new([v1, v2, v6, v5])  # 后面
    bm.faces.new([v2, v3, v7, v6])  # 右面
    bm.faces.new([v3, v4, v8, v7])  # 前面
    bm.faces.new([v4, v1, v5, v8])  # 左面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Offset_Frustum_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    frustum = bpy.data.objects.new("Offset_Frustum", mesh)
    bpy.context.collection.objects.link(frustum)
    
    return frustum

def calculate_frustum_properties(bottom_length, bottom_width, top_length, top_width, height):
    """计算四棱台的几何属性"""
    # 底面面积
    bottom_area = bottom_length * bottom_width
    top_area = top_length * top_width
    
    # 体积 (四棱台体积公式: V = h/3 * (A1 + A2 + √(A1*A2)))
    volume = height/3 * (bottom_area + top_area + math.sqrt(bottom_area * top_area))
    
    # 侧面积（4个梯形的面积）
    # 计算四个侧面的斜高
    # 对于长度方向的侧面
    length_side_slant_height = math.sqrt(height**2 + ((bottom_length - top_length)/2)**2)
    # 对于宽度方向的侧面
    width_side_slant_height = math.sqrt(height**2 + ((bottom_width - top_width)/2)**2)
    
    # 侧面梯形面积
    length_side_area = 2 * 0.5 * (bottom_length + top_length) * length_side_slant_height
    width_side_area = 2 * 0.5 * (bottom_width + top_width) * width_side_slant_height
    lateral_area = length_side_area + width_side_area
    
    # 总表面积
    surface_area = bottom_area + top_area + lateral_area
    
    return {
        'bottom_area': bottom_area,
        'top_area': top_area,
        'volume': volume,
        'lateral_area': lateral_area,
        'surface_area': surface_area,
        'length_side_slant_height': length_side_slant_height,
        'width_side_slant_height': width_side_slant_height
    }

def calculate_square_frustum_properties(bottom_size, top_size, height):
    """计算正方形四棱台的几何属性"""
    bottom_area = bottom_size * bottom_size
    top_area = top_size * top_size
    
    # 体积
    volume = height/3 * (bottom_area + top_area + math.sqrt(bottom_area * top_area))
    
    # 侧面积（4个相同的梯形）
    slant_height = math.sqrt(height**2 + ((bottom_size - top_size)/2)**2)
    side_area = 4 * 0.5 * (bottom_size + top_size) * slant_height
    
    # 总表面积
    surface_area = bottom_area + top_area + side_area
    
    return {
        'bottom_area': bottom_area,
        'top_area': top_area,
        'volume': volume,
        'side_area': side_area,
        'surface_area': surface_area,
        'slant_height': slant_height
    }

def create_stone_material():
    """创建石材材质"""
    mat = bpy.data.materials.new(name="Stone_Frustum_Material")
    mat.use_nodes = True
    
    # 设置石材色
    stone_color = frustum_dimensions['material_color']  # 现在是3个值的元组
    mat.diffuse_color = (*stone_color, 1.0)  # 转换为4个值给diffuse_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*stone_color, 1.0)  # 3个值加透明度
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.7
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_metal_material():
    """创建金属材质"""
    mat = bpy.data.materials.new(name="Metal_Frustum_Material")
    mat.use_nodes = True
    
    # 设置金属色
    metal_color = (0.85, 0.85, 0.9)  # 3个值
    mat.diffuse_color = (*metal_color, 1.0)  # 转换为4个值
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*metal_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_wood_material():
    """创建木材材质"""
    mat = bpy.data.materials.new(name="Wood_Frustum_Material")
    mat.use_nodes = True
    
    # 设置木材色
    wood_color = (0.6, 0.4, 0.2)  # 3个值
    mat.diffuse_color = (*wood_color, 1.0)  # 转换为4个值
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*wood_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_glass_material():
    """创建玻璃材质"""
    mat = bpy.data.materials.new(name="Glass_Frustum_Material")
    mat.use_nodes = True
    
    # 设置玻璃色
    glass_color = (0.9, 0.9, 0.9)  # 3个值
    mat.diffuse_color = (*glass_color, 0.7)  # 转换为4个值，带透明度
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*glass_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.1
    
    # 修复：检查并使用正确的透射参数名称
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = 0.9
    elif 'Transmission' in bsdf.inputs:  # 兼容旧版本
        bsdf.inputs['Transmission'].default_value = 0.9
    
    if 'IOR' in bsdf.inputs:
        bsdf.inputs['IOR'].default_value = 1.5
    
    if 'Alpha' in bsdf.inputs:
        bsdf.inputs['Alpha'].default_value = 0.7
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_simple_glass_material():
    """创建简化的玻璃材质（不使用透射参数）"""
    mat = bpy.data.materials.new(name="Simple_Glass_Frustum_Material")
    mat.use_nodes = True
    
    # 设置玻璃色
    glass_color = (0.9, 0.9, 0.9)  # 3个值
    mat.diffuse_color = (*glass_color, 0.5)  # 转换为4个值
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加透明BSDF节点
    transparent_bsdf = nodes.new(type='ShaderNodeBsdfTransparent')
    transparent_bsdf.location = (0, 0)
    
    # 添加光泽BSDF节点
    glossy_bsdf = nodes.new(type='ShaderNodeBsdfGlossy')
    glossy_bsdf.location = (0, -100)
    glossy_bsdf.inputs['Color'].default_value = (1.0, 1.0, 1.0, 1.0)  # 4个值
    glossy_bsdf.inputs['Roughness'].default_value = 0.0
    
    # 添加混合着色器节点
    mix_shader = nodes.new(type='ShaderNodeMixShader')
    mix_shader.location = (200, 0)
    mix_shader.inputs['Fac'].default_value = 0.3  # 混合因子
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # 连接节点
    mat.node_tree.links.new(transparent_bsdf.outputs['BSDF'], mix_shader.inputs[1])
    mat.node_tree.links.new(glossy_bsdf.outputs['BSDF'], mix_shader.inputs[2])
    mat.node_tree.links.new(mix_shader.outputs['Shader'], output.inputs['Surface'])
    
    return mat

def create_four_frustums():
    """创建四种不同的四棱台并排列展示"""
    # 清理场景
    clear_scene()
    
    # 创建主集合
    collection = bpy.data.collections.new("Four_Frustums_Collection")
    bpy.context.scene.collection.children.link(collection)
    
    print("创建四种四棱台3D模型")
    print("=" * 60)
    
    # 1. 创建正方形四棱台
    print("1. 创建正方形四棱台...")
    frustum1 = create_square_frustum()
    frustum1.location = (-6, 6, 0)
    frustum1.data.materials.clear()
    mat1 = create_stone_material()
    frustum1.data.materials.append(mat1)
    collection.objects.link(frustum1)
    
    # 计算几何属性
    props1 = calculate_square_frustum_properties(4.0, 2.0, 3.0)
    print(f"   尺寸: 下底4.0×4.0mm, 上底2.0×2.0mm, 高3.0mm")
    print(f"   体积: {props1['volume']:.4f} mm³")
    print(f"   表面积: {props1['surface_area']:.4f} mm²")
    
    # 2. 创建长方形四棱台
    print("\n2. 创建长方形四棱台...")
    frustum2 = create_rectangular_frustum(
        bottom_length=4.0, bottom_width=3.0,
        top_length=2.0, top_width=1.5,
        height=3.0
    )
    frustum2.location = (6, 6, 0)
    frustum2.data.materials.clear()
    mat2 = create_metal_material()
    frustum2.data.materials.append(mat2)
    collection.objects.link(frustum2)
    
    # 计算几何属性
    props2 = calculate_frustum_properties(4.0, 3.0, 2.0, 1.5, 3.0)
    print(f"   尺寸: 下底4.0×3.0mm, 上底2.0×1.5mm, 高3.0mm")
    print(f"   体积: {props2['volume']:.4f} mm³")
    print(f"   表面积: {props2['surface_area']:.4f} mm²")
    
    # 3. 创建中心对齐四棱台
    print("\n3. 创建中心对齐四棱台...")
    frustum3 = create_centered_frustum(bottom_size=5.0, top_size=1.5, height=4.0)
    frustum3.location = (-6, -6, 0)
    frustum3.data.materials.clear()
    mat3 = create_wood_material()
    frustum3.data.materials.append(mat3)
    collection.objects.link(frustum3)
    
    # 计算几何属性
    props3 = calculate_square_frustum_properties(5.0, 1.5, 4.0)
    print(f"   尺寸: 下底5.0×5.0mm, 上底1.5×1.5mm, 高4.0mm")
    print(f"   体积: {props3['volume']:.4f} mm³")
    print(f"   表面积: {props3['surface_area']:.4f} mm²")
    
    # 4. 创建偏移四棱台
    print("\n4. 创建偏移四棱台...")
    frustum4 = create_offset_frustum(
        bottom_size=3.0, top_size=1.0, 
        height=2.5, offset_x=0.5, offset_y=0.3
    )
    frustum4.location = (6, -6, 0)
    frustum4.data.materials.clear()
    
    # 尝试创建玻璃材质，如果失败则使用简化版本
    try:
        mat4 = create_glass_material()
    except Exception as e:
        print(f"   注意: 使用简化玻璃材质，原因: {e}")
        mat4 = create_simple_glass_material()
    
    frustum4.data.materials.append(mat4)
    collection.objects.link(frustum4)
    
    # 计算近似几何属性（使用平均值）
    props4 = calculate_square_frustum_properties(3.0, 1.0, 2.5)
    print(f"   尺寸: 下底3.0×3.0mm, 上底1.0×1.0mm, 高2.5mm")
    print(f"   偏移: (0.5, 0.3)")
    print(f"   近似体积: {props4['volume']:.4f} mm³")
    print(f"   近似表面积: {props4['surface_area']:.4f} mm²")
    
    print("\n四棱台排列位置:")
    print("  1. 正方形四棱台: 左上(-6, 6, 0) - 石材")
    print("  2. 长方形四棱台: 右上(6, 6, 0) - 金属")
    print("  3. 中心对齐四棱台: 左下(-6, -6, 0) - 木材")
    print("  4. 偏移四棱台: 右下(6, -6, 0) - 玻璃")
    print("")
    
    # 创建网格平面作为参考
    print("创建参考平面和坐标轴...")
    bpy.ops.mesh.primitive_grid_add(size=20, x_subdivisions=10, y_subdivisions=10, location=(0, 0, 0))
    grid = bpy.context.active_object
    grid.name = "Reference_Grid"
    grid.scale = (1, 1, 0.1)
    collection.objects.link(grid)
    
    # 添加平面材质
    grid.data.materials.clear()
    grid_mat = bpy.data.materials.new(name="Grid_Material")
    grid_mat.diffuse_color = (0.5, 0.5, 0.5, 0.3)  # 4个值
    grid.data.materials.append(grid_mat)
    
    print("\n四种四棱台对比:")
    print("  A. 正方形四棱台: 上下底面都是正方形，中心对齐")
    print("  B. 长方形四棱台: 上下底面都是长方形，中心对齐")
    print("  C. 中心对齐四棱台: 底面中心在原点，上底面中心在Z轴")
    print("  D. 偏移四棱台: 上下底面中心不垂直对齐")
    print("")
    
    # 统计信息
    print("模型统计:")
    print(f"  创建了4个四棱台模型")
    print(f"  总计顶点数: 8×4 = 32个")
    print(f"  总计面数: 6×4 = 24个")
    print(f"  使用了4种不同材质")
    print(f"  所有模型已添加到集合: {collection.name}")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用正交视图
            area.spaces[0].region_3d.view_perspective = 'ORTHO'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 0.15
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.5, 0.5, 0.5, 0.5)
            # 设置显示模式
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
            # 设置背景
            area.spaces[0].shading.background_type = 'VIEWPORT'
            area.spaces[0].shading.background_color = (0.1, 0.1, 0.1)
            # 设置网格显示
            area.spaces[0].overlay.show_floor = True
            area.spaces[0].overlay.show_axis_x = True
            area.spaces[0].overlay.show_axis_y = True
            area.spaces[0].overlay.show_axis_z = True
    
    return collection

def main():
    """主函数"""
    print("四棱台3D模型生成器")
    print("=" * 60)
    print("四棱台定义:")
    print("  四棱台是截去顶部的四棱锥，也称为平截头体")
    print("  它有上下两个平行的矩形面，侧面是四个梯形")
    print("")
    print("几何特征:")
    print("  - 顶点数: 8个")
    print("  - 面数: 6个 (2个矩形面 + 4个梯形面)")
    print("  - 边数: 12条")
    print("")
    print("创建选项:")
    print("  A. 创建所有四种四棱台 (推荐)")
    print("  B. 只创建标准四棱台")
    
    # 创建所有四种四棱台
    collection = create_four_frustums()
    
    return collection

if __name__ == "__main__":
    collection = main()