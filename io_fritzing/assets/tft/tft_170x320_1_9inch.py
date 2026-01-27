import bpy
import bmesh
from mathutils import Vector
import math
from ..utils.scene import clear_scene
from ..utils.material import create_material
from ..commons.rounded_rect import create_rounded_rectangle
from ..resistors.smd_resistors import generate_smd_resistor, SMD_SIZES
from ..sot.sot23_3 import create_sot23_3_model
from ..capacitors.smd_capacitor import create_smd_capacitor_model

# 创建4层TFT结构
def create_tft_layers():
    # PCB板实际尺寸：长61.90mm，宽29.00mm，厚1.20mm
    # 长边57.90mm是两个安装孔中心距离，每个孔中心距离边缘2mm
    pcb_length = 0.0619  # 57.90 + 2×2 = 61.90mm，转换为米
    pcb_width = 0.029  # 29.00mm，转换为米
    pcb_thickness = 0.0012  # 1.20mm，转换为米
    
    # 第4层：屏幕排线插座 (2mm高)
    socket_height = 0.002  # 2mm
    socket_width = 0.0155  # 插座宽度为(n + 1) * 0.5mm, n为排线线数, 这里n=30
    socket_depth = 0.006   # 深度6mm
    
    bpy.ops.mesh.primitive_cube_add(size=1)
    socket = bpy.context.object
    socket.name = "FPC_Socket"
    socket.scale = (socket_depth, socket_width, socket_height)
    
    # 插座底部z=0
    socket_x = 0.03909 - pcb_length / 2  # 导线槽距PCB板边（4.89mm） + 导线槽宽度（1.2mm） + 宽排线长（30mm） + 排线插座宽度的一半（3mm） = 39.09
    socket.location = (socket_x, 0, socket_height/2)
    
    # 插座材质（白色）
    mat_socket = create_material(name="Socket_Material", base_color=(0.85, 0.85, 0.85, 1.0), metallic=0.3, roughness=0.7)
    socket.data.materials.append(mat_socket)
    
    # 第3层：PCB板
    pcb = create_rounded_rectangle(pin_number=1, width=pcb_length, height=pcb_width, depth=pcb_thickness, radius=0.0015, segments=8, rounded_corners="all")
    pcb.name = "PCB_Board"
    pcb.location = (0, 0, socket_height)  # 放置在插座顶部
    
    # PCB材质（蓝色）
    mat_pcb = create_material(name="PCB_Material", base_color=(0, 0.141, 0.357, 0.99), metallic=0.1, roughness=0.8)
    pcb.data.materials.append(mat_pcb)
    
    # 第2层：背胶层 (厚度假设为0.1mm)
    adhesive_thickness = 0.0002  # 0.2mm
    adhesive_length = 0.04972    # 49.72mm
    adhesive_width = 0.0237
    
    bpy.ops.mesh.primitive_cube_add(size=1)
    adhesive = bpy.context.object
    adhesive.name = "Adhesive_Layer"
    adhesive.scale = (adhesive_length, adhesive_width, adhesive_thickness)
    adhesive_x = (pcb_length - adhesive_length)/2 - 0.00614 - 0.0002
    adhesive.location = (adhesive_x, 0, socket_height + pcb_thickness + adhesive_thickness/2)
    
    # 背胶材质（白色）
    mat_adhesive = create_material(name="Adhesive_Material", base_color=(0.95, 0.95, 0.95, 1.0), roughness=0.8)
    adhesive.data.materials.append(mat_adhesive)
    
    # 屏幕层 (厚度1.43mm ± 0.1mm)
    # 第3层：玻璃底板
    glass_thickness = 0.00093  # 1.43mm - 0.2 - 0.3
    glass_length = 0.04972     # 49.72mm
    glass_width = 0.0237       # 23.7mm
    bpy.ops.mesh.primitive_cube_add(size=1)
    glass = bpy.context.object
    glass.name = "Glass_Backplate"
    glass.scale = (glass_length, glass_width, glass_thickness)
    glass.location = (adhesive_x, 0, socket_height + pcb_thickness + adhesive_thickness + glass_thickness/2)

    
    # 第2层：Visible Area层，可见层
    va_thickness = 0.0003      # 0.3mm
    va_length = 0.04372        # 43.72mm
    va_width = glass_width     # 23.7mm
    bpy.ops.mesh.primitive_cube_add(size=1)
    va = bpy.context.object
    va.name = "Visible_Area_Layer"
    va.scale = (va_length, va_width, va_thickness)
    va_x = (pcb_length - va_length)/2 - 0.00614 - 0.0002
    va.location = (va_x, 0, glass.location.z + glass_thickness/2 + va_thickness/2)

    # 第1层：Active Area层，可操作层
    aa_thickness = 0.0002      # 0.2mm
    aa_length = 0.04272        # 42.72mm
    aa_width = 0.0227          # 22.7mm
    bpy.ops.mesh.primitive_cube_add(size=1)
    aa = bpy.context.object
    aa.name = "Active_Area_Layer"
    aa.scale = (aa_length, aa_width, aa_thickness)
    aa_x = (pcb_length - aa_length)/2 - 0.00614 - 0.0007
    aa.location = (aa_x, 0, va.location.z + va_thickness/2 + aa_thickness/2)

    # 屏幕材质（黑色）
    mat_screen = create_material(name="Screen_Material", base_color=(0.02, 0.02, 0.02, 0.99), roughness=0.2)
    aa.data.materials.append(mat_screen)
    va.data.materials.append(mat_screen)

    mat_glass = create_material(name="Glass_Material", base_color=(0.02, 0.02, 0.02, 1.0), roughness=0.8)
    glass.data.materials.append(mat_glass)

    return socket, pcb, adhesive, glass, va, aa

