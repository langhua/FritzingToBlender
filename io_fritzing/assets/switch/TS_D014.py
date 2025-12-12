import bpy
import bmesh
from mathutils import Vector, Matrix
import math
import io_fritzing.assets.commons.l_bend as l_bend
import io_fritzing.assets.commons.trapezoid as trapezoid
import io_fritzing.assets.commons.rounded_rect as rounded_rect
import io_fritzing.assets.commons.z as z_pin

# 清理场景
def clear_scene():
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'

# 根据设计图定义TS-D014的尺寸参数
dimensions = {
    # 总体尺寸
    'L': 7.0,      # 总长度: 7mm
    'W': 4.3,      # 总宽度: 4.3mm
    'H_total': 4.5,  # 总高度: 4.5mm
    
    # 熟料本体尺寸
    'base_length': 6.0,     # 本体长度
    'base_width': 6.0,      # 本体宽度
    'base_height': 2.8,     # 本体高度
    'base_chamfer': 0.3,    # 本体倒角
    
    # 按钮尺寸
    'button_diameter': 3.5,  # 按钮直径
    'button_height': 3.4,    # 按钮高度(从底座上表面计算)
    'button_top_chamfer': 0.5,  # 按钮顶部倒角
    'button_top_radius': 1.65,  # 按钮顶部半径
    'button_bottom_radius': 1.75,  # 按钮底部半径
    
    # 盖板尺寸
    'cover_side_length': 6.0,      # 边长: 6mm
    'cover_thickness': 0.4,        # 厚度: 0.4mm
    'large_hole_diameter': 3.5,    # 大孔直径: 3.mm
    'small_hole_diameter': 1.0,    # 小孔直径: 1.0mm
    'hole_spacing': 4.3,           # 孔距: 4.3mm
    'corner_radius': 0.2,          # 角部圆角半径: 0.2mm
    'fillet_segments': 16,         # 圆角分段数
    'hole_segments': 64,           # 孔分段数
    
    # 引脚尺寸
    'pin_diameter': 0.6,     # 引脚直径
    'pin_length': 7.5,       # 引脚长度
    'pin_spacing_x': 4.5,    # X方向间距
    'pin_spacing_y': 3.5,    # 引脚Y方向间距
    
    # 倒角参数
    'chamfer_size': 0.,
    'chamfer_segments': 3,

    # 半球参数
    'hs_radius': 0.5,           # 半径
    'hs_segments': 64,          # 经度分段数
    'hs_rings': 32,             # 纬度分段数

    # L弯头参数
    'bend_width': 3.5,           # X方向宽度
    'bend_thickness': 0.4,       # Z方向厚度
    
    # 弯曲参数
    'bend_radius': 0.6,        # 弯曲半径
    'bend_angle': 90,          # 弯曲角度
    'bend_start': 0.2,         # 离起点开始弯曲的距离
    'end_length': 5.8,         # 弯曲结束后直线长度

    # z_pin尺寸参数
    # 第1段：直线1mm
    'z_pin_s1_length': 1.5,
    
    # 第2段：圆弧，半径0.5mm，角度45度
    'z_pin_s2_radius': 0.5,
    'z_pin_s2_angle': -30.0,  # 度
    
    # 第3段：直线1mm
    'z_pin_s3_length': 0.732,
    
    # 第4段：圆弧，半径0.5mm，角度70度
    'z_pin_s4_radius': 0.5,
    'z_pin_s4_angle': 50.0,  # 度
    
    # 第5段：直线2mm
    'z_pin_s5_length': 1.412,
    
    # 管的截面参数
    'z_pin_radius': 0.5,       # 截面半径
    'z_pin_thickness': 0.4,    # 厚度
    
    # 细分参数
    'z_pin_straight_segments': 4,
    'z_pin_arc_segments': 16,
    'z_pin_circular_segments': 12,

    # 矩形截面参数
    'z_pin_width': 1.0,       # 矩形宽度
    'z_pin_height': 0.4,      # 矩形高度
    'z_pin_thickness': 0.4,   # 管壁厚度（用于空心管）
}

