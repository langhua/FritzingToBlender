import bpy
import bmesh
from mathutils import Vector, Matrix
import math
from ..utils.material import create_material
from ..utils.scene import clear_scene


def create_single_L_pin(dims, name: str) -> bpy.types.Object:
    """创建单个L型引脚"""
    # 存储路径点
    path_points = []

    # 步骤1: 定义起点和方向
    start_point = Vector((0, 0, 0))
    current_point = start_point.copy()
    current_direction = Vector((1, 0, 0))
    
    s2_radius = 0.5
    angle_deg = -90
    
    # 第1段: 直线s1_len
    straight_segments = 4
    hole_spacing = dims['hole_spacing']
    body_length = dims['body_length']
    horizontal_length = hole_spacing/2 - body_length/2 - s2_radius
    print(f"第1段: 从{current_point}开始，方向{current_direction}，长度{horizontal_length}mm")
    for i in range(straight_segments + 1):
        t = i / straight_segments
        point = start_point + current_direction * horizontal_length * t
        path_points.append(point)
    
    # 更新当前位置
    current_point = start_point + current_direction * horizontal_length
    print(f"  终点: {current_point}")
    
    # 第2段: 圆弧，半径s2_radius，角度angle_deg
    # 圆心在(horizontal_length, 0, s2_radius)
    center = Vector((horizontal_length, 0, -s2_radius))
    # print(f"\n第2段: 圆弧，半径{s2_radius}mm，角度{angle_deg}度")
    # print(f"  圆心: {center}")
    # print(f"  起始点: {current_point}")
    # print(f"  圆弧从0度到{angle_deg}度")
    
    # 计算圆弧起始角度
    start_vec = current_point - center
    start_angle2 = math.atan2(start_vec.z, start_vec.x)
    s2_angle = math.radians(angle_deg)
    
    # 生成圆弧点
    arc_segments = 16
    for i in range(1, arc_segments + 1):
        t = i / arc_segments
        angle = start_angle2 + s2_angle * t
        
        x = center.x + s2_radius * math.cos(angle)
        y = 0
        z = center.z + s2_radius * math.sin(angle)
        
        point = Vector((x, y, z))
        path_points.append(point)
    
    # 更新当前位置和方向
    current_point = path_points[-1]
    end_angle2 = start_angle2 + math.radians(angle_deg)
    current_direction = Vector((math.cos(end_angle2), 0, math.sin(end_angle2))).normalized()
    # print(f"  终点: {current_point}")
    # print(f"  新方向: {current_direction}")
    
    cos_s2 = math.cos(s2_angle)
    sin_s2 = math.sin(s2_angle)
    # 第3段: 直线vertical_length，方向(cos_s2,0,sin_s2)
    s3_dir = Vector((cos_s2, 0, sin_s2)).normalized()
    vertical_length = dims['lead_length'] - horizontal_length - s2_radius * s2_angle
    # print(f"\n第3段: 方向{s3_dir}，长度{vertical_length}mm")
    # print(f"  起始点: {current_point}")
    
    for i in range(1, straight_segments + 1):
        t = i / straight_segments
        point = current_point + s3_dir * vertical_length * t
        path_points.append(point)
    
    # 更新当前位置
    current_point = current_point + s3_dir * vertical_length
    current_direction = s3_dir.copy()
    # print(f"  终点: {current_point}")
    
    # 计算路径总长度
    total_length = horizontal_length + s2_radius * s2_angle + vertical_length
    print(f"\n路径总长度: {total_length:.2f}mm")
    
    sections = []
    # 创建3D管状模型
    circular_segments = 12
    bm = bmesh.new()
    pin_radius = dims['lead_diameter']/2

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
            offset = binormal * (pin_radius * math.cos(angle)) + normal * (pin_radius * math.sin(angle))
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

    # 转换为网格
    mesh = bpy.data.meshes.new("L_Pin_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    model = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(model)
    
    return model

def create_L_pins(dims):
    """创建L型引脚"""
    body_length = dims['body_length']
    body_diameter_mm = dims['body_diameter']
    
    # 创建引脚材质（金属色）
    pin_mat = create_material("Pin_Material", (0.8, 0.8, 0.8, 1.0), metallic=0.8, roughness=0.3)
    
    # 创建左侧引脚
    left_pin = create_single_L_pin(dims, name="Pin_Left")
    left_pin.rotation_euler.z = math.pi
    left_pin.location.x -= body_length/2
    left_pin.location.z += body_diameter_mm * 1.05/2
    
    # 创建右侧引脚
    right_pin = create_single_L_pin(dims, name="Pin_Right")
    right_pin.location.x += body_length/2
    right_pin.location.z += body_diameter_mm * 1.05/2
    
    # 应用材质
    left_pin.data.materials.append(pin_mat)
    right_pin.data.materials.append(pin_mat)
    
    # 添加平滑着色
    for pin in [left_pin, right_pin]:
        bpy.ops.object.select_all(action='DESELECT')
        pin.select_set(True)
        bpy.context.view_layer.objects.active = pin
        bpy.ops.object.shade_smooth()
    
    return (left_pin, right_pin)

def main():
    # 清理场景
    clear_scene()
    
    # 创建弯曲模型
    create_L_pins(dims={
        'hole_spacing': 10.16,
        'body_length': 5.7,
        'body_diameter': 2.15,
        'lead_length': 26,
        'lead_diameter': 0.35,
        'band_width': 0.4,
        'band_spacing': 1.0
    })
   
    print("L型弯针模型创建完成！")

if __name__ == "__main__":
    main()