# 创建Screen Border（矩形边框）
def create_screen_border(glass):
    # 边框尺寸：比屏幕稍大，高度等于屏幕厚度+背胶厚度
    border_length = glass.dimensions.x + 0.0001 * 2  # 比屏幕每边宽0.5mm
    border_width = glass.dimensions.y + 0.0001 * 2
    border_height = glass.dimensions.z  # 高度等于屏幕厚度
    
    # 创建外边框（简单立方体边框）
    bpy.ops.mesh.primitive_cube_add(size=1)
    border = bpy.context.object
    border.name = "Screen_Border"
    
    # 设置边框尺寸和位置
    border.scale = (border_length, border_width, border_height - 0.0001)
    border.location = (glass.location.x, glass.location.y, glass.location.z - 0.00005)
    
    # 边框材质（白色）
    mat_border = create_material(name = "Border_Material", base_color = (0.99, 0.99, 0.99, 1.0), roughness = 0.8, metallic = 0.0, alpha = 0.8)
    border.data.materials.append(mat_border)
    
    return border

# 在PCB四个角创建4个安装孔
def create_mounting_holes_and_pads(pcb_length, pcb_width, pcb_thickness, socket_height):
    # 安装孔参数
    hole_diameter = 0.002  # 2mm直径的安装孔
    hole_radius = hole_diameter / 2
    
    # 安装孔中心到PCB边缘的距离
    edge_distance_x = 0.002  # 2mm
    edge_distance_y = 0.0016 # 1.6mm
    
    # 计算四个角的位置
    # 左上角
    hole1_x = -pcb_length/2 + edge_distance_x
    hole1_y = pcb_width/2 - edge_distance_y
    
    # 右上角
    hole2_x = pcb_length/2 - edge_distance_x
    hole2_y = pcb_width/2 - edge_distance_y
    
    # 左下角
    hole3_x = -pcb_length/2 + edge_distance_x
    hole3_y = -pcb_width/2 + edge_distance_y
    
    # 右下角
    hole4_x = pcb_length/2 - edge_distance_x
    hole4_y = -pcb_width/2 + edge_distance_y
    
    # 焊盘厚度
    pad_thickness = 0.0002  # 0.2mm

    holes = []
    pads = []
    
    positions = [(hole1_x, hole1_y), (hole2_x, hole2_y), (hole3_x, hole3_y), (hole4_x, hole4_y)]
    
    for i, (x, y) in enumerate(positions):
        # 创建通孔（圆柱体表示孔洞）
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=hole_radius, depth=pcb_thickness + 0.0002)
        hole = bpy.context.object
        hole.name = f"Mounting_Hole_{i+1}"
        hole.location = (x, y, socket_height + pcb_thickness/2)
        
        # 孔材质（内部银色）
        mat_hole = create_material(name=f"Mounting_Hole_Material", base_color=(0.9, 0.9, 0.9, 1.0), roughness=0.6, metallic=0.8)
        hole.data.materials.append(mat_hole)
        holes.append(hole)

        # 圆形焊盘（比孔稍大）
        pad_diameter = hole_diameter * 1.1
        pad_radius = pad_diameter / 2
        
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=pad_radius, depth=pcb_thickness + pad_thickness)
        pad = bpy.context.object
        pad.name = f"Mounting_Pad_{i+1}"
        pad.location = (x, y, socket_height + pcb_thickness/2)
        
        # 圆形焊盘材质（银色）
        mat_pad = create_material(name=f"Pad_Material_Circle", base_color=(0.9, 0.9, 0.9, 1.0), metallic=0.9, roughness=0.5)
        pad.data.materials.append(mat_pad)
    
        pads.append(pad)
    
    return holes, pads