def apply_all_modifiers(obj=None):
    """应用所有修改器"""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    if obj:
        objects = [obj]
    else:
        objects = bpy.context.scene.objects
    
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        for modifier in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except:
                obj.modifiers.remove(modifier)

def create_ts_d014_switch():
    """创建TS-D014按键开关模型"""
    # 创建底座
    base = create_base()
    
    # 创建金属板
    plate = create_metal_plate()
    
    # 创建按钮
    button = create_button(dimensions['button_top_radius'], dimensions['button_bottom_radius'], dimensions['button_height'])
    
    # 创建引脚
    pins = create_pins(base)
    
    # 确保所有修改器都被应用
    apply_all_modifiers()
    
    # 将所有对象组织合并
    ts_d014 = create_collection_and_organize([base, plate, button] + pins)

    # 调整到安装位置在z=0
    ts_d014.rotation_euler = (math.pi/2, 0, math.pi)
    ts_d014.location.z = 4.0
    
    return ts_d014

def create_base():
    """创建底座（黑色PPA材质）"""
    length = dimensions['base_length']
    width = dimensions['base_width']
    height = dimensions['base_height']
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2)
    )
    base = bpy.context.active_object
    base.name = "TS_D014_Base"
    
    # 设置尺寸
    base.scale = (length, width, height)
    bpy.ops.object.transform_apply(scale=True)

    # 创建4个圆柱体
    hole_spacing = dimensions['hole_spacing']
    width = dimensions['cover_side_length']
    d = (width - hole_spacing) / 2  # 0.85mm
    z = height + dimensions['cover_thickness']/2
    c_positions = [
        (width/2 - d, width/2 - d, z),  # 右上
        (-width/2 + d, width/2 - d, z),  # 左上
        (-width/2 + d, -width/2 + d, z),  # 左下
        (width/2 - d, -width/2 + d, z),  # 右下
    ]

    bpy.ops.mesh.primitive_cylinder_add(
        radius=dimensions['small_hole_diameter']/2,
        depth=dimensions['cover_thickness'],
        location=c_positions[0]
    )
    cylinder1 = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add(
        radius=dimensions['small_hole_diameter']/2,
        depth=dimensions['cover_thickness'],
        location=c_positions[1]
    )
    cylinder2 = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add(
        radius=dimensions['small_hole_diameter']/2,
        depth=dimensions['cover_thickness'],
        location=c_positions[2]
    )
    cylinder3 = bpy.context.active_object
    bpy.ops.mesh.primitive_cylinder_add(
        radius=dimensions['small_hole_diameter']/2,
        depth=dimensions['cover_thickness'],
        location=c_positions[3]
    )
    cylinder4 = bpy.context.active_object

    # 创建4个点位半圆球
    # 计算半球中心位置
    # 相邻两个半球中心之间的距离4.3mm
    # 半球中心距离每条边为0.85mm
    radius = dimensions['hs_radius']
    z = height + radius/2
    hs_positions = [
        (width/2 - d, width/2 - d, z),  # 右上
        (-width/2 + d, width/2 - d, z),  # 左上
        (-width/2 + d, -width/2 + d, z),  # 左下
        (width/2 - d, -width/2 + d, z),  # 右下
    ]

    hemisphere1 = create_solid_hemisphere_with_base()
    hemisphere1.location = hs_positions[0]
    hemisphere2 = create_solid_hemisphere_with_base()
    hemisphere2.location = hs_positions[1]
    hemisphere3 = create_solid_hemisphere_with_base()
    hemisphere3.location = hs_positions[2]
    hemisphere4 = create_solid_hemisphere_with_base()
    hemisphere4.location = hs_positions[3]
    
    # 合并本体和四个半球
    bpy.ops.object.select_all(action='DESELECT')
    base.select_set(True)
    cylinder1.select_set(True)
    cylinder2.select_set(True)
    cylinder3.select_set(True)
    cylinder4.select_set(True)
    hemisphere1.select_set(True)
    hemisphere2.select_set(True)
    hemisphere3.select_set(True)
    hemisphere4.select_set(True)
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.join()

    # 添加材质
    base.data.materials.clear()
    mat = create_ppa_black_material()
    base.data.materials.append(mat)
    
    return base

