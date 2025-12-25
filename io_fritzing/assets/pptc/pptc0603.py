import bpy
import bmesh
from mathutils import Vector, Matrix
import math
from io_fritzing.assets.utils.scene import clear_scene
from io_fritzing.assets.utils.material import create_material
from io_fritzing.assets.utils.origin import set_origin_to_bottom

#根据技术规格说明书定义PPTC0603的精确尺寸
dimensions = {
    # 从表格中取PPTC0603的尺寸范围
    'A': 1.65,  # 总体宽度: 1.45-1.85mm, 取1.65mm
    'B': 0.85,  # 总体宽度: 0.65-1.05mm, 取0.85mm
    'C': 0.85,  # 总体厚度: 0.5-1.2mm, 取0.85mm
    'D': 0.15,  # 电极宽度: 最小0.15mm, 取0.15mm
    'E': 0.10,  # 电极中间半圆槽的半径: 最小0.1mm, 取0.1mm
    
    # 料号解析
    'part_number': 'PPTC0603',
    'serial_no': 'BN: Normal series',
    'size': '0603',
    'ih': '0.5A',  # 维持电流: 0.5A (500mA)
    'vmax': '6V',  # 最大: 6V
    'packing': '4000',  # 包装数量: 4000
    'supplementary_code': '000',
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

def create_smd0603_fuse_model(text = '5'):
    """创建自恢复保险丝完整模型"""
    # 创建保险丝主体
    body = create_fuse_body()
    
    # 创建2个电极（带半圆槽）
    terminals = create_terminals()
    
    # 创建文字标记"5"（代表500mA）
    text_obj = create_text_marking(body, text)
    
    # 确保所有修改器都被应用
    apply_all_modifiers()

    # 合并所有对象
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    for terminal in terminals:
        terminal.select_set(True)
    text_obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    body.name = 'PPTC0603_Package'

    # 调整位置
    body.location.z = body.dimensions.z/2
    body = set_origin_to_bottom(body)
    
    return body

def create_fuse_body():
    """创建保险丝主体"""
    length = dimensions['A'] - 2 * dimensions['D']
    width = dimensions['B']   # 0.85mm
    height = dimensions['C']  # 0.85mm
    
    # 创建立方体
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, 0)
    )
    body = bpy.context.active_object
    body.name = "PPTC0603_Body"
    
    # 设置尺寸
    body.scale = (length, width, height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 设置材质
    body.data.materials.clear()
    mat_body = create_material(name = "Plastic_Black", base_color = (0.1, 0.1, 0.1, 1.0), metallic = 0.0, roughness = 0.8)
    body.data.materials.append(mat_body)
    
    return body

def create_terminals():
    """创建2个带半圆槽的电极"""
    terminals = []
    
    # 创建左侧电极
    terminal_left = create_single_terminal(side='left')
    terminals.append(terminal_left)
    
    # 创建右侧电极
    terminal_right = create_single_terminal(side='right')
    terminals.append(terminal_right)
    
    return terminals

def create_single_terminal(side='left'):
    """创建单个带半圆槽的电极"""
    bm = bmesh.new()
    
    # 电极尺寸
    terminal_width = dimensions['D']       # 电极宽度: 0.15mm
    notch_radius = dimensions['E']         # 半圆槽半径: 0.10mm 
    body_length = dimensions['A']         # 主体长度: 1.65mm
    body_width = dimensions['B']          # 主体宽度: 0.85mm
    body_height = dimensions['C']         # 主体高度: 0.85mm
    
    # 计算侧向因子
    side_factor = 1.0 if side == 'right' else -1.0
    
    # 电极位置计算
    # 电极在主体的两端
    terminal_x = side_factor * (body_length / 2 - terminal_width / 2)
    terminal_y = 0
    terminal_z = 0
    
    # 创建电极的基本长方体
    # 电极的尺寸: 宽度×主体宽度×主体高度
    terminal_dx = terminal_width
    terminal_dy = body_width
    terminal_dz = body_height
    
    # 定义8个顶点
    half_dx = terminal_dx / 2
    half_dy = terminal_dy / 2
    half_dz = terminal_dz / 2
    
    # 局部坐标下的顶点
    vertices_local = [
        Vector((-half_dx, -half_dy, -half_dz)),  # 0: 左下后
        Vector((half_dx, -half_dy, -half_dz)),   # 1: 右下后
        Vector((half_dx, half_dy, -half_dz)),    # 2: 右后上
        Vector((-half_dx, half_dy, -half_dz)),   # 3: 左后上
        Vector((-half_dx, -half_dy, half_dz)),   # 4: 左下前
        Vector((half_dx, -half_dy, half_dz)),    # 5: 右下前
        Vector((half_dx, half_dy, half_dz)),     # 6: 右前上
        Vector((-half_dx, half_dy, half_dz)),    # 7: 左前上
    ]
    
    # 变换到世界坐标
    vertices_world = []
    for v in vertices_local:
        v_world = Vector((terminal_x, terminal_y, terminal_z)) + v
        vertices_world.append(bm.verts.new(v_world))
    
    # 创建立方体的面
    # 底部
    bm.faces.new([vertices_world[0], vertices_world[1], vertices_world[2], vertices_world[3]])
    # 顶部
    bm.faces.new([vertices_world[4], vertices_world[5], vertices_world[6], vertices_world[7]])
    # 前面
    bm.faces.new([vertices_world[0], vertices_world[4], vertices_world[7], vertices_world[3]])
    # 后面
    bm.faces.new([vertices_world[1], vertices_world[5], vertices_world[6], vertices_world[2]])
    # 左面
    bm.faces.new([vertices_world[0], vertices_world[1], vertices_world[5], vertices_world[4]])
    # 右面
    bm.faces.new([vertices_world[3], vertices_world[2], vertices_world[6], vertices_world[7]])
    
    # 转换为网格
    terminal_name = f"Terminal_{'1' if side == 'left' else '2'}"
    mesh = bpy.data.meshes.new(f"{terminal_name}_Mesh")
    bm.to_mesh(mesh)
    bm.free()
    
    # 创建对象
    terminal = bpy.data.objects.new(terminal_name, mesh)
    bpy.context.collection.objects.link(terminal)
    
    # 创建半圆槽
    create_terminal_notch(terminal, side)
    
    # 设置材质
    terminal.data.materials.clear()
    mat_terminal = create_material(name = "Metal_Silver", base_color = (0.85, 0.85, 0.88, 1.0), metallic = 0.9, roughness = 0.3)
    terminal.data.materials.append(mat_terminal)
    
    return terminal

def create_terminal_notch(terminal, side):
    """在电极上创建半圆槽"""
    bm = bmesh.new()
    bm.from_mesh(terminal.data)
    
    # 半圆槽参数
    notch_radius = dimensions['E']  # 0.10mm
    body_width = dimensions['B']    # 0.85mm
    body_height = dimensions['C']   # 0.85mm
    terminal_width = dimensions['D']  # 0.15mm
    
    # 计算侧向因子
    side_factor = 1.0 if side == 'right' else -1.0
    
    # 半圆槽的位置
    # 在电极的中间，Y方向
    notch_y = 0
    notch_z = 0
    
    # 半圆槽的X位置取决于电极的位置
    terminal_x = side_factor * (dimensions['A'] / 2 - terminal_width / 2)
    notch_x = terminal_x + side_factor * terminal_width / 2
    
    # 创建半圆槽的顶点
    segments = 16
    vertices = []
    
    # 创建半圆的顶点（从-Y到+Y方向）
    for i in range(segments + 1):
        angle = math.pi * (i / segments) - math.pi/2
        x = notch_x
        y = notch_y + notch_radius * math.cos(angle)
        z = notch_z + notch_radius * math.sin(angle)
        vertices.append(bm.verts.new(Vector((x, y, z))))
    
    # 创建半圆面
    for i in range(segments):
        v1 = vertices[i]
        v2 = vertices[i + 1]
        
        # 找到最近的边缘顶点来创建四边形
        # 这里我们简单地将半圆顶点与电极的对应边连接
        
    # 更新网格
    bm.to_mesh(terminal.data)
    bm.free()
    
    # 简化：使用布尔运算创建凹槽
    # 创建圆柱体作为切割工具
    notch_depth = notch_radius
    cylinder_location = Vector((
        notch_x,
        notch_y,
        notch_z
    ))
    
    # 创建一个小的圆柱体作为凹槽
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=64,
        radius=notch_radius,
        depth=body_width + 0.1,  # 稍微超出电极宽度
        location=cylinder_location,
        rotation=(0, 0, 0)
    )
    notch_cutter = bpy.context.active_object
    notch_cutter.name = f"Notch_Cutter_{'L' if side == 'left' else 'R'}"
    
    # 设置布尔修改器
    bool_mod = terminal.modifiers.new(name=f"Notch_{side}", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = notch_cutter
    
    # 应用布尔修改器
    bpy.ops.object.select_all(action='DESELECT')
    terminal.select_set(True)
    bpy.context.view_layer.objects.active = terminal
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    # 删除切割工具
    bpy.ops.object.select_all(action='DESELECT')
    notch_cutter.select_set(True)
    bpy.ops.object.delete(use_global=False)

def create_text_marking(body, marker = '5'):
    """在主体上创建文字标记"""
    # 创建文字对象
    bpy.ops.object.text_add(
        location=(0, 0, dimensions['C']/2 + 0.042)
    )
    text_obj = bpy.context.active_object
    text_obj.name = "PPTC0603_Text"
    
    # 设置文字内容
    text_obj.data.body = marker
    
    # 设置文字尺寸
    text_size = dimensions['B'] * 0.5  # 文字大小为宽度的一半
    text_obj.data.size = text_size
    text_obj.data.extrude = 0.01
    
    # 设置文字对齐
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 转换文字为网格
    bpy.ops.object.select_all(action='DESELECT')
    text_obj.select_set(True)
    bpy.context.view_layer.objects.active = text_obj
    bpy.ops.object.convert(target='MESH')
    
    # 调整文字厚度
    text_obj.data.transform(Matrix.Translation((0, 0, -0.05)))
    
    # 设置文字材质（白色）
    text_obj.data.materials.clear()
    mat_text = create_material(name = "Text_White", base_color = (1.0, 1.0, 1.0, 1.0), metallic = 0.0, roughness = 0.8)
    text_obj.data.materials.append(mat_text)
    
    return text_obj

def main():
    """主函数"""
    # 清理场景
    clear_scene()
    
    # 创建自恢复保险丝模型
    pptc0603 = create_smd0603_fuse_model()
    
    # 打印规格信息
    print("自恢复保险丝 PPTC0603 3D模型创建完成！")
    print("=" * 60)
    print("料号解析 (PART NUMBERING SYSTEM):")
    print(f"  料号: {dimensions['part_number']}")
    print(f"  系列号: {dimensions['serial_no']}")
    print(f"  尺寸: {dimensions['size']}")
    print(f"  维持电流(IH): {dimensions['ih']} (: 5)")
    print(f"  最大工作电压(VMAX): {dimensions['vmax']}")
    print(f"  包装数量: {dimensions['packing']}")
    print(f"  补充码: {dimensions['supplementary_code']}")
    print("")
    print("结构特性 (CONSTRUCTION AND MECHANICAL CHARACTERISTICS):")
    print("  尺寸参数 (单位:mm):")
    print(f"    A (总体长度): {dimensions['A']} mm (范围: 1.45-1.85mm)")
    print(f"    B (总体宽度): {dimensions['B']} mm (范围: 0.65-1.05mm)")
    print(f"    C (总体厚度): {dimensions['C']} mm (范围: 0.5-1.2mm)")
    print(f"    D (电极宽度): {dimensions['D']} mm (最小: 0.15mm)")
    print(f"    E (半圆槽半径): {dimensions['E']} mm (最小: 0.1mm)")
    print("")
    print("模型特性:")
    print("  - 黑色塑料主体")
    print("  - 银色金属电极")
    print("  - 电极带半圆槽")
    print("  - 顶部白色数字标记'5' (表示500mA/0.5A)")
    print("  - 0603封装尺寸")
    print("")
    print("应用说明:")
    print("  - 自恢复保险丝，过流保护后自动恢复")
    print("  - 最大电压: 6V/8V 16V")
    print("  - 维持电流: 0.5A (500mA)")
    print("  - 过流保护: 通常为维持电流的2倍以上")
    print("  - 典型应用: USB端口保护、电池保护、电路板保护")
    print("=" * 60)
    
    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].shading.type = 'SOLID'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
            area.spaces[0].shading.object_outline_color = (0, 0, 0)
    
    return pptc0603

if __name__ == "__main__":
    main()