# 在PCB短边创建8个电气连接孔和焊盘
def create_connection_holes_and_pads(pcb_length, pcb_width, pcb_thickness, socket_height):
    # 8个孔，间距2.54mm
    hole_count = 8
    hole_spacing = 0.00254  # 2.54mm
    
    # 计算总宽度
    total_width = (hole_count - 1) * hole_spacing
    
    # 起始位置（居中放置）
    start_y = total_width / 2
    
    # x位置：在PCB短边上，距离边缘1.5mm
    x_pos = pcb_length/2 - 0.0015
    
    holes = []
    pads = []
    text_objs = []
    
    # 孔直径（通孔直径）
    hole_diameter = 0.0009  # 0.9mm
    hole_radius = hole_diameter / 2
    
    # 焊盘厚度
    pad_thickness = 0.0002  # 0.2mm
    
    texts = ['GND', 'VCC', 'SCL', 'SDA', 'RES', 'DC', 'CS', 'BLK']
    mat_pad = create_material("Pad_Material_Square", (0.9, 0.9, 0.9, 1.0), metallic=0.9, roughness=0.5)
    mat_text = create_material(name="Text_White", base_color=(0.9, 0.9, 0.9, 1.0))
    for i in range(hole_count):
        y_pos = start_y - i * hole_spacing
        
        # 创建通孔（圆柱体表示孔洞）
        bpy.ops.mesh.primitive_cylinder_add(vertices=16, radius=hole_radius, depth=pcb_thickness + 0.0002)
        hole = bpy.context.object
        hole.name = f"Connection_Hole_{i+1}"
        hole.location = (x_pos, y_pos, socket_height + pcb_thickness/2)
        holes.append(hole)
        
        # 创建焊盘（在PCB顶部）
        # 第一个焊盘是正方形，其它是圆形
        if i == 0:  # 第一个是正方形焊盘（GND）
            # 正方形焊盘
            bpy.ops.mesh.primitive_cube_add(size=1)
            pad = bpy.context.object
            pad.name = f"Pad_GND_Square"
            pad.scale = (hole_diameter * 2, hole_diameter * 2, pcb_thickness + pad_thickness)
            pad.location = (x_pos, y_pos, socket_height + pcb_thickness/2)
            
            # 正方形焊盘材质（银色）
            pad.data.materials.append(mat_pad)

        else:  # 其它是圆形焊盘
            # 圆形焊盘（比孔稍大）
            pad_diameter = hole_diameter * 1.5
            pad_radius = pad_diameter / 2
            
            bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=pad_radius, depth=pcb_thickness + pad_thickness)
            pad = bpy.context.object
            pad.name = f"Pad_{i+1}_Circle"
            pad.location = (x_pos, y_pos, socket_height + pcb_thickness/2)
            
            # 圆形焊盘材质（银色）
            pad.data.materials.append(mat_pad)

        pads.append(pad)

        # 创建文本标签
        # 在PCB顶部添加文字标记
        text_location = (x_pos - hole_diameter - 0.001 , y_pos, socket_height + pcb_thickness + 0.0001)
        
        # 创建文本对象
        bpy.ops.object.text_add(location=text_location, rotation=(0, 0, -math.pi/2))
        text_obj = bpy.context.active_object
        text_obj.name = texts[i] + "_Text_Top"
        
        # 设置文本内容
        text_obj.data.body = texts[i]
        
        # 设置文本大小
        text_obj.data.size = 0.0015
        text_obj.data.align_x = 'CENTER'
        text_obj.data.align_y = 'CENTER'
        
        # 转换为网格
        bpy.ops.object.convert(target='MESH')
        
        # 缩放文本以适应主体
        text_obj.scale = (0.6, 0.6, 0.1)
        bpy.ops.object.transform_apply(scale=True)
        
        # 设置文本材质
        text_obj.data.materials.clear()
        text_obj.data.materials.append(mat_text)

        text_objs.append(text_obj)
    
        # 在PCB底部添加文字标记
        text_location = (x_pos - hole_diameter - 0.001 , y_pos, socket_height - 0.0001)
        
        # 创建文本对象
        bpy.ops.object.text_add(location=text_location, rotation=(0, 0, -math.pi/2))
        text_obj = bpy.context.active_object
        text_obj.name = texts[i] + "_Text_Bottom"
        
        # 设置文本内容
        text_obj.data.body = texts[i]
        
        # 设置文本大小
        text_obj.data.size = 0.0015
        text_obj.data.align_x = 'CENTER'
        text_obj.data.align_y = 'CENTER'
        
        # 转换为网格
        bpy.ops.object.convert(target='MESH')
        
        # 缩放文本以适应主体
        text_obj.scale = (0.6, 0.6, 0.1)
        bpy.ops.object.transform_apply(scale=True)
        
        # 设置文本材质
        text_obj.data.materials.clear()
        text_obj.data.materials.append(mat_text)

        text_objs.append(text_obj)

    return holes, pads, text_objs