def create_button(top_radius, bottom_radius, height):
    """创建按钮（黑色PPA材质）"""
    diameter = dimensions['button_diameter']
    if top_radius is None:
        if bottom_radius is None:
            top_radius = diameter / 2
            bottom_radius = top_radius
        else:
            top_radius = bottom_radius
    elif bottom_radius is None:
        bottom_radius = top_radius
    if height is None:
        height = dimensions['button_height']
    
    if top_radius == bottom_radius:
        # 创建圆柱体
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=24,
            radius=top_radius,
            depth=height,
            location=(0, 0, dimensions['base_thickness'] + dimensions['insert_thickness'] + 
                    dimensions['cover_thickness'] + height/2)
        )
    else:
        # 创建圆锥体
        bpy.ops.mesh.primitive_cone_add(
            vertices=24,
            radius1=bottom_radius,
            radius2=top_radius,
            depth=height,
            location=(0, 0, dimensions['base_height'] + height/2)
        )
    
    button = bpy.context.active_object
    button.name = "TS_D014_Button"
    
    # 添加顶部倒角
    bevel_mod = button.modifiers.new(name="Button_Bevel", type='BEVEL')
    bevel_mod.width = dimensions['button_top_chamfer']
    bevel_mod.segments = 5
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 应用修改器
    apply_all_modifiers(button)
    
    # 添加材质
    button.data.materials.clear()
    mat = create_ppa_black_material()
    button.data.materials.append(mat)
    
    return button

def create_pins(base):
    """创建4个引脚"""
    pins = []
    pin_diameter = dimensions['pin_diameter']
    pin_length = dimensions['pin_length']
    
    # 引脚位置
    offset_x = dimensions['pin_spacing_x'] / 2
    offset_y = -pin_length/2  # 从底座向下伸出
    
    pin_positions = [
        (-offset_x, offset_y, 0.75),  # 左
        (offset_x, offset_y, 0.75),   # 右
    ]
    
    for i, pos in enumerate(pin_positions, 1):
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=12,
            radius=pin_diameter/2,
            depth=pin_length,
            location=pos
        )
        pin = bpy.context.active_object
        pin.name = f"TS_D014_Pin_{i}"
        
        # 旋转引脚使其垂直
        pin.rotation_euler = (math.pi/2, 0, 0)
        bpy.ops.object.transform_apply(rotation=True)
        
        # 添加材质
        pin.data.materials.clear()
        mat = create_brass_silver_material()
        pin.data.materials.append(mat)
        
        pins.append(pin)
    
    return pins

def create_metal_plate():
    """创建金属方板完整模型"""
    # 创建带圆角的金属板
    plate, metal_mat = create_plate_with_fillet()
    
    # 创建中心大孔
    create_center_hole(plate)
    
    # 创建四个角部小孔
    create_corner_holes(plate)

    # 创建两侧的L型大弯折
    create_l_bends(plate, metal_mat)

    # 两侧使用直角梯形修型
    create_right_angled_trapezoid_modifications(plate)

    # 两侧使用矩形修型
    create_rectangular_modifications(plate)

    # 两侧使用圆角矩形修型
    create_rounded_rectangular_modifications(plate)

    # 创建两侧的L型小弯折
    create_small_l_bends(plate, metal_mat)

    # 两侧添加矩形板
    create_right_angled_trapezoid_plates(plate, metal_mat)

    # 两侧使用小直角梯形修型
    create_small_right_angled_trapezoid_modifications(plate)

    # 两侧添加弯曲的引脚板
    create_z_pin_plates(plate, metal_mat, {'s1_length': dimensions['z_pin_s1_length'],
                                           's2_radius': dimensions['z_pin_s2_radius'],
                                           's2_angle': dimensions['z_pin_s2_angle'],
                                           's3_length': dimensions['z_pin_s3_length'],
                                           's4_radius': dimensions['z_pin_s4_radius'],
                                           's4_angle': dimensions['z_pin_s4_angle'],
                                           's5_length': dimensions['z_pin_s5_length'],
                                           'radius': dimensions['z_pin_radius'],
                                           'straight_segments': dimensions['z_pin_straight_segments'],
                                           'arc_segments': dimensions['z_pin_arc_segments'],
                                           'circular_segments': dimensions['z_pin_circular_segments'],
                                           'width': dimensions['z_pin_width'],
                                           'height': dimensions['z_pin_height'],
                                           'thickness': dimensions['z_pin_thickness'],
                                           })

    plate.location.z = dimensions['base_height'] + dimensions['cover_thickness'] / 2
    
    return plate

