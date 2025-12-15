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

# 三棱柱尺寸参数
triangular_prism_dimensions = {
    'base_size': 2.0,       # 三角形底面边长
    'height': 3.0,          # 棱柱高度
    'location': (0, 0, 0),  # 位置
    'rotation': (0, 0, 0),  # 旋转
    'material_color': (0.3, 0.6, 0.8),  # 蓝色材质
}

def create_regular_triangular_prism():
    """创建一个规则三棱柱（等边三角形底面）"""
    bm = bmesh.new()
    
    base_size = triangular_prism_dimensions['base_size']
    height = triangular_prism_dimensions['height']
    
    # 等边三角形的高度
    triangle_height = (math.sqrt(3) / 2) * base_size
    
    # 下底面三角形顶点
    # 等边三角形，中心在原点
    v1 = bm.verts.new((-base_size/2, -triangle_height/3, 0))  # 左下
    v2 = bm.verts.new((base_size/2, -triangle_height/3, 0))   # 右下
    v3 = bm.verts.new((0, 2*triangle_height/3, 0))            # 顶部
    
    # 上底面三角形顶点
    v4 = bm.verts.new((-base_size/2, -triangle_height/3, height))  # 左下
    v5 = bm.verts.new((base_size/2, -triangle_height/3, height))   # 右下
    v6 = bm.verts.new((0, 2*triangle_height/3, height))            # 顶部
    
    # 创建下底面（三角形）
    bm.faces.new([v1, v2, v3])
    
    # 创建上底面（三角形）- 注意顶点顺序以保证法线朝外
    bm.faces.new([v6, v5, v4])
    
    # 创建三个侧面（矩形）
    bm.faces.new([v1, v2, v5, v4])  # 底部侧面
    bm.faces.new([v2, v3, v6, v5])  # 右侧面
    bm.faces.new([v3, v1, v4, v6])  # 左侧面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Regular_Triangular_Prism_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    prism = bpy.data.objects.new("Regular_Triangular_Prism", mesh)
    bpy.context.collection.objects.link(prism)
    
    return prism

def create_right_triangular_prism(base_a=3.0, base_b=4.0, height=3.0):
    """创建一个直角三棱柱（底面是直角三角形）"""
    bm = bmesh.new()
    
    # 下底面直角三角形顶点
    v1 = bm.verts.new((0, 0, 0))           # 直角顶点
    v2 = bm.verts.new((base_a, 0, 0))      # 沿X轴
    v3 = bm.verts.new((0, base_b, 0))      # 沿Y轴
    
    # 上底面直角三角形顶点
    v4 = bm.verts.new((0, 0, height))      # 直角顶点
    v5 = bm.verts.new((base_a, 0, height)) # 沿X轴
    v6 = bm.verts.new((0, base_b, height)) # 沿Y轴
    
    # 创建下底面（直角三角形）
    bm.faces.new([v1, v2, v3])
    
    # 创建上底面（直角三角形）- 注意顶点顺序
    bm.faces.new([v6, v5, v4])
    
    # 创建三个侧面（矩形）
    bm.faces.new([v1, v2, v5, v4])  # 沿X轴的侧面
    bm.faces.new([v2, v3, v6, v5])  # 斜边侧面
    bm.faces.new([v3, v1, v4, v6])  # 沿Y轴的侧面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Right_Triangular_Prism_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    prism = bpy.data.objects.new("Right_Triangular_Prism", mesh)
    bpy.context.collection.objects.link(prism)
    
    return prism

def create_isosceles_triangular_prism(base=3.0, leg=2.5, height=3.0):
    """创建一个等腰三棱柱（底面是等腰三角形）"""
    bm = bmesh.new()
    
    # 计算等腰三角形的高度
    triangle_height = math.sqrt(leg**2 - (base/2)**2)
    
    # 下底面等腰三角形顶点
    v1 = bm.verts.new((-base/2, 0, 0))         # 左底点
    v2 = bm.verts.new((base/2, 0, 0))          # 右底点
    v3 = bm.verts.new((0, triangle_height, 0)) # 顶点
    
    # 上底面等腰三角形顶点
    v4 = bm.verts.new((-base/2, 0, height))    # 左底点
    v5 = bm.verts.new((base/2, 0, height))     # 右底点
    v6 = bm.verts.new((0, triangle_height, height))  # 顶点
    
    # 创建下底面（等腰三角形）
    bm.faces.new([v1, v2, v3])
    
    # 创建上底面（等腰三角形）- 注意顶点顺序
    bm.faces.new([v6, v5, v4])
    
    # 创建三个侧面（矩形）
    bm.faces.new([v1, v2, v5, v4])  # 底边侧面
    bm.faces.new([v2, v3, v6, v5])  # 右侧面
    bm.faces.new([v3, v1, v4, v6])  # 左侧面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Isosceles_Triangular_Prism_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    prism = bpy.data.objects.new("Isosceles_Triangular_Prism", mesh)
    bpy.context.collection.objects.link(prism)
    
    return prism

