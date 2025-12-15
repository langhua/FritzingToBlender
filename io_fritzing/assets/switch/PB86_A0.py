import bpy
import bmesh
from mathutils import Vector
import math
import io_fritzing.assets.commons.triangle as triangle
import io_fritzing.assets.commons.rounded_rect as rounded_rect
import io_fritzing.assets.commons.frustum as frustum
import io_fritzing.assets.commons.trapezoid as trapezoid

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

# 根据技术图纸定义PB86-A0按键准确尺寸
pb86_a0_dimensions = {
    # 按键整体尺寸
    'length': 17.6,         # 按键长度
    'width': 12.5,          # 按键宽度
    
    # 按键帽尺寸
    'button_protrusion_height': 2.0,      # 按键凸出高度
    'button_protrusion_width': 10.1,      # 按键凸出宽度
    'button_radius': 0.5,                 # 按键圆角半径
    'button_cap_board_width': 3.3,        # 按键帽板宽（按键帽前左右板的上下两边宽度）
    'button_cap_backboard_width': 4.7,    # 按键帽后板宽（后板的上下两边宽度）
    'button_cap_width': 12.3,             # 按键帽宽度
    'button_cap_board_thickness': 1.0,    # 按键帽壁厚
    'button_cap_length': 17.0,            # 按键帽长度
    'button_cap_backboard_height': 11.5,  # 按键帽后板高度（底座底部到后板顶部的距离）
    'button_cap_cross_h_width': 4.0,      # 按键十字柱水平宽度
    'button_cap_cross_v_width': 1.7,      # 按键十字柱垂直宽度
    
    # 引脚尺寸
    'pin_spacing': 5.08,       # 引脚间距
    'pin_width': 0.8,          # 引脚宽度
    'pin_thickness': 0.4,      # 引脚厚度
    'pin_length': 3.5,         # 引脚长度
    'pin_stage_height': 0.5,   # 引脚台阶高度'
    'pin_stage_width': 2.4,    # 引脚基座宽度

    # 固定钉尺寸
    'nail_stage_width': 1.8,   # 固定钉基座宽度
    'nail_stage_height': 0.8,  # 固定钉基座高度
    'nail_height': 1.8,        # 固定钉高度
    'nail_diameter': 0.8,      # 固定钉直径
    'nail_stage_spacing': 7.62,      # 固定钉基座间距
    
    # 底座尺寸
    'base_height': 6.7,              # 底座高度
    'base_front_height': 5.9,        # 底座前高
    
    'base_wing_height': 4.4,         # 底座翼高
    'base_wing_width': 1.2,          # 底座翼宽
    'base_wing_depth': 1.7,          # 底座翼深
    'base_wing_bottom_thickness': 0.7,        # 底座翼底部厚度
    'base_wing_slot_width': 2.8,     # 底座翼槽宽

    'base_front_slot_width': 2.6,    # 底座前槽宽
    'base_front_slot_depth': 1.0,    # 底座前槽深
    'base_front_slot_bottom_thickness': 1.9,  # 底座前槽底部厚度
}

def create_pb86_button(dims = pb86_a0_dimensions, color = 'Black'):
    """创建PB86按键完整模型"""
    # 创建主集合
    collection = bpy.data.collections.new("PB86_A0_Button")
    bpy.context.scene.collection.children.link(collection)

    if color.capitalize() == 'Red':
        print("选择红色按键帽")
        button_cap_color = ((0.8, 0.2, 0.2, 1.0), 0.5, 0.0)
    elif color.capitalize() == 'Blue':
        print("选择蓝色按键帽")
        button_cap_color = ((0.2, 0.2, 0.8, 1.0), 0.5, 0.0)
    elif color.capitalize() == 'Green':
        print("选择绿色按键帽")
        button_cap_color = ((0.2, 0.8, 0.2, 1.0), 0.5, 0.0)
    elif color.capitalize() == 'Yellow':
        print("选择黄色按键帽")
        button_cap_color = ((0.8, 0.8, 0.2, 1.0), 0.5, 0.0)
    elif color.capitalize() == 'White':
        print("选择白色按键帽")
        button_cap_color = ((0.9, 0.9, 0.9, 1.0), 0.5, 0.0)
    elif color.capitalize() == 'Gray' or color.capitalize() == 'Grey':
        print("选择灰色按键帽")
        button_cap_color = ((0.5, 0.5, 0.5, 1.0), 0.5, 0.0)
    else:
        print("选择默认按键帽（黑色）")
        button_cap_color = ((0.1, 0.1, 0.1, 1.0), 0.5, 0.0)

    # 1. 创建底座（黑色，PA66材料）
    print("创建底座...")
    base, pa66_mat = create_base(dims)
    bpy.context.scene.collection.objects.unlink(base)
    collection.objects.link(base)
    
    # 2. 创建固定钉（黑色，PA66材料）
    print("创建固定钉...")
    fixed_nails = create_fixed_nails(dims, pa66_mat)
    for obj in fixed_nails:
        bpy.context.scene.collection.objects.unlink(obj)
        collection.objects.link(obj)
    
    # 3. 创建引脚
    print("创建引脚...")
    pins = create_pins(dims, pa66_mat)
    for obj in pins:
        bpy.context.scene.collection.objects.unlink(obj)
        collection.objects.link(obj)

    # 4. 创建按键帽（ABS材料）
    print("创建按键帽...")
    button_cap, abs_mat = create_button_cap(dims, color = button_cap_color)
    collection.objects.link(button_cap)

    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = collection.objects[0]
    bpy.ops.object.join()
    
    return collection


