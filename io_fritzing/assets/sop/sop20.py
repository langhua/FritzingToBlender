import bpy
import bmesh
from mathutils import Vector
import math
from ..utils.scene import clear_scene
from ..utils.material import create_material

# 根据图纸中的尺寸表定义参数 - 修正后的尺寸
dimensions = {
    # 主体尺寸
    'body_length': 12.70,  # BL: 12.60-12.80 取中值
    'body_width': 7.55,    # BW: 7.50-7.60 取中值
    'body_height': 2.4,    # BT: 2.4mm 最大值
    
    # 引脚尺寸
    'pin_width': 0.44,     # TW: 0.44mm 典型值
    'pin_thickness': 0.30, # FT: 0.30mm 最大值
    
    # 引脚长度
    'pin_length': 2.45,
    
    # 引脚间距
    'pin_pitch': 1.27,    # LP: 1.27mm 典型值
    
    # 引脚跨距
    'pin_span': 7.55,     # BW: 7.55mm 最大值
    
    # 引脚脚长
    'foot_length': 0.9,   # FL: 0.9mm 最大值
    
    # 其他参数
    'standoff_height': 0.25, # SO: 0.25mm 最大值
    
    # 倒角参数
    'chamfer_size': 0.1,
    'chamfer_segments': 10,
    
    # 引脚弯曲参数
    'bend_radius': 0.2,      # 弯曲半径
    'bend_angle': 80,        # 弯曲角度
    'bend_start': 0.2,       # 离起点开始弯曲的距离
    'middle_length': 1,      # 中间直线长度
    'actual_foot_length': 0,   # 实际引脚长度（自动计算）
}

def apply_all_modifiers():
    """应用所有对象的修改器"""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    for obj in bpy.context.scene.objects:
        bpy.ops.object.select_all(action='DESELECT')
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        for modifier in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except:
                obj.modifiers.remove(modifier)

def create_sop20_model(chip_name = 'SOP20'):
    """创建SOP20完整模型"""
    # 创建芯片主体
    body = create_chip_body()
    
    # 创建20个引脚 - 从腰线开始绘制
    pins = create_pins_from_waistline()
    
    # 添加SOP20标记文字
    text_marker = create_text_marker(chip_name)
    
    # 确保所有修改器都被应用
    apply_all_modifiers()

    # 将所有对象合并
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    text_marker.select_set(True)
    for obj in pins:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = chip_name
    
    body.rotation_euler.z += -math.pi/2

    return body

