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

# 定义尺寸参数
dimensions = {
    'long_edge': 10.0,    # 长边: 10mm
    'short_edge': 8.0,    # 短边: 8mm
    'width': 4.0,         # 宽度(高): 4mm
    'thickness': 0.4,     # 厚度: 0.4mm
    'location': (0, 0, 0),  # 位置
}

def create_isosceles_trapezoid():
    """创建等腰梯板"""
    long_edge = dimensions['long_edge']  # 10mm
    short_edge = dimensions['short_edge']  # 8mm
    width = dimensions['width']  # 4mm
    thickness = dimensions['thickness']  # 0.4mm
    
    # 创建bmesh
    bm = bmesh.new()
    
    # 计算等腰梯形的顶点坐标
    # 我们假设：
    # 1. 梯形放在X-Y平面上
    # 2. 直角在左下角
    # 3. 长边在X轴上，短边在上面
    # 4. 梯形的高（宽度）是4mm
    
    # 下底（长边）顶点
    bottom_left = Vector((0, 0, 0))  # 左下角顶点（直角顶点）
    bottom_right = Vector((long_edge, 0, 0))  # 右下角顶点
    
    # 上底（短边）顶点
    # 短边比长边短2mm，所以短边长度8mm
    # 短边在Y方向偏移宽度4mm
    # 为了使梯形对称，短边在X方向偏移(10-8)/2 = 1mm
    offset_x = (long_edge - short_edge) / 2
    top_left = Vector((offset_x, width, 0))  # 左上角顶点
    top_right = Vector((offset_x + short_edge, width, 0))  # 右上角顶点
    
    # 底部梯形的四个顶点
    bottom_vertices = [
        bm.verts.new(bottom_left),
        bm.verts.new(bottom_right),
        bm.verts.new(top_right),
        bm.verts.new(top_left)
    ]
    
    # 创建梯形面
    trapezoid_face = bm.faces.new(bottom_vertices)
    
    # 挤出厚度
    extruded = bmesh.ops.extrude_face_region(bm, geom=[trapezoid_face])
    extruded_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]
    
    # 向上移动挤出的顶点
    bmesh.ops.translate(bm, vec=Vector((0, 0, thickness)), verts=extruded_verts)
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Right_Trapezoid_Metal_Plate_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    plate = bpy.data.objects.new("Right_Trapezoid_Metal_Plate", mesh)
    bpy.context.collection.objects.link(plate)
    
    return plate

def create_right_angled_trapezoid(long_edge = None, short_edge = None, width = None, thickness = None):
    """创建直角梯形（直角在右侧）"""
    if long_edge is None:
        long_edge = dimensions['long_edge']
    if short_edge is None:
        short_edge = dimensions['short_edge']
    if width is None:
        width = dimensions['width']
    if thickness is None:
        thickness = dimensions['thickness']
    
    # 创建bmesh
    bm = bmesh.new()
    
    # 计算直角梯形的顶点坐标
    # 直角在右侧
    # 下底：从(0,0)到(long_edge,0)
    # 右侧边：从(long_edge,0)到(long_edge,width)
    # 上底：从(long_edge,width)到(long_edge-short_edge,width)
    # 左侧边：从(0,0)到(long_edge-short_edge,width)
    
    # 底部顶点
    bottom_left = Vector((0, 0, 0))
    bottom_right = Vector((long_edge, 0, 0))
    
    # 顶部顶点
    top_left = Vector((long_edge - short_edge, width, 0))
    top_right = Vector((long_edge, width, 0))
    
    # 底部梯形的四个顶点
    bottom_vertices = [
        bm.verts.new(bottom_left),
        bm.verts.new(bottom_right),
        bm.verts.new(top_right),
        bm.verts.new(top_left)
    ]
    
    # 创建梯形面
    trapezoid_face = bm.faces.new(bottom_vertices)
    
    # 挤出厚度
    extruded = bmesh.ops.extrude_face_region(bm, geom=[trapezoid_face])
    extruded_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]
    
    # 向上移动挤出的顶点
    bmesh.ops.translate(bm, vec=Vector((0, 0, thickness)), verts=extruded_verts)
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Right_Trapezoid_Alt_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    plate = bpy.data.objects.new("Right_Trapezoid_Alt", mesh)
    bpy.context.collection.objects.link(plate)
    
    return plate