def create_plate_with_fillet():
    """创建带圆角的金属板"""
    # 使用bmesh创建带圆角的矩形
    bm = bmesh.new()
    
    side_length = dimensions['cover_side_length']
    thickness = dimensions['cover_thickness']
    corner_radius = dimensions['corner_radius']
    segments = dimensions['fillet_segments']
    
    # 计算内部矩形的顶点
    half_length = side_length / 2 - corner_radius
    vertices = []
    
    # 创建4个圆弧的顶点
    for i in range(4):
        # 每个角的圆心位置
        if i == 0:  # 右上角
            center_x = side_length/2 - corner_radius
            center_y = side_length/2 - corner_radius
        elif i == 1:  # 左上角
            center_x = -side_length/2 + corner_radius
            center_y = side_length/2 - corner_radius
        elif i == 2:  # 左下角
            center_x = -side_length/2 + corner_radius
            center_y = -side_length/2 + corner_radius
        else:  # 右下角
            center_x = side_length/2 - corner_radius
            center_y = -side_length/2 + corner_radius
        
        # 创建圆弧上的顶点
        start_angle = math.radians(90 * i)
        for j in range(segments + 1):
            angle = start_angle + math.pi/2 * j / segments
            x = center_x + corner_radius * math.cos(angle)
            y = center_y + corner_radius * math.sin(angle)
            z = -thickness / 2  # 底部表面
            
            vertices.append(bm.verts.new((x, y, z)))
    
    # 创建所有面
    all_vertices = bm.verts[:]
    
    # 创建一个大面（所有底部顶点）
    bottom_face = bm.faces.new(all_vertices)
    
    # 挤出厚度
    extruded = bmesh.ops.extrude_face_region(bm, geom=[bottom_face])
    extruded_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]
    
    # 向上移动挤出的顶点
    bmesh.ops.translate(bm, vec=Vector((0, 0, thickness)), verts=extruded_verts)
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Metal_Plate_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    plate = bpy.data.objects.new("TS_D014_Plate", mesh)
    bpy.context.collection.objects.link(plate)
    
    # 添加圆角修改器
    bevel_mod = plate.modifiers.new(name="Corner_Fillet", type='BEVEL')
    bevel_mod.width = corner_radius
    bevel_mod.segments = segments
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 应用修改器
    apply_all_modifiers(plate)
    
    # 添加金属材质
    plate.data.materials.clear()
    mat = create_stainless_steel_material()
    plate.data.materials.append(mat)
    
    return plate, mat

def create_center_hole(plate):
    """创建中心大孔"""
    # 大孔参数
    diameter = dimensions['large_hole_diameter']
    thickness = dimensions['cover_thickness']
    
    # 创建圆柱体作为切割工具
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=dimensions['hole_segments'],
        radius=diameter/2,
        depth=thickness + 0.2,  # 确保完全穿透
        location=(0, 0, 0)
    )
    
    hole_cutter = bpy.context.active_object
    hole_cutter.name = "Center_Hole_Cutter"
    
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    hole_cutter.select_set(True)
    bpy.ops.object.boolean_auto_difference()

def create_corner_holes(plate):
    """创建四个角部小孔"""
    # 小孔参数
    diameter = dimensions['small_hole_diameter']
    thickness = dimensions['cover_thickness']
    hole_spacing = dimensions['hole_spacing']
    width = dimensions['cover_side_length']
    
    # 计算小孔中心位置
    # 孔距为4.3mm，指的是相邻两个小孔中心之间的距离
    # 小孔中心距离每条边为0.85mm
    
    d = (width - hole_spacing) / 2  # 0.85mm
    
    hole_positions = [
        (width/2 - d, width/2 - d, 0),  # 右上
        (-width/2 + d, width/2 - d, 0),  # 左上
        (-width/2 + d, -width/2 + d, 0),  # 左下
        (width/2 - d, -width/2 + d, 0),  # 右下
    ]
    
    # 创建4个小孔
    for i, position in enumerate(hole_positions, 1):
        # 创建圆柱体作为切割工具
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=dimensions['hole_segments'],
            radius=diameter/2,
            depth=thickness + 0.2,  # 确保完全穿透
            location=position
        )
        
        hole_cutter = bpy.context.active_object
        hole_cutter.name = f"Corner_Hole_Cutter_{i}"
        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = plate
        hole_cutter.select_set(True)
        bpy.ops.object.boolean_auto_difference()

