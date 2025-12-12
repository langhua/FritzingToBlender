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

# L弯折参数
dimensions = {
    'bend_width': 3.5,           # X方向宽度
    'bend_thickness': 0.4,        # Z方向厚度
    
    # 弯曲参数
    'bend_radius': 0.5,      # 弯曲半径
    'bend_angle': 90,        # 弯曲角度
    'bend_start': 0.8,         # 离起点开始弯曲的距离
    'end_length': 2.7,         # 弯曲结束后直线长度
}

def create_l_bend(width, thickness, bend_radius, bend_angle, bend_start, end_length):
    """创建弯曲模型，特别关注弯曲结束后直线段的方向和厚度"""
    bm = bmesh.new()
    
    # 创建弯曲的弯曲路径
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
        y = end_y + end_length * t * tangent_y
        z = end_z + end_length * t * tangent_z
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
    mesh = bpy.data.meshes.new("L_Bend_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    l_bend = bpy.data.objects.new("L_Bend", mesh)
    bpy.context.collection.objects.link(l_bend)
    
    # 添加平滑着色
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.update()
    
    return l_bend

def main():
    # 清理场景
    clear_scene()
    
    # 创建弯曲模型
    # 弯曲尺寸
    width = dimensions['bend_width']
    thickness = dimensions['bend_thickness']
    
    # 弯曲参数
    bend_radius = dimensions['bend_radius']
    bend_angle = math.radians(dimensions['bend_angle'])
    bend_start = dimensions['bend_start']
    end_length = dimensions['end_length']
    l_bend = create_l_bend(width, thickness, bend_radius, bend_angle, bend_start, end_length)
    
    # 设置材质
    l_bend.data.materials.clear()
    mat_l_bend = bpy.data.materials.new(name="L_Bend_Material")
    mat_l_bend.use_nodes = True
    
    # 清除默认节点
    mat_l_bend.node_tree.nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = mat_l_bend.node_tree.nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.75, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.8
    bsdf.inputs['Roughness'].default_value = 0.3
   
    # 添加材质输出节点
    output = mat_l_bend.node_tree.nodes.new(type='ShaderNodeOutputMaterial')
   
    # 连接节点
    mat_l_bend.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
   
    l_bend.data.materials.append(mat_l_bend)
   
    print("L型弯折模型创建完成！")

if __name__ == "__main__":
    main()