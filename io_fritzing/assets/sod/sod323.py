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
    scene.unit_settings.scale_length = 0.001

# 根据图纸定义SOD-323参数
dimensions = {
    # 总体尺寸
    'total_height': 1.0,         # 总高度: 1.0mm
    'standoff_height': 0.15,     # 引脚底部到本体的距离: 0.00-0.10 取中值0.05mm
    'body_height': 0.85,         # 本体高度: 0.80-0.90 取中值0.85mm
    
    # 引脚尺寸
    'pin_width': 0.30,           # 引脚宽度: 0.250-0.350 取中值0.30mm
    'pin_thickness': 0.1,        # 引脚厚度: 0.008-0.150 取中值0.1mm
    
    # 本体尺寸
    'body_length': 1.70,         # 本体长度: 1.60-1.80 取中值1.70mm
    'body_width': 1.30,          # 本体宽度: 1.20-1.40 取中值1.30mm
    'pin_span': 1.70,            # 引脚跨距: 1.70mm
    
    # 引脚长度
    'pin_length': 0.6,          # 引脚长度
    'foot_length': 0.4,          # 引脚脚部延伸长度: 0.25-0.40 取最大值0.4mm
    'actual_foot_length': 0,     # 板上引脚长度，自动计算
    'actual_standoff_height': 0, # 引脚底部到本体的距离, 自动计算

    # 引脚弯曲参数
    'bend_radius': 0.2,          # 弯曲半径
    'bend_angle': 80,            # 弯曲角度
    'bend_start': 0.1,           # 离起点开始弯曲的距离
    'middle_length': 0.1,        # 中间直线长度

    # 倒角参数
    'chamfer_size': 0.05,
    'chamfer_segments': 10,
    
    # 倾斜角度
    'theta': 4,                  # 倾斜角度θ: 0-8° 取中值4°
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

def create_sod323_model():
    """创建SOD-323完整模型"""
    # 创建芯片主体
    body = create_chip_body()
    
    # 创建2个引脚
    pins = create_pins()
    
    # 创建白色标记
    marker = create_cathode_marking(body)
    
    # 确保所有修改器都被应用
    apply_all_modifiers()
    
    # 将所有对象组织到一个组合中
    collection = create_collection_and_organize(body, pins, marker)
    
    return body, pins, collection

def create_chip_body():
    """创建芯片主体"""
    # 使用图纸中的实际尺寸
    length = dimensions['body_length']
    width = dimensions['body_width']
    height = dimensions['body_height']

    bend_radius = dimensions['bend_radius']
    angle = math.radians(90 - dimensions['bend_angle'])
    middle_length = dimensions['middle_length']  # 0.2mm
    dimensions['actual_standoff_height'] = bend_radius * math.cos(angle) + \
                    middle_length * math.cos(angle) + \
                    bend_radius * math.cos(angle) + dimensions['pin_thickness'] * 1.5 - \
                    (dimensions['body_height'] / 2)
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, height/2 + dimensions['actual_standoff_height'])
    )
    body = bpy.context.active_object
    body.name = "SOD-323_Body"
    
    # 直接设置尺寸
    body.scale = (length, width, height)
    bpy.ops.object.transform_apply(scale=True)
    
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
    mat_body = create_plastic_material("Plastic_Black")
    body.data.materials.append(mat_body)
    
    return body