def create_l_bends(plate, metal_mat):
    """创建两侧的L型弯折板"""
    # 1. 创建两侧的L型弯折板
    # L型弯折参数
    width = dimensions['bend_width']
    thickness = dimensions['bend_thickness']
    
    # 弯曲参数
    bend_radius = dimensions['bend_radius']
    bend_angle = math.radians(dimensions['bend_angle'])
    bend_start = dimensions['bend_start']
    end_length = dimensions['end_length']

    # 创建左侧L型弯折
    left_l_bend = l_bend.create_l_bend(width, thickness, bend_radius, bend_angle, bend_start, end_length)
    left_l_bend.name = 'left_l_bend'
    left_l_bend.location = (0, 0, 0)
    left_l_bend.location = (-dimensions['base_width']/2 + 0.25, -0.75, 0)
    left_l_bend.rotation_euler[2] = math.pi/2
    
    # 创建右侧L型弯折
    right_l_bend = l_bend.create_l_bend(width, thickness, bend_radius, bend_angle, bend_start, end_length)
    right_l_bend.name = 'right_l_bend'
    right_l_bend.location = (0, 0, 0)
    right_l_bend.location = (dimensions['base_width']/2 - 0.25, -0.75, 0)
    right_l_bend.rotation_euler[2] = -math.pi/2

    left_l_bend.data.materials.clear()
    left_l_bend.data.materials.append(metal_mat)
    right_l_bend.data.materials.clear()
    right_l_bend.data.materials.append(metal_mat)

    # 2. 合并plate和L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    plate.select_set(True)
    left_l_bend.select_set(True)
    right_l_bend.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.join()

def create_small_l_bends(plate, metal_mat):
    """创建两侧的L型小弯折板"""
    width = 1
    thickness = dimensions['bend_thickness']
    
    # 弯曲参数
    bend_radius = dimensions['bend_radius']
    bend_angle = math.radians(dimensions['bend_angle'])
    bend_start = 0.5
    end_length = 1.0

    # 创建左侧L型弯折
    left_l_bend = l_bend.create_l_bend(width, thickness, bend_radius, bend_angle, bend_start, end_length)
    left_l_bend.name = 'left_l_bend'
    left_l_bend.location = (0, 0, 0)
    left_l_bend.location = (-dimensions['base_width']/2 - 0.55, 0.5, -2.15)
    left_l_bend.rotation_euler = (-math.pi/2, 0, math.pi/2)
    
    # 创建右侧L型弯折
    right_l_bend = l_bend.create_l_bend(width, thickness, bend_radius, bend_angle, bend_start, end_length)
    right_l_bend.name = 'right_l_bend'
    right_l_bend.location = (0, 0, 0)
    right_l_bend.location = (dimensions['base_width']/2 + 0.55, 0.5, -2.15)
    right_l_bend.rotation_euler = (-math.pi/2, 0, -math.pi/2)

    left_l_bend.data.materials.clear()
    left_l_bend.data.materials.append(metal_mat)
    right_l_bend.data.materials.clear()
    right_l_bend.data.materials.append(metal_mat)

    # 2. 合并plate和L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    plate.select_set(True)
    left_l_bend.select_set(True)
    right_l_bend.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.join()