# 创建基本电路元件（在PCB下面）
def create_components(pcb_length, socket_height):
    components = []
    
    # 创建几个电阻（在PCB下面）
    resistor_values = [51000.0, 10000.0, 2200.0, 5.1]
    x = pcb_length/2 - 0.0115
    resistor_positions = [
        (x, -0.0097),
        (x, -0.0065),
        (x, -0.0049),
        (x, 0.000)
    ]
    
    for i, (x, y) in enumerate(resistor_positions):
        resistor_collection = generate_smd_resistor(resistor_values[i], '5%', '0603')
        resistor = resistor_collection.objects[0]
        bpy.ops.object.select_all(action='DESELECT')
        for obj in resistor_collection.objects:
            obj.select_set(True)
        if bpy.context:
            bpy.context.view_layer.objects.active = resistor
        bpy.ops.object.join()

        resistor.scale.x *= 0.001
        resistor.scale.y *= 0.001
        resistor.scale.z *= 0.001
        resistor.location = (x, y, socket_height)
        resistor.rotation_euler = (math.pi, 0, 0)

        components.append(resistor)
        bpy.context.collection.objects.link(resistor)
        bpy.data.collections.remove(resistor_collection)
    
    # 创建电容（在PCB下面）
    capacitor_positions = [
        (x, -0.0081),
        (x, 0.0016),
        (x, 0.0032),
        (x, 0.0080),
        (x, 0.0096)
    ]
    
    for i, (x, y) in enumerate(capacitor_positions):
        capacitor = create_smd_capacitor_model('0603')
        capacitor.name = f"Capacitor_C{i+1}"
        capacitor.scale.x *= 0.001
        capacitor.scale.y *= 0.001
        capacitor.scale.z *= 0.001
        capacitor.location = (x, y, socket_height)
        capacitor.rotation_euler = (math.pi, 0, 0)
        components.append(capacitor)

    sot233_positions = [
        (x, -0.0025),
        (x, 0.0056),
    ]
    sot233_texts = [
        "Y1",
        "662K",
    ]

    for i, (x, y) in enumerate(sot233_positions):
        sot233 = create_sot23_3_model(text=sot233_texts[i])
        sot233.scale.x *= 0.001
        sot233.scale.y *= 0.001
        sot233.scale.z *= 0.001
        sot233.location = (x, y, socket_height)
        sot233.rotation_euler = (math.pi, 0, math.pi/2)
        components.append(sot233)
    
    return components