def create_base(dims):
    """创建底座 - PA66材料，黑色"""
    bm = bmesh.new()
    
    width = dims['width']
    length = dims['length']
    base_height = dims['base_height']
    front_height = dims['base_front_height']
    nail_stage_height = dims['nail_stage_height']

    front_slot_depth = dims['base_front_slot_depth']
    front_slot_width = dims['base_front_slot_width']
    front_slot_bottom_thickness = dims['base_front_slot_bottom_thickness']

    base_wing_slot_width = dims['base_wing_slot_width']
    base_wing_depth = dims['base_wing_depth']
    base_wing_width = dims['base_wing_width']
    base_wing_bottom_thickness = dims['base_wing_bottom_thickness']
    base_wing_height = dims['base_wing_height']
    
    # 1. 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, base_height/2 + nail_stage_height)
    )
    base = bpy.context.active_object
    base.name = "PB86_A0_Base"
    base.scale = (length, width, base_height)

    # 2. 开正面中心槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(length/2 - front_slot_depth/2 + 0.01, 0, base_height/2 + nail_stage_height + front_slot_bottom_thickness/2 + 0.01)
    )
    front_slot_cutter = bpy.context.active_object
    front_slot_cutter.name = "PB86_A0_Front_Slot_Cutter"
    front_slot_cutter.scale = (front_slot_depth + 0.02, front_slot_width, base_height - front_slot_bottom_thickness + 0.02)

    modifier = base.modifiers.new(name="Front_Slot_Cut", type="BOOLEAN")
    modifier.object = front_slot_cutter
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(front_slot_cutter, do_unlink=True)

    # 3. 开背面中心槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-length/2 + front_slot_depth/2 - 0.01, 0, base_height/2 + nail_stage_height + front_slot_bottom_thickness/2 + 0.01)
    )
    back_slot_cutter = bpy.context.active_object
    back_slot_cutter.name = "PB86_A0_Back_Slot_Cutter"
    back_slot_cutter.scale = (front_slot_depth + 0.02, front_slot_width, base_height - front_slot_bottom_thickness + 0.02)

    modifier = base.modifiers.new(name="Back_Slot_Cut", type="BOOLEAN")
    modifier.object = back_slot_cutter
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(back_slot_cutter, do_unlink=True)

    # 4. 顶部切掉一个斜角
    top_slope_cutter = triangle.create_right_triangular_prism(
            base_a = length * 0.4 + 0.02,
            base_b = base_height - front_height + 0.02,
            height = width + 0.02
    )
    top_slope_cutter.name = "PB86_A0_Top_Slope_Cutter"
    top_slope_cutter.rotation_euler = (-math.pi/2, 0, math.pi)
    top_slope_cutter.location = (length/2 + 0.01, width/2 + 0.01, base_height/2 + nail_stage_height * 1.5 + front_height/2 + 0.01)

    modifier = base.modifiers.new(name="Top_Slope_Cut", type="BOOLEAN")
    modifier.object = top_slope_cutter
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(top_slope_cutter, do_unlink=True)

    # 5. 开左侧槽
    # 5.1 开左侧竖槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-length/2 + base_wing_width + base_wing_slot_width/2, -width/2 + base_wing_depth/2 - 0.01, base_height/2 + nail_stage_height + base_wing_bottom_thickness/2 + 0.01)
    )
    left_slot_cutter1 = bpy.context.active_object
    left_slot_cutter1.name = "PB86_A0_Left_Slot_Cutter1"
    left_slot_cutter1.scale = (base_wing_slot_width, base_wing_depth + 0.02, base_height - base_wing_bottom_thickness + 0.02)

    modifier = base.modifiers.new(name="Left_Slot_Cutter1", type="BOOLEAN")
    modifier.object = left_slot_cutter1
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(left_slot_cutter1, do_unlink=True)

    # 5.2 开左侧水平槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-length/2 + base_wing_width/2 + 0.01, -width/2 + base_wing_depth/2 - 0.01, base_height/2 + nail_stage_height + base_wing_height/2 + 0.01)
    )
    left_slot_cutter2 = bpy.context.active_object
    left_slot_cutter2.name = "PB86_A0_Left_Slot_Cutter2"
    left_slot_cutter2.scale = (base_wing_width + 0.02, base_wing_depth + 0.02, base_height - base_wing_height + 0.02)

    modifier = base.modifiers.new(name="Left_Slot_Cutter2", type="BOOLEAN")
    modifier.object = left_slot_cutter2
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(left_slot_cutter2, do_unlink=True)

    # 6. 开右侧槽
    # 6.1 开右侧竖槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-length/2 + base_wing_width + base_wing_slot_width/2, width/2 - base_wing_depth/2 + 0.01, base_height/2 + nail_stage_height + base_wing_bottom_thickness/2 + 0.01)
    )
    right_slot_cutter1 = bpy.context.active_object
    right_slot_cutter1.name = "PB86_A0_Right_Slot_Cutter1"
    right_slot_cutter1.scale = (base_wing_slot_width, base_wing_depth + 0.02, base_height - base_wing_bottom_thickness + 0.02)

    modifier = base.modifiers.new(name="Right_Slot_Cutter1", type="BOOLEAN")
    modifier.object = right_slot_cutter1
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(right_slot_cutter1, do_unlink=True)

    # 6.2 开右侧水平槽
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-length/2 + base_wing_width/2 + 0.01, width/2 - base_wing_depth/2 + 0.01, base_height/2 + nail_stage_height + base_wing_height/2 + 0.01)
    )
    right_slot_cutter2 = bpy.context.active_object
    right_slot_cutter2.name = "PB86_A0_Right_Slot_Cutter2"
    right_slot_cutter2.scale = (base_wing_width + 0.02, base_wing_depth + 0.02, base_height - base_wing_height + 0.02)

    modifier = base.modifiers.new(name="Right_Slot_Cutter2", type="BOOLEAN")
    modifier.object = right_slot_cutter2
    bpy.context.view_layer.objects.active = base
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    bpy.data.objects.remove(right_slot_cutter2, do_unlink=True) 
    
    # 添加材质
    base.data.materials.clear()
    mat = create_pa66_material()
    base.data.materials.append(mat)
    
    return base, mat


