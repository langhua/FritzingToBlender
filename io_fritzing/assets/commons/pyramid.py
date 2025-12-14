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

# 扩展的四棱锥参数
pyramid_configs = [
    {
        'name': '标准四棱锥',
        'type': 'square',
        'base_size': 2.0,
        'height': 3.0,
        'material': 'golden',
        'position': (-6, 6, 0),
        'rotation': (0, 0, 0),
    },
    {
        'name': '长方形四棱锥',
        'type': 'rectangular',
        'base_length': 3.0,
        'base_width': 2.0,
        'height': 4.0,
        'material': 'red',
        'position': (6, 6, 0),
        'rotation': (0, 0, 0),
    },
    {
        'name': '中心对齐四棱锥',
        'type': 'centered',
        'base_size': 2.5,
        'height': 3.5,
        'material': 'blue',
        'position': (-6, -6, 0),
        'rotation': (0, 0, 0),
    },
    {
        'name': '偏移顶部四棱锥',
        'type': 'offset_top',
        'base_size': 2.0,
        'height': 3.0,
        'top_offset_x': 0.3,
        'top_offset_y': 0.2,
        'material': 'stone',
        'position': (6, -6, 0),
        'rotation': (0, 0, 0),
    },
    {
        'name': '大型四棱锥',
        'type': 'square',
        'base_size': 3.0,
        'height': 5.0,
        'material': 'emerald',
        'position': (0, 0, 0),
        'rotation': (0, 0, 0),
    },
    {
        'name': '扁平四棱锥',
        'type': 'rectangular',
        'base_length': 4.0,
        'base_width': 4.0,
        'height': 1.5,
        'material': 'amethyst',
        'position': (0, 12, 0),
        'rotation': (0, 0, 0),
    }
]

def create_square_pyramid(base_size=2.0, height=3.0, name="Square_Pyramid"):
    """创建一个标准四棱锥（底面为正方形的金字塔）"""
    bm = bmesh.new()
    
    half_size = base_size / 2
    
    # 创建底面四个顶点
    v1 = bm.verts.new((-half_size, -half_size, 0))  # 左后
    v2 = bm.verts.new((half_size, -half_size, 0))   # 右后
    v3 = bm.verts.new((half_size, half_size, 0))    # 右前
    v4 = bm.verts.new((-half_size, half_size, 0))   # 左前
    
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

