import bpy
import bmesh
from mathutils import Vector
import math
from io_fritzing.assets.utils.scene import clear_scene
from io_fritzing.assets.utils.material import create_material
from io_fritzing.assets.utils.origin import set_origin_to_bottom

# 根据图纸中的尺寸表定义SOT23-3参数
dimensions = {
    # 主体尺寸
    'body_length': 2.92,  # D: 2.82-3.02 取中值2.92mm
    'body_width': 1.30,   # 本体宽度1.3mm (SOT23-3)
    'body_height': 1.10,  # A2: 1.05-1.15 取中值1.10mm
    
    # 引脚尺寸
    'pin_width': 0.40,     # b: 0.30-0.50 取中值0.40mm
    'pin_thickness': 0.15, # c: 0.10-0.20 取中值0.15mm
    
    # 引脚跨距
    'pin_span': 1.60,     # E: 1.50-1.70 取中值1.60mm
    
    # 引脚间距
    'pin_pitch': 0.95,    # e1: 0.950 (BSC)
    
    # 引脚长度
    'pin_length': 0.40,   # L: 0.30-0.50 取中值0.40mm
    
    # 其他参数
    'standoff_height': 0.075, # A1: 0.00-0.15 取中值0.075mm
    'total_height': 1.15,     # A: 最大1.15mm
    
    # 倒角参数
    'chamfer_size': 0.08,
    'chamfer_segments': 6,
    
    # 引脚弯曲参数
    'bend_radius': 0.2,      # 弯曲半径
    'bend_angle': 80,        # 弯曲角度
    'bend_start': 0.2,       # 离起点开始弯曲的距离
    'middle_length': 0.2,    # 中间直线长度
    
    # 倾斜角度
    'tilt_angle': 4,         # θ: 0-8° 取中值4°，这个值暂时没有使用
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

def create_sot23_3_model(text="SOT23-3"):
    """创建SOT23-3完整模型"""
    # 创建芯片主体
    body = create_chip_body()
    
    # 创建3个引脚
    pins = create_pins()
    
    text_marker = create_text_marker(text)
    
    # 确保所有修改器都被应用
    apply_all_modifiers()

    if body is not None:
        bpy.ops.object.select_all(action='DESELECT')
        for obj in [body] + pins + [text_marker]:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.join()
        body.name = "SOT23-3_Package"
    
    set_origin_to_bottom(body)

    return body

def create_text_marker(text="SOT23-3"):
    """创建SOT23-3标记文字"""
    # 在主体顶部添加SOT23-3文字标记
    text_location = (0, 0, dimensions['body_height'] + dimensions['standoff_height'] + 0.01)
    
    # 创建文本对象
    bpy.ops.object.text_add(location=text_location)
    text_obj = bpy.context.active_object
    text_obj.name = text + "_Text"
    
    # 设置文本内容
    text_obj.data.body = text
    
    # 设置文本大小
    text_obj.data.size = 0.5
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 转换为网格
    bpy.ops.object.convert(target='MESH')
    
    # 缩放文本以适应主体
    text_obj.scale = (0.8, 0.8, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    
    # 设置文本材质
    text_obj.data.materials.clear()
    mat_text = create_material(name="Text_White", base_color=(0.9, 0.9, 0.9, 1.0))
    text_obj.data.materials.append(mat_text)
    
    return text_obj

def create_chip_body():
    """创建芯片主体"""
    # 使用图纸中的实际尺寸
    length = dimensions['body_length']  # 2.92mm
    width = dimensions['body_width']    # 1.30mm
    height = dimensions['body_height']  # 0.975mm
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2 + dimensions['standoff_height'])
    )
    body = bpy.context.active_object
    body.name = "SOT23-3_Body"
    
    # 直接设置尺寸
    body.scale = (length, width, height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 创建Pin1标记凹坑
    # create_pin1_marker_cut(body)
    
    # 添加倒角修改器
    bevel_mod = body.modifiers.new(name="Bevel", type='BEVEL')
    bevel_mod.width = dimensions['chamfer_size']
    bevel_mod.segments = dimensions['chamfer_segments']
    bevel_mod.limit_method = 'ANGLE'
    bevel_mod.angle_limit = math.radians(30)
    
    # 应用修改器
    bpy.ops.object.modifier_apply(modifier=bevel_mod.name)
    
    # 设置材质
    body.data.materials.clear()
    mat_body = create_material(name="Plastic_Black", base_color=(0.05, 0.05, 0.05, 1.0), metallic=0.0, roughness=0.8)
    body.data.materials.append(mat_body)
    
    return body

def create_pin1_marker_cut(body):
    """创建Pin1标记凹坑"""
    # 标记位置
    marker_x = -dimensions['pin_pitch']  # 引脚1在左侧
    marker_y = -dimensions['body_width'] / 2 + 0.2  # 主体边缘内偏移
    marker_z = dimensions['body_height'] + dimensions['standoff_height'] - 0.05
    
    # 创建圆柱体作为凹坑切割工具
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=12,
        radius=0.08,
        depth=0.15,
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

def create_pins():
    """创建3个引脚 - 修正后的布局"""
    pins = []
    
    # 引脚跨距
    body_width = dimensions['body_width']
    pin_pitch = dimensions['pin_pitch']
    
    # 引脚1: 底部左侧
    pin1 = create_pin_with_caps(
        x_pos=-pin_pitch,  # 左侧，X = -0.95mm
        y_pos=-body_width/2,  # 主体下边缘
        pin_number=1,
        side='left',
        is_top_pin=False
    )
    pins.append(pin1)
    
    # 引脚2: 底部右侧
    pin2 = create_pin_with_caps(
        x_pos=pin_pitch,  # 右侧，X = 0.95mm
        y_pos=-body_width/2,  # 主体下边缘
        pin_number=2,
        side='right',
        is_top_pin=False
    )
    pins.append(pin2)
    
    # 引脚3: 顶部中间
    pin3 = create_pin_with_caps(
        x_pos=0,  # 中间，X = 0mm
        y_pos=body_width/2,  # 主体上边缘
        pin_number=3,
        side='right',  # 右侧引脚布局
        is_top_pin=True
    )
    pins.append(pin3)
    
    return pins

def create_pin_with_caps(x_pos, y_pos, pin_number, side, is_top_pin=True):
    """创建引脚 - 包含端面封面"""
    # 引脚尺寸
    width = dimensions['pin_width']      # 0.40mm
    thickness = dimensions['pin_thickness'] # 0.15mm
    
    # 弯曲参数
    bend_radius = dimensions['bend_radius']
    bend_angle = math.radians(dimensions['bend_angle'])
    bend_start = dimensions['bend_start']
    middle_length = dimensions['middle_length']
    
    # 计算引脚总长度
    pin_length = dimensions['pin_length']
    
    # 计算主体腰线高度
    waistline_z = dimensions['body_height'] / 2 + dimensions['standoff_height']
    
    # 使用bmesh创建精确的引脚几何体
    bm = bmesh.new()
    
    # 计算各段长度
    bend_length = bend_radius * bend_angle
    remaining_length = pin_length - bend_start - bend_length - middle_length - bend_length
    
    # 创建引脚的弯曲路径
    path_points = []
    
    # 1. 第一段直线 (从腰线开始水平延伸)
    segments = 8
    for i in range(segments):
        t = i / (segments - 1)
        y = bend_start * t
        z = 0
        path_points.append((0, y, z))
    
    # 2. 第一次弯曲
    segments = 16
    for i in range(1, segments + 1):
        t = i / segments
        angle = t * bend_angle
        y = bend_start + bend_radius * math.sin(angle)
        z = -bend_radius * (1 - math.cos(angle))
        path_points.append((0, y, z))
    
    # 3. 中间直线段
    segments = 6
    end_y = path_points[-1][1]
    end_z = path_points[-1][2]
    
    tangent_y = math.cos(bend_angle)
    tangent_z = -math.sin(bend_angle)
    
    for i in range(1, segments + 1):
        t = i / segments
        y = end_y + middle_length * t * tangent_y
        z = end_z + middle_length * t * tangent_z
        path_points.append((0, y, z))
    
    # 4. 第二次弯曲
    segments = 16
    end_y = path_points[-1][1]
    end_z = path_points[-1][2]
    
    for i in range(1, segments + 1):
        t = i / segments
        angle = bend_angle - t * bend_angle
        y = end_y + bend_radius * (math.sin(bend_angle) - math.sin(angle))
        z = end_z - bend_radius * (math.cos(angle) - math.cos(bend_angle))
        path_points.append((0, y, z))
    
    # 5. 最后一段直线
    segments = 8
    end_y = path_points[-1][1]
    end_z = path_points[-1][2]
    
    for i in range(1, segments + 1):
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
            binormal = Vector((1, 0, 0))
        
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
    
    # 定位引脚
    if side == 'left':
        if is_top_pin:
            # 左侧上方引脚 (引脚1)
            pin.rotation_euler = (0, 0, 0)  # 不旋转
        else:
            # 左侧下方引脚 (引脚2) - 旋转180度
            pin.rotation_euler = (0, 0, math.radians(180))
    else:  # 'right'
        if is_top_pin:
            # 右侧上方引脚 (引脚3)
            pin.rotation_euler = (0, 0, 0)  # 不旋转
        else:
            # 右侧下方引脚 (引脚2)
            pin.rotation_euler = (0, 0, math.radians(180))
    
    # 设置引脚位置
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
    
    # 设置材质
    pin.data.materials.clear()
    mat_pin = create_material(name="Metal_Silver", base_color = (0.8, 0.8, 0.85, 1.0), metallic = 1.0, roughness = 0.2)
    pin.data.materials.append(mat_pin)
    
    return pin

def create_collection_and_organize(body, pins):
    """将所有对象组织到一个组合中"""
    # 创建新的组合
    collection = bpy.data.collections.new("SOT23-3_Package")
    bpy.context.scene.collection.children.link(collection)
    
    # 将对象从主场景中移除
    bpy.context.scene.collection.objects.unlink(body)
    for pin in pins:
        bpy.context.scene.collection.objects.unlink(pin)
    
    # 将对象添加到新组合中
    collection.objects.link(body)
    for pin in pins:
        collection.objects.link(pin)
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    for pin in pins:
        pin.select_set(True)
    
    return collection

def main():
    # 清理场景
    clear_scene()
    
    # 创建SOT23-3封装模型
    sot23_3 = create_sot23_3_model()
    
    # 打印尺寸信息
    print("SOT23-3封装模型创建完成！")
    print(f"主体尺寸: {dimensions['body_length']} x {dimensions['body_width']} x {dimensions['body_height']} mm")
    print(f"引脚数量: 3")
    print(f"引脚宽度: {dimensions['pin_width']} mm")
    print(f"引脚厚度: {dimensions['pin_thickness']} mm")
    print(f"引脚间距: {dimensions['pin_pitch']} mm (BSC)")
    print(f"引脚跨距: {dimensions['pin_span']} mm")
    print(f"引脚长度: {dimensions['pin_length']} mm")
    print(f"总高度: {dimensions['total_height']} mm")
    print("引脚端面已封面，符合图纸要求")
    
    # 打印引脚布局
    print("\n引脚布局:")
    print("引脚1: 左侧上方, X = -0.95mm, Y = 0.65mm")
    print("引脚2: 底部右侧, X = 0.95mm, Y = -0.65mm")
    print("引脚3: 顶部中间, X = 0mm, Y = 0.65mm")

if __name__ == "__main__":
    main()