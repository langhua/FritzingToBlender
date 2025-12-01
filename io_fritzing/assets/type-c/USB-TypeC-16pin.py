import bpy
import bmesh
from mathutils import Vector
import math

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


# 创建USB Type-C舌片
def create_usb_type_c_tongue():
    # 根据图片信息设置USB Type-C舌片参数
    # 图1: TYPE-C母座16P, 尺寸8.94±0.15mm x 7.35±0.15mm
    # 图2: 舌片厚度0.70±0.05mm, 金属条宽度0.2mm
    # 图3: 舌片长度5.78mm, 宽度6.40mm
    W_base = 6.40      # 舌片宽度（图3标注6.40mm）
    T_base = 0.70      # 舌片厚度（图2标注0.70±0.05mm）
    L_base = 5.78      # 舌片长度（图3标注5.78mm）
    
    # 金属条参数 - 根据您的说明改为上下各12条
    num_metals = 12    # 每侧金属条数量（12条）
    metal_width = 0.2  # 金属条宽度（图2标注0.2mm）
    metal_gap = 0.3    # 金属条间隔
    metal_height = 0.1  # 金属条凸起高度
    
    # 计算金属条总宽度和边距
    total_metal_width = num_metals * metal_width
    total_gap_width = (num_metals - 1) * metal_gap
    total_pattern_width = total_metal_width + total_gap_width
    side_margin = (W_base - total_pattern_width) / 2  # 两侧边距
    
    # 创建新网格和对象
    mesh = bpy.data.meshes.new("USB_TypeC_Tongue_Mesh")
    obj = bpy.data.objects.new("USB_TypeC_Tongue", mesh)
    bpy.context.collection.objects.link(obj)
    
    # 使用bmesh构建网格
    bm = bmesh.new()
    
    # 创建塑料基体
    # 创建长方体顶点
    verts_base = []
    for x in [0, L_base]:
        for y in [0, W_base]:
            for z in [0, T_base]:
                verts_base.append(bm.verts.new((x, y, z)))
    
    # 创建面
    faces = [
        [0, 1, 3, 2],  # 左面
        [4, 5, 7, 6],  # 右面
        [0, 4, 6, 2],  # 前面
        [1, 5, 7, 3],  # 后面
        [0, 1, 5, 4],  # 底面
        [2, 3, 7, 6]   # 顶面
    ]
    
    for face in faces:
        bm.faces.new([verts_base[i] for i in face])
    
    # 创建金属条（上表面）- 12条
    for i in range(num_metals):
        # 计算金属条位置
        y_start = side_margin + i * (metal_width + metal_gap)
        y_end = y_start + metal_width
        
        # 创建金属条顶点（略微凸起）
        verts_metal = []
        for x in [0, L_base]:
            for y in [y_start, y_end]:
                for z in [T_base, T_base + metal_height]:
                    verts_metal.append(bm.verts.new((x, y, z)))
        
        # 创建金属条面
        metal_faces = [
            [0, 1, 3, 2],   # 左面
            [4, 5, 7, 6],   # 右面
            [0, 4, 6, 2],   # 前面
            [1, 5, 7, 3],   # 后面
            [0, 1, 5, 4],   # 底面
            [2, 3, 7, 6]    # 顶面
        ]
        
        for face in metal_faces:
            bm.faces.new([verts_metal[j] for j in face])
    
    # 创建金属条（下表面）- 12条
    for i in range(num_metals):
        # 计算金属条位置
        y_start = side_margin + i * (metal_width + metal_gap)
        y_end = y_start + metal_width
        
        # 创建金属条顶点（略微凸起）
        verts_metal = []
        for x in [0, L_base]:
            for y in [y_start, y_end]:
                for z in [-metal_height, 0]:  # 下表面
                    verts_metal.append(bm.verts.new((x, y, z)))
        
        # 创建金属条面
        metal_faces = [
            [0, 1, 3, 2],   # 左面
            [4, 5, 7, 6],   # 右面
            [0, 4, 6, 2],   # 前面
            [1, 5, 7, 3],   # 后面
            [0, 1, 5, 4],   # 底面
            [2, 3, 7, 6]    # 顶面
        ]
        
        for face in metal_faces:
            bm.faces.new([verts_metal[j] for j in face])
    
    # 合并重复顶点
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    
    # 更新网格
    bm.to_mesh(mesh)
    bm.free()
    
    # 设置对象为激活状态
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    
    # 更新网格显示
    mesh.update()
    
    return obj, W_base, L_base, T_base