# 设置场景灯光和相机
def setup_scene():
    # 清除默认灯光
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.context.scene.objects:
        if obj.type == 'LIGHT':
            obj.select_set(True)
    bpy.ops.object.delete()
    
    # 创建主光
    bpy.ops.object.light_add(type='SUN')
    sun = bpy.context.object
    sun.location = (0.2, -0.2, 0.3)
    sun.rotation_euler = (math.radians(45), 0, math.radians(-30))
    sun.data.energy = 3
    
    # 创建补光灯
    bpy.ops.object.light_add(type='AREA')
    fill_light = bpy.context.object
    fill_light.location = (-0.1, 0.15, 0.2)
    fill_light.data.energy = 150
    fill_light.data.size = 0.1
    
    # 创建背光
    bpy.ops.object.light_add(type='AREA')
    back_light = bpy.context.object
    back_light.location = (0, -0.3, 0.1)
    back_light.data.energy = 80
    back_light.data.size = 0.15
    
    # 创建相机 - 从侧面视角，可以看到分层结构
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.location = (0.05, -0.08, 0.02)
    camera.rotation_euler = (math.radians(75), 0, math.radians(35))
    
    # 设置活动相机
    bpy.context.scene.camera = camera
    
    # 设置渲染引擎为Cycles
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 256
    
    # 创建背景平面
    bpy.ops.mesh.primitive_plane_add(size=0.2)
    plane = bpy.context.object
    plane.name = "Background"
    plane.location = (0, 0, -0.02)
    
    # 平面材质（浅灰色）
    mat_plane = create_material(name="Background_Material", base_color=(0.85, 0.85, 0.85, 1.0), roughness=0.9)
    plane.data.materials.append(mat_plane)
    
    return camera, plane

def create_cable_tracks(pcb_length, pcb_thickness, socket_height):
    """创建排线槽"""
    tracks = []
    
    # 定义排线槽参数
    track_height = pcb_thickness + 0.0002
    track_width = 0.0012   # 1.2mm宽
    track_length = 0.02    # 20mm
    
    # 计算排线槽数量
    num_tracks = 2
    x = -pcb_length/2 + 0.00489 + track_width/2
    
    # 创建两个圆柱
    # 计算位置
    y = (track_length - track_width)/2
    z = socket_height + track_height/2

    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=track_width/2, depth=track_height)
    track = bpy.context.object
    track.name = f"Cable_Track_1"
    track.location = (x, y, z)
    # 应用缩放
    bpy.ops.object.transform_apply(scale=True)

    tracks.append(track)

    # 计算位置
    y = -(track_length - track_width)/2

    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=track_width/2, depth=track_height)
    track = bpy.context.object
    track.name = f"Cable_Track_2"
    track.location = (x, y, z)
    # 应用缩放
    bpy.ops.object.transform_apply(scale=True)

    tracks.append(track)

    bpy.ops.mesh.primitive_cube_add(size=1)
    track = bpy.context.object
    track.name = f"Cable_Track_3"
    track.scale = (track_width, track_length - track_width, track_height)
    track.location = (x, 0, z)
    # 应用缩放
    bpy.ops.object.transform_apply(scale=True)

    tracks.append(track)

    return tracks


def create_tft_170x320_1_9inch_model():
    """创建1.9英寸TFT显示屏3D模型（4层结构）"""
    # 创建4层TFT结构
    print("创建4层TFT结构...")
    socket, pcb, adhesive, glass, va, aa = create_tft_layers()
    
    # 创建屏幕边框
    print("创建Screen_Border（白色边框）...")
    border = create_screen_border(glass)
    
    # 获取PCB尺寸
    pcb_length = 0.0619  # 61.90mm
    pcb_width = 0.029    # 29.00mm
    pcb_thickness = 0.0012
    socket_height = 0.002
    
    # 在PCB四个角创建4个安装孔
    print("创建4个安装孔在PCB四个角...")
    mounting_holes, mounting_pads = create_mounting_holes_and_pads(pcb_length, pcb_width, pcb_thickness, socket_height)
    i = 0
    for hole in mounting_holes:
        bpy.ops.object.select_all(action='DESELECT')
        hole_mod = pcb.modifiers.new(type='BOOLEAN', name=hole.name)
        hole_mod.object = hole
        hole_mod.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = pcb
        bpy.ops.object.modifier_apply(modifier=hole_mod.name)

        bpy.ops.object.select_all(action='DESELECT')
        pad_mod = mounting_pads[i].modifiers.new(type='BOOLEAN', name=mounting_pads[i].name)
        pad_mod.object = hole
        pad_mod.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = mounting_pads[i]
        bpy.ops.object.modifier_apply(modifier=pad_mod.name)
        i += 1
    
        bpy.data.objects.remove(hole, do_unlink=True)
        
    # 在PCB短边创建8个电气连接孔和焊盘
    print("创建8个电气连接孔和焊盘（1个正方形+7个圆形）...")
    connection_holes, pads, text_objs = create_connection_holes_and_pads(pcb_length, pcb_width, pcb_thickness, socket_height)
    i = 0
    for hole in connection_holes:
        bpy.ops.object.select_all(action='DESELECT')
        hole_mod = pcb.modifiers.new(type='BOOLEAN', name=hole.name)
        hole_mod.object = hole
        hole_mod.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = pcb
        bpy.ops.object.modifier_apply(modifier=hole_mod.name)

        bpy.ops.object.select_all(action='DESELECT')
        pad_mod = pads[i].modifiers.new(type='BOOLEAN', name=pads[i].name)
        pad_mod.object = hole
        pad_mod.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = pads[i]
        bpy.ops.object.modifier_apply(modifier=pad_mod.name)
        i += 1
    
        bpy.data.objects.remove(hole, do_unlink=True)

    # 创建排线槽
    print("创建排线槽...")
    tracks = create_cable_tracks(pcb_length, pcb_thickness, socket_height)
    for track in tracks:
        bpy.ops.object.select_all(action='DESELECT')
        track_mod = pcb.modifiers.new(type='BOOLEAN', name=track.name)
        track_mod.object = track
        track_mod.operation = 'DIFFERENCE'
        bpy.context.view_layer.objects.active = pcb
        bpy.ops.object.modifier_apply(modifier=track_mod.name)
        bpy.data.objects.remove(track, do_unlink=True)
    
    # 创建基本电路元件（在PCB下面）
    print("创建电路元件（在PCB下面）...")
    components = create_components(pcb_length, socket_height)

    all_objects = [socket, pcb, adhesive, glass, border, va, aa] + mounting_pads + pads + text_objs + components
    bpy.ops.object.select_all(action='DESELECT')
    for obj in all_objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = pcb
    bpy.ops.object.join()
    pcb.name = "TFT_170x320_1.9inch"

    if pcb.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(pcb)
    bpy.context.collection.objects.link(pcb)

    return pcb

