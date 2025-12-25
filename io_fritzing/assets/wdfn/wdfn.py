import bpy
import bmesh
import math
from mathutils import Vector
import io_fritzing.assets.commons.triangle as triangle
from io_fritzing.assets.utils.material import create_material
from io_fritzing.assets.utils.scene import clear_scene

wdfn_3x3_10_dimensions = {
    'body': {
        'length': 3.0,      # D: 3mm (封装长度)
        'width': 3.0,       # E: 3mm (封装宽度)
        'height': 0.75,     # A: 封装总高度
        'base_height': 0.02, # A1: 底部厚度
    },
    'thermal_pad': {
        'length': 2.0,      # D2: 热焊盘长度
        'width': 1.6,       # E2: 热焊盘宽度
    },
    'pins': {
        'count': 10,        # 引脚总数
        'per_side': 5,      # 每边引脚数
        'width': 0.25,      # 引脚宽度
        'length': 0.5,      # 引脚延伸长度
        'height': 0.15,     # 引脚高度
        'pitch': 0.5,       # 引脚间距
    },
    'markings': {
        'pin1_indicator': True,  # Pin #1标识
        'text': "WDFN_3x3_10",     # 芯片表面文字
    }
}
    
def create_chip_body(dims):
    """创建芯片主体"""
    # 创建主体网格
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, dims['height']/2 + dims['base_height'])
    )
    body = bpy.context.object
    body.name = "Chip_Body"
    body.scale = (dims['length'], dims['width'], dims['height'])
    
    # 应用缩放
    bpy.ops.object.transform_apply(scale=True)
    
    # 添加材质
    body.data.materials.append(create_material(
        name="Chip_Body_Material",
        base_color=(0.05, 0.05, 0.05, 1.0),
        roughness=0.8,
        metallic=0.1
    ))
    
    return body
    
def create_thermal_pad(dims):
    """创建热焊盘（底部焊盘）"""
    body_dims = dims['body']
    thermal_pad_dims = dims['thermal_pad']
    
    # 创建热焊盘
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=(0, 0, body_dims['base_height']/2 + 0.01)  # 略高于底面
    )
    thermal_pad = bpy.context.object
    thermal_pad.name = "Thermal_Pad"
    thermal_pad.scale = (thermal_pad_dims['length'], thermal_pad_dims['width'], body_dims['base_height'])
    
    # 应用缩放
    bpy.ops.object.transform_apply(scale=True)

    # 从pin2中心线的位置，切去Pin 1所在的角
    pitch = dims['pins']['pitch']
    corner_cutter = triangle.create_right_triangular_prism(
        base_a=pitch,
        base_b=pitch,
        height=body_dims['base_height'] + 0.1,
    )
    corner_cutter.name = 'Corner_Cutter'
    corner_cutter.location=(
            -dims['pins']['pitch'] * 2 - 0.01,
            -thermal_pad_dims['width']/2 - 0.01,
            -body_dims['base_height']
        )
    
    bool_mod = thermal_pad.modifiers.new(name="Thermal_Pad_Cut", type='BOOLEAN')
    bool_mod.operation = 'DIFFERENCE'
    bool_mod.object = corner_cutter
    
    # 应用布尔修改器
    bpy.ops.object.select_all(action='DESELECT')
    corner_cutter.select_set(True)
    bpy.context.view_layer.objects.active = thermal_pad
    bpy.ops.object.modifier_apply(modifier=bool_mod.name)

    bpy.data.objects.remove(corner_cutter, do_unlink=True)

    # 添加材质
    thermal_pad.data.materials.append(create_material(
        name="Thermal_Pad_Material",
        base_color=(0.85, 0.85, 0.88, 1.0),
        roughness=0.2,
        metallic=1.0
    ))
    
    return thermal_pad
    
def create_pins(dims):
    """创建引脚"""
    pin_dims = dims['pins']
    body_dims = dims['body']
    
    pins = []
    
    # 计算引脚起始位置
    total_pin_length = (pin_dims['per_side'] - 1) * pin_dims['pitch']
    start_x = -total_pin_length / 2
    
    # 创建左侧引脚（Pin 1-5）
    for i in range(pin_dims['per_side']):
        # 左侧引脚
        x_pos = start_x + i * pin_dims['pitch']
        y_pos = -body_dims['width']/2 + pin_dims['length']/2 - 0.01
        z_pos = pin_dims['height']/2
        
        pin_left = create_single_pin(
            pin_dims,
            name=f"Pin_{i+1}",
            location=(x_pos, y_pos, z_pos),
            rotation=(0, 0, 0)
        )
        pins.append(pin_left)
        
        # 右侧引脚（Pin 6-10）
        y_pos = body_dims['width']/2 - pin_dims['length']/2 + 0.01
        
        pin_right = create_single_pin(
            pin_dims,
            name=f"Pin_{i+6}",
            location=(x_pos, y_pos, z_pos),
            rotation=(0, 0, math.pi)
        )
        pins.append(pin_right)
    
    return pins