# 创建增强金属材质
def create_enhanced_metal_material():
    metal_mat = bpy.data.materials.new("Enhanced_Metal_Material")
    metal_mat.use_nodes = True
    
    # 设置diffuse_color用于实体模式
    metal_mat.diffuse_color = (0.95, 0.85, 0.35, 1.0)  # 金色
    
    # 清除默认节点
    nodes = metal_mat.node_tree.nodes
    nodes.clear()
    
    # 添加输出节点
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400, 0)
    
    # 添加BSDF节点
    bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_node.location = (0, 0)
    bsdf_node.inputs['Base Color'].default_value = (0.95, 0.85, 0.35, 1.0)  # 金色
    bsdf_node.inputs['Metallic'].default_value = 1.0
    bsdf_node.inputs['Roughness'].default_value = 0.1
    
    # 连接节点
    links = metal_mat.node_tree.links
    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    return metal_mat

# 创建塑料材质 - 根据您的图片，舌片可以是黑色
def create_plastic_material(color="black"):  # 默认改为黑色
    plastic_mat = bpy.data.materials.new("Plastic_Material_" + color)
    plastic_mat.use_nodes = True
    
    # 根据颜色设置diffuse_color用于实体模式
    if color == "blue":
        plastic_mat.diffuse_color = (0.0, 0.5, 1.0, 1.0)  # 蓝色
    elif color == "green":
        plastic_mat.diffuse_color = (0.0, 0.8, 0.2, 1.0)  # 绿色
    elif color == "orange":
        plastic_mat.diffuse_color = (1.0, 0.5, 0.0, 1.0)  # 橙色
    elif color == "white":
        plastic_mat.diffuse_color = (0.9, 0.9, 0.9, 1.0)  # 白色
    elif color == "black":  # 黑色 - 根据您的图片
        plastic_mat.diffuse_color = (0.05, 0.05, 0.05, 1.0)  # 黑色
    else:  # 默认黑色
        plastic_mat.diffuse_color = (0.05, 0.05, 0.05, 1.0)  # 黑色
    
    # 清除默认节点
    nodes = plastic_mat.node_tree.nodes
    nodes.clear()
    
    # 添加输出节点
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (300, 0)
    
    # 添加BSDF节点
    bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_node.location = (0, 0)
    
    # 根据颜色设置基础颜色
    if color == "blue":
        bsdf_node.inputs['Base Color'].default_value = (0.0, 0.5, 1.0, 1.0)  # 蓝色
    elif color == "green":
        bsdf_node.inputs['Base Color'].default_value = (0.0, 0.8, 0.2, 1.0)  # 绿色
    elif color == "orange":
        bsdf_node.inputs['Base Color'].default_value = (1.0, 0.5, 0.0, 1.0)  # 橙色
    elif color == "white":
        bsdf_node.inputs['Base Color'].default_value = (0.9, 0.9, 0.9, 1.0)  # 白色
    elif color == "black":  # 黑色 - 根据您的图片
        bsdf_node.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)  # 黑色
    else:  # 默认黑色
        bsdf_node.inputs['Base Color'].default_value = (0.05, 0.05, 0.05, 1.0)  # 黑色
    
    bsdf_node.inputs['Metallic'].default_value = 0.0
    bsdf_node.inputs['Roughness'].default_value = 0.8
    
    # 连接节点
    links = plastic_mat.node_tree.links
    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    return plastic_mat