# 主函数
def main():
    print("开始创建1.9英寸TFT显示屏3D模型（4层结构）...")
    print("修正内容：")
    print("1. 根据图片修正PCB尺寸：61.90mm × 29.00mm")
    print("2. 添加4个安装孔在PCB四个角")
    print("3. 8个电气连接孔在PCB短边")
    print("4. 电阻等元件放置在PCB下面")
    print("5. 背胶白色，屏幕黑色，Screen_Border白色")
    
    try:
        # 清除场景
        clear_scene()
        
        # 创建屏幕
        screen = create_tft_170x320_1_9inch_model()
        
        # 设置场景
        print("设置场景...")
        camera, background = setup_scene()
        
        # 将所有对象组织到集合中
        display_collection = bpy.data.collections.new("1.9_Inch_TFT")
        bpy.context.scene.collection.children.link(display_collection)
        
        # 获取所有对象
        all_objects = screen, camera, background
        
        for obj in all_objects:
            # 将对象从当前集合移除（如果存在）
            for col in obj.users_collection:
                col.objects.unlink(obj)
            # 添加到新集合
            display_collection.objects.link(obj)
        
        print("\n" + "=" * 60)
        print("1.9英寸TFT显示屏3D模型（4层结构）创建完成！")
        print("=" * 60)
        print("\n模型结构详情:")
        print("1. 屏幕排线插座 (第4层): 高度 2.0mm")
        print("2. PCB板 (第3层): 厚度 1.2mm，尺寸 61.90mm × 29.00mm")
        print("3. 背胶层 (第2层): 厚度 0.1mm (白色)")
        print("4. TFT屏幕 (第1层): 厚度 1.43mm (黑色)")
        print("5. Screen_Border: 白色边框，高度=1.43+0.1=1.53mm")
        print("\n安装孔布局:")
        print("- 4个安装孔在PCB四个角，直径2mm")
        print("- 安装孔中心距离PCB边缘2mm")
        print("- 长边安装孔中心距离57.90mm")
        print("\n电气连接孔布局:")
        print("- 8个连接孔，间距2.54mm，位于PCB短边")
        print("- 1个正方形焊盘 (GND) + 7个圆形焊盘")
        print("\n元件位置:")
        print("- 所有电阻、电容、芯片都在PCB下面")
        print("\n总对象数:", len(all_objects))
        print("=" * 60)
        
    except Exception as e:
        print(f"创建模型时发生错误: {e}")
        print("错误类型:", type(e).__name__)
        import traceback
        traceback.print_exc()

# 执行主函数
if __name__ == "__main__":
    main()