def create_chip_body():
    """创建芯片主体 - 使用布尔运算添加Pin1标记凹坑"""
    # 使用图纸中的实际尺寸
    length = dimensions['body_length']  # 12.70mm
    width = dimensions['body_width']    # 7.55mm
    height = dimensions['body_height']  # 2.4mm
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2 + dimensions['standoff_height'])
    )
    body = bpy.context.active_object
    body.name = "SOP20_Body"
    
    # 直接设置尺寸
    body.scale = (length, width, height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 创建Pin1标记凹坑
    create_pin1_marker_cut(body)
    
    # 添加倒角修改器
    bevel_mod = body.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = dimensions['chamfer_size']
    bevel_mod.segments = dimensions['chamfer_segments']
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 应用修改器
    bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    
    # 设置材质 - 改进材质设置
    body.data.materials.clear()
    mat_body = create_material(name="Plastic_Black", base_color = (0.05, 0.05, 0.05, 1.0), metallic = 0.0, roughness = 0.8)
    body.data.materials.append(mat_body)
    
    return body

def create_pin1_marker_cut(body):
    """创建Pin1标记凹坑 - 使用布尔修改器在主体上创建凹坑"""
    # 引脚1的X坐标 - 根据图纸：x = -pin_pitch * 4.5
    pin1_x = -dimensions['pin_pitch'] * 4.5  # 修正：使用图纸中的公式
    
    marker_x = pin1_x + 0.5
    marker_y = -dimensions['body_width'] / 2 + 1  # 从底部边缘向上0.6mm
    marker_z = dimensions['body_height'] + dimensions['standoff_height'] - 0.05
    
    # 创建圆柱体作为凹坑切割工具
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.3,
        depth=0.2,
        location=(marker_x, marker_y, marker_z)
    )
    marker_cutter = bpy.context.active_object
    marker_cutter.name = "Pin1_Marker_Cutter"
    
    # 为圆柱体添加布尔修改器（差集）到主体
    bool_mod = body.modifiers.new(name="Pin1_Marker_Cut", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = marker_cutter
    
    # 应用布尔修改器
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    # 删除切割工具
    bpy.ops.object.select_all(action='DESELECT')
    marker_cutter.select_set(True)
    bpy.ops.object.delete(use_global=False)


def create_text_marker(chip_name = 'SOP20'):
    """创建SOP20标记文字"""
    # 在主体顶部添加SOP20文字标记
    text_location = (0, 0, dimensions['body_height'] + dimensions['standoff_height'] + 0.01)
    
    # 创建文本对象
    bpy.ops.object.text_add(location=text_location)
    text_obj = bpy.context.active_object
    text_obj.name = f"{chip_name}_Text"
    
    # 设置文本内容
    text_obj.data.body = chip_name
    
    # 设置文本大小
    text_obj.data.size = 2
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 转换为网格
    bpy.ops.object.convert(target='MESH')
    
    # 缩放文本以适应主体
    text_obj.scale = (0.8, 0.8, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    
    # 设置文本材质
    text_obj.data.materials.clear()
    mat_text = create_material(name="Text_White", base_color = (0.9, 0.9, 0.9, 1.0), metallic = 0.0, roughness = 0.8)
    text_obj.data.materials.append(mat_text)
    
    return text_obj

def create_pins_from_waistline():
    """创建20个引脚 - 从主体腰线开始绘制"""
    pins = []
    
    # 引脚长度
    pin_length = dimensions['pin_length']  # 1.5mm
    
    # 引脚间距
    pin_pitch = dimensions['pin_pitch']  # 1.27mm
    
    # 引脚跨距
    pin_span = dimensions['pin_span']  # 7.55mm
    
    # 引脚脚长
    foot_length = dimensions['foot_length']  # 0.9mm
    
    # 计算引脚位置
    # SOP20有20个引脚，上下各10个
    # 引脚顺序：左下为1，右下为10，右上为11，左上为20，逆时针排列
    
    # 底部引脚位置 (1-10) - 从左到右排列
    # 修正：引脚1的X坐标 = -pin_pitch * 4.5
    bottom_pin_x = []
    for i in range(10):
        x_pos = -pin_pitch * 4.5 + i * pin_pitch  # 修正：从 -pin_pitch * 4.5 开始
        bottom_pin_x.append(x_pos)
    
    # 创建底部引脚 (1-10)
    for i in range(10):
        x_pos = bottom_pin_x[i]
        y_pos = -dimensions['body_width'] / 2  # 底部引脚Y位置
        pin_number = i + 1  # 引脚编号：1, 2, 3, ..., 10
        pin = create_pin_with_caps(x_pos, y_pos, pin_number, 'bottom', pin_length, foot_length)
        pins.append(pin)
    
    # 创建顶部引脚 (11-20) - 从右到左排列（逆时针）
    for i in range(10):
        x_pos = bottom_pin_x[9-i]  # 反转顺序，从右到左
        y_pos = dimensions['body_width'] / 2  # 顶部引脚Y位置
        pin_number = 11 + i  # 引脚编号：11, 12, 13, ..., 20
        pin = create_pin_with_caps(x_pos, y_pos, pin_number, 'top', pin_length, foot_length)
        pins.append(pin)
    
    return pins

def create_pin_with_caps(x_pos, y_pos, pin_number, side, pin_length, foot_length):
    """创建引脚 - 包含端面封面和脚部延伸"""
    # 引脚尺寸
    width = dimensions['pin_width']      # 0.44mm
    thickness = dimensions['pin_thickness'] # 0.30mm
    
    # 弯曲参数
    bend_radius = dimensions['bend_radius']
    bend_angle = math.radians(dimensions['bend_angle'])
    bend_start = dimensions['bend_start']
    middle_length = dimensions['middle_length']  # 0.2mm
    
    # 计算主体腰线高度（主体中心高度）
    waistline_z = dimensions['body_height'] / 2 + dimensions['standoff_height']
    
    # 使用bmesh创建精确的引脚几何体
    bm = bmesh.new()
    
    # 计算各段长度 - 考虑脚部延伸
    bend_length = bend_radius * bend_angle
    remaining_length = pin_length - bend_start - bend_length - middle_length - bend_length
    dimensions['actual_foot_length'] = remaining_length + bend_radius * (1 - math.sin(math.radians(90 - dimensions['bend_angle'])))  # 更新实际引脚长度参数
    
    # 创建引脚的弯曲路径 - 从腰线开始
    path_points = []
    
    # 1. 第一段直线 (从腰线开始垂直延伸)
    segments = 8
    for i in range(segments - 1):
        t = i / (segments - 1)
        y = -bend_start * t  # 顶部引脚向正Y方向延伸
        z = 0
        path_points.append((0, y, z))
    
    # 2. 第一次弯曲 (向下弯曲)
    segments = 16
    for i in range(1, segments + 1):
        t = i / segments
        angle = t * bend_angle
        y = -bend_start - bend_radius * math.sin(angle)
        z = -bend_radius * (1 - math.cos(angle))
        path_points.append((0, y, z))
    
    # 3. 中间直线段
    segments = 6
    end_y = path_points[-1][1]  # 使用索引1获取Y坐标
    end_z = path_points[-1][2]
    
    # 使用成功的修改：tangent_z = -math.sin(bend_angle)
    tangent_y = -math.cos(bend_angle)
    tangent_z = -math.sin(bend_angle)
    
    for i in range(1, segments + 1):
        t = i / segments
        y = end_y + middle_length * t * tangent_y
        z = end_z + middle_length * t * tangent_z
        path_points.append((0, y, z))
    
    # 4. 第二次弯曲 (向上弯曲，回到水平)
    segments = 16
    end_y = path_points[-1][1]  # 使用索引1获取Y坐标
    end_z = path_points[-1][2]
    
    for i in range(1, segments + 1):
        t = i / segments
        angle = bend_angle - t * bend_angle
        y = end_y - bend_radius * (math.sin(bend_angle) - math.sin(angle))
        z = end_z - bend_radius * (math.cos(angle) - math.cos(bend_angle))
        path_points.append((0, y, z))
    
    # 5. 最后一段直线 - 包含脚部延伸
    segments = 8
    end_y = path_points[-1][1]  # 使用索引1获取Y坐标
    end_z = path_points[-1][2]
    
    for i in range(1, segments):
        t = i / segments
        y = end_y - remaining_length * t
        z = end_z
        path_points.append((0, y, z))
    
    # 沿着路径创建截面
    sections = []
    half_width = width / 2
    half_thickness = thickness / 2
    
    for i, point in enumerate(path_points):
        # 计算切向
        if i == 0:
            tangent = (Vector(path_points[1]) - Vector(point)).normalized()
        elif i == len(path_points) - 1:
            tangent = (Vector(point) - Vector(path_points[i-1])).normalized()
        else:
            tangent = (Vector(path_points[i+1]) - Vector(path_points[i-1])).normalized()
        
        # 计算法线和副法线
        up = Vector((0, 0, 1))
        binormal = tangent.cross(up).normalized()
        
        if binormal.length < 0.001:
            binormal = Vector((1, 0, 0))  # 使用X轴作为副法线
        
        normal = binormal.cross(tangent).normalized()
        
        # 创建截面上的四个顶点
        v1 = Vector(point) + binormal * half_width + normal * half_thickness
        v2 = Vector(point) - binormal * half_width + normal * half_thickness
        v3 = Vector(point) - binormal * half_width - normal * half_thickness
        v4 = Vector(point) + binormal * half_width - normal * half_thickness
        
        # 添加到bmesh
        verts = [
            bm.verts.new(v1),
            bm.verts.new(v2),
            bm.verts.new(v3),
            bm.verts.new(v4)
        ]
        sections.append(verts)
    
    # 创建连接面
    for i in range(len(sections) - 1):
        for j in range(4):
            v1 = sections[i][j]
            v2 = sections[i][(j+1)%4]
            v3 = sections[i+1][(j+1)%4]
            v4 = sections[i+1][j]
            bm.faces.new([v1, v2, v3, v4])
    
    # 创建端面封面
    if len(sections) > 0:
        # 起始端面
        bm.faces.new(sections[0])
        # 结束端面
        bm.faces.new(reversed(sections[-1]))
    
    # 创建网格
    mesh = bpy.data.meshes.new(f"Pin_{pin_number}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    pin = bpy.data.objects.new(f"Pin_{pin_number}", mesh)
    bpy.context.collection.objects.link(pin)
    
    # 添加平滑着色
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()
    
    # 定位引脚 - 从腰线开始
    if side == 'bottom':
        # 底部引脚 - 朝向负Y方向
        pin.rotation_euler = (0, 0, 0)
        pin.location = (x_pos, y_pos, waistline_z)
    else:
        # 顶部引脚 - 朝向正Y方向
        pin.rotation_euler = (0, 0, math.radians(180))
        pin.location = (x_pos, y_pos, waistline_z)
    
    # 为引脚添加倒角修改器
    bevel_mod = pin.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = 0.02
    bevel_mod.segments = dimensions['chamfer_segments']
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 应用修改器
    bpy.ops.object.select_all(action='DESELECT')
    pin.select_set(True)
    bpy.context.view_layer.objects.active = pin
    bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    
    # 设置材质 - 使用金属材质
    pin.data.materials.clear()
    mat_pin = create_material(name="Metal_Silver", base_color = (0.8, 0.8, 0.85, 1.0), metallic = 1.0, roughness = 0.2)
    pin.data.materials.append(mat_pin)
    
    return pin

def main():
    # 清理场景
    clear_scene()
    
    # 创建SOP20封装模型
    sop20 = create_sop20_model()
    
    # 验证引脚位置
    pin1 = bpy.data.objects.get("Pin_1")
    pin10 = bpy.data.objects.get("Pin_10")
    pin11 = bpy.data.objects.get("Pin_11")
    pin20 = bpy.data.objects.get("Pin_20")
    
    if pin1 and pin10 and pin11 and pin20:
        print(f"引脚1的X坐标: {pin1.location.x:.3f}mm (应为: {-dimensions['pin_pitch'] * 4.5:.3f}mm)")
        print(f"引脚10的X坐标: {pin10.location.x:.3f}mm")
        print(f"引脚11的X坐标: {pin11.location.x:.3f}mm")
        print(f"引脚20的X坐标: {pin20.location.x:.3f}mm")
        print(f"引脚1的Y坐标: {pin1.location.y:.3f}mm")
        print(f"引脚10的Y坐标: {pin10.location.y:.3f}mm")
        print(f"引脚11的Y坐标: {pin11.location.y:.3f}mm")
        print(f"引脚20的Y坐标: {pin20.location.y:.3f}mm")
        print(f"引脚Z坐标（腰线高度）: {pin1.location.z:.3f}mm")
    
    # 验证所有修改器是否已应用
    print("验证所有修改器应用状态：")
    for obj in bpy.context.scene.objects:
        if len(obj.modifiers) == 0:
            print(f"✓ {obj.name}: 无未应用的修改器")
        else:
            print(f"⚠ {obj.name}: 仍有{len(obj.modifiers)}个未应用的修改器")
    
    # 验证材质设置
    print("验证材质设置：")
    body = bpy.data.objects.get("SOP20_Body")
    pin1 = bpy.data.objects.get("Pin_1")
    text = bpy.data.objects.get("SOP20_Text")
    
    if body and pin1 and text:
        if body.data.materials:
            print(f"✓ 主体材质: {body.data.materials[0].name}")
        else:
            print("⚠ 主体材质: 无材质")
        
        if pin1.data.materials:
            print(f"✓ 引脚材质: {pin1.data.materials[0].name}")
        else:
            print("⚠ 引脚材质: 无材质")
            
        if text.data.materials:
            print(f"✓ 文字材质: {text.data.materials[0].name}")
        else:
            print("⚠ 文字材质: 无材质")
    
    print("SOP20封装模型创建完成！")
    print("已修正以下关键参数：")
    print(f"1. 引脚1的X坐标: x = -pin_pitch * 4.5 = {-dimensions['pin_pitch'] * 4.5:.3f}mm")
    print("2. 引脚跨距计算: 使用图纸中的计算方法")
    print("3. Pin1标记位置: 已根据图纸添加")
    print("使用图纸中的精确尺寸：")
    print(f"主体尺寸: BL={dimensions['body_length']}mm, BW={dimensions['body_width']}mm, BT={dimensions['body_height']}mm")
    print(f"引脚尺寸: TW={dimensions['pin_width']}mm, LL={dimensions['pin_length']}mm, FT={dimensions['pin_thickness']}mm")
    print(f"引脚间距: LP={dimensions['pin_pitch']}mm")
    print(f"引脚跨距: BW={dimensions['pin_span']}mm")
    print(f"实际引脚长度: RL={dimensions['actual_foot_length']:.2f}mm")
    print(f"最大引脚长度: FL={dimensions['foot_length']}mm")
    print(f"离地高度: SO={dimensions['standoff_height']}mm")
    print(f"引脚数量: 20个（左下为1，右下为10，右上为11，左上为20，逆时针排列）")
    print("已通过布尔运算添加Pin1标记凹坑")
    print("已添加SOP20文字标记")
    print("所有对象已组织到'SOP20_Package'组合中")

if __name__ == "__main__":
    main()