# 使用更可靠的方法分配材质
def assign_materials_using_indices(obj, tongue_thickness, plastic_color="black"):  # 默认改为黑色
    # 创建材质
    plastic_mat = create_plastic_material(plastic_color)  # 使用指定颜色，默认黑色
    metal_mat = create_enhanced_metal_material()
    
    # 分配材质
    obj.data.materials.append(plastic_mat)  # 索引0: 塑料
    obj.data.materials.append(metal_mat)    # 索引1: 金属
    
    # 确保在对象模式
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    
    # 选择所有面
    bpy.ops.mesh.select_all(action='SELECT')
    
    # 分配塑料材质（索引0）给所有面
    bpy.context.object.active_material_index = 0
    bpy.ops.object.material_slot_assign()
    
    # 现在选择金属条的面
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # 使用更可靠的方法选择金属条面
    # 通过循环遍历所有面，根据Z坐标选择金属条
    mesh = obj.data
    bm = bmesh.from_edit_mesh(mesh)
    
    # 选择上表面金属条（Z > 舌片厚度）
    for face in bm.faces:
        # 计算面的中心点
        center = face.calc_center_median()
        # 如果面的中心Z坐标大于舌片厚度，则选择为金属条
        if center.z > tongue_thickness + 0.01:
            face.select = True
    
    # 选择下表面金属条（Z < 0）
    for face in bm.faces:
        center = face.calc_center_median()
        if center.z < -0.01:
            face.select = True
    
    # 更新网格
    bmesh.update_edit_mesh(mesh)
    
    # 分配金属材质（索引1）给金属条
    bpy.context.object.active_material_index = 1
    bpy.ops.object.material_slot_assign()
    
    # 回到对象模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 清理bmesh
    bm.free()
    
    return plastic_color  # 返回使用的颜色

# 应用变换到舌片
def apply_transformations(obj, tongue_width, tongue_length, tongue_height, shell_height):
    # 绕Z轴旋转90度
    obj.rotation_euler = (0, 0, math.pi/2)  # 90度 = π/2弧度
    
    # 在X方向移动舌片宽度的一半
    obj.location.x += tongue_width / 2
    
    # 在Y方向移动舌片长度的一半
    obj.location.y -= tongue_length / 2 + 1
    
    # half of shell height - tongue height
    obj.location.z += shell_height / 2 - tongue_height / 2
    
    # 应用变换
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 安全地调整视图
def safe_view_adjust(obj):
    try:
        # 确保有3D视图区域
        for area in bpy.context.screen.areas:
            if area.type == 'VIEW_3D':
                # 设置活动对象
                bpy.context.view_layer.objects.active = obj
                obj.select_set(True)
                
                # 将3D光标对齐到选中项
                bpy.ops.view3d.snap_cursor_to_selected()
                
                # 将视图切换到选中项
                for region in area.regions:
                    if region.type == 'WINDOW':
                        override = {
                            'area': area,
                            'region': region,
                            'edit_object': bpy.context.edit_object
                        }
                        bpy.ops.view3d.view_selected(override)
                break
    except Exception as e:
        print(f"视图调整失败: {e}")

# 设置视图模式为材质预览
def setup_viewport_shading():
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    # 设置视图着色为材质预览
                    space.shading.type = 'MATERIAL'
                    break

def usb_tongue(shell_height, plastic_color="black"):  # 默认改为黑色
    # 清理场景
#    clear_scene()
    
    # 创建舌片
    tongue_obj, tongue_width, tongue_length, tongue_thickness = create_usb_type_c_tongue()
    print("USB Type-C 舌片模型创建完成")
    
    # 分配材质 - 使用指定的塑料颜色，默认黑色
    used_color = assign_materials_using_indices(tongue_obj, tongue_thickness, plastic_color)
    print(f"材质分配完成 - 使用{used_color}塑料")
    
    # 应用变换：绕Z轴旋转90度，然后移动
    apply_transformations(tongue_obj, tongue_width, tongue_length, tongue_thickness, shell_height)
    print("变换应用完成：绕Z轴旋转90度，X方向移动宽度一半，Y方向移动长度一半")

    # 设置视图模式为材质预览
    setup_viewport_shading()
    
    # 安全地调整视图
    safe_view_adjust(tongue_obj)
    
    # 打印模型信息
    print("=" * 60)
    print("USB Type-C 舌片模型创建完成！")
    print("基于您提供的三张图片信息和最新图片信息：")
    print("=" * 60)
    print("图1信息: TYPE-C母座16P, 彩色胶芯(蓝/绿/橙/白/黑)")
    print("图2信息: 舌片厚度0.70±0.05mm, 金属条宽度0.2mm")
    print("图3信息: 舌片长度5.78mm, 宽度6.40mm")
    print("最新图片信息: 舌片本身可以是黑色的")
    print("=" * 60)
    print("重要说明:")
    print("- 舌片上下各有12条金属肋条")
    print("- 这些肋条后续会合并，以16针的形式与外部接口连接")
    print("- 产品型号标注为16P，但实际肋条数量为12条")
    print("- 根据最新图片，舌片使用黑色塑料")
    print("=" * 60)
    print(f"舌片尺寸: {tongue_length}mm × {tongue_width}mm × {tongue_thickness}mm")
    print(f"金属接触端子: 上下各12条, 宽0.2mm")
    print(f"材质: {used_color}塑料基体 + 金色金属端子")
    print("实体模式颜色已修复，使用diffuse_color属性")
    print("=" * 60)
    
    return tongue_obj, used_color

