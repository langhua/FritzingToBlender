import bpy
import bmesh
from mathutils import Vector
import math
from ..utils.scene import clear_scene
from ..utils.material import create_material
from ..commons.rounded_rect import create_rounded_rectangle

# 创建基础USB Type-C母座外壳
def create_usb_type_c_shell():
    # 目标尺寸：XYZ轴尺寸 8.94mm x 3.16mm x 7.33mmm, radius = 3.16/2 - 0.7 = 0.88
    shell = create_rounded_rectangle(pin_number=1, width=8.94, height=3.16, depth=7.33, radius=0.88, rounded_corners="all")
    shell.name = "USB_TypeC_Female_Shell"
    
    # 按照壁厚建一个内腔模具，按壁厚0.15mm计算，内腔尺寸为8.64mm x 2.86mm x 6.2mm
    cavity = create_rounded_rectangle(pin_number=2, width=8.64, height=2.86, depth=6.3, radius=0.88, rounded_corners="all")
    cavity.name = "USB_TypeC_Female_Cavity"
    cavity.location.z -= 0.1

    # 布尔差值运算，挖出内腔
    bpy.ops.object.select_all(action='DESELECT')
    modifier = shell.modifiers.new(name="Boolean", type="BOOLEAN")
    modifier.operation = 'DIFFERENCE'
    modifier.object = cavity
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.modifier_apply(modifier=modifier.name)

    # 删除cavity
    bpy.data.objects.remove(cavity, do_unlink=True)
    
    # 调整位置和方向
    shell.rotation_euler.x = -math.radians(90)
    shell.location.y = -shell.dimensions.z/2
    
    return shell

# 创建USB Type-C舌片
def create_usb_type_c_tongue():
    # 设置USB Type-C舌片参数
    # 舌片厚度0.70±0.05mm, 金属条宽度0.2mm
    # 舌片长度5.78mm, 宽度5.50mm
    W_base = 6.69      # 舌片宽度
    T_base = 0.70      # 舌片厚度
    L_base = 4.45      # 舌片长度
    
    # 金属条参数 - 上下各12条
    num_metals = 12     # 每侧金属条数量（12条）
    metal_width = 0.25  # 金属条宽度
    metal_gap = 0.25    # 金属条间隔
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

# 创建塑料材质
def create_plastic_material(color="black"):
    if color == "blue":
        plastic_mat = create_material("Plastic_Material_" + color, (0.0, 0.5, 1.0, 1.0))
    elif color == "green":
        plastic_mat = create_material("Plastic_Material_" + color, (0.0, 0.8, 0.2, 1.0))
    elif color == "orange":
        plastic_mat = create_material("Plastic_Material_" + color, (1.0, 0.5, 0.0, 1.0))
    elif color == "white":
        plastic_mat = create_material("Plastic_Material_" + color, (0.9, 0.9, 0.9, 1.0))
    else:  # 默认黑色
        plastic_mat = create_material("Plastic_Material_" + color, (0.05, 0.05, 0.05, 1.0))
    
    return plastic_mat

# 分配材质
def assign_materials_using_indices(obj, tongue_thickness, plastic_color="black"):  # 默认改为黑色
    # 创建材质
    plastic_mat = create_plastic_material(plastic_color)  # 使用指定颜色，默认黑色
    metal_mat = create_material("Enhanced_Metal_Material", base_color=(0.95, 0.85, 0.35, 1.0), metallic=1.0, roughness=0.1)
    
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
    
    # 在Y方向移动舌片长度的一半，边缘距离外壳口0.6mm
    obj.location.y -= tongue_length / 2 + 0.85
    
    # half of shell height - tongue height
    obj.location.z += shell_height / 2 - tongue_height / 2
    
    # 应用变换
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

def create_16_pins_precise():
    # 针脚尺寸
    pin_length = 0.3  # X方向：0.3mm
    pin_width = 0.2   # Y方向：针脚宽度0.2mm
    pin_height = 0.1  # Z方向：0.1mm
    
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

