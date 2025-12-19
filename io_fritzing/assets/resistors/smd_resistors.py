import bpy
import bmesh
from mathutils import Vector, Matrix
import math
from typing import List, Tuple, Optional, Dict
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import FloatProperty, StringProperty, EnumProperty, IntProperty, BoolProperty, PointerProperty
from io_fritzing.assets.resistors.eia_96 import calculate_eia96_code
from io_fritzing.assets.utils.material import create_material

bl_info = {
    "name": "贴片电阻",
    "version": (1, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N > 电阻工具 > 贴片电阻",
    "description": "生成带有丝印的贴片电阻模型，支持E-24/E-96标准/EIA-96标准",
    "category": "3D View"
}

# ==================== 标准电阻系列 ====================
# E-24系列 (5% 公差)
E24_SERIES = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
]

# E-96系列 (1% 公差)
E96_SERIES = [
    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
    1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
    1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
    2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
    3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
    4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
    5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
    7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
]

# 贴片电阻封装尺寸 (单位: mm)
SMD_SIZES = {
    '0402': (1.0, 0.5, 0.35, 0.2),   # 长, 宽, 高, 焊盘长度
    '0603': (1.6, 0.8, 0.45, 0.3),   # 长, 宽, 高, 焊盘长度
    '0805': (2.0, 1.25, 0.5, 0.4),   # 长, 宽, 高, 焊盘长度
    '1206': (3.2, 1.6, 0.55, 0.5),   # 长, 宽, 高, 焊盘长度
    '1210': (3.2, 2.5, 0.55, 0.5),   # 长, 宽, 高, 焊盘长度
    '1812': (4.5, 3.2, 0.55, 0.6),   # 长, 宽, 高, 焊盘长度
    '2010': (5.0, 2.5, 0.55, 0.6),   # 长, 宽, 高, 焊盘长度
    '2512': (6.3, 3.2, 0.55, 0.7),   # 长, 宽, 高, 焊盘长度
}

