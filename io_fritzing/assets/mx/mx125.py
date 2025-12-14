import bpy
import bmesh
from mathutils import Vector
import math
import io_fritzing.assets.commons.trapezoid as trapezoid
import io_fritzing.assets.commons.rounded_rect as rounded_rect

# 清理场景
def clear_scene():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001

# 根据实物照片定义MX1.25 2P连接器的尺寸
mx125_2p_dimensions = {
    # 总体尺寸
    'total_length': 7.3,      # 总长度
    'total_width': 5.15,      # 总宽度
    'total_height': 5.25,     # 总高度

    # 壳尺寸
    'housing_length': 4.3,       # 壳长度
    'housing_width': 4.30,        # 壳宽度
    'housing_height': 3.50,       # 壳高度
    'housing_roof_width': 3.30,   # 壳顶宽度
    
    # 外壳壁厚
    'wall_thickness': 0.4,   # 壳体壁厚

    # 固定件尺寸
    'wing_width': 1.5,       # (total_length - housing_length)/2 = (7.3 - 4.3)/2 = 1.5
    'wing_length': 3.3,
    'wing_height': 2.4,
    
    # 引脚相关
    'pin_pitch': 1.25,             # 引脚间距
    'pin_width': 0.6,              # 引脚宽度
    'pin_thickness': 0.3,          # 引脚厚度
    'pin_horizontal_length': 1.5,  # 引脚水平部分长度
    'pin_vertical_length': 2.5,    # 引脚垂直部分长度
    
    # 材料特性
    'material': 'LCP',                 # 材料：液晶聚合物（耐高温）
    'color': (0.96, 0.94, 0.88, 1.0),  # 米白色
}

def create_housing_with_thickness(dims):
    """创建带有0.2mm壁厚的外壳"""
    # 外壳外部尺寸
    outer_length = dims['housing_length']
    outer_width = dims['housing_width']
    outer_height = dims['housing_height']
    outer_roof_width = dims['housing_roof_width']
    
    # 壁厚
    wall_thickness = dims['wall_thickness']
    
    # 创建壳体的5个面
    # 1. 底面
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, wall_thickness/2)
    )
    housing = bpy.context.active_object
    housing.name = "Housing_Walls"
    housing.scale = (outer_length, outer_width, wall_thickness)
    bpy.ops.object.transform_apply(scale=True)

    # 2. 底部开方形卡位孔
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, outer_width/4 - wall_thickness/2, wall_thickness/2)
    )
    bottom_hole = bpy.context.active_object
    bottom_hole.name = "Housing_Bottom_Hole"
    bottom_hole.scale = (dims['pin_pitch'] - dims['pin_thickness'], outer_width/2 - wall_thickness, wall_thickness + 0.2)
    bpy.ops.object.transform_apply(scale=True)

    modifier = housing.modifiers.new(name="Bottom_Hole_Cut", type="BOOLEAN")
    modifier.object = bottom_hole
    bpy.context.view_layer.objects.active = housing
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(bottom_hole, do_unlink=True)

    # 3. 背面
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, outer_width/2 - wall_thickness/2, outer_height/2)
    )
    backwall = bpy.context.active_object
    backwall.name = "Housing_Back_Wall"
    backwall.scale = (outer_length, wall_thickness, outer_height)
    bpy.ops.object.transform_apply(scale=True)

    # 4. 左侧
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-outer_length/2 + wall_thickness/2, 0, outer_height/2)
    )
    leftwall = bpy.context.active_object
    leftwall.name = "Housing_Left_Wall"
    leftwall.scale = (wall_thickness, outer_width, outer_height)
    bpy.ops.object.transform_apply(scale=True)

    # 5. 左墙开槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-outer_length/2 + wall_thickness * 3/4, -wall_thickness/2, outer_height/2 + wall_thickness/2)
    )
    left_guide = bpy.context.active_object
    left_guide.name = "Housing_Left_Guide"
    left_guide.scale = (wall_thickness/2, outer_width - wall_thickness, wall_thickness)
    bpy.ops.object.transform_apply(scale=True)

    modifier = leftwall.modifiers.new(name="Left_Guide_Cut", type="BOOLEAN")
    modifier.object = left_guide
    bpy.context.view_layer.objects.active = leftwall
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(left_guide, do_unlink=True)

    # 6. 右侧
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(outer_length/2 - wall_thickness/2, 0, outer_height/2)
    )
    rightwall = bpy.context.active_object
    rightwall.name = "Housing_Right_Wall"
    rightwall.scale = (wall_thickness, outer_width, outer_height)
    bpy.ops.object.transform_apply(scale=True)

    # 7. 右墙开槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(outer_length/2 - wall_thickness * 3/4, -wall_thickness/2, outer_height/2 + wall_thickness/2)
    )
    right_guide = bpy.context.active_object
    right_guide.name = "Housing_Right_Guide"
    right_guide.scale = (wall_thickness/2, outer_width - wall_thickness, wall_thickness)
    bpy.ops.object.transform_apply(scale=True)

    modifier = rightwall.modifiers.new(name="Right_Guide_Cut", type="BOOLEAN")
    modifier.object = right_guide
    bpy.context.view_layer.objects.active = rightwall
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(right_guide, do_unlink=True)

    # 8. 顶部
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, outer_width/2 - outer_roof_width/2, outer_height - wall_thickness/2)
    )
    roof = bpy.context.active_object
    roof.name = "Housing_Roof"
    roof.scale = (outer_length, outer_roof_width, wall_thickness)
    bpy.ops.object.transform_apply(scale=True)

    # 7. 合并housing和各个墙板
    bpy.ops.object.select_all(action='DESELECT')
    housing.select_set(True)
    backwall.select_set(True)
    leftwall.select_set(True)
    rightwall.select_set(True)
    roof.select_set(True)
    bpy.context.view_layer.objects.active = housing
    bpy.ops.object.join()

    # 8. 添加材质
    housing.data.materials.clear()
    mat = create_lcp_material()
    housing.data.materials.append(mat)

    return housing, mat

