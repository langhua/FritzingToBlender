import bpy
import bmesh
from mathutils import Vector
import math
from io_fritzing.assets.utils.scene import clear_scene

# 定义精确的尺寸参数
dimensions = {
    # 第1段：直线5mm
    's1_length': 5.0,
    
    # 第2段：圆弧，半径3mm，角度45度
    's2_radius': 3.0,
    's2_angle': -45.0,  # 度
    
    # 第3段：直线8mm
    's3_length': 8.0,
    
    # 第4段：圆弧，半径4mm，角度40度
    's4_radius': 4.0,
    's4_angle': 80.0,  # 度
    
    # 第5段：直线15mm
    's5_length': 15.0,
    
    # 管的截面参数
    'radius': 0.5,       # 截面半径
    'thickness': 0.4,    # 厚度
    
    # 细分参数
    'straight_segments': 4,
    'arc_segments': 16,
    'circular_segments': 12,

    # 矩形截面参数
    'width': 4.0,       # 矩形宽度
    'height': 0.4,      # 矩形高度
    'thickness': 0.1,   # 管壁厚度（用于空心管）
}

def create_z_model(type='tubular', dimensions=dimensions, name='z_model'):
    """严格按照给定步骤创建模型"""
    bm = bmesh.new()
    
    # 获取参数
    s1_len = dimensions['s1_length']
    s2_rad = dimensions['s2_radius']
    s2_angle_deg = dimensions['s2_angle']
    s3_len = dimensions['s3_length']
    s4_rad = dimensions['s4_radius']
    s4_angle_deg = dimensions['s4_angle']
    s5_len = dimensions['s5_length']
    
    # 矩形截面尺寸
    width = dimensions['width']
    height = dimensions['height']
    thickness = dimensions['thickness']
    
    # 角度转换为弧度
    s2_angle = math.radians(s2_angle_deg)
    s4_angle = math.radians(s4_angle_deg)
    
    # 计算常用三角函数值
    cos_s2 = math.cos(s2_angle)
    sin_s2 = math.sin(s2_angle)
    cos_s4_s2 = math.cos(s4_angle + s2_angle)
    sin_s4_s2 = math.sin(s4_angle + s2_angle)
    
    # 步骤1: 定义起点和方向
    start_point = Vector((0, 0, 0))
    current_point = start_point.copy()
    current_direction = Vector((1, 0, 0))  # X轴正方向
    
    # 存储路径点
    path_points = []
    
    # 第1段: 直线s1_len
    # print(f"第1段: 从{current_point}开始，方向{current_direction}，长度{s1_len}mm")
    for i in range(dimensions['straight_segments'] + 1):
        t = i / dimensions['straight_segments']
        point = start_point + current_direction * s1_len * t
        path_points.append(point)
    
    # 更新当前位置
    current_point = start_point + current_direction * s1_len
    # print(f"  终点: {current_point}")
    
    # 第2段: 圆弧，半径s2_rad，角度s2_angle_deg
    # 圆心在(s1_len,0,-s2_rad)
    center2 = Vector((s1_len, 0, -s2_rad))
    # print(f"\n第2段: 圆弧，半径{s2_rad}mm，角度{s2_angle_deg}度")
    # print(f"  圆心: {center2}")
    # print(f"  起始点: {current_point}")
    # print(f"  圆弧从0度到{s2_angle_deg}度")
    
    # 计算圆弧起始角度
    start_vec = current_point - center2
    start_angle2 = math.atan2(start_vec.z, start_vec.x)
    
    # 生成圆弧点
    for i in range(1, dimensions['arc_segments'] + 1):
        t = i / dimensions['arc_segments']
        angle = start_angle2 + s2_angle * t
        
        x = center2.x + s2_rad * math.cos(angle)
        y = 0
        z = center2.z + s2_rad * math.sin(angle)
        
        point = Vector((x, y, z))
        path_points.append(point)
    
    # 更新当前位置和方向
    current_point = path_points[-1]
    end_angle2 = start_angle2 + s2_angle
    current_direction = Vector((math.cos(end_angle2), 0, math.sin(end_angle2))).normalized()
    # print(f"  终点: {current_point}")
    # print(f"  新方向: {current_direction}")
    
    # 第3段: 直线s3_len，方向(cos_s2,0,sin_s2)
    s3_dir = Vector((cos_s2, 0, sin_s2)).normalized()
    # print(f"\n第3段: 方向{s3_dir}，长度{s3_len}mm")
    # print(f"  起始点: {current_point}")
    
    for i in range(1, dimensions['straight_segments'] + 1):
        t = i / dimensions['straight_segments']
        point = current_point + s3_dir * s3_len * t
        path_points.append(point)
    
    # 更新当前位置
    current_point = current_point + s3_dir * s3_len
    current_direction = s3_dir.copy()
    # print(f"  终点: {current_point}")
    
    # 第4段: 圆弧，半径s4_rad，角度s4_angle_deg
    # 需要计算圆心
    # print(f"\n第4段: 圆弧，半径{s4_rad}mm，角度{s4_angle_deg}度")
    # print(f"  起始点: {current_point}")
    # print(f"  当前方向: {current_direction}")
    
    # 计算圆心：圆心在当前点的垂直方向
    # 对于在XZ平面的弯曲，圆心在当前点的法线方向
    # 假设向右弯曲，圆心在方向向量的右侧
    normal = Vector((-current_direction.z, 0, current_direction.x))  # 法线方向
    center4 = current_point + normal * s4_rad
    
    # print(f"  圆心: {center4}")
    # print(f"  圆弧从当前方向弯曲{s4_angle_deg}度")
    
    # 计算圆弧起始角度
    start_vec4 = current_point - center4
    start_angle4 = math.atan2(start_vec4.z, start_vec4.x)
    
    # 生成圆弧点
    for i in range(1, dimensions['arc_segments'] + 1):
        t = i / dimensions['arc_segments']
        angle = start_angle4 + s4_angle * t
        
        x = center4.x + s4_rad * math.cos(angle)
        y = 0
        z = center4.z + s4_rad * math.sin(angle)
        
        point = Vector((x, y, z))
        path_points.append(point)
    
    # 更新当前位置和方向
    current_point = path_points[-1]
    end_angle4 = start_angle4 + s4_angle
    current_direction = Vector((math.cos(end_angle4), 0, math.sin(end_angle4))).normalized()
    # print(f"  终点: {current_point}")
    # print(f"  新方向: {current_direction}")
    
    # 第5段: 直线s5_len，方向(cos_s4_s2,0,sin_s4_s2)
    s5_dir = Vector((cos_s4_s2, 0, sin_s4_s2)).normalized()
    # print(f"\n第5段: 方向{s5_dir}，长度{s5_len}mm")
    # print(f"  起始点: {current_point}")
    
    for i in range(1, dimensions['straight_segments'] + 1):
        t = i / dimensions['straight_segments']
        point = current_point + s5_dir * s5_len * t
        path_points.append(point)
    
    # 最终点
    final_point = current_point + s5_dir * s5_len
    # print(f"  终点: {final_point}")
    
    # 计算路径总长度
    total_length = s1_len + s2_rad * s2_angle + s3_len + s4_rad * s4_angle + s5_len
    # print(f"\n路径总长度: {total_length:.2f}mm")
    
    sections = []
    if type == 'tubular':
        # 创建3D管状模型
        radius = dimensions['radius']
        circular_segments = dimensions['circular_segments']
        
        for i, point in enumerate(path_points):
            point_vec = Vector(point)
            
            # 计算切线方向
            if i == 0:
                tangent = (Vector(path_points[1]) - point_vec).normalized()
            elif i == len(path_points) - 1:
                tangent = (point_vec - Vector(path_points[i-1])).normalized()
            else:
                tangent = (Vector(path_points[i+1]) - Vector(path_points[i-1])).normalized()
            
            # 计算局部坐标系
            up = Vector((0, 1, 0))
            binormal = tangent.cross(up).normalized()
            
            if binormal.length < 0.001:
                binormal = Vector((0, 0, 1))
            
            normal = binormal.cross(tangent).normalized()
            
            # 创建截面顶点
            verts = []
            for j in range(circular_segments):
                angle = 2 * math.pi * j / circular_segments
                offset = binormal * (radius * math.cos(angle)) + normal * (radius * math.sin(angle))
                verts.append(bm.verts.new(point_vec + offset))
            
            sections.append(verts)
        
        # 创建连接面
        for i in range(len(sections) - 1):
            for j in range(circular_segments):
                v1 = sections[i][j]
                v2 = sections[i][(j+1)%circular_segments]
                v3 = sections[i+1][(j+1)%circular_segments]
                v4 = sections[i+1][j]
                
                try:
                    bm.faces.new([v1, v2, v3, v4])
                except:
                    pass
        
        # 创建端面
        if len(sections) > 0:
            try:
                bm.faces.new(sections[0])
            except:
                pass
            
            try:
                bm.faces.new(list(reversed(sections[-1])))
            except:
                pass

    elif type == 'rectangular_solid':
        # 创建实心矩形截面管
        half_width = width / 2
        half_height = height / 2
        
        for i, point in enumerate(path_points):
            point_vec = Vector(point)
            
            # 计算切线方向
            if i == 0:
                tangent = (Vector(path_points[1]) - point_vec).normalized()
            elif i == len(path_points) - 1:
                tangent = (point_vec - Vector(path_points[i-1])).normalized()
            else:
                tangent = (Vector(path_points[i+1]) - Vector(path_points[i-1])).normalized()
            
            # 计算局部坐标系
            up = Vector((0, 1, 0))
            binormal = tangent.cross(up).normalized()
            
            if binormal.length < 0.001:
                binormal = Vector((0, 0, 1))
            
            normal = binormal.cross(tangent).normalized()
            
            # 创建矩形截面的四个顶点
            # 矩形的宽度方向沿binormal，高度方向沿normal
            verts = []
            
            # 矩形四个顶点的位置
            vertices = [
                Vector((-half_height, -half_width, 0)),  # 左下
                Vector((-half_height, half_width, 0)),   # 右下
                Vector((half_height, half_width, 0)),    # 右上
                Vector((half_height, -half_width, 0)),   # 左上
            ]
            
            # 将局部坐标变换到世界坐标
            for v_local in vertices:
                # 从局部坐标转换到世界坐标
                v_world = point_vec + binormal * v_local.x + normal * v_local.y
                verts.append(bm.verts.new(v_world))
            
            sections.append(verts)
        
        # 创建连接面
        for i in range(len(sections) - 1):
            for j in range(4):
                v1 = sections[i][j]
                v2 = sections[i][(j+1)%4]
                v3 = sections[i+1][(j+1)%4]
                v4 = sections[i+1][j]
                
                try:
                    bm.faces.new([v1, v2, v3, v4])
                except:
                    pass
        
        # 创建端面
        if len(sections) > 0:
            try:
                bm.faces.new(sections[0])
            except:
                pass
            
            try:
                bm.faces.new(reversed(sections[-1]))
            except:
                pass

    elif type == 'rectangular_hollow':
        # 创建空心矩形截面管
        sections_outer = []  # 外矩形
        sections_inner = []  # 内矩形
        
        half_width_outer = width / 2
        half_height_outer = height / 2
        half_width_inner = (width - 2 * thickness) / 2
        half_height_inner = (height - 2 * thickness) / 2
        
        for i, point in enumerate(path_points):
            point_vec = Vector(point)
            
            # 计算切线方向
            if i == 0:
                tangent = (Vector(path_points[1]) - point_vec).normalized()
            elif i == len(path_points) - 1:
                tangent = (point_vec - Vector(path_points[i-1])).normalized()
            else:
                tangent = (Vector(path_points[i+1]) - Vector(path_points[i-1])).normalized()
            
            # 计算局部坐标系
            up = Vector((0, 1, 0))
            binormal = tangent.cross(up).normalized()
            
            if binormal.length < 0.001:
                binormal = Vector((0, 0, 1))
            
            normal = binormal.cross(tangent).normalized()
            
            # 创建外矩形的四个顶点
            outer_verts = []
            outer_vertices = [
                Vector((-half_height_outer, -half_width_outer, 0)),  # 左下
                Vector((-half_height_outer, half_width_outer, 0)),   # 右下
                Vector((half_height_outer, half_width_outer, 0)),    # 右上
                Vector((half_height_outer, -half_width_outer, 0)),   # 左上
            ]
            
            for v_local in outer_vertices:
                v_world = point_vec + binormal * v_local.x + normal * v_local.y
                outer_verts.append(bm.verts.new(v_world))
            
            sections_outer.append(outer_verts)
            
            # 创建内矩形的四个顶点
            inner_verts = []
            inner_vertices = [
                Vector((-half_height_inner, -half_width_inner, 0)),  # 左下
                Vector((-half_height_inner, half_width_inner, 0)),   # 右下
                Vector((half_height_inner, half_width_inner, 0)),    # 右上
                Vector((half_height_inner, -half_width_inner, 0)),   # 左上
            ]
            
            for v_local in inner_vertices:
                v_world = point_vec + binormal * v_local.x + normal * v_local.y
                inner_verts.append(bm.verts.new(v_world))
            
            sections_inner.append(inner_verts)
        
        # 创建外表面
        for i in range(len(sections_outer) - 1):
            for j in range(4):
                v1 = sections_outer[i][j]
                v2 = sections_outer[i][(j+1)%4]
                v3 = sections_outer[i+1][(j+1)%4]
                v4 = sections_outer[i+1][j]
                
                try:
                    bm.faces.new([v1, v2, v3, v4])
                except:
                    pass
        
        # 创建内表面
        for i in range(len(sections_inner) - 1):
            for j in range(4):
                v1 = sections_inner[i][j]
                v2 = sections_inner[i][(j+1)%4]
                v3 = sections_inner[i+1][(j+1)%4]
                v4 = sections_inner[i+1][j]
                
                try:
                    bm.faces.new([v1, v2, v3, v4])
                except:
                    pass
        
        # 创建端面侧面
        for i in [0, -1]:  # 只创建起始和结束端面
            for j in range(4):
                v1 = sections_outer[i][j]
                v2 = sections_outer[i][(j+1)%4]
                v3 = sections_inner[i][(j+1)%4]
                v4 = sections_inner[i][j]
                
                try:
                    bm.faces.new([v1, v2, v3, v4])
                except:
                    pass
        
        # 创建端面
        if len(sections_outer) > 0 and len(sections_inner) > 0:
            # 起始端面
            try:
                bm.faces.new(sections_outer[0])
            except:
                pass
            try:
                bm.faces.new(sections_inner[0])
            except:
                pass
            
            # 结束端面
            try:
                bm.faces.new(reversed(sections_outer[-1]))
            except:
                pass
            try:
                bm.faces.new(reversed(sections_inner[-1]))
            except:
                pass

    # 转换为网格
    mesh = bpy.data.meshes.new("Z_Model_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    model = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(model)
    
    return model

def create_material():
    """创建材质"""
    mat = bpy.data.materials.new(name="Model_Material")
    mat.use_nodes = True
    
    # 设置颜色
    mat.diffuse_color = (0.7, 0.7, 0.7, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.7, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.3
    bsdf.inputs['Roughness'].default_value = 0.5
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def main():
    """主函数"""
    # 清理场景
    clear_scene()
    
    print("=" * 60)
    print("严格按照给定步骤创建5段模型")
    print("=" * 60)
    
    # 创建模型
    model1 = create_z_model(type='tubular', dimensions=dimensions)
    
    # 添加材质
    mat = create_material()
    model1.data.materials.append(mat)
    
    # 创建模型
    model2 = create_z_model(type='rectangular_solid', dimensions=dimensions)
    model2.location = (0, 12, 0)
    
    # 添加材质
    model2.data.materials.append(mat)
    
    # 创建模型
    model3 = create_z_model(type='rectangular_hollow', dimensions=dimensions)
    model3.location = (0, 24, 0)
    
    # 添加材质
    model3.data.materials.append(mat)
    
    # 计算各段长度
    s1_len = dimensions['s1_length']
    s2_len = dimensions['s2_radius'] * math.radians(dimensions['s2_angle'])
    s3_len = dimensions['s3_length']
    s4_len = dimensions['s4_radius'] * math.radians(dimensions['s4_angle'])
    s5_len = dimensions['s5_length']
    
    print(f"\n各段长度:")
    print(f"  第1段: {s1_len}mm")
    print(f"  第2段: {s2_len:.2f}mm")
    print(f"  第3段: {s3_len}mm")
    print(f"  第4段: {s4_len:.2f}mm")
    print(f"  第5段: {s5_len}mm")
    print(f"  总长: {s1_len+s2_len+s3_len+s4_len+s5_len:.2f}mm")
    
    print("\n模型创建完成!")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用正交视图
            area.spaces[0].region_3d.view_perspective = 'ORTHO'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 50
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.5, 0.5, 0.5, 0.5)
            # 设置显示模式
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
    
    return model1, model2, model3

if __name__ == "__main__":
    model = main()