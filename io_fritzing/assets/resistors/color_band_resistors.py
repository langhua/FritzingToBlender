import bpy
import bmesh
import math
from mathutils import Matrix
from typing import List, Tuple, Dict
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import FloatProperty, StringProperty, EnumProperty, IntProperty, BoolProperty, PointerProperty, FloatVectorProperty
from io_fritzing.assets.resistors.band_colors import RESISTOR_COLORS, TOLERANCE_COLORS
from io_fritzing.assets.utils.material import create_material
from io_fritzing.assets.resistors.color_4band import resistance_tolerance_to_4bands
from io_fritzing.assets.resistors.color_5band import resistance_tolerance_to_5bands
from io_fritzing.assets.commons.l_pin import create_L_pins


bl_info = {
    "name": "色环电阻生成器",
    "version": (3, 8, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N > 电阻工具 > 色环电阻",
    "description": "生成任意阻值的四色环和五色环电阻3D模型，支持碳膜、金属膜、金属氧化物膜电阻，公差≥5%时只能选碳膜电阻",
    "category": "3D View"
}

# 电阻本体颜色定义
RESISTOR_BODY_COLORS = {
    'CARBON': {
        'name': '碳膜电阻',
        'color': (0.88, 0.78, 0.58, 1.0),
        'description': '碳膜电阻，本体为浅棕色/米黄色，精度较低（公差通常为±5%、±10%）',
        'tolerance_limit': 5.0,  # 公差下限
        'color_desc': '浅棕色/米黄色',
        'typical_tolerance': ['5%', '10%'],
        'typical_wattage': ['1/8W', '1/4W', '1/2W', '1W']
    },
    'METAL': {
        'name': '金属膜电阻',
        'color': (0.3, 0.5, 0.8, 1.0),
        'description': '金属膜电阻，本体为蓝色，精度较高（公差通常为±1%、±2%）',
        'tolerance_limit': 1.0,  # 公差下限
        'color_desc': '蓝色',
        'typical_tolerance': ['1%', '2%'],
        'typical_wattage': ['1/8W', '1/4W', '1/2W', '1W', '2W']
    },
    'METAL_OXIDE': {
        'name': '金属氧化物膜电阻',
        'color': (0.7, 0.7, 0.7, 1.0),
        'description': '金属氧化物膜电阻，本体为灰色，精度较高（公差通常为±1%、±2%）',
        'tolerance_limit': 1.0,  # 公差下限
        'color_desc': '灰色',
        'typical_tolerance': ['1%', '2%'],
        'typical_wattage': ['1/2W', '1W', '2W', '3W', '5W']
    }
}

# 电阻功率与焊孔孔距对应关系
dimensions = {
    '1_8W': {
        'hole_spacing': 7.62,
        'body_length': 3.45,
        'body_diameter': 1.8,
        'lead_length': 30,       # 单边引线长度
        'lead_diameter': 0.35,   # 引线外径
        'band_width': 0.2,
        'band_spacing': 0.4
    },
    '1_4W': {
        'hole_spacing': 10.16,
        'body_length': 5.7,
        'body_diameter': 2.15,
        'lead_length': 26,
        'lead_diameter': 0.35,
        'band_width': 0.4,
        'band_spacing': 0.8
    },
    '1_2W': {
        'hole_spacing': 12.7,
        'body_length': 8.7,
        'body_diameter': 2.9,
        'lead_length': 25,
        'lead_diameter': 0.4,
        'band_width': 0.5,
        'band_spacing': 1.2
    },
    '1W': {
        'hole_spacing': 15.24,
        'body_length': 10.8,
        'body_diameter': 3.5,
        'lead_length': 23,
        'lead_diameter': 0.45,
        'band_width': 0.7,
        'band_spacing': 1.6
    },
}

# ==================== 工具函数 ====================
def format_resistance(value: float) -> str:
    """格式化电阻值显示"""
    if value >= 1000000:  # 1MΩ以上
        return f"{value/1000000:.3f}MΩ"
    elif value >= 1000:   # 1kΩ以上
        return f"{value/1000:.3f}kΩ"
    elif value >= 1:      # 1Ω以上
        return f"{value:.3f}Ω"
    elif value >= 0.001:  # 1mΩ以上
        return f"{value*1000:.3f}mΩ"
    else:                 # 小于1mΩ
        return f"{value*1000000:.3f}μΩ"

def calculate_resistor_bands(resistance: float, tolerance_percent: float, band_type: str = '4BAND') -> List[Dict]:
    """
    计算任意电阻值的色环
    """
    if resistance <= 0:
        return []
    
    if band_type == '4BAND':
        return resistance_tolerance_to_4bands(resistance, tolerance_percent)
    elif band_type == '5BAND':
        return resistance_tolerance_to_5bands(resistance, tolerance_percent)
    else:
        raise ValueError("Invalid band_type")


# ==================== 属性组 ====================
class ResistorColorBandProperties(PropertyGroup):
    """电阻色环属性组"""
    
    # 基本参数
    resistance: FloatProperty(
        name="电阻值",
        description="电阻值 (单位: Ω)",
        default=4700.0,
        min=0.001,
        max=10000000.0,
        precision=4,
        step=100,
        update=lambda self, context: self.update_band_preview()
    )  # type: ignore
    
    # 公差
    tolerance: EnumProperty(
        name="公差",
        description="选择电阻公差百分比",
        items=[
            ('1%', "1%", "1% 公差 (棕色)"),
            ('2%', "2%", "2% 公差 (红色)"),
            ('5%', "5%", "5% 公差 (金色)"),
            ('10%', "10%", "10% 公差 (银色)"),
        ],
        default='5%',
        update=lambda self, context: self.update_resistor_type_options()
    )  # type: ignore
    
    # 色环类型
    band_type: EnumProperty(
        name="色环类型",
        description="选择色环类型",
        items=[
            ('4BAND', "四色环", "4色环电阻"),
            ('5BAND', "五色环", "5色环电阻"),
        ],
        default='4BAND',
        update=lambda self, context: self.update_band_preview()
    )  # type: ignore
    
    # 电阻类型
    resistor_type: EnumProperty(
        name="电阻类型",
        description="选择电阻类型，注意：公差≥5%时只能选碳膜电阻",
        items=[
            ('CARBON', "碳膜电阻", "碳膜电阻，本体为浅棕色/米黄色，精度较低（公差通常为±5%、±10%）"),
            ('METAL', "金属膜电阻", "金属膜电阻，本体为蓝色，精度较高（公差通常为±1%、±2%）"),
            ('METAL_OXIDE', "金属氧化物膜电阻", "金属氧化物膜电阻，本体为灰色，精度较高（公差通常为±1%、±2%）"),
        ],
        default='CARBON',
        update=lambda self, context: self.update_band_preview()
    )  # type: ignore
    
    # 电阻尺寸 - 更新为毫米单位
    resistor_size: EnumProperty(
        name="电阻尺寸",
        description="选择电阻尺寸（基于真实电阻尺寸）",
        items=[
            ('1_8W', "1/8W", "1/8W轴向电阻"),
            ('1_4W', "1/4W", "1/4W轴向电阻"),
            ('1_2W', "1/2W", "1/2W轴向电阻"),
            ('1W', "1W", "1W轴向电阻"),
        ],
        default='1_4W'
    )  # type: ignore
    
    show_resistance_text: BoolProperty(
        name="显示电阻值",
        description="在电阻上显示电阻值文本",
        default=True
    )  # type: ignore
    
    # 引脚选项
    add_pins: BoolProperty(
        name="添加引脚",
        description="在电阻两端添加引脚",
        default=True
    )  # type: ignore
    
    pin_length: FloatProperty(
        name="引脚长度",
        description="引脚长度 (单位: mm)",
        default=25.0,
        min=5.0,
        max=50.0,
        precision=1,
        step=1
    )  # type: ignore
    
    # 预览信息
    band_preview: StringProperty(
        name="色环预览",
        description="当前设置的色环预览",
        default=""
    )  # type: ignore
    
    # 电阻类型与公差兼容性警告
    type_tolerance_warning: BoolProperty(
        name="电阻类型与公差不匹配",
        description="当前电阻类型与公差不匹配，公差≥5%时只能选碳膜电阻",
        default=False
    )  # type: ignore
    
    def update_band_preview(self):
        """更新色环预览"""
        tolerance_str = self.tolerance.strip('%')
        try:
            tolerance_value = float(tolerance_str)
        except ValueError:
            tolerance_value = 5.0
            
        bands = calculate_resistor_bands(self.resistance, tolerance_value, '4BAND' if self.band_type == '4BAND' else '5BAND')
        if bands:
            band_names = [band['color']['name'] for band in bands]
            self.band_preview = " - ".join(band_names)
        else:
            self.band_preview = "无法计算色环"
    
    def update_resistor_type_options(self):
        """更新电阻类型选项，根据公差限制选项"""
        tolerance_str = self.tolerance.strip('%')
        try:
            tolerance_value = float(tolerance_str)
        except ValueError:
            tolerance_value = 5.0
        
        # 如果公差≥5%，检查当前电阻类型
        if tolerance_value >= 5.0 and self.resistor_type != 'CARBON':
            # 自动切换到碳膜电阻
            self.resistor_type = 'CARBON'
            self.type_tolerance_warning = True
        else:
            self.type_tolerance_warning = False
        
        # 更新色环预览
        self.update_band_preview()

# ==================== 操作类 ====================
class OBJECT_OT_CreateResistor(Operator):
    """生成电阻色环模型"""
    bl_idname = "object.create_resistor_bands"
    bl_label = "生成色环电阻"
    bl_description = "生成带有色环的电阻3D模型，可选择电阻类型"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.resistor_band_props
        
        # 检查电阻类型与公差兼容性
        tolerance_str = props.tolerance.strip('%')
        try:
            tolerance_value = float(tolerance_str)
        except ValueError:
            tolerance_value = 5.0
        
        # 获取当前电阻类型的公差限制
        resistor_info = RESISTOR_BODY_COLORS.get(props.resistor_type, RESISTOR_BODY_COLORS['CARBON'])
        tolerance_limit = resistor_info.get('tolerance_limit', 5.0)
        
        # 检查兼容性
        if tolerance_value >= 5.0 and props.resistor_type != 'CARBON':
            self.report({'ERROR'}, f"公差≥5%时只能选择碳膜电阻！当前选择：{resistor_info['name']}")
            return {'CANCELLED'}
        
        if tolerance_value < 5.0 and props.resistor_type == 'CARBON':
            # 公差<5%时选择碳膜电阻是可以的，但显示警告
            self.report({'WARNING'}, f"公差<5%时建议选择更高精度的电阻类型（金属膜、金属氧化物膜电阻）")
        
        if tolerance_value < tolerance_limit and props.resistor_type != 'CARBON':
            self.report({'ERROR'}, f"{resistor_info['name']}的公差下限是±{tolerance_limit}%，当前公差±{tolerance_value}%不符合要求")
            return {'CANCELLED'}
        
        bands = calculate_resistor_bands(props.resistance, tolerance_value, '4BAND' if props.band_type == '4BAND' else '5BAND')
        
        if not bands:
            self.report({'ERROR'}, "无法计算电阻色环")
            return {'CANCELLED'}
        
        resistor = self.create_resistor_body(props.resistor_size, props.resistor_type)
        if not resistor:
            self.report({'ERROR'}, "无法创建电阻主体")
            return {'CANCELLED'}
        
        self.create_color_bands(resistor, bands, props.resistor_size)
        
        if props.add_pins:
            # self.create_pins(resistor, props.resistor_size, props.pin_length)
            left_pin, right_pin = create_L_pins(dimensions[props.resistor_size])
        
        if props.show_resistance_text:
            # 添加电阻类型到文本
            resistor_type_name = RESISTOR_BODY_COLORS[props.resistor_type]['name']
            self.create_resistance_text(resistor, props.resistance, tolerance_value, resistor_type_name)
        
        resistor.rotation_euler.y = -math.pi/2
        resistor.location.z = dimensions[props.resistor_size]['body_diameter']/2

        for area in context.screen.areas:
            if area.type == 'VIEW_3D':
                area.spaces[0].shading.type = 'SOLID'
                area.spaces[0].shading.color_type = 'MATERIAL'
        
        resistor_type_display = RESISTOR_BODY_COLORS[props.resistor_type]['name']
        tolerance_info = f"公差±{tolerance_value}%" if tolerance_value >= 1 else f"公差±{tolerance_value*100:.1f}%"
        self.report({'INFO'}, f"已生成{resistor_type_display} {props.band_type}电阻: {format_resistance(props.resistance)} ({tolerance_info})")
        return {'FINISHED'}
    
    def create_resistor_body(self, size: str, resistor_type: str) -> bpy.types.Object:
        """创建电阻主体（两端为球体，中间为圆柱体）- 使用毫米单位"""
        body_length_mm = dimensions[size]['body_length']
        body_radius_mm = dimensions[size]['body_diameter'] / 2
        cylinder_radius = body_radius_mm / 1.05
        
        # 使用bmesh创建组合网格
        bm = bmesh.new()
        
        # 创建圆柱体
        bmesh.ops.create_cone(
            bm,
            cap_ends=True,
            cap_tris=False,
            segments=64,
            radius1=cylinder_radius,
            radius2=cylinder_radius,
            depth=body_length_mm - body_radius_mm * 2
        )
        
        # 获取圆柱体顶点
        cylinder_verts = [v for v in bm.verts]
        
        # 创建第一个端部球体
        bmesh.ops.create_uvsphere(
            bm,
            u_segments=32,
            v_segments=16,
            radius=body_radius_mm
        )
        
        # 获取新创建的顶点（球体1）
        sphere1_verts = [v for v in bm.verts if v not in cylinder_verts]
        
        # 平移第一个球体到圆柱体一端
        bmesh.ops.translate(
            bm,
            verts=sphere1_verts,
            vec=(0, 0, body_length_mm/2 - cylinder_radius)
        )
        
        # 获取所有当前顶点
        all_verts = [v for v in bm.verts]
        
        # 创建第二个端部球体
        bmesh.ops.create_uvsphere(
            bm,
            u_segments=32,
            v_segments=16,
            radius=body_radius_mm
        )
        
        # 获取新创建的顶点（球体2）
        sphere2_verts = [v for v in bm.verts if v not in all_verts]
        
        # 平移第二个球体到圆柱体另一端
        bmesh.ops.translate(
            bm,
            verts=sphere2_verts,
            vec=(0, 0, -body_length_mm/2 + cylinder_radius)
        )
        
        # 合并所有顶点
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.01)
        
        # 创建网格和对象
        mesh = bpy.data.meshes.new("Resistor_Mesh")
        bm.to_mesh(mesh)
        bm.free()
        
        resistor = bpy.data.objects.new("Resistor_Body", mesh)
        
        # 链接到当前场景
        scene = bpy.context.scene
        scene.collection.objects.link(resistor)
        
        # 选择并激活电阻对象
        bpy.ops.object.select_all(action='DESELECT')
        resistor.select_set(True)
        bpy.context.view_layer.objects.active = resistor
        
        # 根据电阻类型选择颜色
        resistor_color_info = RESISTOR_BODY_COLORS.get(resistor_type, RESISTOR_BODY_COLORS['CARBON'])
        body_mat = create_material(f"Resistor_Body_{resistor_type}", 
                                  resistor_color_info['color'], 
                                  metallic=0.0, 
                                  roughness=0.8)
        resistor.data.materials.append(body_mat)
        
        return resistor
    
    def create_color_bands(self, resistor: bpy.types.Object, bands: List[Dict], size: str):
        """创建色环，第一个色环在第二个位置，最后一个色环在第一个位置的对称位置 - 使用毫米单位"""
        # 色环尺寸（毫米单位）
        band_width_mm = dimensions[size]['band_width']
        band_spacing_mm = dimensions[size]['band_spacing']
        resistor_length = resistor.dimensions.z
        resistor_radius = resistor.dimensions.x / 2
        
        num_bands = len(bands)
        
        if num_bands == 0:
            return
        
        # 计算色环位置
        if num_bands == 4:  # 4色环
            band_positions = []
            # 第一个色环位置：从左向右第一个位置
            band_positions.append(2 * band_spacing_mm)
            # 第二个色环位置：在第一个右边
            band_positions.append(band_spacing_mm)
            # 第三个色环位置：在第二个右边
            band_positions.append(0)
            # 第四个色环（公差）位置：在第一个的对称位置
            band_positions.append(-2 * band_spacing_mm)
            
        elif num_bands == 5:  # 5色环
            band_positions = []
            # 第一个色环位置：从右向左第二个位置
            band_positions.append(2 * band_spacing_mm)
            # 第二个色环位置：在第一个右边
            band_positions.append(band_spacing_mm)
            # 第三个色环位置：在第二个右边
            band_positions.append(0)
            # 第四个色环位置：在第三个右边
            band_positions.append(-band_spacing_mm)
            # 第五个色环（公差）位置：在第一个的对称位置
            band_positions.append(-2 * band_spacing_mm)
        
        else:
            # 默认处理
            start_z = -resistor_length/2 + band_spacing_mm
            for i in range(num_bands):
                band_positions.append(start_z + i * band_spacing_mm)
        
        # 创建色环
        for i, (band, pos_z) in enumerate(zip(bands, band_positions)):
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=32,
                radius=resistor_radius + 0.0001,
                depth=band_width_mm,
                location=(0, 0, pos_z)
            )
            
            color_band = bpy.context.active_object
            if not color_band:
                continue
                
            color_band.name = f"ColorBand_{i+1}"
            
            color = band['color']['color']
            mat_name = f"Band_{band['color']['name']}"
            band_mat = create_material(mat_name, color, metallic=0.0, roughness=0.6)
            color_band.data.materials.append(band_mat)
            
            color_band.parent = resistor
    
    def create_pins(self, resistor: bpy.types.Object, size: str, pin_length_mm: float, pin_diameter_mm: float) -> Tuple[bpy.types.Object|None, bpy.types.Object|None]:
        """创建电阻引脚 - 使用毫米单位"""
        resistor_length = resistor.dimensions.z
        
        # 创建左侧引脚
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=pin_diameter_mm / 2,
            depth=pin_length_mm,
            location=(0, 0, -resistor_length/2 - pin_length_mm/2 + 0.01)
        )
        pin_left = bpy.context.active_object
        pin_left.name = "Pin_Left"
        
        # 创建右侧引脚
        bpy.ops.mesh.primitive_cylinder_add(
            vertices=16,
            radius=pin_diameter_mm / 2,
            depth=pin_length_mm,
            location=(0, 0, resistor_length/2 + pin_length_mm/2 - 0.01)
        )
        pin_right = bpy.context.active_object
        pin_right.name = "Pin_Right"
        
        # 应用引脚材质（金属色）
        pin_mat = create_material("Pin_Material", (0.8, 0.8, 0.8, 1.0), metallic=0.8, roughness=0.3)
        pin_left.data.materials.append(pin_mat)
        pin_right.data.materials.append(pin_mat)
        
        # 将引脚设置为电阻的子对象
        pin_left.parent = resistor
        pin_right.parent = resistor
        
        # 添加平滑着色
        bpy.ops.object.select_all(action='DESELECT')
        pin_left.select_set(True)
        bpy.context.view_layer.objects.active = pin_left
        bpy.ops.object.shade_smooth()
        
        bpy.ops.object.select_all(action='DESELECT')
        pin_right.select_set(True)
        bpy.context.view_layer.objects.active = pin_right
        bpy.ops.object.shade_smooth()

        return (pin_left, pin_right)
    
    # def create_L_pins(self, resistor: bpy.types.Object, size: str):
    #     """创建L型引脚 - 用于PCB焊接的L型引脚，焊孔间距按AXIAL标准"""
    #     # 引脚直径（毫米单位）- 根据电阻尺寸调整
    #     pin_diameter_mm = dimensions[size]['body_diameter']
        
    #     # 焊孔间距（毫米单位）- 根据AXIAL标准
    #     hole_spacing_mm = dimensions[size]['hole_spacing']
        
    #     # 引脚各部分长度（毫米单位）
    #     vertical_length_mm = 2.5  # 垂直段长度
    #     horizontal_length_mm = hole_spacing_mm / 2  # 水平段长度为焊孔间距的一半
        
    #     # 电阻尺寸
    #     resistor_length = resistor.dimensions.z
        
    #     # 创建引脚材质（金属色）
    #     pin_mat = create_material("Pin_Material", (0.8, 0.8, 0.8, 1.0), metallic=0.8, roughness=0.3)
        
    #     # 创建左侧引脚
    #     left_pin = self.create_single_L_pin(
    #         pin_radius=pin_diameter_mm / 2,
    #         vertical_length=vertical_length_mm,
    #         horizontal_length=horizontal_length_mm,
    #         position_z=-resistor_length/2,
    #         direction=1,  # 左侧引脚向右弯折
    #         name="Pin_Left"
    #     )
        
    #     # 创建右侧引脚
    #     right_pin = self.create_single_L_pin(
    #         pin_radius=pin_diameter_mm / 2,
    #         vertical_length=vertical_length_mm,
    #         horizontal_length=horizontal_length_mm,
    #         position_z=resistor_length/2,
    #         direction=-1,  # 右侧引脚向左弯折
    #         name="Pin_Right"
    #     )
        
    #     # 应用材质
    #     left_pin.data.materials.append(pin_mat)
    #     right_pin.data.materials.append(pin_mat)
        
    #     # 将引脚设置为电阻的子对象
    #     left_pin.parent = resistor
    #     right_pin.parent = resistor
        
    #     # 添加平滑着色
    #     bpy.ops.object.select_all(action='DESELECT')
    #     left_pin.select_set(True)
    #     bpy.context.view_layer.objects.active = left_pin
    #     bpy.ops.object.shade_smooth()
        
    #     bpy.ops.object.select_all(action='DESELECT')
    #     right_pin.select_set(True)
    #     bpy.context.view_layer.objects.active = right_pin
    #     bpy.ops.object.shade_smooth()
    #     return left_pin, right_pin
    
    # def create_single_L_pin(self, pin_radius: float, vertical_length: float, 
    #                        horizontal_length: float, position_z: float, 
    #                        direction: int, name: str) -> bpy.types.Object:
    #     """
    #     创建单个L型引脚
        
    #     参数:
    #     - pin_radius: 引脚半径
    #     - vertical_length: 垂直段长度
    #     - horizontal_length: 水平段长度
    #     - position_z: 引脚在Z轴的位置
    #     - direction: 弯折方向 (1: 向右, -1: 向左)
    #     - name: 引脚名称
    #     """
    #     # 创建新的bmesh
    #     bm = bmesh.new()
        
    #     # 创建垂直段（圆柱体）
    #     bmesh.ops.create_cone(
    #         bm,
    #         cap_ends=True,
    #         cap_tris=False,
    #         segments=16,
    #         radius1=pin_radius,
    #         radius2=pin_radius,
    #         depth=vertical_length
    #     )
        
    #     # 创建水平段（圆柱体）
    #     bmesh.ops.create_cone(
    #         bm,
    #         cap_ends=True,
    #         cap_tris=False,
    #         segments=16,
    #         radius1=pin_radius,
    #         radius2=pin_radius,
    #         depth=horizontal_length
    #     )
        
    #     # 获取水平段的所有顶点
    #     vertical_verts = [v for v in bm.verts[:16 * 2]]  # 垂直段顶点
    #     horizontal_verts = [v for v in bm.verts[16 * 2:]]  # 水平段顶点
        
    #     # 移动水平段到垂直段末端
    #     bmesh.ops.translate(
    #         bm,
    #         verts=horizontal_verts,
    #         vec=(0, 0, vertical_length/2)
    #     )
        
    #     # 旋转水平段90度，使其与垂直段垂直
    #     bmesh.ops.rotate(
    #         bm,
    #         verts=horizontal_verts,
    #         matrix=Matrix.Rotation(math.radians(90), 4, 'Y')
    #     )
        
    #     # 将水平段移动到弯折点
    #     bmesh.ops.translate(
    #         bm,
    #         verts=horizontal_verts,
    #         vec=(0, 0, vertical_length/2)
    #     )
        
    #     # 如果方向是向左，旋转水平段180度
    #     if direction < 0:
    #         bmesh.ops.rotate(
    #             bm,
    #             verts=horizontal_verts,
    #             matrix=Matrix.Rotation(math.radians(180), 4, 'Z')
    #         )
        
    #     # 将所有引脚移动到正确位置
    #     bmesh.ops.translate(
    #         bm,
    #         verts=bm.verts,
    #         vec=(0, 0, position_z)
    #     )
        
    #     # 合并重叠的顶点
    #     bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
        
    #     # 创建网格和对象
    #     mesh = bpy.data.meshes.new(f"{name}_Mesh")
    #     bm.to_mesh(mesh)
    #     bm.free()
        
    #     pin_obj = bpy.data.objects.new(name, mesh)
        
    #     # 链接到当前场景
    #     scene = bpy.context.scene
    #     scene.collection.objects.link(pin_obj)
        
    #     return pin_obj
    
    def create_resistance_text(self, resistor: bpy.types.Object, resistance: float, 
                              tolerance: float, resistor_type_name: str = ""):
        """创建电阻值文本"""
        resistor_z = resistor.location.z
        resistor_length = resistor.dimensions.z
        
        # 构造文本内容
        if resistor_type_name:
            text_content = f"{resistor_type_name}: {format_resistance(resistance)} ±{tolerance:.1f}%"
        else:
            text_content = f"{format_resistance(resistance)} ±{tolerance:.1f}%"
        
        bpy.ops.object.text_add(location=(resistor_z + resistor_length/2 + 0.002, 0, 0))
        text_obj = bpy.context.active_object
        if not text_obj:
            return
            
        text_obj.name = "Resistance_Text"
        text_obj.data.body = text_content
        
        # 根据电阻尺寸调整文本大小
        if resistor.dimensions.x < 3.0:  # 小电阻
            text_obj.data.size = 1.0
        elif resistor.dimensions.x < 5.0:  # 中等电阻
            text_obj.data.size = 1.5
        else:  # 大电阻
            text_obj.data.size = 2.0
        
        text_obj.data.align_x = 'CENTER'
        text_obj.data.align_y = 'CENTER'
        
        text_obj.rotation_euler.x = math.pi/2  # 90度
        text_obj.rotation_euler.y = math.pi/2  # 90度
        
        # 如果文本太长，调整字体大小
        if len(text_content) > 20:
            text_obj.data.size = text_obj.data.size * 0.8
        
        text_mat = create_material("Text_Black", (0.1, 0.1, 0.1, 1.0), metallic=0.0, roughness=0.8)
        text_obj.data.materials.append(text_mat)
        
        text_obj.parent = resistor
        