def create_metal_material():
    """创建金属材质"""
    mat = bpy.data.materials.new(name="Metal_Plate_Material")
    mat.use_nodes = True
    
    # 设置金属色
    mat.diffuse_color = (0.7, 0.7, 0.75, 1.0)
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.75, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.3
    
    # 添加材质输出节点
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (400, 0)
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def calculate_trapezoid_properties(long_edge, short_edge, width, thickness):
    """计算梯形几何属性"""
    # 计算梯形面积
    area = (long_edge + short_edge) * width / 2
    
    # 计算体积
    volume = area * thickness
    
    # 计算周长
    # 需要计算斜边长度
    offset_x = (long_edge - short_edge) / 2
    slant_height = math.sqrt(offset_x**2 + width**2)
    perimeter = long_edge + short_edge + 2 * slant_height
    
    # 计算表面积
    surface_area = 2 * area + perimeter * thickness
    
    return {
        'area': area,
        'volume': volume,
        'perimeter': perimeter,
        'surface_area': surface_area,
        'slant_height': slant_height,
        'offset_x': offset_x
    }

def main():
    """主函数"""
    # 清理场景
    clear_scene()
    
    long_edge = dimensions['long_edge']
    short_edge = dimensions['short_edge']
    width = dimensions['width']
    thickness = dimensions['thickness']
    
    # 计算几何属性
    props = calculate_trapezoid_properties(long_edge, short_edge, width, thickness)
    
    print("梯形金属板3D模型创建完成！")
    print("=" * 60)
    print("模型参数:")
    print(f"  长边: {long_edge}mm")
    print(f"  短边: {short_edge}mm")
    print(f"  宽度(高): {width}mm")
    print(f"  厚度: {thickness}mm")
    print("")
    print("几何属性:")
    print(f"  梯形面积: {props['area']:.4f} mm²")
    print(f"  体积: {props['volume']:.4f} mm³")
    print(f"  斜边长度: {props['slant_height']:.4f} mm")
    print(f"  周长: {props['perimeter']:.4f} mm")
    print(f"  表面积: {props['surface_area']:.4f} mm²")
    print(f"  短边偏移: {props['offset_x']:.2f} mm (中心对称)")
    print("")
    print("顶点坐标 (底部):")
    print(f"  左下角: (0.00, 0.00, 0.00)")
    print(f"  右下角: ({long_edge:.2f}, 0.00, 0.00)")
    print(f"  左上角: ({props['offset_x']:.2f}, {width:.2f}, 0.00)")
    print(f"  右上角: ({props['offset_x'] + short_edge:.2f}, {width:.2f}, 0.00)")
    print("")
    print("模型特性:")
    print("  - 金属材质，不锈钢外观")
    print("  - 厚度均匀: 0.4mm")
    print("  - 梯形对称放置")
    print("  - 短边在中心位置")
    print("  - 底面是梯形，通过挤出形成立体")
    print("")
    print("应用说明:")
    print("  - 可用于机械结构的楔形连接件")
    print("  - 适合作为垫片或调节片")
    print("  - 可用于模具或夹具的定位块")
    print("  - 可以作为PCB板的支撑结构")
    print("=" * 60)
    
    # 创建模型
    print("创建等腰梯形金属板...")
    plate1 = create_isosceles_trapezoid()
    
    # 创建直角直角梯形（可选）
    print("创建直角梯形金属板（直角在右侧）...")
    plate2 = create_right_angled_trapezoid()
    plate2.location = (12, 0, 0)  # 移动到旁边
    
    # 添加材质
    mat = create_metal_material()
    plate1.data.materials.append(mat)
    if plate2:
        plate2.data.materials.append(mat)
    
    print("模型创建完成！")
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用正交视图
            area.spaces[0].region_3d.view_perspective = 'ORTHO'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 30
            # 设置合适的视角
            # area.spaces[0].region_3d.view_rotation = (0.5, 0.5, 0.5, 0.5)  # 从45度角观察
            # 设置显示模式
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
    
    return plate1

if __name__ == "__main__":
    plate = main()