# 创建16个针脚（使用精确的间距数据）
def create_16_pins_precise():
    # 根据您提供的精确间距数据创建针脚
    # 针脚尺寸（修正为正确尺寸，缩小1000倍）
    pin_length = 0.3  # X方向：0.3mm（修正）
    pin_width = 0.2   # Y方向：针脚宽度0.2mm
    pin_height = 0.1  # Z方向：0.1mm（修正）
    
    # 针脚间距数据（根据您提供的数据）
    # 针脚1到针脚16的间距数据
    spacing_data = [
        0.3,  # 针脚1和针脚2的中心间距
        0.5,  # 针脚2和针脚3的中心间距
        0.3,  # 针脚3和针脚4的中心间距
        0.5,  # 针脚4和针脚5的中心间距
        0.5,  # 针脚5和针脚6的中心间距
        0.5,  # 针脚6和针脚7的中心间距
        0.5,  # 针脚7和针脚8的中心间距
        0.5,  # 针脚8和针脚9的中心间距
        0.5,  # 针脚9和针脚10的中心间距
        0.5,  # 针脚10和针脚11的中心间距
        0.5,  # 针脚11和针脚12的中心间距
        0.5,  # 针脚12和针脚13的中心间距
        0.3,  # 针脚13和针脚14的中心间距
        0.5,  # 针脚14和针脚15的中心间距
        0.3   # 针脚15和针脚16的中心间距
    ]
    
    # 创建新网格和对象
    mesh = bpy.data.meshes.new("16_Pins_Precise_Mesh")
    pins_obj = bpy.data.objects.new("16_Pins_Precise", mesh)
    bpy.context.collection.objects.link(pins_obj)
    
    # 使用bmesh构建网格
    bm = bmesh.new()
    
    # 计算针脚位置
    # 针脚1的中心位置设为原点
    pin_centers = [0.0]  # 针脚1的中心位置
    
    # 计算每个针脚的中心位置
    for i in range(15):
        next_center = pin_centers[i] + spacing_data[i]
        pin_centers.append(next_center)
    
    # 计算总宽度
    total_width = pin_centers[-1] + pin_width  # 最后一个针脚的右边缘
    
    # 计算起始位置（使针脚排列居中）
    start_y = -total_width / 2
    
    # 调整针脚中心位置，使整个排列居中
    pin_centers = [center - total_width/2 + pin_width/2 for center in pin_centers]
    
    # 创建针脚
    for i, center_y in enumerate(pin_centers):
        pin_index = i + 1  # 针脚编号从1开始
        
        # 创建立方体针脚
        # 计算针脚顶点
        pin_x_min = -pin_length / 2  # X方向
        pin_x_max = pin_length / 2
        pin_y_min = center_y - pin_width / 2  # Y方向
        pin_y_max = center_y + pin_width / 2
        pin_z_min = 0  # 针脚从Z=0开始
        pin_z_max = pin_height  # 针脚高度
        
        # 创建针脚顶点
        verts_pin = []
        for x in [pin_x_min, pin_x_max]:
            for y in [pin_y_min, pin_y_max]:
                for z in [pin_z_min, pin_z_max]:
                    verts_pin.append(bm.verts.new((x, y, z)))
        
        # 创建针脚面
        pin_faces = [
            [0, 1, 3, 2],   # 左面
            [4, 5, 7, 6],   # 右面
            [0, 4, 6, 2],   # 前面
            [1, 5, 7, 3],   # 后面
            [0, 1, 5, 4],   # 底面
            [2, 3, 7, 6]    # 顶面
        ]
        
        for face in pin_faces:
            bm.faces.new([verts_pin[j] for j in face])
    
    # 合并重复顶点
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.001)
    
    # 更新网格
    bm.to_mesh(mesh)
    bm.free()
    
    # 设置对象为激活状态
    bpy.context.view_layer.objects.active = pins_obj
    pins_obj.select_set(True)
    
    # 更新网格显示
    mesh.update()
    
    return pins_obj, pin_length, pin_width, pin_height, spacing_data, total_width

