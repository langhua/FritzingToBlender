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

# 四棱锥尺寸参数
pyramid_dimensions = {
    'base_size': 2.0,      # 底面边长
    'height': 3.0,         # 棱锥高度
    'material_color': (0.8, 0.6, 0.2, 1.0),  # 金色材质
}

def create_square_pyramid(base_size=2.0, height=3.0, name="Square_Pyramid"):
    """创建一个标准四棱锥（底面为正方形的金字塔）"""
    bm = bmesh.new()
    
    half_size = base_size / 2
    
    # 创建底面四个顶点
    # 底面是正方形，位于Z=0平面
    v1 = bm.verts.new((-half_size, -half_size, 0))  # 左后
    v2 = bm.verts.new((half_size, -half_size, 0))   # 右后
    v3 = bm.verts.new((half_size, half_size, 0))    # 右前
    v4 = bm.verts.new((-half_size, half_size, 0))   # 左前
    
    # 创建顶部顶点
    # 顶部在Z轴正方向，位于中心上方
    v5 = bm.verts.new((0, 0, height))  # 顶部
    
    # 创建底面（正方形）
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建四个侧面（三角形）
    # 左侧面
    bm.faces.new([v1, v4, v5])
    # 前面
    bm.faces.new([v4, v3, v5])
    # 右侧面
    bm.faces.new([v3, v2, v5])
    # 后面
    bm.faces.new([v2, v1, v5])
    
    # 转换为网格
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    pyramid = bpy.data.objects.new(name, mesh)
    
    return pyramid

def create_rectangular_pyramid(base_length=3.0, base_width=2.0, height=4.0, name="Rectangular_Pyramid"):
    """创建一个底面为长方形的四棱锥"""
    bm = bmesh.new()
    
    half_length = base_length / 2
    half_width = base_width / 2
    
    # 创建底面四个顶点
    v1 = bm.verts.new((-half_length, -half_width, 0))  # 左后
    v2 = bm.verts.new((half_length, -half_width, 0))   # 右后
    v3 = bm.verts.new((half_length, half_width, 0))    # 右前
    v4 = bm.verts.new((-half_length, half_width, 0))   # 左前
    
    # 创建顶部顶点
    v5 = bm.verts.new((0, 0, height))  # 顶部
    
    # 创建底面
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建四个侧面
    bm.faces.new([v1, v4, v5])  # 左侧面
    bm.faces.new([v4, v3, v5])  # 前面
    bm.faces.new([v3, v2, v5])  # 右侧面
    bm.faces.new([v2, v1, v5])  # 后面
    
    # 转换为网格
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    pyramid = bpy.data.objects.new(name, mesh)
    
    return pyramid

def create_pyramid_with_base_centered(base_size=2.5, height=3.5, name="Centered_Pyramid"):
    """创建一个底面中心在原点，顶部在Z轴正方向的四棱锥"""
    bm = bmesh.new()
    
    half_size = base_size / 2
    
    # 底面顶点
    v1 = bm.verts.new((-half_size, -half_size, 0))
    v2 = bm.verts.new((half_size, -half_size, 0))
    v3 = bm.verts.new((half_size, half_size, 0))
    v4 = bm.verts.new((-half_size, half_size, 0))
    
    # 顶部顶点
    v5 = bm.verts.new((0, 0, height))
    
    # 创建底面
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建侧面
    bm.faces.new([v1, v4, v5])
    bm.faces.new([v4, v3, v5])
    bm.faces.new([v3, v2, v5])
    bm.faces.new([v2, v1, v5])
    
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    pyramid = bpy.data.objects.new(name, mesh)
    
    return pyramid

def create_pyramid_with_custom_top(base_size=2.0, height=3.0, top_offset_x=0.3, top_offset_y=0.2, name="Offset_Top_Pyramid"):
    """创建一个顶部不在中心上方的四棱锥"""
    bm = bmesh.new()
    
    half_size = base_size / 2
    
    # 底面顶点
    v1 = bm.verts.new((-half_size, -half_size, 0))
    v2 = bm.verts.new((half_size, -half_size, 0))
    v3 = bm.verts.new((half_size, half_size, 0))
    v4 = bm.verts.new((-half_size, half_size, 0))
    
    # 顶部顶点不在正中心，偏移一些
    v5 = bm.verts.new((top_offset_x, top_offset_y, height))
    
    # 创建底面
    bm.faces.new([v1, v2, v3, v4])
    
    # 创建侧面
    bm.faces.new([v1, v4, v5])
    bm.faces.new([v4, v3, v5])
    bm.faces.new([v3, v2, v5])
    bm.faces.new([v2, v1, v5])
    
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    pyramid = bpy.data.objects.new(name, mesh)
    
    return pyramid

