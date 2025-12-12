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
    'leg_length': 1.0,      # 腰长: 1mm
    'thickness': 0.4,       # 厚度: 0.4mm
    'location': (0, 0, 0),  # 位置
}

def apply_all_modifiers(obj=None):
    """应用所有修改器"""
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    if obj:
        objects = [obj]
    else:
        objects = bpy.context.scene.objects
    
    for obj in objects:
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        
        for modifier in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=modifier.name)
            except:
                obj.modifiers.remove(modifier)

def create_isosceles_right_triangle():
    """创建等腰直角三角形的三棱柱"""
    leg_length = dimensions['leg_length']
    thickness = dimensions['thickness']
    location = dimensions['location']
    
    # 创建bmesh
    bm = bmesh.new()
    
    # 计算三角形顶点
    # 等腰直角三角形，两个直角边长度都是leg_length
    # 我们将直角放在原点(0,0,0)
    
    # 底部三角形的三个顶点
    bottom_vertices = [
        Vector((0, 0, 0)),                     # 顶点0: 直角顶点
        Vector((leg_length, 0, 0)),            # 顶点1: 沿X轴的顶点
        Vector((0, leg_length, 0))             # 顶点2: 沿Y轴的顶点
    ]
    
    # 顶部三角形的三个顶点（沿Z轴偏移厚度）
    top_vertices = [
        Vector((0, 0, thickness)),             # 顶点3: 直角顶点
        Vector((leg_length, 0, thickness)),    # 顶点4: 沿X轴的顶点
        Vector((0, leg_length, thickness))     # 顶点5: 沿Y轴的顶点
    ]
    
    # 创建顶点
    verts = []
    for v in bottom_vertices + top_vertices:
        verts.append(bm.verts.new(v))
    
    # 创建面
    # 1. 底部面（直角三角形）
    bm.faces.new([verts[0], verts[2], verts[1]])  # 逆时针顺序
    
    # 2. 顶部面（直角三角形）
    bm.faces.new([verts[3], verts[4], verts[5]])  # 注意顺序，确保法线朝外
    
    # 3. 侧面（连接底部和顶部）
    # 侧面1: 连接直角边1 (X轴边)
    bm.faces.new([verts[0], verts[1], verts[4], verts[3]])
    
    # 侧面2: 连接直角边2 (Y轴边)
    bm.faces.new([verts[0], verts[3], verts[5], verts[2]])
    
    # 侧面3: 连接斜边
    bm.faces.new([verts[1], verts[2], verts[5], verts[4]])
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Isosceles_Right_Triangle_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    triangle = bpy.data.objects.new("Isosceles_Right_Triangle", mesh)
    bpy.context.collection.objects.link(triangle)
    
    # 设置位置
    triangle.location = location
    
    return triangle

def create_isosceles_right_triangle_2():
    """另一种创建方法：先创建三角形，然后挤出厚度"""
    leg_length = dimensions['leg_length']
    thickness = dimensions['thickness']
    location = dimensions['location']
    
    # 创建bmesh
    bm = bmesh.new()
    
    # 创建等腰直角三角形
    # 顶点坐标
    vertices = [
        Vector((0, 0, 0)),
        Vector((leg_length, 0, 0)),
        Vector((0, leg_length, 0))
    ]
    
    # 添加顶点
    verts = []
    for v in vertices:
        verts.append(bm.verts.new(v))
    
    # 创建三角形面
    triangle_face = bm.faces.new(verts)
    
    # 挤出厚度
    extruded = bmesh.ops.extrude_face_region(bm, geom=[triangle_face])
    extruded_verts = [v for v in extruded['geom'] if isinstance(v, bmesh.types.BMVert)]
    
    # 向上移动挤出的顶点
    bmesh.ops.translate(bm, vec=Vector((0, 0, thickness)), verts=extruded_verts)
    
    # 转换为网格
    mesh = bpy.data.meshes.new("Isosceles_Right_Triangle_Mesh_2")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    triangle = bpy.data.objects.new("Isosceles_Right_Triangle_2", mesh)
    bpy.context.collection.objects.link(triangle)
    
    # 设置位置
    triangle.location = location
    
    return triangle

def create_material():
    """创建材质"""
    mat = bpy.data.materials.new(name="Triangle_Material")
    mat.use_nodes = True
    
    # 设置材质颜色
    mat.diffuse_color = (0.5, 0.7, 0.9, 1.0)  # 浅蓝色
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加原理化BSDF节点
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    bsdf.inputs['Base Color'].default_value = (0.5, 0.7, 0.9, 1.0)
    bsdf.inputs['Metallic'].default_value = 0.1
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
    
    leg_length = dimensions['leg_length']
    thickness = dimensions['thickness']
    
    # 计算几何属性
    triangle_area = 0.5 * leg_length * leg_length
    prism_volume = triangle_area * thickness
    hypotenuse = math.sqrt(2) * leg_length
    
    print("等腰直角三角形的三棱柱模型创建完成！")
    print("=" * 60)
    print("模型参数:")
    print(f"  腰长: {leg_length}mm")
    print(f"  厚度: {thickness}mm")
    print(f"  位置: {dimensions['location']}")
    print("")
    print("几何属性:")
    print(f"  三角形面积: {triangle_area:.4f} mm²")
    print(f"  斜边长度: {hypotenuse:.4f} mm")
    print(f"  体积: {prism_volume:.4f} mm³")
    print(f"  表面积: {triangle_area*2 + (leg_length+leg_length+hypotenuse)*thickness:.4f} mm²")
    print("")
    print("三角形顶点坐标 (底部):")
    print(f"  顶点0: (0, 0, 0) - 直角顶点")
    print(f"  顶点1: ({leg_length}, 0, 0) - X轴顶点")
    print(f"  顶点2: (0, {leg_length}, 0) - Y轴顶点")
    print("")
    print("模型特性:")
    print("  - 等腰直角三角形，两个直角边长度相等")
    print("  - 厚度均匀，形成三棱柱")
    print("  - 共有6个顶点，5个面")
    print("  - 底部和顶部是三角形，侧面是3个矩形")
    print("  - 使用两种方法创建，确保几何正确")
    print("")
    print("创建方法:")
    print("  1. 手动创建所有顶点和面 (推荐)")
    print("  2. 创建三角形后挤出 (简化)")
    print("")
    
    # 使用方法1创建
    print("使用方法1创建等腰直角三角形的三棱柱...")
    triangle1 = create_isosceles_right_triangle()
    
    # 添加材质
    mat = create_material()
    triangle1.data.materials.append(mat)
    
    # 使用方法2创建（可选，可以注释掉）
    print("使用方法2创建等腰直角三角形的三棱柱...")
    triangle2 = create_isosceles_right_triangle_2()
    triangle2.location = (2, 0, 0)  # 移到旁边避免重叠
    triangle2.data.materials.append(mat)
    
    print("模型创建完成！")
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 使用正交视图
            area.spaces[0].region_3d.view_perspective = 'ORTHO'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 15
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.707, 0, 0, 0.707)  # 从45度角观察
            # 设置显示模式
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
    
    return triangle1

if __name__ == "__main__":
    triangle = main()