# ==================== 面板类 ====================
class VIEW3D_PT_ResistorColorBand(Panel):
    """色环电阻生成器面板"""
    bl_label = "色环电阻生成器"
    bl_idname = "VIEW3D_PT_resistor_color_band"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电阻工具"
    bl_order = 1
    
    def draw(self, context):
        layout = self.layout
        props = context.scene.resistor_band_props
        
        # 输入参数部分
        box = layout.box()
        box.label(text="电阻参数", icon='SETTINGS')
        
        row = box.row()
        row.label(text="电阻值:")
        row.prop(props, "resistance", text="")
        
        # 公差选择
        row = box.row()
        row.label(text="公差:")
        row.prop(props, "tolerance", text="")
        
        # 解析当前公差值
        tolerance_str = props.tolerance.strip('%')
        try:
            tolerance_value = float(tolerance_str)
        except ValueError:
            tolerance_value = 5.0
        
        # 显示公差与电阻类型匹配规则
        if tolerance_value >= 5.0:
            row = box.row()
            row.alert = True
            row.label(text="公差≥5%，只能选择碳膜电阻", icon='ERROR')
        else:
            row = box.row()
            row.label(text="公差<5%，可选择高精度电阻类型", icon='INFO')
        
        # 色环类型
        row = box.row()
        row.label(text="色环类型:")
        row.prop(props, "band_type", expand=True)
        
        # 电阻类型选择
        row = box.row()
        row.label(text="电阻类型:")
        
        # 根据公差动态显示可用的电阻类型
        if tolerance_value >= 5.0:
            # 公差≥5%，只显示碳膜电阻
            row.prop(props, "resistor_type", text="")
            # 禁用其他选项
            row.enabled = False
        else:
            # 公差<5%，显示所有电阻类型
            row.prop(props, "resistor_type", text="")
        
        # 电阻尺寸
        row = box.row()
        row.label(text="电阻尺寸:")
        row.prop(props, "resistor_size", text="")
        
        # 显示电阻尺寸说明
        resistor_sizes = {
            'TINY_1_8W': "1/8W (直径2.5mm, 长度6.5mm)",
            'SMALL_1_4W': "1/4W (直径2.5mm, 长度6.5mm)",
            'MEDIUM_1_2W': "1/2W (直径3.2mm, 长度9mm)",
            'LARGE_3_4W': "3/4W (直径4.5mm, 长度12mm)",
            'LARGE_1W': "1W (直径5mm, 长度15mm)"
        }
        
        size_desc = resistor_sizes.get(props.resistor_size, "")
        if size_desc:
            row = box.row()
            row.label(text=f"尺寸: {size_desc}", icon='INFO')

        row = box.row()
        if not props.band_preview:
            bands = calculate_resistor_bands(props.resistance, tolerance_value, '4BAND' if props.band_type == '4BAND' else '5BAND')
            if bands:
                band_names = [band['color']['name'] for band in bands]
                band_preview = " - ".join(band_names)
            else:
                band_preview = "无法计算色环"
            row.label(text=f"色环: {band_preview}", icon='INFO')
        else:
            row.label(text=f"色环: {props.band_preview}", icon='INFO')
        
        layout.separator()
        
        # 引脚设置
        pin_box = layout.box()
        pin_box.label(text="引脚设置", icon='CON_PIVOT')
        
        row = pin_box.row()
        row.prop(props, "add_pins", text="添加引脚")
        
        if props.add_pins:
            row = pin_box.row()
            row.prop(props, "pin_length", text="引脚长度")
            
            # 显示引脚长度说明
            row = pin_box.row()
            row.label(text=f"引脚长度: {props.pin_length}mm", icon='EMPTY_AXIS')
        
        layout.separator()
        
        # 获取当前电阻类型信息
        resistor_info = RESISTOR_BODY_COLORS.get(props.resistor_type, RESISTOR_BODY_COLORS['CARBON'])
        
        # 操作按钮
        action_box = layout.box()
        # 检查是否允许生成
        tolerance_str = props.tolerance.strip('%')
        try:
            tolerance_value = float(tolerance_str)
        except ValueError:
            tolerance_value = 5.0
        
        resistor_info = RESISTOR_BODY_COLORS.get(props.resistor_type, RESISTOR_BODY_COLORS['CARBON'])
        tolerance_limit = resistor_info.get('tolerance_limit', 5.0)
        
        can_generate = True
        if tolerance_value >= 5.0 and props.resistor_type != 'CARBON':
            can_generate = False
        elif tolerance_value < tolerance_limit and props.resistor_type != 'CARBON':
            can_generate = False
        
        if can_generate:
            row = action_box.row()
            row.scale_y = 2.0
            row.operator("object.create_resistor_bands", text="生成色环电阻", icon='ADD')
        else:
            row = action_box.row()
            row.scale_y = 2.0
            row.alert = True
            row.label(text="电阻类型与公差不匹配，无法生成", icon='ERROR')
            
            # 显示修复建议
            if tolerance_value >= 5.0 and props.resistor_type != 'CARBON':
                action_box.label(text="请将电阻类型改为'碳膜电阻'")
            elif tolerance_value < tolerance_limit and props.resistor_type != 'CARBON':
                action_box.label(text=f"请将公差改为≥{tolerance_limit}%，或选择更高精度电阻")

# ==================== 注册和注销 ====================
classes = [
    ResistorColorBandProperties,
    OBJECT_OT_CreateResistor,
    VIEW3D_PT_ResistorColorBand,
]

def register():
    """注册插件"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.resistor_band_props = PointerProperty(type=ResistorColorBandProperties)
    
    print("电阻色环生成器已注册")

def unregister():
    """注销插件"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    try:
        del bpy.types.Scene.resistor_band_props
    except AttributeError:
        pass
    
    print("电阻色环生成器已注销")

# 如果直接运行，则注册插件
if __name__ == "__main__":
    register()