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

# 根据图纸中的尺寸表定义参数
dimensions = {
    # 主体尺寸
    'body_length': 2.80,  # L1: 2.60-3.00 取中值
    'body_width': 1.60,   # B: 1.50-1.70 取中值
    'body_height': 1.10,  # C: 0.90-1.30 取中值
    
    # 引脚尺寸
    'pin_width': 0.42,    # a: 0.35-0.50 取中值
    'pin_thickness': 0.15, # c: 0.10-0.20 取中值
    
    # 引脚间距
    'pin_pitch': 0.45,    # b: 0.35-0.55 取中值
    
    # 引脚跨距
    'pin_span': 1.90,     # E: 1.80-2.00 取中值
    
    # 其他参数
    'standoff_height': 0.075, # F: 0-0.15 取中值
    
    # 倒角参数
    'chamfer_size': 0.1,
    'chamfer_segments': 10,
    
    # 引脚弯曲参数
    'bend_radius': 0.2,      # 弯曲半径
    'bend_angle': 80,       # 弯曲角度
    'bend_start': 0.2,       # 离起点开始弯曲的距离
    'middle_length': 0.2,    # 中间直线长度
}

# 计算引脚长度
dimensions['pin_length'] = (dimensions['body_length'] - dimensions['body_width']) / 2

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

def create_sot23_6_model():
    """创建SOT23-6完整模型"""
    # 创建芯片主体
    body = create_chip_body()
    
    # 创建6个引脚 - 从腰线开始绘制
    pins = create_pins_from_waistline()
    
    # 确保所有修改器都被应用
    apply_all_modifiers()
    
    if body is not None:
        bpy.ops.object.select_all(action='DESELECT')
        body.select_set(True)
        for obj in pins:
            obj.select_set(True)
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.join()
    
    return body

def create_chip_body():
    """创建芯片主体 - 使用布尔运算添加Pin1标记凹坑"""
    # 使用图纸中的实际尺寸
    length = dimensions['body_length']  # 2.80mm
    width = dimensions['body_width']    # 1.60mm
    height = dimensions['body_height']  # 1.10mm
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2 + dimensions['standoff_height'])
    )
    body = bpy.context.active_object
    body.name = "SOT23-6_Body"
    
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
    # 引脚跨距
    pin_span = dimensions['pin_span']
    
    # 引脚1的X坐标
    pin1_x = -0.95
    
    # 标记位置
    marker_x = pin1_x
    marker_y = -pin_span / 2 + 0.1 + 0.3  # 底部引脚Y位置加上偏移，再增加0.3mm
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

def create_pins_from_waistline():
    """创建6个引脚 - 从主体腰线开始绘制"""
    pins = []
    
    # 引脚跨距
    pin_span = dimensions['pin_span']
    body_width = dimensions['body_width']
    
    # 计算引脚长度
    pin_length = dimensions['pin_length']
    
    # 底部引脚 (1, 2, 3) - 从左到右排列
    # 引脚1: X = -0.95mm
    # 引脚2: X = 0mm
    # 引脚3: X = 0.95mm
    
    # 底部引脚位置
    bottom_pin_x = [-0.95, 0, 0.95]  # 引脚1, 2, 3的X坐标
    
    for i in range(3):
        x_pos = bottom_pin_x[i]
        y_pos = -body_width / 2  # 基于body_width/2
        pin = create_pin_with_caps(x_pos, y_pos, i+1, 'bottom', pin_length)
        pins.append(pin)
    
    # 顶部引脚 (6, 5, 4) - 从右到左排列（逆时针）
    for i in range(3):
        x_pos = bottom_pin_x[2-i]  # 反转顺序
        y_pos = body_width / 2  # 基于body_width/2
        pin_number = 6 - i  # 引脚编号：6, 5, 4
        pin = create_pin_with_caps(x_pos, y_pos, pin_number, 'top', pin_length)
        pins.append(pin)
    
    return pins

def create_pin_with_caps(x_pos, y_pos, pin_number, side, pin_length):
    """创建引脚 - 包含端面封面"""
    # 引脚尺寸
    width = dimensions['pin_width']      # 0.42mm
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
        y = bend_start * t
        z = 0
        path_points.append((0, y, z))
    
    # 2. 第一次弯曲 (向下弯曲)
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
    
    # 使用成功的修改：tangent_z = -math.sin(bend_angle)
    tangent_y = math.cos(bend_angle)
    tangent_z = -math.sin(bend_angle)
    
    for i in range(1, segments + 1):
        t = i / segments
        y = end_y + middle_length * t * tangent_y
        z = end_z + middle_length * t * tangent_z
        path_points.append((0, y, z))
    
    # 4. 第二次弯曲 (向上弯曲，回到水平)
    segments = 16
    end_y = path_points[-1][1]
    end_z = path_points[-1][2]
    
    for i in range(1, segments + 1):
        t = i / segments
        angle = bend_angle - t * bend_angle
        y = end_y + bend_radius * (math.sin(bend_angle) - math.sin(angle))
        z = end_z - bend_radius * (math.cos(angle) - math.cos(bend_angle))
        path_points.append((0, y, z))
    
    # 5. 最后一段直线 - 修正Y值计算
    segments = 8
    end_y = path_points[-1][1]
    end_z = path_points[-1][2]
    
    for i in range(1, segments + 1):
        t = i / segments
        # 修正：使用 y = end_y - remaining_length * t
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
    
    # 创建端面封面 - 修正：添加引脚两端的封面
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
        pin.rotation_euler = (0, 0, math.radians(180))
        pin.location = (x_pos, y_pos, waistline_z)
    else:
        # 顶部引脚 - 朝向正Y方向
        pin.rotation_euler = (0, 0, 0)
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

def create_collection_and_organize(body, pins):
    """将所有对象组织到一个组合中"""
    # 创建新的组合
    collection = bpy.data.collections.new("SOT23-6_Package")
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
    
    # 创建SOT23-6封装模型
    body, pins, collection = create_sot23_6_model()
    
    print("SOT23-6封装模型创建完成！")
    print("引脚端面已封面，符合图纸要求")

if __name__ == "__main__":
    main()