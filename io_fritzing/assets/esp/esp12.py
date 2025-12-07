import bpy
import math
import bmesh
from mathutils import Vector
from io_fritzing.assets.commons.antenna import create_esp12f_antenna
from io_fritzing.assets.led.led0603 import create_led_with_color

def clear_scene():
    # 清除默认场景
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # 设置单位为毫米
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'

def create_esp12f_model():
    """创建ESP-12F模型的完整函数"""
    
    # 创建新集合
    esp12f_collection = bpy.data.collections.new("ESP12F_Model")
    bpy.context.scene.collection.children.link(esp12f_collection)
    
    def add_to_collection(obj):
        if obj.name not in esp12f_collection.objects:
            esp12f_collection.objects.link(obj)
        if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
    
    def create_material(name, color, metallic=0.0, roughness=0.5):
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        for node in nodes:
            nodes.remove(node)
        
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.location = (0, 0)
        output = nodes.new(type='ShaderNodeOutputMaterial')
        output.location = (300, 0)
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        bsdf.inputs['Base Color'].default_value = (*color, 1.0)
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        return mat
    
    # ============================================
    # 1. 创建PCB板 (24×16×0.6mm)
    # ============================================
    pcb_length = 24
    pcb_width = 16
    pcb_thickness = 0.6
    
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    pcb = bpy.context.active_object
    pcb.name = "ESP12_Body"
    pcb.scale = (pcb_length, pcb_width, pcb_thickness)
    pcb.location = (0, 0, 0)
    
    add_to_collection(pcb)
    
    pcb_mat = create_material("PCB_Mat", (0.1, 0.3, 0.1))
    pcb_mat.diffuse_color=(0.1, 0.3, 0.1, 1)
    pcb.data.materials.append(pcb_mat)
    
    # ============================================
    # 2. 创建金属屏蔽罩 (15×12×2.4mm，距离1.2mm)
    # ============================================
    shield_length = 15
    shield_width = 12
    shield_thickness = 2.4
    
    # 金属盒位置
    shield_x = -pcb_length/2 + 1.2 + shield_length/2
    shield_y = 0
    shield_z = pcb_thickness/2 + shield_thickness/2
    
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    shield = bpy.context.active_object
    shield.name = "Metal_Shield"
    shield.scale = (shield_length, shield_width, shield_thickness)
    shield.location = (shield_x, shield_y, shield_z)
    
    add_to_collection(shield)
    
    shield_mat = create_material("Shield_Mat", (0.8, 0.8, 0.85), metallic=0.9, roughness=0.3)
    shield_mat.diffuse_color = (0.8, 0.8, 0.85, 1)
    shield.data.materials.append(shield_mat)
    
    # ============================================
    # 3. 创建引脚系统
    # 引脚厚度0.7mm，在PCB上下都露出0.05mm
    # 根据图片重新排序引脚名称
    # ============================================
    pin_mat = create_material("Pin_Mat", (1.0, 0.84, 0.0), metallic=0.9, roughness=0.2)
    pin_mat.diffuse_color = (1.0, 0.84, 0.0, 1)
    
    # 引脚尺寸
    pin_width = 1
    pin_thickness = 0.7
    pin_length = 1.5
    pin_spacing = 2
    
    def create_pin(x, y, z, rot_z=0, name="Pin"):
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        pin = bpy.context.active_object
        pin.name = name
        pin.scale = (pin_width, pin_length, pin_thickness)
        pin.location = (x, y, z)
        pin.rotation_euler.z = math.radians(rot_z)
        pin.data.materials.append(pin_mat)
        add_to_collection(pin)
        return pin
    
    # 引脚Z位置
    pin_z = 0.0
    
    # 引脚在PCB上下露出的量
    pin_protrusion = (pin_thickness - pcb_thickness) / 2
    
    # ① 顶部8个引脚
    # 从右到左：RST, ADC, EN, GPIO16, GPIO14, GPIO12, GPIO13, VCC
    # 在模型中从左到右
    top_pin_names = ["VCC", "GPIO13", "GPIO12", "GPIO14", "GPIO16", "EN", "ADC", "RST"]
    first_pin_x = -pcb_length/2 + 1.5
    
    for i in range(8):
        x_pos = first_pin_x + i * pin_spacing
        y_pos = pcb_width/2 - pin_length/2
        create_pin(x_pos, y_pos, pin_z, 0, f"Top_{top_pin_names[i]}")
    
    # ② 底部8个引脚
    # 从右到左：TXD0, RXD0, GPIO5, GPIO4, GPIO0,, GPIO15, GND
    # 在模型中从左到右
    bottom_pin_names = ["GND", "GPIO15", "GPIO2", "GPIO0", "GPIO4", "GPIO5", "RXD0", "TXD0"]
    
    for i in range(8):
        x_pos = first_pin_x + i * pin_spacing
        y_pos = -pcb_width/2 + pin_length/2
        create_pin(x_pos, y_pos, pin_z, 0, f"Bottom_{bottom_pin_names[i]}")
    
    # ③ 左侧6个引脚
    # 从上到下：CS0, MISO, GPIO9, GPIO10, MOSI, SCLK
    # 在模型中从上到下
    left_pin_names = ["CS0", "MISO", "GPIO9", "GPIO10", "MOSI", "SCLK"]
    
    for i in range(6):
        y_pos = (i - 2.5) * pin_spacing
        x_pos = -pcb_length/2 + pin_length/2
        create_pin(x_pos, y_pos, pin_z, 90, f"Left_{left_pin_names[i]}")
    
    # 根据图片，没有右侧引脚

    # ④ 创建右侧天线
    antenna_collection = bpy.data.collections.new("ESP12F_Antenna")
    esp12f_collection.children.link(antenna_collection)
    trace_thickness = 0.035  # 1oz = 0.035mm
    antenna_width = 6
    antenna_segments = create_esp12f_antenna(pcb_width, antenna_width, 0.5, 0.3, 0.5, trace_thickness, pin_mat, antenna_collection)
    for segment in antenna_segments:
        segment.location.x += pcb_length/2 - antenna_width/2
        segment.location.z += pcb_thickness/2 + trace_thickness/2
        segment.rotation_euler.z = math.radians(-90)

    led_collection, led_body, led_lens = create_led_with_color("blue")
    esp12f_collection.children.link(led_collection)
    for obj in led_collection.objects:
        obj.location.x += pcb_length/2 - antenna_width - led_body.dimensions.y
        obj.location.y += -pcb_width/2 + pin_length
        obj.location.z += pcb_thickness/2 + trace_thickness/2
        obj.rotation_euler.z = math.radians(-90)
    
    # ============================================
    # 4. 创建文字
    # 根据图片中的文字
    # ============================================
    def add_text(text, location, size=1.5, extrude=0.1):
        bpy.ops.object.text_add(location=location)
        text_obj = bpy.context.active_object
        text_obj.name = f"Text_{text}"
        text_obj.data.body = text
        text_obj.data.size = size
        text_obj.data.extrude = extrude
        text_obj.data.align_x = 'CENTER'
        text_obj.data.align_y = 'CENTER'
        add_to_collection(text_obj)
        return text_obj
    
    # 文字位置
    text_z = shield_z + shield_thickness/2 + 0.1
    
    # 根据图片添加文字
    # 中间区域
    esp12_text = add_text("ESP12", (shield_x, 3, text_z), 1.5)
    esp_text = add_text("ESP8266MOD", (shield_x, 0, text_z), 1.5)
    
    # 设置文字材质
    text_mat = create_material("Text_Mat", (1, 1, 1))
    text_mat.diffuse_color = (1, 1, 1, 1)
    for text_obj in [esp12_text, esp_text]:
        text_obj.data.materials.append(text_mat)
    
    # ============================================
    # 5. 设置视图
    # ============================================
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].shading.type = 'MATERIAL'
    
    return esp12f_collection, pcb, shield