# 丝印颜色映射
SILK_SCREEN_COLORS = {
    'white': (1.0, 1.0, 1.0, 1.0),    # 白色丝印
    'black': (0.0, 0.0, 0.0, 1.0),    # 黑色丝印
    'yellow': (1.0, 1.0, 0.0, 1.0),   # 黄色丝印
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

def get_nearest_standard_value(value: float, series: List[float] = E96_SERIES) -> Tuple[float, int]:
    """
    获取最接近的标准电阻值和对应的10的幂次
    
    返回: (标准值, 指数)
    """
    if value <= 0:
        return series[0], 0
    
    min_diff = float('inf')
    nearest_std = series[0]
    nearest_exp = 0
    
    for std in series:
        # 计算对数差值，找到最接近的10的幂次
        if value > 0 and std > 0:
            # 计算应该的指数
            exp = round(math.log10(value / std))
            # 计算缩放后的标准值
            scaled_std = std * (10 ** exp)
            # 计算相对误差
            diff = abs(math.log10(value) - math.log10(scaled_std))
            
            if diff < min_diff:
                min_diff = diff
                nearest_std = std
                nearest_exp = exp
    
    return nearest_std, nearest_exp

def calculate_smd_code(resistance: float, tolerance: float = 0.01, 
                      use_e96: bool = True) -> Dict:
    """
    计算贴片电阻的3位/4位数字代码
    
    返回字典包含:
    - digits_code: 数字代码字符串
    - standard_value: 标准电阻值
    - code_3digit: 3位数字代码
    - code_4digit: 4位数字代码
    - tolerance_percent: 公差百分比
    - relative_error: 相对误差百分比
    """
    if resistance <= 0:
        return {
            'digits_code': "000",
            'standard_value': 0,
            'code_3digit': '000',
            'code_4digit': '0000',
            'tolerance_percent': 5.0,
            'relative_error': 0.0
        }
    
    # 选择标准系列
    series = E96_SERIES if use_e96 else E24_SERIES
    
    # 获取最接近的标准值和指数
    std_value, exp = get_nearest_standard_value(resistance, series)
    
    # 计算有效数字和乘数
    # 将标准值缩放到1.00-9.99之间
    digits_float = std_value
    multiplier_exp = exp
    
    # 调整到1.00-9.99之间
    while digits_float >= 10.0:
        digits_float /= 10.0
        multiplier_exp += 1
    
    while digits_float < 1.0 and digits_float > 0:
        digits_float *= 10.0
        multiplier_exp -= 1
    
    # 确保是三位有效数字
    if digits_float >= 10.0:
        digits_float /= 10.0
        multiplier_exp += 1
    
    if digits_float < 1.0:
        digits_float *= 10.0
        multiplier_exp -= 1
    
    # 四舍五入到适当的小数位数
    if use_e96:
        # E-96系列: 保留2位小数
        digits_float = round(digits_float, 2)
    else:
        # E-24系列: 保留1位小数
        digits_float = round(digits_float, 1)
    
    if digits_float >= 10.0:
        digits_float /= 10.0
        multiplier_exp += 1
    
    # 计算数字代码
    if use_e96:
        # E-96系列: 4位数字代码 (前3位有效数字 + 1位乘数)
        # 获取三位有效数字
        digit1 = int(digits_float)
        digit2 = int((digits_float * 10) % 10)
        digit3 = int((digits_float * 100) % 10)
        
        # 处理乘数为0的特殊情况
        if multiplier_exp == 0:
            code_4digit = f"{digit1}{digit2}{digit3}0"
        else:
            code_4digit = f"{digit1}{digit2}{digit3}{multiplier_exp}"
        
        # 3位数字代码 (E-24风格，精度较低)
        digits_float_e24 = round(digits_float, 1)
        if digits_float_e24 >= 10.0:
            digits_float_e24 /= 10.0
            multiplier_exp_e24 = multiplier_exp + 1
        else:
            multiplier_exp_e24 = multiplier_exp
        
        digit1_e24 = int(digits_float_e24)
        digit2_e24 = int((digits_float_e24 * 10) % 10)
        
        if multiplier_exp_e24 == 0:
            code_3digit = f"{digit1_e24}{digit2_e24}0"
        else:
            code_3digit = f"{digit1_e24}{digit2_e24}{multiplier_exp_e24}"
        
        digits_code = code_4digit
        
    else:
        # E-24系列: 3位数字代码 (前2位有效数字 + 1位乘数)
        digit1 = int(digits_float)
        digit2 = int((digits_float * 10) % 10)
        
        if multiplier_exp == 0:
            code_3digit = f"{digit1}{digit2}0"
        else:
            code_3digit = f"{digit1}{digit2}{multiplier_exp}"
        
        # 4位数字代码 (E-96风格，精度较低)
        code_4digit = f"{digit1}{digit2}0{multiplier_exp}"
        digits_code = code_3digit
    
    # 计算标准电阻值
    standard_value = (digits_float) * (10 ** multiplier_exp)
    
    # 计算相对误差
    if resistance > 0:
        relative_error = ((standard_value - resistance) / resistance) * 100
    else:
        relative_error = 0.0
    
    # 公差百分比
    tolerance_percent = tolerance * 100
    
    return {
        'digits_code': digits_code,
        'standard_value': standard_value,
        'code_3digit': code_3digit,
        'code_4digit': code_4digit,
        'tolerance_percent': tolerance_percent,
        'relative_error': relative_error,
        'is_e96': use_e96
    }

# ==================== 属性组 ====================
class SMDResistorProperties(PropertyGroup):
    """贴片电阻属性组"""
    
    # 基本参数
    resistance: FloatProperty(
        name="电阻值",
        description="电阻值 (单位: Ω)",
        default=4700.0,
        min=0.001,
        max=10000000.0,
        precision=4,
        step=100
    )  # type: ignore 忽略类型检查器的类型提示错误
    
    tolerance: EnumProperty(
        name="公差",
        description="选择电阻公差百分比",
        items=[
            ('0.5%', "0.5%", "0.5% 公差"),
            ('1%', "1%", "1% 公差"),
            ('2%', "2%", "2% 公差"),
            ('5%', "5%", "5% 公差"),
            ('10%', "10%", "10% 公差"),
        ],
        default='1%',
        update=lambda self, context: self.on_value_update(context)
    )  # type: ignore 忽略类型检查器的类型提示错误
    
    # 封装选择
    package_size: EnumProperty(
        name="封装尺寸",
        description="选择贴片电阻封装尺寸",
        items=[
            ('0402', "0402 (1.0×0.5mm)", "超小型封装"),
            ('0603', "0603 (1.6×0.8mm)", "常用小型封装"),
            ('0805', "0805 (2.0×1.25mm)", "常用标准封装"),
            ('1206', "1206 (3.2×1.6mm)", "标准功率封装"),
            ('1210', "1210 (3.2×2.5mm)", "中功率封装"),
            ('1812', "1812 (4.5×3.2mm)", "大功率封装"),
            ('2010', "2010 (5.0×2.5mm)", "大功率封装"),
            ('2512', "2512 (6.3×3.2mm)", "超大功率封装"),
        ],
        default='0805',
        update=lambda self, context: self.on_value_update(context)
    )  # type: ignore 忽略类型检查器的类型提示错误
    
    # 标准系列
    standard_series: EnumProperty(
        name="标准系列",
        description="选择电阻标准系列",
        items=[
            ('E24', "E-24 (5%)", "E-24系列，5%公差，3位数字代码"),
            ('E96', "E-96 (1%)", "E-96系列，1%公差，4位数字代码"),
            ('EIA-96', "EIA-96 (1%)", "EIA-96系列，1%公差，2位数字1位字母代码"),
        ],
        default='E96'
    )  # type: ignore 忽略类型检查器的类型提示错误
    
    def on_value_update(self, context):
        """当封装尺寸改变时的回调函数"""
        # 根据封装尺寸自动设置标准系列
        # 大封装（0805及以上）建议使用E-96
        if self.package_size in ['0805', '1206', '1210', '1812', '2010', '2512']:
            self.standard_series = 'E96'
        elif self.tolerance == '1%':
            self.standard_series = 'EIA-96'
        else:
            self.standard_series = 'E24'


# ==================== 操作类 ====================
class SMD_OT_GenerateResistor(Operator):
    """生成带有丝印的贴片电阻"""
    bl_idname = "smd.generate_resistor"
    bl_label = "生成贴片电阻"
    bl_description = "生成带有丝印的贴片电阻模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        props = context.scene.smd_resistor_props
        
        # 计算电阻代码
        use_e96 = (props.standard_series == 'E96')
        result = calculate_smd_code(props.resistance, get_tolerance_value(props.tolerance), use_e96)
        
        # 获取封装尺寸
        if props.package_size in SMD_SIZES:
            length_mm, width_mm, height_mm, pad_length_mm = SMD_SIZES[props.package_size]
        else:
            # 默认0805封装
            length_mm, width_mm, height_mm, pad_length_mm = SMD_SIZES['0805']
        
        # 创建电阻集合
        code_to_show = result['code_4digit'] if use_e96 else result['code_3digit']
        collection_name = f"SMD_Resistor_{props.package_size}_{code_to_show}"
        
        # 如果集合已存在，先删除
        if collection_name in bpy.data.collections:
            old_collection = bpy.data.collections[collection_name]
            for obj in list(old_collection.objects):
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(old_collection)
        
        collection = bpy.data.collections.new(collection_name)
        context.scene.collection.children.link(collection)
        
        # 创建电阻主体
        self.create_resistor_body(collection, props, length_mm, width_mm, height_mm, pad_length_mm)
        
        # 创建焊盘
        self.create_pads(collection, props, length_mm, width_mm, height_mm, pad_length_mm)
        
        # 创建丝印
        # if props.show_silk_screen:
        self.create_silk_screen(collection, props, code_to_show, length_mm, width_mm, height_mm)
        
        # 选择所有生成的对象
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.objects:
            obj.select_set(True)
        if collection.objects:
            context.view_layer.objects.active = collection.objects[0]
        
        # 报告结果
        self.report({'INFO'}, f"已生成{props.package_size}电阻: {format_resistance(props.resistance)} 丝印: {code_to_show}")
        return {'FINISHED'}
    
    def create_resistor_body(self, collection, props, length_mm, width_mm, height_mm, pad_length_mm):
        """创建电阻主体"""
        # 转换为Blender单位 (1单位 = 1米)
        scale = 0.001
        length = length_mm * scale
        width = width_mm * scale
        height = height_mm * scale
        
        # 创建材质
        body_mat = create_material("Resistor_Body", (0.9, 0.9, 0.9), metallic=0.0, roughness=0.8)
        
        # 创建网格
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        
        # 缩放
        for v in bm.verts:
            v.co.x *= length
            v.co.y *= width
            v.co.z *= height
        
        # 创建网格对象
        mesh = bpy.data.meshes.new("Resistor_Body")
        bm.to_mesh(mesh)
        bm.free()
        
        obj = bpy.data.objects.new("Resistor_Body", mesh)
        collection.objects.link(obj)
        
        # 应用材质
        obj.data.materials.append(body_mat)
        
        # # 设置位置和旋转
        # obj.rotation_euler.z = math.radians(props.rotation)
        # obj.location.z = props.position
        
        return obj
    
    def create_pads(self, collection, props, length_mm, width_mm, height_mm, pad_length_mm):
        """创建焊盘"""
        scale = 0.001
        length = length_mm * scale
        width = width_mm * scale
        height = height_mm * scale
        pad_length = pad_length_mm * scale
        
        # 创建材质
        pad_mat = create_material("Resistor_Pad", (0.85, 0.55, 0.25), metallic=0.8, roughness=0.3)
        
        # 左焊盘
        bm_left = bmesh.new()
        bmesh.ops.create_cube(bm_left, size=1.0)
        
        for v in bm_left.verts:
            v.co.x *= pad_length
            v.co.y *= width * 1.1
            v.co.z *= height * 0.8
            v.co.x -= (length/2 + pad_length/2)
        
        mesh_left = bpy.data.meshes.new("Left_Pad")
        bm_left.to_mesh(mesh_left)
        bm_left.free()
        
        obj_left = bpy.data.objects.new("Left_Pad", mesh_left)
        collection.objects.link(obj_left)
        obj_left.data.materials.append(pad_mat)
        
        # 右焊盘
        bm_right = bmesh.new()
        bmesh.ops.create_cube(bm_right, size=1.0)
        
        for v in bm_right.verts:
            v.co.x *= pad_length
            v.co.y *= width * 1.1
            v.co.z *= height * 0.8
            v.co.x += (length/2 + pad_length/2)
        
        mesh_right = bpy.data.meshes.new("Right_Pad")
        bm_right.to_mesh(mesh_right)
        bm_right.free()
        
        obj_right = bpy.data.objects.new("Right_Pad", mesh_right)
        collection.objects.link(obj_right)
        obj_right.data.materials.append(pad_mat)
        
        # 设置位置和旋转
        # for obj in [obj_left, obj_right]:
        #     obj.rotation_euler.z = math.radians(props.rotation)
        #     obj.location.z = props.position
        
        return [obj_left, obj_right]
    
    def create_silk_screen(self, collection, props, code, length_mm, width_mm, height_mm):
        """创建丝印"""
        scale = 0.001
        length = length_mm * scale
        width = width_mm * scale
        height = height_mm * scale
        
        # 获取丝印颜色
        color = SILK_SCREEN_COLORS.get('black')
        silk_mat = create_material("Silk_Screen", color[:4], metallic=0.0, roughness=0.9)
        
        # 创建文本曲线
        curve_data = bpy.data.curves.new(type="FONT", name="Silk_Screen_Text")
        curve_data.body = code
        curve_data.align_x = 'CENTER'
        curve_data.align_y = 'CENTER'
        curve_data.size = width * 0.5
        
        # 尝试使用默认字体
        if bpy.data.fonts:
            curve_data.font = bpy.data.fonts[0]
        
        # 创建文本对象
        text_obj = bpy.data.objects.new("Silk_Screen_Text", curve_data)
        collection.objects.link(text_obj)
        
        # 设置文本对象的位置、旋转和缩放
        # text_obj.rotation_euler.z = math.radians(props.rotation)
        # text_obj.location.z = props.position + height/2 + 0.001
        text_obj.scale = (1, 1, 0.1)
        
        # 转换为网格
        text_mesh = bpy.data.meshes.new_from_object(text_obj)
        
        # 创建新的网格对象
        mesh_obj = bpy.data.objects.new("Silk_Screen", text_mesh)
        collection.objects.link(mesh_obj)
        
        # 设置网格对象的位置、旋转
        # mesh_obj.rotation_euler.z = math.radians(props.rotation)
        # mesh_obj.location.z = props.position + height/2 + 0.001
        
        # 应用材质
        mesh_obj.data.materials.append(silk_mat)
        
        # 删除文本对象
        bpy.data.objects.remove(text_obj, do_unlink=True)
        
        return mesh_obj

def get_tolerance_value(tolerance_enum: str) -> float:
    """从枚举值获取公差百分比的小数形式"""
    tolerance_map = {
        '0.5%': 0.005,
        '1%': 0.01,
        '2%': 0.02,
        '5%': 0.05,
        '10%': 0.10
    }
    return tolerance_map.get(tolerance_enum, 0.01)  # 默认1%

# ==================== 面板类 ====================
class VIEW3D_PT_SMDResistorGenerator(Panel):
    """贴片电阻生成器面板"""
    bl_label = "贴片电阻"
    bl_idname = "VIEW3D_PT_smd_resistor_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电阻工具"
    bl_order = 1
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        props = bpy.context.scene.smd_resistor_props
        
        # 输入参数部分
        box = layout.box()
        box.label(text="电阻参数", icon='SETTINGS')
        
        # 电阻值
        row = box.row()
        row.label(text="电阻值:")
        row.prop(props, "resistance", text="")
        
        # 公差
        row = box.row()
        row.label(text="公差:")
        row.prop(props, "tolerance", text="")
        
        # 封装尺寸
        row = box.row()
        row.label(text="封装尺寸:")
        row.prop(props, "package_size", text="")
        
        layout.separator()
        
        # 实时计算结果
        tolerance = get_tolerance_value(props.tolerance)
        if tolerance == 0.01:
            if props.package_size == '0603':
                eia96_result = calculate_eia96_code(props.resistance)
                result = {
                            'digits_code': eia96_result['eia96_mark'],
                            'standard_value': eia96_result['standard_value'],
                            'code_3digit': '000',
                            'code_4digit': '0000',
                            'tolerance_percent': 1.0,
                            'relative_error': eia96_result['relative_error']
                        }
            elif props.package_size == '0402':
                eia96_result = calculate_eia96_code(props.resistance)
                result = {
                            'digits_code': None,
                            'standard_value': eia96_result['standard_value'],
                            'code_3digit': '000',
                            'code_4digit': '0000',
                            'tolerance_percent': 1.0,
                            'relative_error': eia96_result['relative_error']
                        }
            else:
                result = calculate_smd_code(props.resistance, tolerance, True)
        else:
            result = calculate_smd_code(props.resistance, tolerance, False)
        
        result_box = layout.box()
        result_box.label(text="计算结果", icon='DRIVER')
        
        row = result_box.row()
        row.label(text="使用标准:")
        row.label(text=f"{props.standard_series}")
        # 显示标准值
        row = result_box.row()
        row.label(text="标准值:")
        row.label(text=f"{format_resistance(result['standard_value'])}")
        
        # 显示丝印代码
        row = result_box.row()
        row.label(text="丝印代码:")

        if result['code_4digit'] != '0000':        
            row.label(text=result['code_4digit'])
        elif result['code_3digit'] != '000':
            row.label(text=result['code_3digit'])
        elif result['digits_code'] is not None:
            row.label(text=result['digits_code'])
        
        # 显示公差
        row = result_box.row()
        row.label(text="公差:")
        row.label(text=f"±{result['tolerance_percent']}%")
        
        row = result_box.row()
        row.scale_y = 1.5
        row.operator("smd.generate_resistor", text="生成电阻")
       

# ==================== 注册和注销 ====================
classes = [
    SMDResistorProperties,
    SMD_OT_GenerateResistor,
    VIEW3D_PT_SMDResistorGenerator,
]

def register():
    """注册插件"""
    # 注册属性组
    for cls in classes:
        bpy.utils.register_class(cls)
    
    bpy.types.Scene.smd_resistor_props = PointerProperty(type=SMDResistorProperties)

    print("贴片电阻生成器已注册")

def unregister():
    """注销插件"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 清理属性组
    try:
        del bpy.types.Scene.smd_resistor_props
    except AttributeError:
        pass
    
    print("贴片电阻生成器已注销")

# 如果直接运行，则注册插件
if __name__ == "__main__":
    register()