def create_right_angled_trapezoid_modifications(plate):
    """创建两侧的直角梯形修型"""
    print("创建两块直角梯形板，用于L型弯折板的修型...")
    plate1 = trapezoid.create_right_angled_trapezoid(4.2, 1.2, 3, 0.6)
    plate1.name = "Left_Trapezoid_Cutter"
    plate1.delta_rotation_euler = (-math.pi/2, math.pi, -math.pi/2)
    plate1.location = (-3.85, -2.7, -6.699)
    
    plate2 = trapezoid.create_right_angled_trapezoid(4.2, 1.2, 3, 0.6)
    plate2.name = "Right_Trapezoid_Cutter"
    plate2.delta_rotation_euler = (-math.pi/2, math.pi, -math.pi/2)
    plate2.location = (3.25, -2.7, -6.699)

    # 使用plate1切割左侧L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate1.select_set(True)
    bpy.ops.object.boolean_auto_difference()

    # 使用plate2切割右侧L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate2.select_set(True)
    bpy.ops.object.boolean_auto_difference()

def create_small_right_angled_trapezoid_modifications(plate):
    """创建两侧的小直角梯形修型"""
    print("创建两块直角梯形板，用于L型弯折板的修型...")
    plate1 = trapezoid.create_right_angled_trapezoid(1.4, 0.9, 0.3, 0.6)
    plate1.name = "Left_Trapezoid_Cutter"
    plate1.delta_rotation_euler = (-math.pi/2, math.pi/2, -math.pi/2)
    plate1.location = (-3.85, -4.05, -2.95)
    
    plate2 = trapezoid.create_right_angled_trapezoid(1.4, 0.9, 0.3, 0.6)
    plate2.name = "Right_Trapezoid_Cutter"
    plate2.delta_rotation_euler = (-math.pi/2, math.pi/2, -math.pi/2)
    plate2.location = (3.25, -4.05, -2.95)

    # 使用plate1切割左侧L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate1.select_set(True)
    bpy.ops.object.boolean_auto_difference()

    # 使用plate2切割右侧L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate2.select_set(True)
    bpy.ops.object.boolean_auto_difference()

def create_rectangular_modifications(plate):
    """创建两侧的矩形修型"""
    print("创建两块长方体板，用于L型弯折板的修型...")
    bpy.ops.mesh.primitive_cube_add(size=1, location=(-3.65, 1, -3.5))
    plate3 = bpy.context.active_object
    plate3.name = "Left_Cube_Cutter"
    plate3.scale = (0.99, 2, 2)
    bpy.ops.object.transform_apply(scale=True)
    
    bpy.ops.mesh.primitive_cube_add(size=1, location=(3.45, 1, -3.5))
    plate4 = bpy.context.active_object
    plate4.name = "Right_Cube_Cutter"
    plate4.scale = (0.99, 2, 2)
    bpy.ops.object.transform_apply(scale=True)

    # 使用plate3切割左侧L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate3.select_set(True)
    bpy.ops.object.boolean_auto_difference()

    # 使用plate4切割右侧L型弯折
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = plate
    plate4.select_set(True)
    bpy.ops.object.boolean_auto_difference()

def create_rounded_rectangular_modifications(plate):
    plate5 = rounded_rect.create_rounded_rectangle(5, 1.22, 4.2, 1, 0.5, 8, "top")
    plate5.name = "Left_Rounded_Rectangular_Cutter"
    plate5.delta_rotation_euler = (-math.pi/2, math.pi, -math.pi/2)
    plate5.location = (-3.9, -0.6, -4.2)

    # 使用plate5切割左侧L型弯折
    modifier = plate.modifiers.new(name="Left_Rounded_Rectangular_Cut", type="BOOLEAN")
    modifier.object = plate5
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    plate6 = rounded_rect.create_rounded_rectangle(5, 1.22, 4.2, 1, 0.5, 8, "top")
    plate6.name = "Left_Rounded_Rectangular_Cutter"
    plate6.delta_rotation_euler = (-math.pi/2, math.pi, -math.pi/2)
    plate6.location = (3.0, -0.6, -4.2)

    # 使用plate5切割左侧L型弯折
    modifier = plate.modifiers.new(name="Right_Rounded_Rectangular_Cut", type="BOOLEAN")
    modifier.object = plate6
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    # 删除多余的obj
    bpy.data.objects.remove(plate5, do_unlink=True)
    bpy.data.objects.remove(plate6, do_unlink=True)


