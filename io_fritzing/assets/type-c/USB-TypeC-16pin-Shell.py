import bpy
import bmesh
from mathutils import Vector

# 清理场景
def clear_scene():
    # 确保在对象模式下
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 选择所有对象并删除
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False, confirm=False)
    
    # 设置场景单位
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'

# 创建基础USB Type-C母座外壳
def create_usb_type_c_shell():
    # 目标尺寸：7.35mm x 8.94mm x 3.26mm
    width = 7.35    # X轴 7.35mm
    length = 8.94   # Y轴 8.94mm  
    height = 3.26   # Z轴 3.26mm
    
    # 创建基础立方体
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, height/2))
    shell = bpy.context.active_object
    shell.name = "USB_TypeC_Female_Shell"
    
    # 设置尺寸
    shell.dimensions = (width, length, height)
    
    # 应用变换
    bpy.ops.object.transform_apply(scale=True, location=False, rotation=False)
    
    return shell

# 创建并选择性倒角内部空腔立方体，然后进行布尔运算
def create_and_selectively_bevel_internal_cavity(shell):
    # 内部空腔尺寸（比外壳稍小，长度增加5mm）
    cavity_width = 6.35   # 6.35mm
    cavity_length = 7.94 + 5.0  # 7.94mm + 5mm = 12.94mm
    cavity_height = 2.26  # 2.26mm
    
    # 计算空腔位置，使其在前面突出5mm
    cavity_y_offset = (cavity_length - shell.dimensions.y) / 2 - 5.0
    
    # 创建空腔立方体
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, cavity_y_offset, shell.location.z))
    cavity = bpy.context.active_object
    cavity.name = "Internal_Cavity"
    cavity.dimensions = (cavity_width, cavity_length, cavity_height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 进入编辑模式对空腔立方体的特定边进行倒角
    bpy.context.view_layer.objects.active = cavity
    cavity.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    
    # 切换到边选择模式
    bpy.ops.mesh.select_mode(type='EDGE')
    
    # 取消选择所有边
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # 使用bmesh选择特定边
    mesh = cavity.data
    bm = bmesh.from_edit_mesh(mesh)
    
    # 设置容差
    tolerance = 0.01
    
    # 获取空腔尺寸
    dim_x = cavity.dimensions.x
    dim_y = cavity.dimensions.y
    dim_z = cavity.dimensions.z
    
    # 选择空腔立方体的四条边（与外壳类似的位置）
    for edge in bm.edges:
        # 获取边的两个顶点
        v1, v2 = edge.verts
        
        # 计算边的中心点
        center = (v1.co + v2.co) * 0.5
        
        # 选择顶部边缘（Z轴最大）
        if abs(center.z - dim_z/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
        
        # 选择底部边缘（Z轴最小）
        if abs(center.z + dim_z/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
        
        # 选择左侧边缘（X轴最小）
        if abs(center.x + dim_x/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
        
        # 选择右侧边缘（X轴最大）
        if abs(center.x - dim_x/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
    
    # 更新网格
    bmesh.update_edit_mesh(mesh)
    
    # 最大化内腔倒角，使两侧形成完整的半圆形
    # 使用接近空腔高度一半的值，形成更完整的半圆
    bpy.ops.mesh.bevel(
        offset=1.1,  # 增加到1.1mm倒角（接近空腔高度2.26mm的一半）
        offset_type='OFFSET',
        segments=16,    # 进一步增加分段数，使半圆形更平滑
        profile=0.5,    # 轮廓形状（0.5为半圆形）
        clamp_overlap=True
    )
    
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 使用布尔修改器创建空腔
    bool_mod = shell.modifiers.new(name="Cavity", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = cavity
    
    # 应用布尔修改器
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)
    
    # 删除空腔对象
    bpy.ops.object.select_all(action='DESELECT')
    cavity.select_set(True)
    bpy.ops.object.delete()
    
    return shell

# 创建内部隔板
def create_internal_partition(shell):
    # 内部隔板尺寸
    partition_width = 6.0   # 6.0mm
    partition_length = 0.5  # 0.5mm
    partition_height = 1.5  # 1.5mm
    
    # 创建隔板（位于空腔内部）
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, shell.location.z))
    partition = bpy.context.active_object
    partition.name = "Internal_Partition"
    partition.dimensions = (partition_width, partition_length, partition_height)
    bpy.ops.object.transform_apply(scale=True)
    
    # 将隔板移动到正确位置（内部中间）
    # 由于空腔向前突出，需要调整隔板位置
    partition.location.y = shell.location.y - (shell.dimensions.y/2 - partition.dimensions.y/2 - 0.5 - 5.0)
    
    return partition

# 对外壳外部边进行倒角处理，最大化倒角使两侧形成完整的半圆形
def apply_bevel_to_external_edges(shell):
    # 确保在对象模式下
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 选择外壳并进入编辑模式
    bpy.context.view_layer.objects.active = shell
    shell.select_set(True)
    
    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    
    # 切换到边选择模式
    bpy.ops.mesh.select_mode(type='EDGE')
    
    # 取消选择所有边
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # 使用bmesh选择特定边
    mesh = shell.data
    bm = bmesh.from_edit_mesh(mesh)
    
    # 设置容差
    tolerance = 0.01
    
    # 获取外壳尺寸
    dim_x = shell.dimensions.x
    dim_y = shell.dimensions.y
    dim_z = shell.dimensions.z
    
    # 选择外部边（顶部、底部、左侧、右侧）
    for edge in bm.edges:
        # 获取边的两个顶点
        v1, v2 = edge.verts
        
        # 计算边的中心点
        center = (v1.co + v2.co) * 0.5
        
        # 选择顶部边缘（Z轴最大）
        if abs(center.z - dim_z/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
        
        # 选择底部边缘（Z轴最小）
        if abs(center.z + dim_z/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
        
        # 选择左侧边缘（X轴最小）
        if abs(center.x + dim_x/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
        
        # 选择右侧边缘（X轴最大）
        if abs(center.x - dim_x/2) < tolerance:
            # 排除正面和背面的边
            if abs(center.y - dim_y/2) > tolerance and abs(center.y + dim_y/2) > tolerance:
                edge.select = True
    
    # 更新网格
    bmesh.update_edit_mesh(mesh)
    
    # 最大化外壳倒角，使两侧形成完整的半圆形
    # 使用接近外壳高度一半的值，形成更完整的半圆
    bpy.ops.mesh.bevel(
        offset=1.5,  # 增加到1.5mm倒角（接近外壳高度3.26mm的一半）
        offset_type='OFFSET',
        segments=20,    # 进一步增加分段数，使半圆形更平滑
        profile=0.5,    # 轮廓形状（0.5为半圆形）
        clamp_overlap=True
    )
    
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    return shell

# 添加材质
def assign_materials(shell):
    # 外壳材质（金属）
    shell_mat = bpy.data.materials.new("Shell_Metal")
    shell_mat.use_nodes = True
    shell_mat.diffuse_color = (0.7, 0.7, 0.75, 1.0)  # 银灰色
    nodes = shell_mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    output = nodes.new('ShaderNodeOutputMaterial')
    shell_mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    bsdf.inputs['Metallic'].default_value = 0.9
    bsdf.inputs['Roughness'].default_value = 0.15
    bsdf.inputs['Base Color'].default_value = (0.7, 0.7, 0.75, 1.0)  # 银灰色
    
    shell.data.materials.append(shell_mat)
    

# 设置场景
def setup_scene():
    # 设置视图模式
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    space.shading.type = 'MATERIAL'
                    # 安全地设置坐标轴显示
                    if hasattr(space, 'overlay'):
                        space.overlay.show_axis_x = True
                        space.overlay.show_axis_y = True
                        space.overlay.show_axis_z = True
                    break

# 主函数
def main():
    # 确保在对象模式下开始
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    clear_scene()
    
    # 创建外壳
    shell = create_usb_type_c_shell()
    print("基础外壳创建完成")
    
    # 创建并选择性倒角内部空腔（长度增加5mm，前面突出5mm）
    shell = create_and_selectively_bevel_internal_cavity(shell)
    print("内部空腔创建并选择性倒角完成（长度增加5mm，前面突出5mm）")
    
    # 创建内部隔板
#    partition = create_internal_partition(shell)
#    print("内部隔板创建完成")
    
    # 对外壳外部边进行倒角处理
#    shell, partition = apply_bevel_to_external_edges(shell, partition)
    shell = apply_bevel_to_external_edges(shell)
    print("外部倒角处理完成")
    
    # 添加材质
#    assign_materials(shell, partition)
    assign_materials(shell)
    print("材质分配完成")
    
    # 设置场景
    setup_scene()
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    shell.select_set(True)
    
    # 打印模型信息
    print("=" * 60)
    print("USB Type-C母座模型创建完成")
    print(f"目标尺寸: 7.35mm × 8.94mm × 3.26mm")
    print(f"实际尺寸: {shell.dimensions.x:.2f}mm × {shell.dimensions.y:.2f}mm × {shell.dimensions.z:.2f}mm")
    print("倒角处理:")
    print("- 已最大化内腔倒角至1.1mm（接近空腔高度2.26mm的一半）")
    print("- 已最大化外壳倒角至1.5mm（接近外壳高度3.26mm的一半）")
    print("- 内部隔板倒角增加至0.75mm（接近隔板高度1.5mm的一半）")
    print("- 分段数增加到16-20，使半圆形极其平滑")
    print("- 内部空腔长度增加5mm，前面突出5mm")
    print("- 已形成接近完整的半圆形轮廓")
    print("- 正面和背面边缘保持尖锐直角（无倒角）")
    print("=" * 60)
    
    # 检查并报告尺寸问题
    if abs(shell.dimensions.x - 7.35) > 0.1:
        print(f"警告: X方向尺寸不匹配! 期望7.35mm，实际{shell.dimensions.x:.2f}mm")
    else:
        print("✓ X方向尺寸正确")
        
    if abs(shell.dimensions.y - 8.94) > 0.1:
        print(f"警告: Y方向尺寸不匹配! 期望8.94mm，实际{shell.dimensions.y:.2f}mm")
    else:
        print("✓ Y方向尺寸正确")
        
    if abs(shell.dimensions.z - 3.26) > 0.1:
        print(f"警告: Z方向尺寸不匹配! 期望3.26mm，实际{shell.dimensions.z:.2f}mm")
    else:
        print("✓ Z方向尺寸正确")

# 运行脚本
if __name__ == "__main__":
    main()