def create_wings(dims, mat):
    wings = []
    width = dims['wing_width']
    length = dims['wing_length']
    height = dims['wing_height']

    outer_length = dims['housing_length']
    outer_width = dims['housing_width']

    # 创建左侧翼
    left_wing = trapezoid.create_right_angled_trapezoid(long_edge=length, short_edge=length - width/2, width=width/2, thickness=height)
    left_wing.name = 'left_wing'
    left_wing.rotation_euler = (0, math.pi, math.pi/2)
    left_wing.location = (-outer_length/2 - width/2, outer_width/2, height)

    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-outer_length/2 - width/4, outer_width/2 - length/2, height/2)
    )
    left_wing2 = bpy.context.active_object
    left_wing2.name = "left_wing2"
    left_wing2.scale = (width/2, length, height)
    bpy.ops.object.transform_apply(scale=True)

    # 合并left_wing和left_wing2
    bpy.ops.object.select_all(action='DESELECT')
    left_wing.select_set(True)
    left_wing2.select_set(True)
    bpy.context.view_layer.objects.active = left_wing
    bpy.ops.object.join()
    left_wing.data.materials.clear()
    left_wing.data.materials.append(mat)

    wings.append(left_wing)

    # 创建右侧翼
    right_wing = trapezoid.create_right_angled_trapezoid(long_edge=length, short_edge=length - width/2, width=width/2, thickness=height)
    right_wing.name = 'right_wing'
    right_wing.rotation_euler = (math.pi, math.pi, math.pi/2)
    right_wing.location = (outer_length/2 + width/2, outer_width/2, 0)

    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(outer_length/2 + width/4, outer_width/2 - length/2, height/2)
    )
    right_wing2 = bpy.context.active_object
    right_wing2.name = "right_wing2"
    right_wing2.scale = (width/2, length, height)
    bpy.ops.object.transform_apply(scale=True)

    # 合并right_wing和right_wing2
    bpy.ops.object.select_all(action='DESELECT')
    right_wing.select_set(True)
    right_wing2.select_set(True)
    bpy.context.view_layer.objects.active = right_wing
    bpy.ops.object.join()
    right_wing.data.materials.clear()
    right_wing.data.materials.append(mat)

    wings.append(right_wing)

    return wings