def create_material(color, roughness=0.3, metallic=0.0, name="Material"):
    """创建材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    mat.diffuse_color = color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def get_material(material_type, name):
    """获取指定类型的材质"""
    materials = {
        'golden': ((0.9, 0.7, 0.3, 1.0), 0.2, 0.8),  # 金色
        'red': ((0.8, 0.2, 0.2, 1.0), 0.5, 0.1),    # 红色
        'blue': ((0.2, 0.3, 0.8, 1.0), 0.5, 0.1),   # 蓝色
        'stone': ((0.7, 0.7, 0.6, 1.0), 0.7, 0.1),  # 石材
        'emerald': ((0.2, 0.8, 0.4, 1.0), 0.3, 0.5), # 翡翠绿
        'amethyst': ((0.6, 0.3, 0.9, 1.0), 0.4, 0.6), # 紫水晶
        'copper': ((0.8, 0.5, 0.2, 1.0), 0.3, 0.7),  # 铜色
        'obsidian': ((0.1, 0.1, 0.2, 1.0), 0.8, 0.9), # 黑曜石
    }
    
    if material_type in materials:
        color, roughness, metallic = materials[material_type]
        return create_material(color, roughness, metallic, f"{name}_{material_type}")
    else:
        # 默认金色材质
        return create_material((0.9, 0.7, 0.3, 1.0), 0.2, 0.8, f"{name}_golden")

def calculate_pyramid_properties(base_size, height):
    """计算四棱锥的几何属性"""
    base_area = base_size * base_size
    slant_height = math.sqrt((base_size/2)**2 + height**2)
    side_area = 4 * (0.5 * base_size * slant_height)
    surface_area = base_area + side_area
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
    base_area = base_length * base_width
    front_back_slant_height = math.sqrt((base_width/2)**2 + height**2)
    left_right_slant_height = math.sqrt((base_length/2)**2 + height**2)
    front_back_area = 2 * (0.5 * base_length * front_back_slant_height)
    left_right_area = 2 * (0.5 * base_width * left_right_slant_height)
    side_area = front_back_area + left_right_area
    surface_area = base_area + side_area
    volume = (1/3) * base_area * height
    
    return {
        'base_area': base_area,
        'front_back_slant_height': front_back_slant_height,
        'left_right_slant_height': left_right_slant_height,
        'side_area': side_area,
        'surface_area': surface_area,
        'volume': volume
    }

def create_grid_plane(size=30, divisions=20, location=(0, 0, 0)):
    """创建网格平面"""
    bpy.ops.mesh.primitive_grid_add(
        size=size,
        x_subdivisions=divisions,
        y_subdivisions=divisions,
        location=location
    )
    grid = bpy.context.active_object
    grid.name = "Reference_Grid"
    grid.scale = (1, 1, 0.1)
    
    # 添加网格材质
    grid.data.materials.clear()
    grid_mat = bpy.data.materials.new(name="Grid_Material")
    grid_mat.diffuse_color = (0.3, 0.3, 0.3, 0.5)
    grid.data.materials.append(grid_mat)
    
    return grid

def create_lighting():
    """创建照明"""
    # 主光源
    bpy.ops.object.light_add(type='SUN', location=(10, 10, 20))
    sun = bpy.context.active_object
    sun.data.energy = 2.0
    sun.name = "Main_Sun_Light"
    
    # 填充光
    bpy.ops.object.light_add(type='AREA', location=(-10, -10, 15))
    fill_light = bpy.context.active_object
    fill_light.data.energy = 1.0
    fill_light.data.size = 5.0
    fill_light.name = "Fill_Light"
    
    return sun, fill_light

def create_camera():
    """创建相机"""
    bpy.ops.object.camera_add(location=(15, -15, 10))
    camera = bpy.context.active_object
    camera.name = "Main_Camera"
    
    # 指向场景中心
    camera.rotation_euler = (1.047, 0, 0.785)  # 约60度俯角，45度方位角
    
    # 设置活动相机
    bpy.context.scene.camera = camera
    
    return camera

def create_pyramid_from_config(config):
    """根据配置创建四棱锥"""
    pyramid_type = config['type']
    
    if pyramid_type == 'square':
        pyramid = create_square_pyramid(
            base_size=config['base_size'],
            height=config['height'],
            name=config['name']
        )
    elif pyramid_type == 'rectangular':
        pyramid = create_rectangular_pyramid(
            base_length=config['base_length'],
            base_width=config['base_width'],
            height=config['height'],
            name=config['name']
        )
    elif pyramid_type == 'centered':
        pyramid = create_pyramid_with_base_centered(
            base_size=config['base_size'],
            height=config['height'],
            name=config['name']
        )
    elif pyramid_type == 'offset_top':
        pyramid = create_pyramid_with_custom_top(
            base_size=config['base_size'],
            height=config['height'],
            top_offset_x=config.get('top_offset_x', 0.3),
            top_offset_y=config.get('top_offset_y', 0.2),
            name=config['name']
        )
    else:
        # 默认创建标准四棱锥
        pyramid = create_square_pyramid(
            base_size=config.get('base_size', 2.0),
            height=config.get('height', 3.0),
            name=config['name']
        )
    
    # 设置位置和旋转
    pyramid.location = config['position']
    pyramid.rotation_euler = (
        math.radians(config['rotation'][0]),
        math.radians(config['rotation'][1]),
        math.radians(config['rotation'][2])
    )
    
    # 应用材质
    pyramid.data.materials.clear()
    mat = get_material(config['material'], config['name'])
    pyramid.data.materials.append(mat)
    
    return pyramid

def main():
    """主函数 - 创建多种四棱锥"""
    # 清理场景
    clear_scene()
    
    # 创建主集合
    collection = bpy.data.collections.new("Pyramids_Collection")
    bpy.context.scene.collection.children.link(collection)
    
    print("创建多种四棱锥3D模型")
    print("=" * 60)
    print(f"将创建 {len(pyramid_configs)} 个四棱锥模型")
    print("")
    
    pyramids = []
    total_volume = 0
    total_surface_area = 0
    
    # 创建所有四棱锥
    for i, config in enumerate(pyramid_configs, 1):
        print(f"{i}. 创建 {config['name']}...")
        
        # 创建四棱锥
        pyramid = create_pyramid_from_config(config)
        
        # 添加到集合
        collection.objects.link(pyramid)
        pyramids.append(pyramid)
        
        # 计算几何属性
        if config['type'] == 'square' or config['type'] == 'centered' or config['type'] == 'offset_top':
            props = calculate_pyramid_properties(
                config.get('base_size', 2.0),
                config.get('height', 3.0)
            )
        elif config['type'] == 'rectangular':
            props = calculate_rectangular_pyramid_properties(
                config.get('base_length', 3.0),
                config.get('base_width', 2.0),
                config.get('height', 4.0)
            )
        else:
            props = {'volume': 0, 'surface_area': 0}
        
        # 累加统计
        total_volume += props.get('volume', 0)
        total_surface_area += props.get('surface_area', 0)
        
        # 打印信息
        if config['type'] == 'square' or config['type'] == 'centered' or config['type'] == 'offset_top':
            print(f"   尺寸: 底面{config.get('base_size', 2.0)}×{config.get('base_size', 2.0)}mm, 高{config.get('height', 3.0)}mm")
        elif config['type'] == 'rectangular':
            print(f"   尺寸: 底面{config.get('base_length', 3.0)}×{config.get('base_width', 2.0)}mm, 高{config.get('height', 4.0)}mm")
        
        print(f"   材质: {config['material']}")
        print(f"   位置: {config['position']}")
        print(f"   体积: {props.get('volume', 0):.4f} mm³")
        print("")
    
    # 创建参考网格
    print("创建参考平面...")
    grid = create_grid_plane(size=30, divisions=20, location=(0, 0, 0))
    collection.objects.link(grid)
    
    # 创建照明
    print("创建照明...")
    sun, fill_light = create_lighting()
    collection.objects.link(sun)
    collection.objects.link(fill_light)
    
    # 创建相机
    print("创建相机...")
    camera = create_camera()
    collection.objects.link(camera)
    
    # 设置渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080
    
    print("")
    print("场景设置完成:")
    print(f"  渲染引擎: {bpy.context.scene.render.engine}")
    print(f"  采样数: {bpy.context.scene.cycles.samples}")
    print(f"  分辨率: {bpy.context.scene.render.resolution_x}×{bpy.context.scene.render.resolution_y}")
    print("")
    
    # 统计信息
    print("模型统计:")
    print(f"  创建了 {len(pyramids)} 个四棱锥模型")
    print(f"  总计顶点数: {len(pyramids) * 5}")
    print(f"  总计面数: {len(pyramids) * 5}")
    print(f"  总计体积: {total_volume:.4f} mm³")
    print(f"  总计表面积: {total_surface_area:.4f} mm²")
    print(f"  使用了 {len(set(cfg['material'] for cfg in pyramid_configs))} 种不同材质")
    print("")
    
    print("控制提示:")
    print("  1. 按F12渲染当前视图")
    print("  2. 按N键打开属性面板")
    print("  3. 使用鼠标中键旋转视图")
    print("  4. 使用Shift+鼠标中键平移视图")
    print("  5. 使用Ctrl+鼠标中键缩放视图")
    print("  6. 按TAB键切换对象/编辑模式")
    print("")
    
    print("模型已准备就绪!")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 透视视图
            area.spaces[0].region_3d.view_perspective = 'PERSP'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 25
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.8, 0.1, 0.4, 0.4)
            # 设置显示模式
            area.spaces[0].shading.type = 'RENDERED'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
    
    return collection

if __name__ == "__main__":
    collection = main()