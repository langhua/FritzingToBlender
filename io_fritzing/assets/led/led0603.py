import bpy
import math
import bmesh
from mathutils import Vector, Matrix
from io_fritzing.assets.utils.material import create_material

def clear_scene():
    # 清除默认场景
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # 设置单位为毫米
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001

def create_led_with_color(color_name, color_rgb = None):
    """创建指定颜色的0603 LED"""
    
    # 根据颜色名称修改集合名称
    led_collection = bpy.data.collections.new(f"0603_{color_name}_LED")
    bpy.context.scene.collection.children.link(led_collection)
    
    def add_to_collection(obj):
        if obj.name not in led_collection.objects:
            led_collection.objects.link(obj)
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
    
    # 根据设计图设置精确尺寸
    # 主体（body）：白色塑料外壳
    body_length = 1.6
    body_width = 0.8
    body_height = 0.18  # 修正：高度是0.18mm
    
    # 电极：左右两侧
    electrode_length = 0.8
    electrode_width = 0.2
    electrode_height = 0.18
    
    # 梯形透镜尺寸
    lens = 1.0
    lens_bottom_length = 1.2
    lens_top_length = 1.0
    lens_width = 0.8
    lens_height = 0.37
    
    # 发光芯片尺寸
    chip_length = 0.55
    chip_width = 0.18
    chip_height = 0.3
    
    # 支撑结构尺寸
    support_length = 0.9
    support_width = 0.6
    support_height = 0.2
    
    # 颜色定义
    color_map = {
        'blue': (0.1, 0.1, 1.0),       # 蓝色
        'orange': (1.0, 0.5, 0.0),    # 橙色
        'red': (1.0, 0.1, 0.1),       # 红色
        'yellow': (1.0, 1.0, 0.0),    # 黄色
        'green': (0.1, 1.0, 0.1),     # 绿色
        'white': (1.0, 1.0, 1.0),     # 白色
        'emerald-green': (0.1, 0.8, 0.1),  # 翠绿色
        'yellow-green': (0.8, 1.0, 0.1),   # 黄绿色
    }
    
    # 获取当前颜色
    if color_rgb is not None:
        led_color = color_map.get(color_name, color_rgb)
    else:
        led_color = color_map.get(color_name, (1.0, 0.1, 0.1))
        
    # 使用更亮的颜色作为发光色
    emission_color = tuple(min(c + 0.3, 1.0) for c in led_color)
    
    # ============================================
    # 1. 创建LED主体
    # ============================================
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    body = bpy.context.active_object
    body.name = f"LED_Body_{color_name}"
    body.dimensions = (body_length, body_width, body_height)
    body.location = (0, 0, body_height/2)
    
    add_to_collection(body)
    
    # 主体材质
    body_mat = create_material(f"Body_Mat_{color_name}", (0.95, 0.95, 0.95), roughness=0.8)
    body_mat.diffuse_color = (0.95, 0.95, 0.95, 1)
    body.data.materials.append(body_mat)
    
    bpy.ops.object.transform_apply(scale=True)
    
    # ============================================
    # 2. 创建电极
    # ============================================
    electrode_mat = create_material(f"Electrode_Mat_{color_name}", (0.8, 0.8, 0.8), metallic=0.9, roughness=0.2)
    electrode_mat.diffuse_color = (0.8, 0.8, 0.8, 1)
    # 左侧电极
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    left_electrode = bpy.context.active_object
    left_electrode.name = f"Left_Electrode_{color_name}"
    left_electrode.dimensions = (electrode_height, electrode_length, electrode_width)
    left_electrode.location = (-body_length/2 + electrode_height/2, 0, body_height/2)
    left_electrode.data.materials.append(electrode_mat)
    add_to_collection(left_electrode)
    
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    
    # 右侧电极
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    right_electrode = bpy.context.active_object
    right_electrode.name = f"Right_Electrode_{color_name}"
    right_electrode.dimensions = (electrode_height, electrode_length, electrode_width)
    right_electrode.location = (body_length/2 - electrode_height/2, 0, body_height/2)
    right_electrode.data.materials.append(electrode_mat)
    add_to_collection(right_electrode)
    
    bpy.ops.object.transform_apply(scale=True, rotation=True)
    
    # ============================================
    # 3. 创建梯形透镜
    # ============================================
    def create_trapezoid_lens(color_name, led_color):
        # 创建梯形网格
        mesh = bpy.data.meshes.new(f"Lens_Mesh_{color_name}")
        lens = bpy.data.objects.new(f"Lens_{color_name}", mesh)
        
        bm = bmesh.new()
        
        # 定义梯形顶点
        # 下表面 (z=0)
        v1 = bm.verts.new((-lens_bottom_length/2, -lens_width/2, 0))
        v2 = bm.verts.new((lens_bottom_length/2, -lens_width/2, 0))
        v3 = bm.verts.new((lens_bottom_length/2, lens_width/2, 0))
        v4 = bm.verts.new((-lens_bottom_length/2, lens_width/2, 0))
        
        # 上表面 (z=lens_height)
        v5 = bm.verts.new((-lens_top_length/2, -lens_width/2, lens_height))
        v6 = bm.verts.new((lens_top_length/2, -lens_width/2, lens_height))
        v7 = bm.verts.new((lens_top_length/2, lens_width/2, lens_height))
        v8 = bm.verts.new((-lens_top_length/2, lens_width/2, lens_height))
        
        # 创建面
        bm.faces.new([v1, v2, v3, v4])  # 底部
        bm.faces.new([v5, v6, v7, v8])  # 顶部
        bm.faces.new([v1, v2, v6, v5])  # 前面
        bm.faces.new([v2, v3, v7, v6])  # 右面
        bm.faces.new([v3, v4, v8, v7])  # 后面
        bm.faces.new([v4, v1, v5, v8])  # 左面
        
        bm.to_mesh(mesh)
        bm.free()
        
        led_collection.objects.link(lens)
        lens.location = (0, 0, body_height + lens_height/2)
        
        # 透镜材质
        lens_mat = create_material(f"Lens_Mat_{color_name}", led_color, 
                                   roughness=0.1, alpha=0.7)
        lens.data.materials.append(lens_mat)
        
        return lens
    
    lens = create_trapezoid_lens(color_name, led_color)
    
    # 放置透镜位置
    lens.location = (0, 0, body_height/2)

    # ============================================
    # 4. 创建内部支撑结构
    # ============================================
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    support = bpy.context.active_object
    support.name = f"Support_{color_name}"
    support.dimensions = (support_length, support_width, support_height)
    support.location = (0, 0, body_height/2 + support_height/2)
    
    support_mat = create_material(f"Support_Mat_{color_name}", (0.3, 0.3, 0.3), roughness=0.6)
    support_mat.diffuse_color = (0.3, 0.3, 0.3, 1)
    support.data.materials.append(support_mat)
    add_to_collection(support)
    bpy.ops.object.transform_apply(scale=True)
    
    # ============================================
    # 5. 创建发光芯片
    # ============================================
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    chip = bpy.context.active_object
    chip.name = f"Chip_{color_name}"
    chip.dimensions = (chip_length, chip_width, chip_height)
    chip.location = (0, 0, support_height/2 + chip_height/2)
    
    chip_mat = create_material(f"Chip_Mat_{color_name}", (1.0, 1.0, 1.0), roughness=0.2, 
                               emission_color=emission_color, emission_strength=2.0)
    chip.data.materials.append(chip_mat)
    add_to_collection(chip)
    bpy.ops.object.transform_apply(scale=True)
    
    # ============================================
    # 6. 左侧电极有绿色T标记
    # ============================================
    # 绿色T标记
    marker_mat = create_material("Marker_Mat", (0.1, 0.8, 0.1))
    marker_mat.diffuse_color = (0.1, 0.8, 0.1, 1)
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    tmarker_segment_1 = bpy.context.active_object
    tmarker_segment_1.name = "TMarker_Segment_1"
    
    # 设置尺寸
    tmarker_segment_1.dimensions = (0.4, body_width - 0.1, 0.035)
    tmarker_segment_1.location = (-0.2, 0, 0.015)
    bpy.ops.object.transform_apply(scale=True)
    
    tmarker_segment_1.data.materials.append(marker_mat)
    add_to_collection(tmarker_segment_1)

    bpy.ops.mesh.primitive_cube_add(size=1.0)
    tmarker_segment_2 = bpy.context.active_object
    tmarker_segment_2.name = "TMarker_Segment_2"
    
    # 设置尺寸
    tmarker_segment_2.dimensions = (0.35, 0.3, 0.035)
    tmarker_segment_2.location = (0.35/2, 0, 0.015)
    bpy.ops.object.transform_apply(scale=True)
    
    tmarker_segment_2.data.materials.append(marker_mat)
    add_to_collection(tmarker_segment_2)
    
    # ============================================
    # 7. 添加圆角
    # ============================================
    def add_bevel(obj, radius_mm=0.15):
        bevel = obj.modifiers.new(name="Bevel", type='BEVEL')
        bevel.width = radius_mm
        bevel.segments = 4
        bevel.limit_method = 'ANGLE'
        bevel.angle_limit = math.radians(30)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.modifier_apply(modifier=bevel.name)
    
    # 为主体和透镜添加圆角
    add_bevel(body, 0.05)
    add_bevel(lens, 0.05)
   
    return led_collection, body, lens

