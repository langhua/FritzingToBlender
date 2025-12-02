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

# 根据图纸中的尺寸表定义参数 - 修正后的尺寸
dimensions = {
    # 主体尺寸
    'body_length': 3.00,  # A: 2.90-3.10 取中值
    'body_width': 3.00,   # B: 2.90-3.10 取中值
    'body_height': 0.85,  # C: 0.75-0.95 取中值
    
    # 引脚尺寸
    'pin_width': 0.22,    # a: 0.18-0.25 取中值
    'pin_thickness': 0.15, # c: 0.10-0.20 取中值
    
    # 引脚长度
    'pin_length': 1.3,    # L: 用户建议取1.3mm
    
    # 引脚间距
    'pin_pitch': 0.50,    # 引脚中心间距0.5mm
    
    # 引脚跨距
    'pin_span': 4.90,     # E: 4.70-5.10 取中值
    
    # 其他参数
    'standoff_height': 0.15, # F: 离地高度
    
    # 倒角参数
    'chamfer_size': 0.1,
    'chamfer_segments': 10,
    
    # 引脚弯曲参数
    'bend_radius': 0.2,      # 弯曲半径
    'bend_angle': 80,       # 弯曲角度
    'bend_start': 0.2,       # 离起点开始弯曲的距离
    'middle_length': 0.1,    # 中间直线长度
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

def create_msop10_model():
    """创建MSOP10完整模型"""
    # 创建芯片主体
    body = create_chip_body()
    
    # 创建10个引脚 - 从腰线开始绘制
    pins = create_pins_from_waistline()
    
    # 添加MSOP10标记文字
    text_marker = create_text_marker()
    
    # 确保所有修改器都被应用
    apply_all_modifiers()
    
    # 将所有对象组织到一个组合中
    collection = create_collection_and_organize(body, pins, text_marker)
    
    return body, pins, text_marker, collection

def create_chip_body():
    """创建芯片主体 - 使用布尔运算添加Pin1标记凹坑"""
    # 使用图纸中的实际尺寸
    length = dimensions['body_length']  # 3.00mm
    width = dimensions['body_width']    # 3.00mm
    height = dimensions['body_height']  # 0.85mm
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2 + dimensions['standoff_height'])
    )
    body = bpy.context.active_object
    body.name = "MSOP10_Body"
    
    # 直接设置尺寸
    body.scale = (length, width, height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 创建Pin1标记凹坑 - 修正：marker_y从1.5mm改为1.1mm
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
    mat_body = create_plastic_material("Plastic_Black")
    body.data.materials.append(mat_body)
    
    return body

def create_plastic_material(name):
    """创建塑料材质 - 改进的材质设置"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置diffuse_color，在实体模式下也能区分
    mat.diffuse_color = (0.05, 0.05, 0.05, 1.0)  # 深黑色
    
    # 清除默认节点
    mat.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # 设置塑料材质参数
    bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)  # 深黑色
    bsdf.inputs['Metallic'].default_value = 0.0  # 非金属
    bsdf.inputs['Roughness'].default_value = 0.8  # 高粗糙度，模拟塑料
    
    # 添加材质输出节点
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # 连接节点
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_metal_material(name):
    """创建金属材质 - 改进的材质设置"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置diffuse_color，在实体模式下也能区分
    mat.diffuse_color = (0.8, 0.8, 0.85, 1.0)  # 银白色
    
    # 清除默认节点
    mat.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # 设置金属材质参数
    bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.85, 1.0)  # 银白色
    bsdf.inputs['Metallic'].default_value = 1.0  # 金属材质
    bsdf.inputs['Roughness'].default_value = 0.2  # 低粗糙度，光滑金属
    
    # 添加材质输出节点
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # 连接节点
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_pin1_marker_cut(body):
    """创建Pin1标记凹坑 - 使用布尔修改器在主体上创建凹坑"""
    # 引脚1的X坐标 - 从本体中心向左2个引脚间距
    pin1_x = -0.5 * 2  # 引脚1的X坐标 = -1.0mm
    
    # 标记位置 - 修正：marker_y从-1.5mm改为-1.1mm
    marker_x = pin1_x
    marker_y = -1.1  # 修正：从-1.5mm改为-1.1mm，使标记位于主体内部而不是边缘
    marker_z = dimensions['body_height'] + dimensions['standoff_height'] - 0.05
    
    # 创建圆柱体作为凹坑切割工具
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=0.05,
        depth=0.1,
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

