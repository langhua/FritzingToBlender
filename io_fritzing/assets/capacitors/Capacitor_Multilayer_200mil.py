import bpy
import bmesh
from mathutils import Vector
import math

def clear_scene():
    """清空场景"""
    # 确保在对象模式下
    if bpy.context.active_object and bpy.context.active_object.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 选择所有对象
    bpy.ops.object.select_all(action='SELECT')
    
    # 删除所有选中的对象
    bpy.ops.object.delete(use_global=False)

    # 设置场景单位
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001

def create_drum_shaped_body(diameter, thickness):
    """创建真正的鼓型电容主体 - 修正下半部分处理"""
    # 创建一个球体
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32,
        ring_count=16,
        radius=diameter/2,
        location=(0, 0, thickness/2)
    )
    body = bpy.context.active_object
    
    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # 压扁球体形成鼓型
    bpy.ops.transform.resize(value=(1, 1, thickness/diameter))
    
    # 选择顶部和底部的顶点并分别拉平
    bpy.ops.mesh.select_all(action='DESELECT')
    
    bm = bmesh.from_edit_mesh(body.data)
    
    # 选择顶部的顶点（Z坐标大于0）
    for vert in bm.verts:
        if vert.co.z > thickness/2 - 0.2:  # 选择顶部附近的顶点
            vert.select = True
    
    # 将选中的顶部顶点在Z轴上缩放为0，使其平坦
    bpy.ops.transform.resize(value=(1, 1, 0))
    
    # 取消选择所有顶点
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # 选择底部的顶点（Z坐标小于0）
    for vert in bm.verts:
        if vert.co.z < -thickness/2 + 0.2:  # 选择底部附近的顶点
            vert.select = True
    
    # 将选中的底部顶点在Z轴上缩放为0，使其平坦
    bpy.ops.transform.resize(value=(1, 1, 0))
    
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return body

def create_radial_capacitor(rad_type="100mil", body_color=(0.2, 0.4, 0.8, 1.0), 
                          pin_color=(0.8, 0.8, 0.8, 1.0)):
    """
    创建直插瓷片电容 - 真正的鼓型版本
    """
    
    # 封装尺寸定义 (单位: mm)
    dimensions = {
        "100mil": {"pin_spacing": 2.54, "diameter": 6.0, "thickness": 1.5},
        "200mil": {"pin_spacing": 5.08, "diameter": 8.0, "thickness": 2.0},
        "300mil": {"pin_spacing": 7.62, "diameter": 10.0, "thickness": 2.5},
        "400mil": {"pin_spacing": 10.16, "diameter": 12.0, "thickness": 3.0},
    }
    
    # 获取尺寸参数
    if rad_type not in dimensions:
        print(f"不支持的封装类型: {rad_type}, 使用默认100mil")
        rad_type = "100mil"
    
    dim = dimensions[rad_type]
    pin_spacing = dim["pin_spacing"]
    diameter = dim["diameter"]
    thickness = dim["thickness"]
    
    # 引脚参数
    pin_diameter = 0.5
    pin_length = 10.0
    
    # 创建鼓型电容主体
    body = create_drum_shaped_body(diameter, thickness)
    body.name = f"Capacitor_{rad_type}_Body"
    
    # 将电容主体绕X轴旋转90度，使其平放
    body.rotation_euler = (math.radians(90), 0, 0)
    
    # 设置主体材质
    mat_body = create_material("Body_Material", body_color)
    body.data.materials.append(mat_body)
    
    # 创建引脚
    create_pins(pin_spacing, pin_diameter, pin_length, pin_color)
    
    # 选择所有部件
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    for obj in bpy.context.scene.objects:
        if "Pin" in obj.name:
            obj.select_set(True)
    
    # 合并为单个物体
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    
    # 重命名最终物体
    body.name = f"Radial_Capacitor_{rad_type}"
    
    print(f"成功创建 {rad_type} 封装鼓型瓷片电容")
    print(f"引脚间距: {pin_spacing}mm, 直径: {diameter}mm, 厚度: {thickness}mm")
    
    return body

def create_pins(pin_spacing, pin_diameter, pin_length, pin_color):
    """创建引脚"""
    
    # 引脚从电容底部中心垂直向下
    pin_positions = [
        (-pin_spacing/2, 0, -pin_length/2),
        (pin_spacing/2, 0, -pin_length/2)
    ]
    
    for i, pos in enumerate(pin_positions):
        # 创建引脚圆柱体
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=pin_diameter/2,
            depth=pin_length,
            location=(pos[0], pos[1], pos[2])
        )
        pin = bpy.context.active_object
        pin.name = f"Capacitor_Pin_{i+1}"
        
        # 设置引脚材质
        mat_pin = create_material("Pin_Material", pin_color)
        pin.data.materials.append(mat_pin)

def create_material(name, color):
    """创建材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # 清除默认节点
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    # 添加PBR材质节点
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    output = nodes.new('ShaderNodeOutputMaterial')
    
    bsdf.inputs['Base Color'].default_value = color
    bsdf.inputs['Roughness'].default_value = 0.4
    bsdf.inputs['Metallic'].default_value = 0.0
    
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    # 设置实体视图下的颜色
    mat.diffuse_color = color
    
    return mat

# 主执行函数
def main():
    """主函数"""
    
    # 清空场景
    clear_scene()
    
    # 创建单个电容
    capacitor = create_radial_capacitor(
        "200mil",
        body_color=(0.2, 0.4, 0.8, 1.0),
        pin_color=(0.8, 0.8, 0.8, 1.0)
    )
    
    # 将电容放置在场景中心
    capacitor.location = (0, 0, 0)
    
    print("完整的鼓型瓷片电容模型生成完成!")

# 直接运行
if __name__ == "__main__":
    # 执行主函数
    main()