def create_multicolor_leds():
    """创建不同颜色的LED模型"""
    
    # 修正后的颜色映射
    color_map = {
        'blue': (0.1, 0.1, 1.0),           # 蓝色
        'orange': (1.0, 0.5, 0.0),         # 橙色
        'red': (1.0, 0.1, 0.1),            # 红色
        'yellow': (1.0, 1.0, 0.0),         # 黄色
        'green': (0.1, 1.0, 0.1),          # 绿色
        'white': (1.0, 1.0, 1.0),          # 白色
        'emerald-green': (0.1, 0.8, 0.1),  # 翠绿色
        'yellow-green': (0.8, 1.0, 0.1),   # 黄绿色
    }
    
    # 主集合
    main_collection = bpy.data.collections.new("Multicolor_LEDs")
    bpy.context.scene.collection.children.link(main_collection)
    
    # 计算布局
    spacing = 2.0
    start_x = -len(color_map) * spacing / 2
    x_positions = [start_x + i * spacing for i in range(len(color_map))]
    
    all_collections = []
    
    for idx, (color_name, color_rgb) in enumerate(color_map.items()):
        # 创建单个LED
        led_collection, body, lens = create_led_with_color(color_name, color_rgb)
        
        # 将LED添加到主集合
        for obj in led_collection.objects:
            main_collection.objects.link(obj)
        
        # 设置位置
        for obj in led_collection.objects:
            obj.location.x += x_positions[idx]
            
        all_collections.append(led_collection)
        
        print(f"创建了{color_name}色LED，RGB: {color_rgb}")
    
    # 设置视图
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].shading.type = 'MATERIAL'
            area.spaces[0].shading.light = 'STUDIO'
    
    return main_collection, all_collections

