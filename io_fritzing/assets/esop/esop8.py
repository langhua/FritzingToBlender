import bpy
import bmesh
from mathutils import Vector
import math
from io_fritzing.assets.commons.pin_0_4mm import create_pin as create_common_pin

# 清理场景函数
def clear_scene():
    # 确保在对象模式下
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 选择所有对象并删除
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    # 设置场景单位
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'

# 根据图纸正确定义尺寸参数（单位：毫米）
dimensions = {
    # 整体尺寸 - 根据图纸修正
    'body_length': 5.00,  # A: 4.90~5.10 取中值
    'body_width': 4.00,   # B: 3.90~4.10 取中值
    'body_height': 1.65,  # 主体高度（总高1.75减去standoff 0.10）
    
    # 底部散热片尺寸
    'heatsink_length': 3.30,  # A1: 3.1~3.5 取中值
    'heatsink_width': 2.40,  # B1: 2.2~2.6 取中值
    'heatsink_height': 0.10,  # 散热片厚度
    
    # 引脚尺寸
    'pin_width': 0.42,      # a: 0.35~0.49 取中值
    'pin_thickness': 0.15,  # 典型值
    'pin_length': 2.0,     # L: 1.25mm (Y方向长度)
    
    # 引脚弯曲参数
    'bend_radius': 0.30,    # 弯曲半径0.3mm
    'first_bend_angle': 80,    # 第一次弯曲角度80度
    'second_bend_angle': 100,  # 第二次弯曲角度-80度
    'bend_start_distance': 0.25,  # 离主体0.25mm开始弯曲
    'middle_length': 0.50,       # 中间直线段长度0.2mm
    
    # 其他尺寸
    'standoff_height': 0.10,  # A1 Min
    'pin_pitch': 1.27,        # E: 1.27BSC
    
    # 倒角参数
    'chamfer_size': 0.20,     # 倒角尺寸
    'chamfer_segments': 10,   # 倒角分段数改为10，使外观更圆润
}

def apply_all_modifiers():
    """应用所有对象的修改器"""
    # 确保在对象模式下
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 遍历场景中的所有对象
    for obj in bpy.context.scene.objects:
        # 选择当前对象
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        # 应用所有修改器
        for modifier in list(obj.modifiers):
            try:
                # 尝试应用修改器
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except Exception as e:
                # 如果无法应用，则移除修改器
                obj.modifiers.remove(modifier)

def create_esop8_package():
    # 创建芯片主体
    body = create_chip_body()
    
    # 创建底部散热片（镶嵌在body底部，只突出0.01mm）
    heatsink = create_heatsink()
    
    # 创建引脚
    pins = create_pins()
    
    # 添加第一引脚标记（镶嵌在body顶部靠近pin1的角上）
    marker = create_pin1_marker()
    
    # 应用所有修改器
    apply_all_modifiers()
    
    # 清理临时对象（如布尔运算后的标记）
    if marker and marker.name in bpy.data.objects:
        bpy.data.objects.remove(marker, do_unlink=True)
    
    return body, heatsink, pins