def create_single_pin(pin_dims, name, location, rotation):
    """创建单个引脚"""
    
    # 创建引脚
    bpy.ops.mesh.primitive_cube_add(
        size=1,
        location=location
    )
    pin = bpy.context.object
    pin.name = name
    pin.scale = (pin_dims['width'], pin_dims['length'], pin_dims['height'])
    pin.rotation_euler = rotation
    
    # 应用缩放
    bpy.ops.object.transform_apply(scale=True)
    
    # 添加材质
    pin.data.materials.append(create_material(
        name="Pin_Material",
        base_color=(0.8, 0.8, 0.8, 1.0),
        roughness=0.2,
        metallic=0.9
    ))
    
    return pin

def create_pin1_indicator(dims):
    """创建Pin #1标识"""
    if not dims['markings']['pin1_indicator']:
        return None
    
    body_dims = dims['body']
    
    # 创建圆形凹坑作为Pin 1标识
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=0.15,
        depth=0.05,
        location=(
            -dims['pins']['pitch'] * 2,
            -body_dims['width']/2 + 0.3,
            body_dims['height'] + body_dims['base_height'] - 0.025
        )
    )
    indicator = bpy.context.object
    indicator.name = "Pin1_Indicator"
    
    # 添加材质（与主体相同但略浅）
    indicator.data.materials.append(create_material(
        name="Indicator_Material",
        base_color=(0.15, 0.15, 0.15, 1.0),
        roughness=0.8,
        metallic=0.1
    ))
    
    return indicator

def create_text_marking(dims):
    """创建芯片表面文字"""
    text = dims['markings']['text']
    body_dims = dims['body']
    
    # 创建文字对象
    bpy.ops.object.text_add()
    text_obj = bpy.context.object
    text_obj.name = "Chip_Text"
    text_obj.data.body = text
    text_obj.data.size = 0.40
    text_obj.data.align_x = 'CENTER'
    text_obj.data.align_y = 'CENTER'
    
    # 放置文字在芯片表面中心
    text_obj.location = (
        0,
        0,
        body_dims['height'] + body_dims['base_height']/2 + 0.005
    )
    text_obj.rotation_euler = (0, 0, 0)
    text_obj.data.extrude = 0.01
    
    # 转换为网格
    bpy.context.view_layer.objects.active = text_obj
    bpy.ops.object.convert(target='MESH')
    
    # 添加材质
    text_obj.data.materials.append(create_material(
        name="Text_Material",
        base_color=(0.9, 0.9, 0.9, 1.0),
        roughness=0.7,
        metallic=0.0
    ))
    
    return text_obj
    
def create_wdfn_3x3_10(dims = wdfn_3x3_10_dimensions):
    """创建完整模型"""
    # 创建组件
    body = create_chip_body(dims['body'])
    thermal_pad = create_thermal_pad(dims)
    pins = create_pins(dims)
    pin1_indicator = create_pin1_indicator(dims)
    text_marking = create_text_marking(dims)

    # body和pin1_indicator做BOOLEAN操作
    if pin1_indicator and body:
        bool_mod = body.modifiers.new(name="Pin1_Marker_Cut", type='BOOLEAN')
        bool_mod.operation = 'DIFFERENCE'
        bool_mod.object = pin1_indicator
        
        # 应用布尔修改器
        bpy.ops.object.select_all(action='DESELECT')
        pin1_indicator.select_set(True)
        bpy.context.view_layer.objects.active = body
        bpy.ops.object.modifier_apply(modifier=bool_mod.name)

        bpy.data.objects.remove(pin1_indicator, do_unlink=True)
    
    # 选择所有芯片组件
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
    thermal_pad.select_set(True)
    text_marking.select_set(True)
    for obj in pins:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()

    body.rotation_euler.z = -math.pi/2

    return body

def create_wdfn_3x3_10_model(text = "WDFN 3x3-10"):
    """创建WDFN 3x3-10芯片模型"""
    dims = wdfn_3x3_10_dimensions
    dims['markings']['text'] = text
    wdfn = create_wdfn_3x3_10(dims)
    wdfn.name = text
    return wdfn

# 主执行函数
def main():
    """主函数"""
    # 设置场景
    clear_scene()
        
    """主函数"""
    print("=" * 50)
    print("WDFN 3x3-10芯片3D建模")
    print("=" * 50)
    
    print("开始创建WDFN 3x3-10芯片模型...")
    
    # 创建建模器实例
    chip_collection = create_wdfn_3x3_10_model(text="RT6150AGQW")
    
    print("芯片模型创建完成！")
    print(f"封装尺寸: {wdfn_3x3_10_dimensions['body']['length']}x{wdfn_3x3_10_dimensions['body']['width']}x{wdfn_3x3_10_dimensions['body']['height']} mm")
    print(f"引脚数量: {wdfn_3x3_10_dimensions['pins']['count']}")
    
# 执行
if __name__ == "__main__":
    main()