def main():
    clear_scene()

    """主函数入口"""
    print("开始创建ESP-12F WiFi模块3D模型...")
    print("=" * 50)
    print("根据图片重新配置:")
    print("顶部引脚 (从右到左): RST, ADC0, EN, GPIO16, GPIO14, GPIO12, GPIO13, VCC")
    print("底部引脚 (从右到左): TXD0, RXD0, GPIO5, GPIO4, GPIO0, GPIO2, GPIO15, GND")
    print("左侧引脚 (从上到下): CS0, MISO, GPIO9, GPIO10, MOSI, SCLK")
    print("=" * 50)
    
    try:
        collection, pcb, shield = create_esp12f_model()
        
        # 获取引脚
        top_pins = [obj for obj in collection.objects if "Top_" in obj.name]
        bottom_pins = [obj for obj in collection.objects if "Bottom_" in obj.name]
        left_pins = [obj for obj in collection.objects if "Left_" in obj.name]
        
        # 按位置排序
        top_pins.sort(key=lambda p: p.location.x)
        bottom_pins.sort(key=lambda p: p.location.x)
        left_pins.sort(key=lambda p: p.location.y, reverse=True)  # 从上到下
        
        # 输出顺序
        print("引脚排列 (从左到右/从上到下):")
        print(f"顶部引脚: {[pin.name.split('_')[1] for pin in top_pins]}")
        print(f"底部引脚: {[pin.name.split('_')[1] for pin in bottom_pins]}")
        print(f"左侧引脚: {[pin.name.split('_')[1] for pin in left_pins]}")
        
        print(f"PCB尺寸: {pcb.scale.x:.3f}×{pcb.scale.y:.3f}×{pcb.scale.z:.3f}mm")
        print(f"引脚厚度: 0.7mm (在PCB上下各露出0.05mm)")
        print("模型创建成功！")
        print("在Outliner中查看'ESP12F_Model'集合")
        
    except Exception as e:
        print(f"创建模型时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()