def create_golden_material(name="Golden_Material"):
    """创建金色材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置金色
    golden_color = pyramid_dimensions['material_color']
    mat.diffuse_color = golden_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = golden_color
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_stone_material(name="Stone_Material"):
    """创建石材材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置石材色
    stone_color = (0.7, 0.7, 0.6, 1.0)
    mat.diffuse_color = stone_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = stone_color
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.7
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_red_material(name="Red_Material"):
    """创建红色材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置红色
    red_color = (0.8, 0.2, 0.2, 1.0)
    mat.diffuse_color = red_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = red_color
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.5
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_blue_material(name="Blue_Material"):
    """创建蓝色材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置蓝色
    blue_color = (0.2, 0.3, 0.8, 1.0)
    mat.diffuse_color = blue_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = blue_color
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.5
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def calculate_pyramid_properties(base_size, height):
    """计算四棱锥的几何属性"""
    # 底面面积
    base_area = base_size * base_size
    
    # 斜高（侧面三角形的高）
    slant_height = math.sqrt((base_size/2)**2 + height**2)
    
    # 侧面积（4个三角形面积）
    side_area = 4 * (0.5 * base_size * slant_height)
    
    # 表面积
    surface_area = base_area + side_area
    
    # 体积
    volume = (1/3) * base_area * height
    
    return {
        'base_area': base_area,
        'slant_height': slant_height,
        'side_area': side_area,
        'surface_area': surface_area,
        'volume': volume
    }

def calculate_rectangular_pyramid_properties(base_length, base_width, height):
    """计算长方形底面四棱锥的几何属性"""
    # 底面面积
    base_area = base_length * base_width
    
    # 计算侧面三角形的高（有4个不同的侧面）
    # 前后面三角形的高
    front_back_slant_height = math.sqrt((base_width/2)**2 + height**2)
    # 左右面三角形的高
    left_right_slant_height = math.sqrt((base_length/2)**2 + height**2)
    
    # 侧面积
    front_back_area = 2 * (0.5 * base_length * front_back_slant_height)
    left_right_area = 2 * (0.5 * base_width * left_right_slant_height)
    side_area = front_back_area + left_right_area
    
    # 表面积
    surface_area = base_area + side_area
    
    # 体积
    volume = (1/3) * base_area * height
    
    return {
        'base_area': base_area,
        'front_back_slant_height': front_back_slant_height,
        'left_right_slant_height': left_right_slant_height,
        'side_area': side_area,
        'surface_area': surface_area,
        'volume': volume
    }

