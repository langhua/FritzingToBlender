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

# 创建16个针脚（使用精确的间距数据）
def create_16_pins_precise():
    # 根据您提供的精确间距数据创建针脚
    # 针脚尺寸（修正为正确尺寸）
    pin_length = 0.3  # X方向：0.3mm
    pin_width = 0.2   # Y方向：针脚宽度0.2mm
    pin_height = 0.1  # Z方向：0.1mm
    
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
    
    # USB壳体尺寸
    shell_length = 16.0  # USB壳体长度16mm
    
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
    
    return pins_obj, pin_length, pin_width, pin_height, spacing_data, total_width, shell_length

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
def apply_transformations(pins_obj, shell_length):
    # 绕Z轴旋转90度（π/2弧度）
    pins_obj.rotation_euler = (0, 0, math.pi/2)
    
    # 在Y轴负方向移动壳体长度的一半
    pins_obj.location.y -= shell_length / 2
    
    # 应用变换
    bpy.context.view_layer.objects.active = pins_obj
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
def main():
    # 清理场景
    clear_scene()
    
    # 创建16个针脚（使用精确的间距数据）
    pins_obj, pin_length, pin_width, pin_height, spacing_data, total_width, shell_length = create_16_pins_precise()
    print("16个针脚模型创建完成（使用精确间距数据）")
    
    # 分配材质
    assign_pin_materials(pins_obj)
    print("材质分配完成")
    
    # 应用变换：绕Z轴旋转90度，然后在Y轴负方向移动壳体长度的一半
    apply_transformations(pins_obj, shell_length)
    print("变换应用完成：绕Z轴旋转90度，Y轴负方向移动壳体长度一半")
    
    # 设置视图模式为材质预览
    setup_viewport_shading()
    
    # 安全地调整视图
    safe_view_adjust(pins_obj)
    
    # 打印模型信息
    print("=" * 60)
    print("16针脚模型创建完成！")
    print("基于您提供的精确针脚宽度和间距数据：")
    print("=" * 60)
    print("针脚尺寸：")
    print(f"- 长度 (X): {pin_length}mm")
    print(f"- 宽度 (Y): {pin_width}mm")
    print(f"- 高度 (Z): {pin_height}mm")
    print("=" * 60)
    print("针脚间距数据（中心到中心）：")
    for i, spacing in enumerate(spacing_data):
        print(f"- 针脚{i+1}和针脚{i+2}的中心间距: {spacing}mm")
    print("=" * 60)
    print("总体宽度：")
    print(f"- 计算总宽度: {total_width:.2f}mm")
    print("=" * 60)
    print("变换应用：")
    print(f"- 绕Z轴旋转90度")
    print(f"- 在Y轴负方向移动壳体长度的一半: {shell_length/2}mm")
    print("=" * 60)
    print("针脚排列：")
    print("- 16个针脚按照精确的间距数据排列")
    print("- 每个针脚宽度为0.2mm")
    print("- 针脚排列已居中")
    print("=" * 60)
    print("材质：")
    print("- 针脚: 银灰色金属")
    print("=" * 60)
    print("修正说明：")
    print("1. 尺寸修正：")
    print("   - 所有尺寸已修正为实际尺寸")
    print("2. 间距使用精确数据：")
    print("   - 按照您提供的15个间距数据精确排列")
    print("   - 每个针脚宽度为0.2mm")
    print("3. 变换应用：")
    print("   - 绕Z轴旋转90度")
    print("   - 在Y轴负方向移动壳体长度的一半")
    print("4. 针脚排列：")
    print("   - 16个立方体针脚精确排列")
    print("   - 总体宽度自动计算")
    print("=" * 60)
    
    return pins_obj

# 运行脚本
if __name__ == "__main__":
    pins_obj = main()