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

# 引脚参数
pin_dimensions = {
    'width': 0.4,            # X方向宽度 - 已调整为0.4mm，符合0.35-0.49mm要求
    'length': 1.59,          # Y方向总长度
    'thickness': 0.15,       # Z方向厚度
    
    # 弯曲参数
    'bend_radius': 0.3,      # 弯曲半径
    'bend_angle': 80,        # 弯曲角度
    'bend_start': 0.25,      # 离起点开始弯曲的距离
    'middle_length': 0.2,    # 中间直线长度
}

def create_pin():
    """创建修正后的引脚模型，特别关注中间直线段的方向和厚度"""
    bm = bmesh.new()
    
    # 引脚尺寸
    width = pin_dimensions['width']
    total_length = pin_dimensions['length']
    thickness = pin_dimensions['thickness']
    
    # 弯曲参数
    bend_radius = pin_dimensions['bend_radius']
    bend_angle = math.radians(pin_dimensions['bend_angle'])
    bend_start = pin_dimensions['bend_start']
    middle_length = pin_dimensions['middle_length']
    
    # 计算各段长度
    bend_length = bend_radius * bend_angle
    remaining_length = total_length - bend_start - bend_length - middle_length - bend_length
    
    # 创建引脚的弯曲路径
    path_points = []
    
    # 1. 第一段直线 (从起点开始)
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
    
    # 3. 中间直线段 - 修正方向
    segments = 6
    end_y = path_points[-1][1]
    end_z = path_points[-1][2]
    
    # 修正方向：使用弯曲结束点的切线方向
    # 计算切线方向
    tangent_y = math.cos(bend_angle)
    tangent_z = -math.sin(bend_angle)  # 注意：这是正值，因为弯曲是向下的
    
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
        # 从当前角度回到0度
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
        y = end_y + remaining_length * t
        z = end_z
        path_points.append((0, y, z))
    
    # 沿着路径创建截面，确保厚度均匀
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
        
        # 计算法线和副法线 - 确保在整个路径上一致
        # 使用全局Z轴作为参考上方向
        up = Vector((0, 0, 1))
        binormal = tangent.cross(up).normalized()
        
        # 如果副法线长度接近0，使用X轴
        if binormal.length < 0.001:
            binormal = Vector((1, 0, 0))
        
        # 重新计算法线，确保与切线和副法线垂直
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
    
    # 创建端面
    bm.faces.new(sections[0])
    bm.faces.new(reversed(sections[-1]))
    
    # 创建网格
    mesh = bpy.data.meshes.new("Corrected_Pin_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    pin = bpy.data.objects.new("Corrected_Pin", mesh)
    bpy.context.collection.objects.link(pin)
    
    # 添加平滑着色
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()
    
    # 设置材质
    pin.data.materials.clear()
    mat_pin = bpy.data.materials.new(name="Pin_Material")
    mat_pin.use_nodes = True
    
    # 清除默认节点
    mat_pin.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat_pin.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.75, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # 添加材质输出节点
    output = mat_pin.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
    
    # 连接节点
    mat_pin.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    pin.data.materials.append(mat_pin)
    
    return pin

def main():
    # 清理场景
    clear_scene()
    
    # 创建修正后的引脚模型
    pin = create_corrected_pin()
    
    # 设置相机和光源
    setup_camera_and_lights()
    
    print("引脚模型创建完成！")
    print("已修正中间直线段的方向和厚度问题")
    print(f"引脚尺寸: X={pin_dimensions['width']}mm, Y={pin_dimensions['length']}mm, Z={pin_dimensions['thickness']}mm")

if __name__ == "__main__":
    main()