def create_button_cap(dims, color):
    """创建按键帽"""
    bm = bmesh.new()
    
    cap_width = dims['button_cap_width']
    cap_length = dims['button_cap_length']
    base_length = dims['length']
    base_height = dims['base_height']
    board_width = dims['button_cap_board_width']
    backboard_width = dims['button_cap_backboard_width']
    protrusion_height = dims['button_protrusion_height']
    protrusion_width = dims['button_protrusion_width']
    board_thickness = dims['button_cap_board_thickness']
    cap_height = dims['button_cap_backboard_height']
    stage_height = dims['nail_stage_height']
    cross_h_width = dims['button_cap_cross_h_width']
    cross_v_width = dims['button_cap_cross_v_width']

    base_wing_slot_width = dims['base_wing_slot_width']
    base_wing_width = dims['base_wing_width']
    base_wing_depth = dims['base_wing_depth']

    # 1. 按键帽中间
    # 1.1 前板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(cap_length - base_length/2 - board_thickness/2, 0, cap_height - board_width/2 + stage_height)
    )
    button_cap = bpy.context.active_object
    button_cap.name = "PB86_A0_Cap"
    button_cap.scale = (board_thickness, cap_width, board_width)

    # 1.2 左侧板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-base_length/2 + cap_length/2, -cap_width/2 + board_thickness/2, cap_height - board_width/2 + stage_height)
    )
    button_cap_left = bpy.context.active_object
    button_cap_left.name = "PB86_A0_Cap_Left"
    button_cap_left.scale = (cap_length, board_thickness, board_width)

    # 1.3 右侧板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-base_length/2 + cap_length/2, cap_width/2 - board_thickness/2, cap_height - board_width/2 + stage_height)
    )
    button_cap_right = bpy.context.active_object
    button_cap_right.name = "PB86_A0_Cap_Right"
    button_cap_right.scale = (cap_length, board_thickness, board_width)

    # 1.4 后板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-base_length/2 + board_thickness/2, 0, cap_height - backboard_width/2 + stage_height)
    )
    button_cap_back = bpy.context.active_object
    button_cap_back.name = "PB86_A0_Cap_Back"
    button_cap_back.scale = (board_thickness, cap_width, backboard_width)

    # 2. 按键帽顶部
    # 2.1 前凸起
    button_cap_top_front = frustum.create_rectangular_frustum(
        bottom_length=protrusion_width, bottom_width=cap_width,
        top_length=protrusion_width - protrusion_height, top_width=cap_width - protrusion_height,
        height=protrusion_height
    )
    button_cap_top_front.name = "PB86_A0_Cap_Top_Front"
    button_cap_top_front.location=(cap_length - base_length/2 - protrusion_width/2, 0, cap_height + stage_height)

    # 2.2 后平板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(cap_length/2 - protrusion_width/2 - base_length/2, 0, cap_height - board_thickness/2 + stage_height)
    )
    button_cap_top_back = bpy.context.active_object
    button_cap_top_back.name = "PB86_A0_Cap_Top_Back"
    button_cap_top_back.scale = (cap_length - protrusion_width, cap_width, board_thickness)

    # 3. 中心十字柱
    # 3.1 中心柱横柱（X轴）
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, base_height * 0.75 + backboard_width/2 + stage_height)
    )
    button_cap_middle_horizontal = bpy.context.active_object
    button_cap_middle_horizontal.name = "PB86_A0_Cap_Middle_Horizontal"
    button_cap_middle_horizontal.scale = (board_thickness, cross_h_width, base_height/2 + backboard_width)

    # 3.2 中心柱纵柱（Y轴）
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, base_height * 0.75 + backboard_width/2 + stage_height)
    )
    button_cap_middle_vertical = bpy.context.active_object
    button_cap_middle_vertical.name = "PB86_A0_Cap_Middle_Vertical"
    button_cap_middle_vertical.scale = (cross_v_width, board_thickness, base_height/2 + backboard_width)

    # 4. 侧翼板
    # 4.1 左侧板
    # 4.1.1 长横板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-base_length/2 + base_wing_slot_width/2 + base_wing_width/2, -cap_width/2 + base_wing_depth/2 - 0.05, cap_height - board_width + stage_height - backboard_width/2 + board_width/2)
    )
    left_wing = bpy.context.active_object
    left_wing.name = "PB86_A0_Cap_Left_Wing"
    both_wing_width = base_wing_slot_width + base_wing_width
    left_wing.scale = (both_wing_width, base_wing_depth - 0.1, backboard_width - board_width)

    # 4.1.2 直角梯形横板
    left_wing_h_trapezoid = trapezoid.create_right_angled_trapezoid(
        long_edge=both_wing_width, short_edge=both_wing_width - 0.4, width=base_wing_depth - 0.1, thickness=base_wing_depth - 0.1
    )
    left_wing_h_trapezoid.name = "PB86_A0_Cap_Left_Wing_H_Trapezoid"
    left_wing_h_trapezoid.rotation_euler = (-math.pi/2, 0, 0)
    left_wing_h_trapezoid.location = (-base_length/2 + both_wing_width/2 - 2.0, -cap_width/2, cap_height + stage_height - backboard_width)

    # 4.1.3 直角梯形竖板
    base_wing_height = dims['base_wing_height']
    left_wing_v_trapezoid = trapezoid.create_right_angled_trapezoid(
        long_edge=base_wing_height, short_edge=base_wing_height - 1.0, width=1.0, thickness=base_wing_depth - 0.1
    )
    left_wing_v_trapezoid.name = "PB86_A0_Cap_Left_Wing_V_Trapezoid"
    left_wing_v_trapezoid.rotation_euler = (0, -math.pi/2, math.pi/2)
    left_wing_v_trapezoid.location = (-base_length/2 + both_wing_width/2 + base_wing_depth - 0.7, -cap_width/2 + base_wing_depth - 0.1, cap_height + stage_height - backboard_width - base_wing_height - base_wing_depth + 0.2)

    # 4.1.4 竖矩形板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-base_length/2 + both_wing_width/2 + base_wing_depth - 0.2, -cap_width/2 + base_wing_depth/2 - 0.05, cap_height + stage_height - backboard_width - base_wing_height/2 - base_wing_depth + 0.2)
    )
    left_wing_v_rectangle = bpy.context.active_object
    left_wing_v_rectangle.name = "PB86_A0_Cap_Left_Wing_V_Rectangle"
    left_wing_v_rectangle.scale = (1.0, base_wing_depth - 0.1, base_wing_height)

    # 4.1.5 组合侧翼板
    bpy.ops.object.select_all(action='DESELECT')
    left_wing.select_set(True)
    left_wing_h_trapezoid.select_set(True)
    left_wing_v_trapezoid.select_set(True)
    left_wing_v_rectangle.select_set(True)
    bpy.context.view_layer.objects.active = left_wing
    bpy.ops.object.join()

    # 4.2 右侧板
    # 4.2.1 长横板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-base_length/2 + base_wing_slot_width/2 + base_wing_width/2, cap_width/2 - base_wing_depth/2 + 0.05, cap_height - board_width + stage_height - backboard_width/2 + board_width/2)
    )
    right_wing = bpy.context.active_object
    right_wing.name = "PB86_A0_Cap_Right_Wing"
    right_wing.scale = (both_wing_width, base_wing_depth - 0.1, backboard_width - board_width)

    # 4.2.2 直角梯形横板
    right_wing_h_trapezoid = trapezoid.create_right_angled_trapezoid(
        long_edge=both_wing_width, short_edge=both_wing_width - 0.4, width=base_wing_depth - 0.1, thickness=base_wing_depth - 0.1
    )
    right_wing_h_trapezoid.name = "PB86_A0_Cap_Right_Wing_H_Trapezoid"
    right_wing_h_trapezoid.rotation_euler = (-math.pi/2, 0, 0)
    right_wing_h_trapezoid.location = (-base_length/2 + both_wing_width/2 - 2.0, cap_width/2 - base_wing_depth + 0.1, cap_height + stage_height - backboard_width)

    # 4.2.3 直角梯形竖板
    right_wing_v_trapezoid = trapezoid.create_right_angled_trapezoid(
        long_edge=base_wing_height, short_edge=base_wing_height - 1.0, width=1.0, thickness=base_wing_depth - 0.1
    )
    right_wing_v_trapezoid.name = "PB86_A0_Cap_Right_Wing_V_Trapezoid"
    right_wing_v_trapezoid.rotation_euler = (0, -math.pi/2, math.pi/2)
    right_wing_v_trapezoid.location = (-base_length/2 + both_wing_width/2 + base_wing_depth - 0.7, cap_width/2, cap_height + stage_height - backboard_width - base_wing_height - base_wing_depth + 0.2)

    # 4.2.4 竖矩形板
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-base_length/2 + both_wing_width/2 + base_wing_depth - 0.2, cap_width/2 - base_wing_depth/2 + 0.05, cap_height + stage_height - backboard_width - base_wing_height/2 - base_wing_depth + 0.2)
    )
    right_wing_v_rectangle = bpy.context.active_object
    right_wing_v_rectangle.name = "PB86_A0_Cap_Right_Wing_V_Rectangle"
    right_wing_v_rectangle.scale = (1.0, base_wing_depth - 0.1, base_wing_height)

    # 4.2.5 组合侧翼板
    bpy.ops.object.select_all(action='DESELECT')
    right_wing.select_set(True)
    right_wing_h_trapezoid.select_set(True)
    right_wing_v_trapezoid.select_set(True)
    right_wing_v_rectangle.select_set(True)
    bpy.context.view_layer.objects.active = right_wing
    bpy.ops.object.join()

    # 5. 合并所有板
    bpy.ops.object.select_all(action='DESELECT')
    button_cap.select_set(True)
    button_cap_left.select_set(True)
    button_cap_right.select_set(True)
    button_cap_back.select_set(True)
    button_cap_top_front.select_set(True)
    button_cap_top_back.select_set(True)
    button_cap_middle_horizontal.select_set(True)
    button_cap_middle_vertical.select_set(True)
    left_wing.select_set(True)
    right_wing.select_set(True)
    bpy.context.view_layer.objects.active = button_cap
    bpy.ops.object.join()
    
    # 添加材质
    button_cap.data.materials.clear()
    mat = create_abs_material(color)
    button_cap.data.materials.append(mat)
    
    return button_cap, mat