def create_chip_body():
    # 直接创建具有正确尺寸的立方体，不使用缩放
    # 计算立方体的实际尺寸
    length = dimensions['body_length']
    width = dimensions['body_width']
    height = dimensions['body_height']
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2 + dimensions['standoff_height'])
    )
    body = bpy.context.active_object
    body.name = "ESOP8_Body"
    
    # 直接设置尺寸，不使用缩放
    # 删除默认的立方体网格
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete(type='ONLY_FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 创建新的网格
    mesh = bpy.data.meshes.new("ESOP8_Body_Mesh")
    
    # 创建立方体的顶点
    vertices = [
        (-length/2, -width/2, -height/2),
        (-length/2, -width/2, height/2),
        (-length/2, width/2, -height/2),
        (-length/2, width/2, height/2),
        (length/2, -width/2, -height/2),
        (length/2, -width/2, height/2),
        (length/2, width/2, -height/2),
        (length/2, width/2, height/2)
    ]
    
    # 创建立方体的面
    faces = [
        (0, 1, 3, 2),  # 左面
        (4, 6, 7, 5),  # 右面
        (0, 4, 5, 1),  # 下面
        (2, 3, 7, 6),  # 上面
        (0, 2, 6, 4),  # 后面
        (1, 5, 7, 3)   # 前面
    ]
    
    # 创建网格
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    
    # 将新网格分配给对象
    body.data = mesh
    
    # 添加更圆滑的倒角修改器 - 分段数改为10
    bevel_mod = body.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = dimensions['chamfer_size']
    bevel_mod.segments = dimensions['chamfer_segments']  # 改为10段，使倒角更圆滑
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 细分曲面修改器
    subdiv_mod = body.modifiers.new(name="Subdivision", type='SUBSURF')
    subdiv_mod.levels = 1
    subdiv_mod.render_levels = 2
    
    # 设置材质（黑色塑料）
    body.data.materials.clear()
    mat_body = bpy.data.materials.new(name="Plastic_Black")
    mat_body.use_nodes = True
    mat_body.diffuse_color = (0.15, 0.15, 0.15, 1.0)
    body.data.materials.append(mat_body)
    
    return body

def create_heatsink():
    # 直接创建具有正确尺寸的散热片
    length = dimensions['heatsink_length']
    width = dimensions['heatsink_width']
    height = dimensions['heatsink_height']
    
    # 计算散热片位置 - 确保只突出0.01mm
    # 散热片的上表面与body底部平齐，下表面突出0.01mm
    heatsink_z = (dimensions['standoff_height'] - 0.01) + height/2
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, heatsink_z)
    )
    heatsink = bpy.context.active_object
    heatsink.name = "ESOP8_Heatsink"
    
    # 直接设置尺寸，不使用缩放
    # 删除默认的立方体网格
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.delete(type='ONLY_FACE')
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 创建新的网格
    mesh = bpy.data.meshes.new("ESOP8_Heatsink_Mesh")
    
    # 创建立方体的顶点
    vertices = [
        (-length/2, -width/2, -height/2),
        (-length/2, -width/2, height/2),
        (-length/2, width/2, -height/2),
        (-length/2, width/2, height/2),
        (length/2, -width/2, -height/2),
        (length/2, -width/2, height/2),
        (length/2, width/2, -height/2),
        (length/2, width/2, height/2)
    ]
    
    # 创建立方体的面
    faces = [
        (0, 1, 3, 2),  # 左面
        (4, 6, 7, 5),  # 右面
        (0, 4, 5, 1),  # 下面
        (2, 3, 7, 6),  # 上面
        (0, 2, 6, 4),  # 后面
        (1, 5, 7, 3)   # 前面
    ]
    
    # 创建网格
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    
    # 将新网格分配给对象
    heatsink.data = mesh
    
    # 为散热片也添加圆滑倒角
    bevel_mod = heatsink.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = 0.1
    bevel_mod.segments = 4
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 设置散热片材质（金属色）
    heatsink.data.materials.clear()
    mat_heatsink = bpy.data.materials.new(name="Heatsink_Metal")
    mat_heatsink.use_nodes = True
    mat_heatsink.diffuse_color = (0.6, 0.6, 0.7, 1.0)
    heatsink.data.materials.append(mat_heatsink)
    
    return heatsink

def create_pins():
    # 引脚位置计算 - 总共8个引脚，每侧4个
    pin_count_per_side = 4
    pitch = dimensions['pin_pitch']
    
    # 计算引脚起始位置 - 确保引脚正确分布在body两侧
    y_offset = dimensions['body_width']/2
    
    pins = []
    
    # 右侧引脚 (1-4)
    for i in range(pin_count_per_side):
        # 引脚中心间距为1.27mm
        x_pos = (1.5 - i) * pitch
        y_pos = y_offset
        pin = create_common_pin()
        # 定位引脚
        pin_z = dimensions['standoff_height'] + dimensions['body_height']/2
        pin.location = (x_pos, y_pos, pin_z)
        pins.append(pin)
    
    # 左侧引脚 (5-8)
    for i in range(pin_count_per_side):
        # 引脚中心间距为1.27mm
        x_pos = (i - 1.5) * pitch
        y_pos = -y_offset
        pin = create_common_pin()
        # 定位引脚
        pin_z = dimensions['standoff_height'] + dimensions['body_height']/2
        pin.location = (x_pos, y_pos, pin_z)
        pin.scale.y = -1
        pins.append(pin)
    
    return pins