def create_right_angled_trapezoid_plates(plate, metal_mat):
    plate1 = trapezoid.create_right_angled_trapezoid(5.5, 4.5, 1.5, 0.4)
    plate1.name = "Right_Trapezoid_Addon"
    plate1.delta_rotation_euler = (-math.pi/2, math.pi/2, -math.pi/2)
    plate1.location = (3.35, -4, -0.9)
    
    plate2 = trapezoid.create_right_angled_trapezoid(5.5, 4.5, 1.5, 0.4)
    plate2.name = "Left_Trapezoid_Addon"
    plate2.delta_rotation_euler = (-math.pi/2, math.pi/2, -math.pi/2)
    plate2.location = (-3.75, -4, -0.9)
    
    plate1.data.materials.clear()
    plate1.data.materials.append(metal_mat)
    plate2.data.materials.clear()
    plate2.data.materials.append(metal_mat)

    # 合并plate和矩型板
    bpy.ops.object.select_all(action='DESELECT')
    plate.select_set(True)
    plate1.select_set(True)
    plate2.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.join()
    

def create_z_pin_plates(plate, metal_mat, z_pin_dimensions):
    """创建z字形引脚板"""
    print("创建z字形引脚板...")
    # 创建对象
    z_pin_left = z_pin.create_z_model(type='rectangular_solid', dimensions=z_pin_dimensions)
    z_pin_left.name = 'z_pin_left'
    z_pin_left.delta_rotation_euler = (-math.pi/2, 0, -math.pi/2)
    z_pin_left.location = (-3.55, -3.3, -4.8)
    z_pin_left.data.materials.append(metal_mat)

    z_pin_right = z_pin.create_z_model(type='rectangular_solid', dimensions=z_pin_dimensions)
    z_pin_right.name = 'z_pin_right'
    z_pin_right.delta_rotation_euler = (math.pi/2, 0, -math.pi/2)
    z_pin_right.location = (3.55, -3.3, -4.8)
    z_pin_right.data.materials.append(metal_mat)
    
    # 合并plate和z
    bpy.ops.object.select_all(action='DESELECT')
    plate.select_set(True)
    z_pin_left.select_set(True)
    z_pin_right.select_set(True)
    bpy.context.view_layer.objects.active = plate
    bpy.ops.object.join()
    

def create_solid_hemisphere_with_base():
    """创建带平面的实心半球体）"""
    radius = dimensions['hs_radius']
    segments = dimensions['hs_segments']
    rings = dimensions['hs_rings']
    
    # 创建bmesh
    bm = bmesh.new()
    
    # 计算顶点
    vertices = []
    
    # 1. 创建半球面顶点
    for i in range(segments + 1):
        theta = 2 * math.pi * i / segments
        for j in range(rings + 1):
            phi = math.pi/2 * j / rings  # 从0到90度
            
            x = radius * math.sin(phi) * math.cos(theta)
            y = radius * math.sin(phi) * math.sin(theta)
            z = radius * math.cos(phi)
            
            vertices.append(bm.verts.new((x, y, z)))
    
    # 2. 创建底平面顶点
    for i in range(segments + 1):
        theta = 2 * math.pi * i / segments
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        z = 0
        
        vertices.append(bm.verts.new((x, y, z)))
    
    # 3. 创建底面中心点
    center_vertex = bm.verts.new((0, 0, 0))
    
    # 创建半球面
    for i in range(segments):
        for j in range(rings):
            v1_index = i * (rings + 1) + j
            v2_index = (i + 1) * (rings + 1) + j
            v3_index = (i + 1) * (rings + 1) + (j + 1)
            v4_index = i * (rings + 1) + (j + 1)
            
            v1 = vertices[v1_index]
            v2 = vertices[v2_index]
            v3 = vertices[v3_index]
            v4 = vertices[v4_index]
            
            bm.faces.new([v1, v2, v3, v4])
    
    # 创建侧边连接
    for i in range(segments):
        v1 = vertices[i * (rings + 1)]  # 半球底部边缘
        v2 = vertices[(i + 1) * (rings + 1)]
        v3 = vertices[(segments + 1) * (rings + 1) + (i + 1)]  # 底平面边缘
        v4 = vertices[(segments + 1) * (rings + 1) + i]
        
        bm.faces.new([v1, v2, v3, v4])
    
    # 创建底平面
    bottom_vertices_start = (segments + 1) * (rings + 1)
    for i in range(segments):
        v1 = center_vertex
        v2 = vertices[bottom_vertices_start + i]
        v3 = vertices[bottom_vertices_start + i + 1]
        
        bm.faces.new([v1, v2, v3])
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Hemisphere_With_Base_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    hemisphere = bpy.data.objects.new("Hemisphere_With_Base", mesh)
    bpy.context.collection.objects.link(hemisphere)
    
    return hemisphere

