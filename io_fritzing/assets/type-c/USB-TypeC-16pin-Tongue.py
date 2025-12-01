import bpy
import bmesh
from mathutils import Vector
import math

# 清理场景函数
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
def apply_transformations(obj, tongue_width, tongue_length):
    # 绕Z轴旋转90度
    obj.rotation_euler = (0, 0, math.pi/2)  # 90度 = π/2弧度
    
    # 在X方向移动舌片宽度的一半
    obj.location.x += tongue_width / 2
    
    # 在Y方向移动舌片长度的一半
    obj.location.y += tongue_length / 2
    
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

# 主函数
def main(plastic_color="black"):  # 默认改为黑色
    # 清理场景
    clear_scene()
    
    # 创建舌片
    tongue_obj, tongue_width, tongue_length, tongue_thickness = create_usb_type_c_tongue()
    print("USB Type-C 舌片模型创建完成")
    
    # 分配材质 - 使用指定的塑料颜色，默认黑色
    used_color = assign_materials_using_indices(tongue_obj, tongue_thickness, plastic_color)
    print(f"材质分配完成 - 使用{used_color}塑料")
    
    # 应用变换：绕Z轴旋转90度，然后移动
    apply_transformations(tongue_obj, tongue_width, tongue_length)
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
    print("- 舌片已绕Z轴旋转90度")
    print("- 舌片已在X方向移动宽度一半，在Y方向移动长度一半")
    print("=" * 60)
    print(f"舌片尺寸: {tongue_length}mm × {tongue_width}mm × {tongue_thickness}mm")
    print(f"金属接触端子: 上下各12条, 宽0.2mm")
    print(f"材质: {used_color}塑料基体 + 金色金属端子")
    print("实体模式颜色已修复，使用diffuse_color属性")
    print("=" * 60)
    
    return tongue_obj, used_color

# 运行脚本
if __name__ == "__main__":
    # 默认使用黑色塑料，符合您提供的图片
    # 可选颜色: "blue", "green", "orange", "white", "black"
    tongue_obj, color_used = main(plastic_color="black")