def create_plastic_material(name):
    """创建塑料材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置diffuse_color
    mat.diffuse_color = (0.05, 0.05, 0.05, 1.0)  # 深黑色
    
    # 清除默认节点
    mat.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # 设置塑料材质参数
    bsdf.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.8
    
    # 添加材质输出节点
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # 连接节点
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_metal_material(name):
    """创建金属材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置diffuse_color
    mat.diffuse_color = (0.8, 0.8, 0.85, 1.0)  # 银白色
    
    # 清除默认节点
    mat.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # 设置金属材质参数
    bsdf.inputs['Base Color'].default_value = (0.8, 0.8, 0.85, 1.0)
    bsdf.inputs['Metallic'].default_value = 1.0
    bsdf.inputs['Roughness'].default_value = 0.2
    
    # 添加材质输出节点
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # 连接节点
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_white_material(name):
    """创建白色标记材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 设置diffuse_color
    mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)  # 纯白色
    
    # 清除默认节点
    mat.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    
    # 设置塑料材质参数
    bsdf.inputs['Base Color'].default_value = (1.0, 1.0, 1.0, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.0
    bsdf.inputs['Roughness'].default_value = 0.6
    
    # 添加材质输出节点
    output = mat.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    # 连接节点
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_pins():
    """创建2个引脚 - SOD-323是对称的"""
    pins = []
    
    # 引脚跨距
    pin_span = dimensions['pin_span']
    
    # 引脚1: 左侧
    pin1 = create_pin_with_caps(
        x_pos=-pin_span/2,
        y_pos=0,
        pin_number=1,
        side='left',
        pin_length=dimensions['pin_length'],
        foot_length=dimensions['foot_length'],
    )
    pins.append(pin1)
    
    # 引脚2: 右侧
    pin2 = create_pin_with_caps(
        x_pos=pin_span/2,
        y_pos=0,
        pin_number=2,
        side='right',
        pin_length=dimensions['pin_length'],
        foot_length=dimensions['foot_length'],
    )
    pins.append(pin2)
    
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
    waistline_z = dimensions['body_height'] / 2 + dimensions['actual_standoff_height']
    
    # 使用bmesh创建精确的引脚几何体
    bm = bmesh.new()
    
    # 计算各段长度 - 考虑脚部延伸
    bend_length = bend_radius * math.radians(bend_angle)
    remaining_length = pin_length - bend_start - bend_length - middle_length - bend_length
    dimensions['actual_foot_length'] = remaining_length
    
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
    elif side == 'top':
        # 顶部引脚 - 朝向正Y方向
        pin.rotation_euler = (0, 0, math.radians(180))
        pin.location = (x_pos, y_pos, waistline_z)
    elif side == 'left':
        # 左侧引脚 - 朝向负x方向
        pin.rotation_euler = (0, 0, math.radians(-90))
        pin.location = (x_pos, y_pos, waistline_z)
    elif side == 'right':
        # 右侧引脚 - 朝向正x方向
        pin.rotation_euler = (0, 0, math.radians(90))
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

def create_cathode_marking(body):
    """在主体上创建白色"SOD-323"标记"""
    # 标记尺寸
    mark_width = dimensions['body_length'] * 0.2
    mark_height = dimensions['body_width'] - dimensions['chamfer_size'] * 2
    mark_thickness = 0.035  # 1oz
    
    # 创建标记位置
    mark_x = -dimensions['body_length'] / 2 + mark_width
    mark_y = 0
    mark_z = dimensions['body_height'] + dimensions['actual_standoff_height'] - mark_thickness / 3
    
    # 在顶部稍微下凹
    
    # 创建一个平面作为标记
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(mark_x, mark_y, mark_z)
    )
    marking = bpy.context.active_object
    marking.name = "Cathode_Marking"
    
    # 缩放标记
    marking.scale = (mark_width, mark_height, mark_thickness)
    bpy.ops.object.transform_apply(scale=True)
    
    # 设置材质
    marking.data.materials.clear()
    mat_marking = create_white_material("Marking_White")
    marking.data.materials.append(mat_marking)
    
    return marking

def create_collection_and_organize(body, pins, marker):
    """将所有对象组织到一个组合中"""
    # 创建新的组合
    collection = bpy.data.collections.new("SOD-323_Package")
    bpy.context.scene.collection.children.link(collection)
    
    # 将对象从主场景中移除
    objects_to_move = [body]
    for pin in pins:
        objects_to_move.append(pin)
    objects_to_move.append(marker)
    
    for obj in objects_to_move:
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
    
    # 将对象添加到新组合中
    for obj in objects_to_move:
        collection.objects.link(obj)
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    for obj in objects_to_move:
        obj.select_set(True)
    
    return collection

def main():
    # 清理场景
    clear_scene()
    
    # 创建SOD-323封装模型
    body, pins, collection = create_sod323_model()
    
    # 打印尺寸信息
    print("SOD-323封装模型创建完成！")
    print(f"本体尺寸: {dimensions['body_length']} x {dimensions['body_width']} x {dimensions['body_height']} mm")
    print(f"总高度: {dimensions['total_height']} mm")
    print(f"本体高度: {dimensions['body_height']} mm")
    print(f"引脚数量: 2")
    print(f"引脚宽度: {dimensions['pin_width']} mm")
    print(f"引脚厚度: {dimensions['pin_thickness']} mm")
    print(f"引脚跨距: {dimensions['pin_span']} mm")
    print(f"引脚长度: {dimensions['pin_length']} mm")
    print(f"焊盘引脚设计长度: {dimensions['foot_length']} mm")
    print(f"焊盘引脚实际长度: {dimensions['actual_foot_length']} mm")
    print(f"引脚本体设计间隙: {dimensions['standoff_height']} mm")
    print(f"引脚本体实际间隙: {dimensions['actual_standoff_height']} mm")
    print(f"倾斜角度: {dimensions['theta']}°")
    print("模型包含白色标记，符合图纸要求")

if __name__ == "__main__":
    main()