def main():
    """主函数入口"""
    clear_scene()
    print("创建多色0603 LED模型...")
    print("=" * 50)
    
    try:
#        main_collection, led_collections = create_multicolor_leds()
#        
#        print(f"\n成功创建了{len(led_collections)}种颜色的LED模型：")
#        for i, coll in enumerate(led_collections):
#            led_count = len([obj for obj in coll.objects if "LED_Body" in obj.name])
#            if led_count > 0:
#                color_name = coll.name.split("_")[1] if "_" in coll.name else f"Color_{i}"
#                print(f"  {color_name}: {len(coll.objects)}个组件")
#        
#        print(f"\n在主集合'Multicolor_LEDs'中包含{len(main_collection.objects)}个对象")
#        print("=" * 50)
#        
#        # 显示模型信息
#        for coll in led_collections:
#            for obj in coll.objects:
#                if "LED_Body" in obj.name:
#                    print(f"\n{obj.name} 尺寸: {obj.dimensions.x:.2f}×{obj.dimensions.y:.2f}×{obj.dimensions.z:.2f}mm")
#                    break
#        
#        print("\n在Outliner中查看'Multicolor_LEDs'集合")
#        print("每个LED都有一个颜色标签标识")
#        print("可以使用Outliner中的集合开关来切换显示")

        create_led_with_color('blue')
            
    except Exception as e:
        print(f"创建模型时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()