def create_scalene_triangular_prism(a=3.0, b=4.0, c=5.0, height=3.0):
    """创建一个不规则三棱柱（底面是不规则三角形）"""
    bm = bmesh.new()
    
    # 使用海伦公式计算三角形面积，然后计算高度
    # 这里我们创建一个简单的坐标系统
    # 假设a边在X轴上，b边从原点出发
    
    # 计算角度
    cos_A = (b**2 + c**2 - a**2) / (2 * b * c) if (2 * b * c) != 0 else 0.5
    cos_A = max(-1.0, min(1.0, cos_A))  # 限制在[-1, 1]范围内
    angle_A = math.acos(cos_A)
    
    # 下底面三角形顶点
    v1 = bm.verts.new((0, 0, 0))                     # 顶点A
    v2 = bm.verts.new((c, 0, 0))                     # 顶点B (c边在X轴上)
    v3 = bm.verts.new((b * math.cos(angle_A), b * math.sin(angle_A), 0))  # 顶点C
    
    # 上底面三角形顶点
    v4 = bm.verts.new((0, 0, height))               # 顶点A
    v5 = bm.verts.new((c, 0, height))               # 顶点B
    v6 = bm.verts.new((b * math.cos(angle_A), b * math.sin(angle_A), height))  # 顶点C
    
    # 创建下底面（不规则三角形）
    bm.faces.new([v1, v2, v3])
    
    # 创建上底面（不规则三角形）- 注意顶点顺序
    bm.faces.new([v6, v5, v4])
    
    # 创建三个侧面（矩形）
    bm.faces.new([v1, v2, v5, v4])  # AB边侧面
    bm.faces.new([v2, v3, v6, v5])  # BC边侧面
    bm.faces.new([v3, v1, v4, v6])  # CA边侧面
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Scalene_Triangular_Prism_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    prism = bpy.data.objects.new("Scalene_Triangular_Prism", mesh)
    bpy.context.collection.objects.link(prism)
    
    return prism

def create_centered_triangular_prism():
    """创建一个中心对齐的三棱柱（中心在原点）"""
    bm = bmesh.new()
    
    base_size = 2.0
    height = 3.0
    
    # 等边三角形的高度
    triangle_height = (math.sqrt(3) / 2) * base_size
    
    # 三角形重心高度
    centroid_height = triangle_height / 3
    
    # 下底面三角形顶点（以重心为中心）
    v1 = bm.verts.new((-base_size/2, -centroid_height, -height/2))
    v2 = bm.verts.new((base_size/2, -centroid_height, -height/2))
    v3 = bm.verts.new((0, triangle_height - centroid_height, -height/2))
    
    # 上底面三角形顶点
    v4 = bm.verts.new((-base_size/2, -centroid_height, height/2))
    v5 = bm.verts.new((base_size/2, -centroid_height, height/2))
    v6 = bm.verts.new((0, triangle_height - centroid_height, height/2))
    
    # 创建下底面
    bm.faces.new([v1, v2, v3])
    
    # 创建上底面
    bm.faces.new([v6, v5, v4])
    
    # 创建三个侧面
    bm.faces.new([v1, v2, v5, v4])
    bm.faces.new([v2, v3, v6, v5])
    bm.faces.new([v3, v1, v4, v6])
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Centered_Triangular_Prism_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    prism = bpy.data.objects.new("Centered_Triangular_Prism", mesh)
    bpy.context.collection.objects.link(prism)
    
    return prism

def calculate_prism_properties(base_size, height):
    """计算等边三角形三棱柱的几何属性"""
    # 等边三角形面积
    triangle_area = (math.sqrt(3) / 4) * base_size**2
    
    # 体积
    volume = triangle_area * height
    
    # 侧面面积（3个矩形）
    side_area = 3 * base_size * height
    
    # 总表面积
    surface_area = 2 * triangle_area + side_area
    
    return {
        'base_area': triangle_area,
        'volume': volume,
        'side_area': side_area,
        'surface_area': surface_area
    }

def calculate_right_prism_properties(base_a, base_b, height):
    """计算直角三角形三棱柱的几何属性"""
    # 直角三角形面积
    triangle_area = 0.5 * base_a * base_b
    
    # 斜边长度
    hypotenuse = math.sqrt(base_a**2 + base_b**2)
    
    # 体积
    volume = triangle_area * height
    
    # 侧面面积（3个矩形）
    side_area_ab = base_a * height
    side_area_bc = base_b * height
    side_area_ca = hypotenuse * height
    side_area = side_area_ab + side_area_bc + side_area_ca
    
    # 总表面积
    surface_area = 2 * triangle_area + side_area
    
    return {
        'base_area': triangle_area,
        'volume': volume,
        'side_area': side_area,
        'surface_area': surface_area,
        'hypotenuse': hypotenuse
    }