def create_c_shape_metal(dims):
    """创建C形金属固定件"""
    c_shapes = []

    # 壳尺寸
    outer_length = dims['housing_length']
    
    # C形金属固定件尺寸
    width = dims['wing_width']
    length = dims['wing_length']/2
    height = dims['wing_height']

    thickness = dims['pin_thickness']
    
    # 创建C形金属固定件
    # 1. 左侧顶部
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-outer_length/2 - width * 3/8, (outer_length - 2 * length)/2 - length/2 - 0.01, height - thickness/2 + 0.01)
    )
    c_shape_left = bpy.context.active_object
    c_shape_left.name = "C_Shape_Left_Metal"
    c_shape_left.scale = (width * 3/4, length, thickness)
    bpy.ops.object.transform_apply(scale=True)
    
    # 2. 左侧底部
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-outer_length/2 - width/2, (outer_length - 2 * length)/2 - length/2 - 0.01, thickness/2 - 0.01)
    )
    c_shape_left_bottom = bpy.context.active_object
    c_shape_left_bottom.name = "C_Shape_Left_Bottom_Metal"
    c_shape_left_bottom.scale = (width, length, thickness)
    bpy.ops.object.transform_apply(scale=True)
    
    # 3. 左侧中间件
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-outer_length/2 - thickness/2, (outer_length - 2 * length)/2 - length/2 - 0.01, height/2)
    )
    c_shape_left_middle = bpy.context.active_object
    c_shape_left_middle.name = "C_Shape_Left_Middle_Metal"
    c_shape_left_middle.scale = (thickness, length, height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 4. 左侧合并
    bpy.ops.object.select_all(action='DESELECT')
    c_shape_left.select_set(True)
    c_shape_left_bottom.select_set(True)
    c_shape_left_middle.select_set(True)
    bpy.context.view_layer.objects.active = c_shape_left
    bpy.ops.object.join()
    c_shape_left.data.materials.clear()
    mat = create_metal_material()
    c_shape_left.data.materials.append(mat)
    
    # 5. 右侧顶部
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(outer_length/2 + width * 3/8, (outer_length - 2 * length)/2 - length/2 - 0.01, height - thickness/2 + 0.01)
    )
    c_shape_right = bpy.context.active_object
    c_shape_right.name = "C_Shape_Right_Metal"
    c_shape_right.scale = (width * 3/4, length, thickness)
    bpy.ops.object.transform_apply(scale=True)
    
    # 6. 右侧底部
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(outer_length/2 + width/2, (outer_length - 2 * length)/2 - length/2 - 0.01, thickness/2 - 0.01)
    )
    c_shape_right_bottom = bpy.context.active_object
    c_shape_right_bottom.name = "C_Shape_Right_Bottom_Metal"
    c_shape_right_bottom.scale = (width, length, thickness)
    bpy.ops.object.transform_apply(scale=True)
    
    # 7. 右侧中间件
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(outer_length/2 + thickness/2, (outer_length - 2 * length)/2 - length/2 - 0.01, height/2)
    )
    c_shape_right_middle = bpy.context.active_object
    c_shape_right_middle.name = "C_Shape_Right_Middle_Metal"
    c_shape_right_middle.scale = (thickness, length, height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 8. 右侧合并
    bpy.ops.object.select_all(action='DESELECT')
    c_shape_right.select_set(True)
    c_shape_right_bottom.select_set(True)
    c_shape_right_middle.select_set(True)
    bpy.context.view_layer.objects.active = c_shape_right
    bpy.ops.object.join()
    c_shape_right.data.materials.clear()
    mat = create_metal_material()
    c_shape_right.data.materials.append(mat)
    
    c_shapes.append(c_shape_left)
    c_shapes.append(c_shape_right)

    return c_shapes, mat


def create_pins(dims, mat):
    """创建引脚"""
    pins = []

    outer_width = dims['housing_width']
    outer_height = dims['housing_height']
    wing_height = dims['wing_height']

    pin_width = dims['pin_width']
    pin_thickness = dims['pin_thickness']
    pin_pitch = dims['pin_pitch']

    foot_length = dims['total_width'] - dims['housing_width']

    # 1. 左侧引脚针
    pin_left = rounded_rect.create_rounded_rectangle(0, pin_width, outer_width * 0.75, pin_thickness, pin_width/2, 8, "bottom")
    pin_left.name = "Left_Pin_Metal"
    pin_left.delta_rotation_euler = (0, math.pi/2, 0)
    pin_left.location = (-pin_pitch/2 - pin_thickness/2, outer_width/8, outer_height/2)
    bpy.ops.object.transform_apply(scale=True)
    
    # 2. 左侧引脚腿板
    pin_left_leg = rounded_rect.create_rounded_rectangle(1, pin_width, wing_height, pin_thickness, pin_width/2, 8, "top")
    pin_left_leg.name = "Left_Pin_Column_Metal"
    pin_left_leg.delta_rotation_euler = (math.pi/2, 0, math.pi/2)
    pin_left_leg.location = (-pin_pitch/2 - pin_thickness/2, outer_width * 3/8 + pin_width, wing_height/2)
    bpy.ops.object.transform_apply(scale=True)

    # 3. 左侧引脚脚板
    pin_left_foot = rounded_rect.create_rounded_rectangle(2, pin_width, foot_length, pin_thickness, pin_width/2, 8, "top")
    pin_left_foot.name = "Left_Pin_Foot_Metal"
    pin_left_foot.delta_rotation_euler = (0, math.pi/2, 0)
    pin_left_foot.location = (-pin_pitch/2 - pin_thickness/2, outer_width/2 + foot_length/2, pin_width/2)
    bpy.ops.object.transform_apply(scale=True)

    # 4. 合并左侧引脚
    bpy.ops.object.select_all(action='DESELECT')
    pin_left.select_set(True)
    pin_left_leg.select_set(True)
    pin_left_foot.select_set(True)
    bpy.context.view_layer.objects.active = pin_left
    bpy.ops.object.join()
    pin_left.data.materials.clear()
    pin_left.data.materials.append(mat)
   
    # 5. 右侧引脚针
    pin_right = rounded_rect.create_rounded_rectangle(0, pin_width, outer_width * 0.75, pin_thickness, pin_width/2, 8, "bottom")
    pin_right.name = "Right_Pin_Metal"
    pin_right.delta_rotation_euler = (0, -math.pi/2, 0)
    pin_right.location = (pin_pitch/2 + pin_thickness/2, outer_width/8, outer_height/2)
    bpy.ops.object.transform_apply(scale=True)
   
    # 6. 右侧引脚腿板
    pin_right_leg = rounded_rect.create_rounded_rectangle(1, pin_width, wing_height, pin_thickness, pin_width/2, 8, "top")
    pin_right_leg.name = "Right_Pin_Column_Metal"
    pin_right_leg.delta_rotation_euler = (math.pi/2, 0, math.pi/2)
    pin_right_leg.location = (pin_pitch/2 + pin_thickness/2, outer_width * 3/8 + pin_width, wing_height/2)
    bpy.ops.object.transform_apply(scale=True)
    
    # 7. 右侧引脚脚板
    pin_right_foot = rounded_rect.create_rounded_rectangle(2, pin_width, foot_length, pin_thickness, pin_width/2, 8, "top")
    pin_right_foot.name = "Right_Pin_Foot_Metal"
    pin_right_foot.delta_rotation_euler = (0, -math.pi/2, 0)
    pin_right_foot.location = (pin_pitch/2 + pin_thickness/2, outer_width/2 + foot_length/2, pin_width/2)
    bpy.ops.object.transform_apply(scale=True)

    # 8. 合并右侧引脚
    bpy.ops.object.select_all(action='DESELECT')
    pin_right.select_set(True)
    pin_right_leg.select_set(True)
    pin_right_foot.select_set(True)
    bpy.context.view_layer.objects.active = pin_right
    bpy.ops.object.join()
    pin_right.data.materials.clear()
    pin_right.data.materials.append(mat)
   
    pins.append(pin_left)
    pins.append(pin_right)

    return pins

def create_lcp_material():
    """创建LCP（液晶聚合物）材质 - 米白色，耐高温"""
    mat = bpy.data.materials.new(name="LCP_Material")
    mat.use_nodes = True
    
    # 设置米白色
    lcp_color = mx125_2p_dimensions['color']
    mat.diffuse_color = lcp_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = lcp_color
    bsdf.inputs['Metallic'].default_value = 0.1
    bsdf.inputs['Roughness'].default_value = 0.6
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_metal_material():
    """创建金属引脚材质"""
    mat = bpy.data.materials.new(name="Metal_Pin_Material")
    mat.use_nodes = True
    
    # 设置金属色
    metal_color = (0.88, 0.88, 0.90, 1.0)
    mat.diffuse_color = metal_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = metal_color
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def create_mx125_2p(collection, dims = mx125_2p_dimensions):
    # 创建模型
    print("正在创建模型...")
    
    # 1. 创建外壳
    print("创建带有0.2mm壁厚的外壳...")
    housing, lcp_mat = create_housing_with_thickness(dims)
    bpy.context.scene.collection.objects.unlink(housing)
    collection.objects.link(housing)

    # 2. 创建两侧固定件
    print("创建两侧固定件...")
    wings = create_wings(dims, lcp_mat)
    for wing in wings:
        bpy.context.scene.collection.objects.unlink(wing)
        collection.objects.link(wing)

    # 3. 创建C形金属固定件
    print("创建C形金属固定件...")
    c_shapes, metal_mat = create_c_shape_metal(dims)
    for c_shape in c_shapes:
        bpy.context.scene.collection.objects.unlink(c_shape)
        collection.objects.link(c_shape)

    # 4. 创建引脚
    print("创建引脚...")
    pins = create_pins(dims, metal_mat)
    for pin in pins:
        bpy.context.scene.collection.objects.unlink(pin)
        collection.objects.link(pin)


def main():
    """主函数 - 创建带有0.2mm壁厚的MX1.25 2P模型"""
    # 清理场景
    clear_scene()
    
    print("=" * 60)
    print("创建带有0.2mm壁厚的MX1.25 2P连接器模型")
    print("=" * 60)
    
    dims = mx125_2p_dimensions
    
    # 创建集合
    collection = bpy.data.collections.new("MX125_2P_Wall")
    bpy.context.scene.collection.children.link(collection)

    create_mx125_2p(collection)
    
    print("尺寸参数:")
    print(f"  总长度: {dims['total_length']}mm")
    print(f"  总宽度: {dims['total_width']}mm")
    print(f"  总高度: {dims['total_height']}mm")
    print(f"  壳体壁厚: {dims['wall_thickness']}mm")
    print(f"  引脚间距: {dims['pin_pitch']}mm")
    print("")
    
    print("壳体结构:")
    print(f"  外部尺寸: {dims['total_length']}×{dims['total_width']}×{dims['total_height']}mm")
    print(f"  内部尺寸: {dims['total_length']-2*dims['wall_thickness']:.2f}×{dims['total_width']-2*dims['wall_thickness']:.2f}×{dims['total_height']-dims['wall_thickness']:.2f}mm")
    print("")
    
    
    print("")
    print("模型组件:")
    print("  1. 外壳 (LCP材质，壁厚0.2mm)")
    print("  2. 引脚 (金属材质，2个)")
    print("  3. 焊盘 (2个)")
    print("")
    print("壳体结构细节:")
    print(f"  - 外壳顶部封闭，底部开口")
    print(f"  - 壁厚均匀: {dims['wall_thickness']}mm")
    print(f"  - 材料: LCP液晶聚合物，耐高温")
    print(f"  - 颜色: 米白色")
    print("")
    print(f"模型已添加到集合: {collection.name}")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用正交视图
            area.spaces[0].region_3d.view_perspective = 'ORTHO'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 20
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.5, 0.5, 0.5, 0.5)
            # 设置显示模式
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
            
            # 设置白色背景，模拟产品照片
            area.spaces[0].shading.background_type = 'VIEWPORT'
            area.spaces[0].shading.background_color = (1.0, 1.0, 1.0)
            
            # 启用线框叠加显示，便于观察壁厚
            area.spaces[0].overlay.show_wireframes = True
    
    return collection

if __name__ == "__main__":
    collection = main()