def main():
    """主函数 - 创建四种不同的四棱锥并排列展示"""
    # 清理场景
    clear_scene()
    
    # 创建集合来组织所有四棱锥
    collection = bpy.data.collections.new("Four_Pyramids_Collection")
    bpy.context.scene.collection.children.link(collection)
    
    print("创建四种四棱锥3D模型")
    print("=" * 60)
    
    # 1. 创建标准四棱锥
    print("1. 创建标准四棱锥...")
    pyramid1 = create_square_pyramid(base_size=2.0, height=3.0, name="Standard_Pyramid")
    pyramid1.location = (-6, 6, 0)  # 左上位置
    pyramid1.data.materials.clear()
    mat1 = create_golden_material("Golden_Pyramid_Material")
    pyramid1.data.materials.append(mat1)
    collection.objects.link(pyramid1)
    
    # 计算几何属性
    props1 = calculate_pyramid_properties(2.0, 3.0)
    print(f"   尺寸: 底面2.0×2.0mm, 高3.0mm")
    print(f"   体积: {props1['volume']:.4f} mm³")
    
    # 2. 创建长方形底面四棱锥
    print("2. 创建长方形底面四棱锥...")
    pyramid2 = create_rectangular_pyramid(base_length=3.0, base_width=2.0, height=4.0, name="Rectangular_Pyramid")
    pyramid2.location = (6, 6, 0)  # 右上位置
    pyramid2.data.materials.clear()
    mat2 = create_red_material("Red_Pyramid_Material")
    pyramid2.data.materials.append(mat2)
    collection.objects.link(pyramid2)
    
    # 计算几何属性
    props2 = calculate_rectangular_pyramid_properties(3.0, 2.0, 4.0)
    print(f"   尺寸: 底面3.0×2.0mm, 高4.0mm")
    print(f"   体积: {props2['volume']:.4f} mm³")
    
    # 3. 创建中心对齐四棱锥
    print("3. 创建中心对齐四棱锥...")
    pyramid3 = create_pyramid_with_base_centered(base_size=2.5, height=3.5, name="Centered_Pyramid")
    pyramid3.location = (-6, -6, 0)  # 左下位置
    pyramid3.data.materials.clear()
    mat3 = create_blue_material("Blue_Pyramid_Material")
    pyramid3.data.materials.append(mat3)
    collection.objects.link(pyramid3)
    
    # 计算几何属性
    props3 = calculate_pyramid_properties(2.5, 3.5)
    print(f"   尺寸: 底面2.5×2.5mm, 高3.5mm")
    print(f"   体积: {props3['volume']:.4f} mm³")
    
    # 4. 创建偏移顶部四棱锥
    print("4. 创建偏移顶部四棱锥...")
    pyramid4 = create_pyramid_with_custom_top(
        base_size=2.0, 
        height=3.0, 
        top_offset_x=0.3, 
        top_offset_y=0.2, 
        name="Offset_Top_Pyramid"
    )
    pyramid4.location = (6, -6, 0)  # 右下位置
    pyramid4.data.materials.clear()
    mat4 = create_stone_material("Stone_Pyramid_Material")
    pyramid4.data.materials.append(mat4)
    collection.objects.link(pyramid4)
    
    # 计算几何属性
    props4 = calculate_pyramid_properties(2.0, 3.0)
    print(f"   尺寸: 底面2.0×2.0mm, 高3.0mm, 顶部偏移(0.3,0.2)")
    print(f"   体积: {props4['volume']:.4f} mm³")
    
    print("\n四棱锥排列位置:")
    print("  1. 标准四棱锥: 左上(-6, 6, 0) - 金色")
    print("  2. 长方形底面: 右上(6, 6, 0) - 红色")
    print("  3. 中心对齐: 左下(-6, -6, 0) - 蓝色")
    print("  4. 偏移顶部: 右下(6, -6, 0) - 石材色")
    print("")
    
    # 创建网格平面作为参考
    print("创建参考平面和坐标轴...")
    bpy.ops.mesh.primitive_grid_add(size=20, x_subdivisions=10, y_subdivisions=10, location=(0, 0, 0))
    grid = bpy.context.active_object
    grid.name = "Reference_Grid"
    grid.scale = (1, 1, 0.1)  # 扁平化
    collection.objects.link(grid)
    
    # 添加平面材质
    grid.data.materials.clear()
    grid_mat = bpy.data.materials.new(name="Grid_Material")
    grid_mat.diffuse_color = (0.5, 0.5, 0.5, 0.3)
    grid.data.materials.append(grid_mat)
    
    print("")
    print("四种四棱锥对比:")
    print("  A. 标准四棱锥: 正方形底面，顶部在正中心")
    print("  B. 长方形底面: 长方形底面，顶部在中心")
    print("  C. 中心对齐: 底面中心在原点，顶部在Z轴正方向")
    print("  D. 偏移顶部: 正方形底面，但顶部不在正中心")
    print("")
    
    # 统计信息
    print("模型统计:")
    print(f"  创建了4个四棱锥模型")
    print(f"  总计顶点数: 5×4 = 20个")
    print(f"  总计面数: 5×4 = 20个")
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
            area.spaces[0].region_3d.view_rotation = (0.5, 0.5, 0.5, 0.5)  # 从45度角观察
            # 设置显示模式
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
            # 设置网格显示
            area.spaces[0].overlay.show_floor = True
            area.spaces[0].overlay.show_axis_x = True
            area.spaces[0].overlay.show_axis_y = True
            area.spaces[0].overlay.show_axis_z = True
    
    return collection

if __name__ == "__main__":
    collection = main()