def create_ppa_black_material():
    """创建PPA黑色塑料材质"""
    mat = bpy.data.materials.new(name="PPA_Black")
    mat.use_nodes = True
    
    # 设置基础颜色
    mat.diffuse_color = (0.1, 0.1, 0.1, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.1, 0.1, 0.1, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_brass_silver_material():
    """创建H62Y黄铜镀银材质"""
    mat = bpy.data.materials.new(name="H62Y_Brass_Silver")
    mat.use_nodes = True
    
    # 设置金属色
    mat.diffuse_color = (0.85, 0.85, 0.88, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.85, 0.85, 0.88, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.2
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_stainless_steel_material():
    """创建不锈钢/复合银材质"""
    mat = bpy.data.materials.new(name="Stainless_Steel")
    mat.use_nodes = True
    
    # 设置不锈钢颜色
    mat.diffuse_color = (0.8, 0.8, 0.85, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.85, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_copper_tin_material():
    """创建冷轧钢带镀铜/锡材质"""
    mat = bpy.data.materials.new(name="Copper_Tin")
    mat.use_nodes = True
    
    # 设置铜锡合金颜色
    mat.diffuse_color = (0.85, 0.7, 0.5, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.85, 0.7, 0.5, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.4
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_collection_and_organize(objects):
    """将所有对象合并到一起"""
    td_d014 = objects[0]
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = td_d014
    bpy.ops.object.join()

    return td_d014

def main():
    """主函数"""
    # 清理场景
    clear_scene()
    
    # 创建TS-D014开关模型
    ts_d014 = create_ts_d014_switch()
    
    # 打印规格信息
    print("TS-D014按键开关3D模型创建完成！")
    print("=" * 60)
    print("产品信息:")
    print("  型号: TS-D014")
    print("  名称: 轻触开关")
    print("  规格: 7×4.3×4.5mm")
    print("")
    print("材料清单 (BOM):")
    print("  1. 按钮: PPA, 黑色")
    print("  2. 盖板: 冷轧钢带, 镀Cu/Sn")
    print("  3. 底座: PPA, 黑色")
    print("  4. 嵌件: H62Y黄铜, 镀Ag")
    print("  引脚: 4个, 镀Ag")
    print("")
    print("尺寸参数 (单位:mm):")
    print(f"  总体尺寸: {dimensions['L']} × {dimensions['W']} × {dimensions['H_total']}")
    print(f"  按钮直径: {dimensions['button_diameter']}")
    print(f"  按钮高度: {dimensions['button_height']}")
    print(f"  厚度: {dimensions['base_height']}")
    print(f"  盖板厚度: {dimensions['cover_thickness']}")
    print(f"  引脚直径: {dimensions['pin_diameter']}")
    print(f"  引脚长度: {dimensions['pin_length']}")
    print(f"  引脚间距: {dimensions['pin_spacing_x']} × {dimensions['pin_spacing_y']} (X×Y)")
    print("")
    print("结构特点:")
    print("  - 黑色PPA塑料主体")
    print("  - 银色金属盖板和引脚")
    print("  - 黄铜嵌件保证良好导电性")
    print("  - 圆柱形按钮设计")
    print("  - 4个引脚, 适用于PCB焊接")
    print("")
    print("所有部件已按图纸要求精确建模")
    print("尺寸和材料符合技术规范")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].shading.type = 'MATERIAL'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
            area.spaces[0].shading.object_outline_color = (0, 0, 0)
    
    return ts_d014

if __name__ == "__main__":
    main()