def create_middle_feet():
    # 创建左侧脚
    left_middle_foot = create_rounded_rectangle(17, width=0.8, height=3.16/2 + 0.9 + 0.1, depth=0.15, radius=0.4, segments=8, rounded_corners="bottom")
    left_middle_foot.name = "Middle_Foot_Left"
    left_middle_foot.rotation_euler = (math.pi/2, 0, math.pi/2)
    left_middle_foot.location.z -= 1.24 + 0.05
    left_middle_foot.location.x -= 4.47
    left_middle_foot.location.y -= 7.33/2 - 2.6
    
    left_middle_foot2 = create_rounded_rectangle(18, width=0.5, height=3.16/2 + 0.1, depth=0.15, radius=0.15, segments=8, rounded_corners="bottom")
    left_middle_foot2.name = "Middle_Foot_Left2"
    left_middle_foot2.rotation_euler = (math.pi/2, 0, math.pi/2)
    left_middle_foot2.location.z -= 0.84
    left_middle_foot2.location.x -= 4.47
    left_middle_foot2.location.y -= 7.33/2 - 3.25
        
    # 创建右侧脚
    right_middle_foot = create_rounded_rectangle(17, width=0.8, height=3.16/2 + 0.9 + 0.1, depth=0.15, radius=0.4, segments=8, rounded_corners="bottom")
    right_middle_foot.name = "Middle_Foot_Right"
    right_middle_foot.rotation_euler = (math.pi/2, 0, math.pi/2)
    right_middle_foot.location.z -= 1.24 + 0.05
    right_middle_foot.location.x += 4.47 - 0.15
    right_middle_foot.location.y -= 7.33/2 - 2.6
    
    right_middle_foot2 = create_rounded_rectangle(18, width=0.5, height=3.16/2 + 0.1, depth=0.15, radius=0.15, segments=8, rounded_corners="bottom")
    right_middle_foot2.name = "Middle_Foot_Right2"
    right_middle_foot2.rotation_euler = (math.pi/2, 0, math.pi/2)
    right_middle_foot2.location.z -= 0.84
    right_middle_foot2.location.x += 4.47 - 0.15
    right_middle_foot2.location.y -= 7.33/2 - 3.25
        
    return (left_middle_foot, left_middle_foot2, right_middle_foot, right_middle_foot2)

def create_tail_feet():
    # 创建左尾脚
    left_tail_foot = create_rounded_rectangle(17, width=1.1, height=3.16/2 + 0.9 + 0.1, depth=0.15, radius=0.55, segments=8, rounded_corners="bottom")
    left_tail_foot.name = "Middle_Foot_Left"
    left_tail_foot.rotation_euler = (math.pi/2, 0, math.pi/2)
    left_tail_foot.location.z -= 1.24 + 0.05
    left_tail_foot.location.x -= 4.47
    left_tail_foot.location.y += 7.33/2 - 1.1/2
    
    # 创建右尾脚
    right_tail_foot = create_rounded_rectangle(17, width=1.1, height=3.16/2 + 0.9 + 0.1, depth=0.15, radius=0.55, segments=8, rounded_corners="bottom")
    right_tail_foot.name = "Middle_Foot_Right"
    right_tail_foot.rotation_euler = (math.pi/2, 0, math.pi/2)
    right_tail_foot.location.z -= 1.24 + 0.05
    right_tail_foot.location.x += 4.47 - 0.15
    right_tail_foot.location.y += 7.33/2 - 1.1/2
        
    return (left_tail_foot, right_tail_foot)

def create_plastic_pins():
    # 创建圆柱体
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=0.5/2,
        depth=0.75,
        location=(-5.78/2, 6.28 - 7.33/2, -3.16/2 - 0.75/2)
    )
    left_plastic_pin = bpy.context.active_object
    left_plastic_pin.name = "Plastic_Pin_Left"

    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=0.5/2,
        depth=0.75,
        location=(5.78/2, 6.28 - 7.33/2, -3.16/2 - 0.75/2)
    )
    right_plastic_pin = bpy.context.active_object
    right_plastic_pin.name = "Plastic_Pin_Right"

    return (left_plastic_pin, right_plastic_pin)