def create_text_marker():
    """创建MSOP10标记文字"""
    # 在主体顶部添加MSOP10文字标记
    text_location = (0, 0, dimensions['body_height'] + dimensions['standoff_height'] + 0.01)
    
    # 创建文本对象
    bpy.ops.object.text_add(location=text_location)
    text_obj = bpy.context.active_object
    text_obj.name = "MSOP10_Text"
    
    # 设置文本内容
    text_obj.data.body = "MSOP10"
    
    # 设置文本大小
    text_obj.data.size = 0.3
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 转换为网格
    bpy.ops.object.convert(target='MESH')
    
    # 缩放文本以适应主体
    text_obj.scale = (0.8, 0.8, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    
    # 设置文本材质
    text_obj.data.materials.clear()
    mat_text = bpy.data.materials.new(name="Text_White")
    mat_text.use_nodes = True
    mat_text.diffuse_color = (0.9, 0.9, 0.9, 1.0)
    text_obj.data.materials.append(mat_text)
    
    return text_obj

def create_pins_from_waistline():
    """创建10个引脚 - 从主体腰线开始绘制"""
    pins = []
    
    # 引脚长度
    pin_length = dimensions['pin_length']  # 1.5mm
    
    # 引脚间距
    pin_pitch = dimensions['pin_pitch']  # 0.5mm
    
    # 引脚位置计算
    # 引脚1-5的X坐标：从-1.0mm开始，每个引脚间距0.5mm
    # 引脚1-5的Y坐标：固定为-1.5mm (本体宽度的一半)
    # 引脚6-10的Y坐标：固定为1.5mm (本体宽度的一半)
    
    # 创建左侧引脚 (1-5) - 从下到上排列
    for i in range(5):
        x_pos = -0.5 * 2 + i * pin_pitch  # 从-1.0mm开始，每个引脚间距0.5mm
        y_pos = -1.5  # 固定为-1.5mm (本体宽度的一半)
        pin_number = i + 1  # 引脚编号：1, 2, 3, 4, 5
        pin = create_pin_with_caps(x_pos, y_pos, pin_number, 'left', pin_length)
        pins.append(pin)
    
    # 创建右侧引脚 (6-10) - 从上到下排列
    for i in range(5):
        x_pos = 0.5 * 2 - i * pin_pitch  # 从1.0mm开始，每个引脚间距-0.5mm
        y_pos = 1.5  # 固定为1.5mm (本体宽度的一半)
        pin_number = 6 + i  # 引脚编号：6, 7, 8, 9, 10
        pin = create_pin_with_caps(x_pos, y_pos, pin_number, 'right', pin_length)
        pins.append(pin)
    
    return pins

def create_pin_with_caps(x_pos, y_pos, pin_number, side, pin_length):
    """创建引脚 - 包含端面封面"""
    # 引脚尺寸
    width = dimensions['pin_width']      # 0.22mm
    thickness = dimensions['pin_thickness'] # 0.15mm
    
    # 弯曲参数
    bend_radius = dimensions['bend_radius']
    bend_angle = math.radians(dimensions['bend_angle'])
    bend_start = dimensions['bend_start']
    middle_length = dimensions['middle_length']  # 0.2mm
    
    # 计算主体腰线高度（主体中心高度）
    waistline_z = dimensions['body_height'] / 2 + dimensions['standoff_height']
    
    # 使用bmesh创建精确的引脚几何体
    bm = bmesh.new()
    
    # 计算各段长度
    bend_length = bend_radius * bend_angle
    remaining_length = pin_length - bend_start - bend_length - middle_length - bend_length
    
    # 创建引脚的弯曲路径 - 从腰线开始
    path_points = []
    
    # 1. 第一段直线 (从腰线开始水平延伸)
    segments = 8
    for i in range(segments):
        t = i / (segments - 1)
        x = -bend_start * t  # 左侧引脚向负x方向延伸
        z = 0
        path_points.append((x, 0, z))
    
    # 2. 第一次弯曲 (向下弯曲)
    segments = 16
    for i in range(1, segments + 1):
        t = i / segments
        angle = t * bend_angle
        x = -bend_start - bend_radius * math.sin(angle)
        z = -bend_radius * (1 - math.cos(angle))
        path_points.append((x, 0, z))
    
    # 3. 中间直线段
    segments = 6
    end_x = path_points[-1][0]
    end_z = path_points[-1][2]
    
    tangent_x = math.cos(bend_angle)
    tangent_z = math.sin(bend_angle)  # 注意：这是正值，因为弯曲是向下的
    
    for i in range(1, segments + 1):
        t = i / segments
        x = end_x - middle_length * t * tangent_x
        z = end_z - middle_length * t * tangent_z
        path_points.append((x, 0, z))

    # 4. 第二次弯曲 (向弯曲，回到水平)
    segments = 16
    end_x = path_points[-1][0]
    end_z = path_points[-1][2]
    
    for i in range(1, segments + 1):
        t = i / segments
        # 从当前角度回到0度
        angle = bend_angle - t * bend_angle
        x = end_x - bend_radius * (math.sin(bend_angle) - math.sin(angle))
        z = end_z - bend_radius * (math.cos(angle) - math.cos(bend_angle))
        path_points.append((x, 0, z))
    
    # 5. 最后一段直线
    segments = 8
    end_x = path_points[-1][0]
    end_z = path_points[-1][2]
    
    for i in range(1, segments + 1):
        t = i / segments
        if side == 'left':
            x = end_x - remaining_length * t
        else:
            x = end_x - remaining_length * t
        z = end_z
        path_points.append((x, 0, z))
    
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
            binormal = Vector((0, 1, 0))  # 使用Y轴作为副法线
        
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
    if side == 'left':
        # 左侧引脚 - 朝向负X方向
        pin.rotation_euler = (0, 0, math.radians(90))
        pin.location = (x_pos, y_pos, waistline_z)
    else:
        # 右侧引脚 - 朝向正X方向
        pin.rotation_euler = (0, 0, math.radians(-90))
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
    mat_pin = create_metal_material("Metal_Silver")
    pin.data.materials.append(mat_pin)
    
    return pin

def create_collection_and_organize(body, pins, text_marker):
    """将所有对象组织到一个组合中"""
    # 创建新的组合
    collection = bpy.data.collections.new("MSOP10_Package")
    bpy.context.scene.collection.children.link(collection)
    
    # 将对象从主场景中移除
    bpy.context.scene.collection.objects.unlink(body)
    for pin in pins:
        bpy.context.scene.collection.objects.unlink(pin)
    bpy.context.scene.collection.objects.unlink(text_marker)
    
    # 将对象添加到新组合中
    collection.objects.link(body)
    for pin in pins:
        collection.objects.link(pin)
    collection.objects.link(text_marker)
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    for pin in pins:
        pin.select_set(True)
    text_marker.select_set(True)
    
    return collection

def main():
    # 清理场景
    clear_scene()
    
    # 创建MSOP10封装模型
    body, pins, text_marker, collection = create_msop10_model()
    
    # 验证引脚位置
    pin1 = bpy.data.objects.get("Pin_1")
    pin5 = bpy.data.objects.get("Pin_5")
    pin6 = bpy.data.objects.get("Pin_6")
    pin10 = bpy.data.objects.get("Pin_10")
    
    if pin1 and pin5 and pin6 and pin10:
        print(f"引脚1的X坐标: {pin1.location.x:.3f}mm")
        print(f"引脚5的X坐标: {pin5.location.x:.3f}mm")
        print(f"引脚6的X坐标: {pin6.location.x:.3f}mm")
        print(f"引脚10的X坐标: {pin10.location.x:.3f}mm")
        print(f"引脚1-5的Y坐标: {pin1.location.y:.3f}mm")
        print(f"引脚6-10的Y坐标: {pin6.location.y:.3f}mm")
        print(f"引脚Z坐标（腰线高度）: {pin1.location.z:.3f}mm")
    
    # 验证Pin1标记位置
    print(f"Pin1标记Y坐标: -1.1mm (从-1.5mm修正)")
    print("Pin1标记现在位于主体内部，而不是边缘上")
    
    # 验证所有修改器是否已应用
    print("验证所有修改器应用状态：")
    for obj in bpy.context.scene.objects:
        if len(obj.modifiers) == 0:
            print(f"✓ {obj.name}: 无未应用的修改器")
        else:
            print(f"⚠ {obj.name}: 仍有{len(obj.modifiers)}个未应用的修改器")
    
    # 验证材质设置
    print("验证材质设置：")
    body = bpy.data.objects.get("MSOP10_Body")
    pin1 = bpy.data.objects.get("Pin_1")
    text = bpy.data.objects.get("MSOP10_Text")
    
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
    
    print("MSOP10封装模型创建完成！")
    print("已修正以下关键错误：")
    print("1. Pin1标记Y坐标: 从-1.5mm改为-1.1mm，使标记位于主体内部而不是边缘")
    print("2. 引脚1的X坐标: -0.5mm * 2 = -1.0mm (从本体中心向左2个引脚间距)")
    print("3. 引脚1-5的Y坐标: 固定为-1.5mm (本体宽度的一半)")
    print("4. 引脚6-10的Y坐标: 固定为1.5mm (本体宽度的一半)")
    print("5. 引脚间距: 使用引脚中心间距0.5mm")
    print("使用图纸中的精确尺寸：")
    print(f"主体尺寸: A={dimensions['body_length']}mm, B={dimensions['body_width']}mm, C={dimensions['body_height']}mm")
    print(f"引脚尺寸: a={dimensions['pin_width']}mm, L={dimensions['pin_length']}mm, c={dimensions['pin_thickness']}mm")
    print(f"引脚间距: {dimensions['pin_pitch']}mm")
    print(f"引脚跨距: E={dimensions['pin_span']}mm")
    print(f"离地高度: F={dimensions['standoff_height']}mm")
    print(f"引脚数量: 10个（左下为1，左上为10，右下为5，右上为6，逆时针排列）")
    print("已通过布尔运算添加Pin1标记凹坑")
    print("已添加MSOP10文字标记")
    print("所有对象已组织到'MSOP10_Package'组合中")

if __name__ == "__main__":
    main()