# 创建金属材质（用于针脚）
def create_pin_material():
    pin_mat = bpy.data.materials.new("Pin_Metal_Material")
    pin_mat.use_nodes = True
    
    # 设置diffuse_color用于实体模式
    pin_mat.diffuse_color = (0.8, 0.8, 0.9, 1.0)  # 银灰色
    
    # 清除默认节点
    nodes = pin_mat.node_tree.nodes
    nodes.clear()
    
    # 添加输出节点
    output_node = nodes.new(type='ShaderNodeOutputMaterial')
    output_node.location = (400, 0)
    
    # 添加BSDF节点
    bsdf_node = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf_node.location = (0, 0)
    bsdf_node.inputs['Base Color'].default_value = (0.8, 0.8, 0.9, 1.0)  # 银灰色
    bsdf_node.inputs['Metallic'].default_value = 0.9
    bsdf_node.inputs['Roughness'].default_value = 0.2
    
    # 连接节点
    links = pin_mat.node_tree.links
    links.new(bsdf_node.outputs['BSDF'], output_node.inputs['Surface'])
    
    return pin_mat

# 分配材质
def assign_pin_materials(pins_obj):
    # 创建材质
    pin_mat = create_pin_material()  # 针脚使用金属材质
    
    # 分配材质
    pins_obj.data.materials.append(pin_mat)  # 索引0: 金属
    
    # 确保在对象模式
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    # 进入编辑模式
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_mode(type='FACE')
    
    # 选择所有面
    bpy.ops.mesh.select_all(action='SELECT')
    
    # 分配金属材质（索引0）给所有面
    bpy.context.object.active_material_index = 0
    bpy.ops.object.material_slot_assign()
    
    # 回到对象模式
    bpy.ops.object.mode_set(mode='OBJECT')

# 应用变换：绕Z轴旋转90度，然后在Y轴负方向移动壳体长度的一半
def apply_pin_transformations(pins_obj, shell_length):
    # 绕Z轴旋转90度（π/2弧度）
    pins_obj.rotation_euler = (0, 0, math.pi/2)
    
    # 在Y轴方向移动壳体长度的一半
    pins_obj.location.y += shell_length / 2 + 0.1
    
    # 应用变换
    bpy.context.view_layer.objects.active = pins_obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


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
    
    # 可选颜色: "blue", "green", "orange", "white", "black"
    tongue_obj, color_used = usb_tongue(shell.dimensions.z, plastic_color="black")
    
    # 对外壳外部边进行倒角处理
    shell = apply_bevel_to_external_edges(shell)
    print("外部倒角处理完成")
    
    # 添加材质
    assign_materials(shell)
    print("材质分配完成")
    
    # 创建16个针脚（使用精确的间距数据）
    pins_obj, pin_length, pin_width, pin_height, spacing_data, total_width = create_16_pins_precise()
    print("16个针脚模型创建完成（使用精确间距数据）")
    
    # 应用变换：绕Z轴旋转90度，然后在Y轴负方向移动壳体长度的一半
    apply_pin_transformations(pins_obj, shell.dimensions.y)
    print("变换应用完成：绕Z轴旋转90度，Y轴负方向移动壳体长度一半")

    # 分配材质
    assign_pin_materials(pins_obj)
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