def create_blue_material():
    """创建蓝色材质"""
    mat = bpy.data.materials.new(name="Blue_Prism_Material")
    mat.use_nodes = True
    
    # 设置蓝色
    blue_color = triangular_prism_dimensions['material_color']
    mat.diffuse_color = (*blue_color, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*blue_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.5
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_green_material():
    """创建绿色材质"""
    mat = bpy.data.materials.new(name="Green_Prism_Material")
    mat.use_nodes = True
    
    # 设置绿色
    green_color = (0.3, 0.8, 0.4)
    mat.diffuse_color = (*green_color, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*green_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.5
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_red_material():
    """创建红色材质"""
    mat = bpy.data.materials.new(name="Red_Prism_Material")
    mat.use_nodes = True
    
    # 设置红色
    red_color = (0.8, 0.2, 0.2)
    mat.diffuse_color = (*red_color, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*red_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.5
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_yellow_material():
    """创建黄色材质"""
    mat = bpy.data.materials.new(name="Yellow_Prism_Material")
    mat.use_nodes = True
    
    # 设置黄色
    yellow_color = (0.9, 0.8, 0.2)
    mat.diffuse_color = (*yellow_color, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*yellow_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.5
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_glass_material():
    """创建玻璃材质"""
    mat = bpy.data.materials.new(name="Glass_Prism_Material")
    mat.use_nodes = True
    
    # 设置玻璃色
    glass_color = (0.9, 0.9, 0.9)
    mat.diffuse_color = (*glass_color, 0.7)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (*glass_color, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.1
    
    # 检查并使用正确的透射参数名称
    if 'Transmission Weight' in bsdf.inputs:
        bsdf.inputs['Transmission Weight'].default_value = 0.8
    elif 'Transmission' in bsdf.inputs:  # 兼容旧版本
        bsdf.inputs['Transmission'].default_value = 0.8
    
    if 'IOR' in bsdf.inputs:
        bsdf.inputs['IOR'].default_value = 1.5
    
    if 'Alpha' in bsdf.inputs:
        bsdf.inputs['Alpha'].default_value = 0.7
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_five_prisms():
    """创建五种不同的三棱柱并排列展示"""
    # 清理场景
    clear_scene()
    
    # 创建主集合
    collection = bpy.data.collections.new("Five_Triangular_Prisms")
    bpy.context.scene.collection.children.link(collection)
    
    print("创建五种三棱柱3D模型")
    print("=" * 60)
    
    # 1. 创建规则三棱柱（等边三角形底面）
    print("1. 创建规则三棱柱（等边三角形）...")
    prism1 = create_regular_triangular_prism()
    prism1.location = (-8, 8, 0)
    prism1.data.materials.clear()
    mat1 = create_blue_material()
    prism1.data.materials.append(mat1)
    collection.objects.link(prism1)
    
    # 计算几何属性
    props1 = calculate_prism_properties(2.0, 3.0)
    print(f"   尺寸: 底面边长2.0mm, 高3.0mm")
    print(f"   体积: {props1['volume']:.4f} mm³")
    print(f"   表面积: {props1['surface_area']:.4f} mm²")
    
    # 2. 创建直角三棱柱
    print("\n2. 创建直角三棱柱...")
    prism2 = create_right_triangular_prism(base_a=3.0, base_b=4.0, height=3.0)
    prism2.location = (8, 8, 0)
    prism2.data.materials.clear()
    mat2 = create_green_material()
    prism2.data.materials.append(mat2)
    collection.objects.link(prism2)
    
    # 计算几何属性
    props2 = calculate_right_prism_properties(3.0, 4.0, 3.0)
    print(f"   尺寸: 直角边3.0×4.0mm, 高3.0mm")
    print(f"   斜边: {props2['hypotenuse']:.4f} mm")
    print(f"   体积: {props2['volume']:.4f} mm³")
    print(f"   表面积: {props2['surface_area']:.4f} mm²")
    
    # 3. 创建等腰三棱柱
    print("\n3. 创建等腰三棱柱...")
    prism3 = create_isosceles_triangular_prism(base=3.0, leg=2.5, height=3.0)
    prism3.location = (-8, 0, 0)
    prism3.data.materials.clear()
    mat3 = create_red_material()
    prism3.data.materials.append(mat3)
    collection.objects.link(prism3)
    
    # 计算近似几何属性
    triangle_height = math.sqrt(2.5**2 - (3.0/2)**2)
    triangle_area = 0.5 * 3.0 * triangle_height
    volume = triangle_area * 3.0
    print(f"   尺寸: 底边3.0mm, 腰2.5mm, 高3.0mm")
    print(f"   三角形高: {triangle_height:.4f} mm")
    print(f"   体积: {volume:.4f} mm³")
    
    # 4. 创建不规则三棱柱
    print("\n4. 创建不规则三棱柱...")
    prism4 = create_scalene_triangular_prism(a=3.0, b=4.0, c=5.0, height=3.0)
    prism4.location = (8, 0, 0)
    prism4.data.materials.clear()
    mat4 = create_yellow_material()
    prism4.data.materials.append(mat4)
    collection.objects.link(prism4)
    
    # 计算几何属性（海伦公式）
    s = (3.0 + 4.0 + 5.0) / 2
    triangle_area = math.sqrt(s * (s-3.0) * (s-4.0) * (s-5.0))
    volume = triangle_area * 3.0
    print(f"   尺寸: 三角形三边3.0×4.0×5.0mm, 高3.0mm")
    print(f"   面积: {triangle_area:.4f} mm²")
    print(f"   体积: {volume:.4f} mm³")
    
    # 5. 创建中心对齐三棱柱
    print("\n5. 创建中心对齐三棱柱...")
    prism5 = create_centered_triangular_prism()
    prism5.location = (0, -8, 0)
    prism5.data.materials.clear()
    
    # 尝试创建玻璃材质
    try:
        mat5 = create_glass_material()
    except Exception as e:
        print(f"   注意: 创建简化材质代替玻璃材质")
        mat5 = create_blue_material()
    
    prism5.data.materials.append(mat5)
    collection.objects.link(prism5)
    
    print(f"   尺寸: 底面边长2.0mm, 高3.0mm")
    print(f"   位置: 中心在原点")
    
    print("\n三棱柱排列位置:")
    print("  1. 规则三棱柱: 左上(-8, 8, 0) - 蓝色")
    print("  2. 直角三棱柱: 右上(8, 8, 0) - 绿色")
    print("  3. 等腰三棱柱: 左中(-8, 0, 0) - 红色")
    print("  4. 不规则三棱柱: 右中(8, 0, 0) - 黄色")
    print("  5. 中心对齐三棱柱: 下方(0, -8, 0) - 玻璃/蓝色")
    print("")
    
    # 创建网格平面作为参考
    print("创建参考平面和坐标轴...")
    bpy.ops.mesh.primitive_grid_add(size=25, x_subdivisions=10, y_subdivisions=10, location=(0, 0, 0))
    grid = bpy.context.active_object
    grid.name = "Reference_Grid"
    grid.scale = (1, 1, 0.1)
    collection.objects.link(grid)
    
    # 添加平面材质
    grid.data.materials.clear()
    grid_mat = bpy.data.materials.new(name="Grid_Material")
    grid_mat.diffuse_color = (0.5, 0.5, 0.5, 0.3)
    grid.data.materials.append(grid_mat)
    
    print("\n五种三棱柱对比:")
    print("  A. 规则三棱柱: 等边三角形底面，所有侧面矩形")
    print("  B. 直角三棱柱: 直角三角形底面，一个侧面是正方形")
    print("  C. 等腰三棱柱: 等腰三角形底面，两个侧面相同")
    print("  D. 不规则三棱柱: 不规则三角形底面，三个侧面都不同")
    print("  E. 中心对齐三棱柱: 几何中心在原点")
    print("")
    
    # 统计信息
    print("模型统计:")
    print(f"  创建了5个三棱柱模型")
    print(f"  总计顶点数: 6×5 = 30个")
    print(f"  总计面数: 5×5 = 25个")
    print(f"  使用了5种不同材质")
    print(f"  所有模型已添加到集合: {collection.name}")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用正交视图
            area.spaces[0].region_3d.view_perspective = 'ORTHO'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 20
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.7, 0.6, 0.5, 0.7)
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
    print("三棱柱3D模型生成器")
    print("=" * 60)
    print("三棱柱定义:")
    print("  三棱柱是由两个平行的三角形底面和三个矩形侧面组成的多面体")
    print("  它是一种五面体，属于柱体的一种")
    print("")
    print("几何特征:")
    print("  - 顶点数: 6个")
    print("  - 面数: 5个 (2个三角形 + 3个矩形)")
    print("  - 边数: 9条")
    print("")
    print("体积公式: V = 底面面积 × 高度")
    print("")
    print("创建选项:")
    print("  A. 创建所有五种三棱柱 (推荐)")
    print("  B. 只创建规则三棱柱")
    
    # 创建所有五种三棱柱
    collection = create_five_prisms()
    
    return collection

if __name__ == "__main__":
    collection = main()