def create_pins(dims, pa66_mat):
    """创建引脚"""
    pins = []
    pin_spacing = dims['pin_spacing']
    pin_length = dims['pin_length']
    pin_width = dims['pin_width']
    pin_thickness = dims['pin_thickness']
    pin_stage_width = dims['pin_stage_width']
    pin_stage_height = dims['pin_stage_height']
    mat = create_copper_material()
    nail_stage_height = dims['nail_stage_height']
    nail_stage_spacing = dims['nail_stage_spacing']
    
    # 1. 创建左侧基座
    left_pin_stage = rounded_rect.create_rounded_rectangle(
        pin_number=0,
        height=pin_spacing + pin_stage_width,
        depth=pin_stage_height,
        width=pin_stage_width,
        radius=pin_stage_width/2,
        rounded_corners="all"
    )
    left_pin_stage.name = "PB86_A0_Left_Pin_Stage"
    left_pin_stage.rotation_euler = (0, 0, math.pi/2)
    left_pin_stage.location = (nail_stage_spacing/2 - pin_stage_width/2, - pin_spacing/2 - pin_stage_width/2, nail_stage_height - pin_stage_height)

    left_pin_stage.data.materials.clear()
    left_pin_stage.data.materials.append(pa66_mat)

    # 2. 创建左侧引脚
    # 2.1 创建底部左侧引脚
    bottom_left_pin = rounded_rect.create_rounded_rectangle(
        pin_number=0,
        height=pin_length,
        depth=pin_thickness,
        width=pin_width,
        radius=pin_width/2,
        rounded_corners="top"
    )
    bottom_left_pin.name = "PB86_A0_Bottom_Left_Pin"
    bottom_left_pin.rotation_euler = (-math.pi/2, 0, 0)
    bottom_left_pin.location = (pin_spacing, - nail_stage_spacing/2 - pin_thickness/2, (nail_stage_height - pin_length)/2)

    bottom_left_pin.data.materials.clear()
    bottom_left_pin.data.materials.append(mat)

    # 2.2 创建左侧中间引脚
    center_left_pin = rounded_rect.create_rounded_rectangle(
        pin_number=1,
        height=pin_length,
        depth=pin_thickness,
        width=pin_width,
        radius=pin_width/2,
        rounded_corners="top"
    )
    center_left_pin.name = "PB86_A0_Center_Left_Pin"
    center_left_pin.rotation_euler = (-math.pi/2, 0, math.pi/2)
    center_left_pin.location = (0, - nail_stage_spacing/2, (nail_stage_height - pin_length)/2)

    center_left_pin.data.materials.clear()
    center_left_pin.data.materials.append(mat)

    # 3. 创建右侧基座
    right_pin_stage = rounded_rect.create_rounded_rectangle(
        pin_number=0,
        height=pin_spacing + pin_stage_width,
        depth=pin_stage_height,
        width=pin_stage_width,
        radius=pin_stage_width/2,
        rounded_corners="all"
    )
    right_pin_stage.name = "PB86_A0_Right_Pin_Stage"
    right_pin_stage.rotation_euler = (0, 0, math.pi/2)
    right_pin_stage.location = (nail_stage_spacing/2 - pin_stage_width/2, pin_spacing/2 + pin_stage_width/2, nail_stage_height - pin_stage_height)

    right_pin_stage.data.materials.clear()
    right_pin_stage.data.materials.append(pa66_mat)

    # 4. 创建右侧引脚
    # 4.1 创建底部右侧引脚
    bottom_right_pin = rounded_rect.create_rounded_rectangle(
        pin_number=0,
        height=pin_length,
        depth=pin_thickness,
        width=pin_width,
        radius=pin_width/2,
        rounded_corners="top"
    )
    bottom_right_pin.name = "PB86_A0_Bottom_Right_Pin"  
    bottom_right_pin.rotation_euler = (-math.pi/2, 0, 0)
    bottom_right_pin.location = (pin_spacing, nail_stage_spacing/2 - pin_thickness/2, (nail_stage_height - pin_length)/2)

    bottom_right_pin.data.materials.clear()
    bottom_right_pin.data.materials.append(mat)

    # 4.2 创建右侧中间引脚
    center_right_pin = rounded_rect.create_rounded_rectangle(
        pin_number=1,
        height=pin_length,
        depth=pin_thickness,
        width=pin_width,
        radius=pin_width/2,
        rounded_corners="top"
    )
    center_right_pin.name = "PB86_A0_Center_Right_Pin"  
    center_right_pin.rotation_euler = (-math.pi/2, 0, math.pi/2)
    center_right_pin.location = (0, nail_stage_spacing/2, (nail_stage_height - pin_length)/2)

    center_right_pin.data.materials.clear()
    center_right_pin.data.materials.append(mat)

    
    pins.append(left_pin_stage)
    pins.append(bottom_left_pin)
    pins.append(center_left_pin)
    pins.append(right_pin_stage)
    pins.append(bottom_right_pin)
    pins.append(center_right_pin)
    
    return pins