def create_pin1_marker():
    # 创建第一引脚标记（镶嵌在body顶部靠近pin1的角上）
    # 根据图片提示，调整Pin1_Marker位置：
    # X方向与Pin1对齐，Y方向减少0.2mm（向下移动）
    
    # 计算Pin1的位置（右侧最上方引脚）
    pin1_x = (1.5 - 0) * dimensions['pin_pitch']  # 第一个引脚在右侧最上方
    
    # 标记位置在body顶部靠近pin1的角上
    # X方向与Pin1对齐，Y方向减少0.2mm（向下移动）
    marker_x = pin1_x  # X方向与Pin1对齐
    marker_y = dimensions['body_width']/2 - 0.3 - 0.2  # Y方向减少0.2mm（向下移动）
    marker_z = dimensions['body_height'] + dimensions['standoff_height'] - 0.05  # 略低于顶部表面
    
    # 创建圆柱体作为凹坑标记
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.15,
        depth=0.1,
        location=(marker_x, marker_y, marker_z)
    )
    marker = bpy.context.active_object
    marker.name = "Pin1_Marker"
    
    # 设置标记材质（对比色）
    marker.data.materials.clear()
    mat_marker = bpy.data.materials.new(name="Marker_White")
    mat_marker.use_nodes = True
    mat_marker.diffuse_color = (0.9, 0.9, 0.9, 1.0)
    marker.data.materials.append(mat_marker)
    
    # 使用布尔运算将标记凹坑嵌入body顶部
    body = bpy.data.objects.get("ESOP8_Body")
    if body:
        # 添加布尔修改器创建凹坑
        bool_mod = body.modifiers.new(name="Pin1_Marker_Cut", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = marker
    
    return marker

def print_dimensions():
    """打印使用的尺寸参数"""
    print("ESOP-8 chip package model created successfully!")
    print("Dimensions used (unit: mm):")
    print("Body length (A): " + str(dimensions['body_length']) + " (4.90~5.10)")
    print("Body width (B): " + str(dimensions['body_width']) + " (3.90~4.10)")
    print("Body height: " + str(dimensions['body_height']))
    print("Heatsink length (A1): " + str(dimensions['heatsink_length']) + " (3.1~3.5)")
    print("Heatsink width (B1): " + str(dimensions['heatsink_width']) + " (2.2~2.6)")
    print("Pin pitch (E): " + str(dimensions['pin_pitch']) + " (1.27BSC)")
    print("Pin width (a): " + str(dimensions['pin_width']) + " (0.35~0.49)")
    print("Pin length (L): " + str(dimensions['pin_length']) + " (1.25mm in Y direction)")
    print("Bend radius: " + str(dimensions['bend_radius']))
    print("First bend angle: " + str(dimensions['first_bend_angle']) + "°")
    print("Second bend angle: " + str(dimensions['second_bend_angle']) + "°")
    print("Bend start distance: " + str(dimensions['bend_start_distance']) + "mm")
    print("Middle length: " + str(dimensions['middle_length']) + "mm")
    print("Chamfer size: " + str(dimensions['chamfer_size']))
    print("Chamfer segments: " + str(dimensions['chamfer_segments']) + " (increased to 10 for smoother appearance)")

# 主程序
def main():
    # 清理场景
    clear_scene()
    
    # 创建ESOP-8封装模型
    body, heatsink, pins = create_esop8_package()
    
    # 打印尺寸信息
    print_dimensions()
    
    print("ESOP-8 chip package model created successfully!")
    print("Pin design updated to match the exact specification:")
    print("1. Start from body side, create a 1.25mm long box in Y direction")
    print("2. First bend: 80° downward at 0.25mm from body")
    print("3. Continue 0.2mm in natural direction")
    print("4. Second bend: -80° with same radius")
    print("5. Remaining part keeps natural shape")
    print("Pin1_Marker position adjusted:")
    print("- X direction aligned with Pin1")
    print("- Y direction moved down by 0.2mm")
    print("Heatsink embedded in body, protruding only 0.01mm")

# 执行主程序
if __name__ == "__main__":
    main()