def create_usb_type_c_16pin_model(plastic_color="black"):
    # 1. 金属外壳
    # 1.1 壳体
    shell = create_usb_type_c_shell()
    
    # 1.2 中间固定脚
    middle_feet = create_middle_feet()

    # 1.3 尾部固定脚
    tail_feet = create_tail_feet()

    # 1.4 合并外壳和固定脚
    bpy.ops.object.select_all(action='DESELECT')
    shell.select_set(True)
    for obj in middle_feet:
        obj.select_set(True)
    for obj in tail_feet:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.join()

    # 1.4 为外壳添加材质
    shell.data.materials.clear()
    shell_mat = create_material("Shell_Metal", base_color=(0.7, 0.7, 0.75, 1.0), metallic=0.9, roughness=0.15)
    shell.data.materials.append(shell_mat)
    
    # 2. 舌头
    # 2.1创建舌片
    tongue_obj, tongue_width, tongue_length, tongue_thickness = create_usb_type_c_tongue()
    
    # 2.2 分配材质 - 使用指定的塑料颜色，默认黑色
    assign_materials_using_indices(tongue_obj, tongue_thickness, plastic_color)
    
    # 2.3 应用变换：绕Z轴旋转90度，然后移动
    apply_transformations(tongue_obj, tongue_width, tongue_length, tongue_thickness, 0)
    
    # 3. 16个针脚
    # 3.1 创建16个针脚（使用精确的间距数据）
    pins_obj, pin_length, pin_width, pin_height, spacing_data, total_width = create_16_pins_precise()
    
    # 3.2 应用变换：绕Z轴旋转90度，然后在Y轴负方向移动壳体长度的一半
    pins_obj.rotation_euler = (0, 0, math.pi/2)
    pins_obj.location.y += 7.33/2 + 0.1
    pins_obj.location.z -= 3.16/2 + pin_height

    # 3.3 分配材质
    pins_obj.data.materials.clear()
    pin_mat = create_material("Pin_Metal", base_color=(0.8, 0.8, 0.9, 1.0), metallic=0.9, roughness=0.2)
    pins_obj.data.materials.append(pin_mat)

    # 6. 塑料固定脚
    plastic_pins = create_plastic_pins()
    for pin in plastic_pins:
        pin.data.materials.clear()
        pin_mat = create_plastic_material(plastic_color)
        pin.data.materials.append(pin_mat)

    # 7. 合并
    bpy.ops.object.select_all(action='DESELECT')
    shell.select_set(True)
    pins_obj.select_set(True)
    tongue_obj.select_set(True)
    for pin in plastic_pins:
        pin.select_set(True)
    bpy.context.view_layer.objects.active = shell
    bpy.ops.object.join()
    shell.name = 'USB_TypeC_16pin'

    # 8. 调整位置
    shell.location.z = (3.16 + 0.9 + 0.1)/2 - 0.9 + 0.1
    shell.location.y = 0.4

    if shell.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(shell)
    bpy.context.collection.objects.link(shell)

    return shell

# 主函数
def main():
    # 确保在对象模式下开始
    if bpy.context.mode != 'OBJECT':
        bpy.ops.object.mode_set(mode='OBJECT')
    
    clear_scene()
    type_c_16pin_model = create_usb_type_c_16pin_model()
    
    # 打印模型信息
    print("=" * 60)
    print("USB Type-C母座模型创建完成")
    print(f"目标尺寸: 8.94mm × 7.58mm(7.33mm + 0.25mm) × 4.16mm(3.16mm + 0.1mm + 0.9mm)")
    print(f"实际尺寸: {type_c_16pin_model.dimensions.x:.2f}mm × {type_c_16pin_model.dimensions.y:.2f}mm × {type_c_16pin_model.dimensions.z:.2f}mm")
    print("=" * 60)
    
    # 检查并报告尺寸问题
    if abs(type_c_16pin_model.dimensions.x - 8.94) > 0.1:
        print(f"警告: X方向尺寸不匹配! 期望8.94mm，实际{type_c_16pin_model.dimensions.x:.2f}mm")
    else:
        print("✓ X方向尺寸正确")
    
    # 8.94mm是壳的长度，0.25mm是引脚露出的长度
    if abs(type_c_16pin_model.dimensions.y - 7.58) > 0.1:
        print(f"警告: Y方向尺寸不匹配! 期望7.58mm，实际{type_c_16pin_model.dimensions.y:.2f}mm")
    else:
        print("✓ Y方向尺寸正确")
        
    if abs(type_c_16pin_model.dimensions.z - 4.16) > 0.1:
        print(f"警告: Z方向尺寸不匹配! 期望4.16mm，实际{type_c_16pin_model.dimensions.z:.2f}mm")
    else:
        print("✓ Z方向尺寸正确")


# 运行脚本
if __name__ == "__main__":
    main()