def create_fixed_nails(dims, pa66_mat):
    """创建固定钉"""
    nails = []

    length = dims['length']
    nail_diameter = dims['nail_diameter']
    nail_height = dims['nail_height']
    nail_stage_height = dims['nail_stage_height']
    nail_stage_width = dims['nail_stage_width']
    nail_stage_spacing = dims['nail_stage_spacing']

    # 1. 左下钉
    # 1.1 创建基座
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(length/2 - nail_stage_width/2, -nail_stage_spacing/2, nail_stage_height/2)
    )
    bottom_left_stage = bpy.context.active_object
    bottom_left_stage.name = "PB86_A0_Bottom_Left_Nail_Stage"
    bottom_left_stage.scale = (nail_stage_width, nail_stage_width, nail_stage_height)

    # 1.2 创建钉
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=nail_diameter/2,
        depth=nail_height,
        location=(length/2 - nail_stage_width/2, -nail_stage_spacing/2, -nail_height/2)  # 将主体放在z轴中心
    )
    bottom_left_nail = bpy.context.active_object
    bottom_left_nail.name = "PB86_A0_Bottom_Left_Nail"

    # 1.3 合并基座和钉
    bpy.ops.object.select_all(action='DESELECT')
    bottom_left_nail.select_set(True)
    bottom_left_stage.select_set(True)
    bpy.context.view_layer.objects.active = bottom_left_nail
    bpy.ops.object.join()

    # 1.4 应用PA66材料
    bottom_left_nail.data.materials.clear()
    bottom_left_nail.data.materials.append(pa66_mat)

    # 2. 左上基座
    # 2.1 创建基座
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-length/2 + nail_stage_width/2, -nail_stage_spacing/2, nail_stage_height/2)
    )
    top_left_stage = bpy.context.active_object
    top_left_stage.name = "PB86_A0_Top_Left_Nail_Stage"
    top_left_stage.scale = (nail_stage_width, nail_stage_width, nail_stage_height)

    # 2.2 应用PA66材料
    top_left_stage.data.materials.clear()
    top_left_stage.data.materials.append(pa66_mat)

    # 3. 右下基座
    # 3.1 创建基座
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(length/2 - nail_stage_width/2, nail_stage_spacing/2, nail_stage_height/2)
    )
    bottom_right_stage = bpy.context.active_object
    bottom_right_stage.name = "PB86_A0_Bottom_Right_Nail_Stage"
    bottom_right_stage.scale = (nail_stage_width, nail_stage_width, nail_stage_height)

    # 3.2 应用PA66材料
    bottom_right_stage.data.materials.clear()
    bottom_right_stage.data.materials.append(pa66_mat)

    # 4. 右上钉
    # 4.1 创建基座
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(-length/2 + nail_stage_width/2, nail_stage_spacing/2, nail_stage_height/2)
    )
    top_right_stage = bpy.context.active_object
    top_right_stage.name = "PB86_A0_Top_Right_Nail_Stage"
    top_right_stage.scale = (nail_stage_width, nail_stage_width, nail_stage_height)

    # 4.2 创建钉
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=nail_diameter/2,
        depth=nail_height,
        location=(-length/2 + nail_stage_width/2, nail_stage_spacing/2, -nail_height/2)  # 将主体放在z轴中心
    )
    top_right_nail = bpy.context.active_object
    top_right_nail.name = "PB86_A0_Top_Right_Nail"

    # 4.3 合并基座和钉
    bpy.ops.object.select_all(action='DESELECT')
    top_right_nail.select_set(True)
    top_right_stage.select_set(True)
    bpy.context.view_layer.objects.active = top_right_nail
    bpy.ops.object.join()

    top_right_nail.data.materials.clear()
    top_right_nail.data.materials.append(pa66_mat)

    # 5. 添加到返回列表中
    nails.append(bottom_left_nail)
    nails.append(top_left_stage)
    nails.append(bottom_right_stage)
    nails.append(top_right_nail)
    
    return nails


def create_pa66_material():
    """创建PA66材料（黑色，底座）"""
    mat = bpy.data.materials.new(name="PA66_Material")
    mat.use_nodes = True
    
    # PA66是黑色塑料
    pa66_color = (0.1, 0.1, 0.1, 1.0)
    mat.diffuse_color = pa66_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = pa66_color
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_abs_material(color):
    """创建ABS材料"""
    mat = bpy.data.materials.new(name="ABS_Material")
    mat.use_nodes = True
    mat.diffuse_color = color[0]
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = color[0]
    bsdf.inputs['Metallic'].default_value = color[2]
    bsdf.inputs['Roughness'].default_value = color[1]
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_metal_material():
    """创建金属材质"""
    mat = bpy.data.materials.new(name="Metal_Material")
    mat.use_nodes = True
    
    # 引脚是银色金属
    metal_color = (0.85, 0.85, 0.9)
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


def create_copper_material():
    """创建铜引脚材质"""
    mat = bpy.data.materials.new(name="Copper_Pin_Material")
    mat.use_nodes = True
    
    # 引脚是铜金属
    copper_color = (0.8, 0.5, 0.2, 1.0)
    mat.diffuse_color = copper_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = copper_color
    bsdf.inputs['Metallic'].default_value = 0.7
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat


def main():
    """主函数 - 创建PB86-A0按键3D模型"""
    # 清理场景
    clear_scene()
    
    print("=" * 60)
    print("创建PB86-A0按键3D模型")
    print("=" * 60)
    
    dims = pb86_a0_dimensions
    
    print("技术规格:")
    print(f"  按键尺寸: {dims['width']}±0.1 × {dims['length']}±0.1 mm")
    print(f"  引脚间距: {dims['pin_spacing']}mm")
    print("  额定电压: 12mA 24VDC")
    print("  工作温度: -20℃ ~ +55℃")
    print("  动作行程: 2±0.4mm")
    print("  动作力: ≤2N")
    print("  连接形式: 焊接导线")
    print("  开关组合: 1常开 1常闭")
    print("")
    
    print("材料信息:")
    print("  按键帽: ABS")
    print("  底座: PA66 (黑色)")
    print("  引脚: 金属")
    print("")
    
    # 创建模型
    print("正在创建PB86-A0红色按键模型...")
    collection = create_pb86_button(color='red')
    for obj in collection.objects:
        obj.rotation_euler.z = math.pi/2
    
    print("")
    print("模型组件:")
    print("  1. 底座 (PA66材料，黑色)")
    print("  2. 按键帽 (ABS材料, 红色)")
    print("  3. 引脚 (C, NO, NC)")
    print("")
    print(f"所有组件已添加到集合: {collection.name}")
    print("=" * 60)
    
    print("正在创建PB86-A0蓝色按键模型...")
    collection = create_pb86_button(color='blue')
    for obj in collection.objects:
        obj.location.x += 20
        obj.rotation_euler.z = math.pi/2
    
    print("")
    print("模型组件:")
    print("  1. 底座 (PA66材料，黑色)")
    print("  2. 按键帽 (ABS材料, 蓝色)")
    print("  3. 引脚 (C, NO, NC)")
    print("")
    print(f"所有组件已添加到集合: {collection.name}")
    print("=" * 60)
    
    print("正在创建PB86-A0绿色按键模型...")
    collection = create_pb86_button(color='green')
    for obj in collection.objects:
        obj.location.x += 40
        obj.rotation_euler.z = math.pi/2

    print("")
    print("模型组件:")
    print("  1. 底座 (PA66材料，黑色)")
    print("  2. 按键帽 (ABS材料, 绿色)")
    print("  3. 引脚 (C, NO, NC)")
    print("")
    print(f"所有组件已添加到集合: {collection.name}")
    print("=" * 60)
    
    print("正在创建PB86-A0灰色按键模型...")
    collection = create_pb86_button(color='gray')
    for obj in collection.objects:
        obj.location.x += 60
        obj.rotation_euler.z = math.pi/2
        
    print("")
    print("模型组件:")
    print("  1. 底座 (PA66材料，黑色)")
    print("  2. 按键帽 (ABS材料, 灰色)")
    print("  3. 引脚 (C, NO, NC)")
    print("")
    print(f"所有组件已添加到集合: {collection.name}")
    print("=" * 60)
    
    print("正在创建PB86-A0黄色按键模型...")
    collection = create_pb86_button(color='yellow')
    for obj in collection.objects:
        obj.location.x -= 20    
        obj.rotation_euler.z = math.pi/2

    print("")
    print("模型组件:")
    print("  1. 底座 (PA66材料，黑色)")
    print("  2. 按键帽 (ABS材料, 黑色)")
    print("  3. 引脚 (C, NO, NC)")
    print("")
    print(f"所有组件已添加到集合: {collection.name}")
    print("=" * 60)
    
    print("正在创建PB86-A0红色按键模型...")
    collection = create_pb86_button()
    for obj in collection.objects:
        obj.location.x -= 40
        obj.rotation_euler.z = math.pi/2
    
    print("")
    print("模型组件:")
    print("  1. 底座 (PA66材料，黑色)")
    print("  2. 按键帽 (ABS材料, 黑色)")
    print("  3. 引脚 (C, NO, NC)")
    print("")
    print(f"所有组件已添加到集合: {collection.name}")
    print("=" * 60)
    
    print("正在创建PB86-A0白色按键模型...")
    collection = create_pb86_button(color='white')
    for obj in collection.objects:
        obj.location.x -= 60
        obj.rotation_euler.z = math.pi/2
    
    print("")
    print("模型组件:")
    print("  1. 底座 (PA66材料，黑色)")
    print("  2. 按键帽 (ABS材料, 白色)")
    print("  3. 引脚 (C, NO, NC)")
    print("")
    print(f"所有组件已添加到集合: {collection.name}")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用正交视图
            area.spaces[0].region_3d.view_perspective = 'ORTHO'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 100
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.2, 0.2, 0.2, 1.0)
            # 设置显示模式
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
            # 设置白色背景
            area.spaces[0].shading.background_type = 'VIEWPORT'
            area.spaces[0].shading.background_color = (1.0, 1.0, 1.0)
    
    return collection

if __name__ == "__main__":
    collection = main()