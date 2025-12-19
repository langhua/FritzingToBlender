import bpy
import bmesh
from mathutils import Matrix
import math
from typing import List, Tuple
import os
from bpy.utils import previews
from bpy.types import Scene, Mesh
from io_fritzing.assets.utils.material import create_material


bl_info = {
    "name": "色环电阻生成器",
    "version": (5, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N > 电阻工具",
    "description": "生成四色环/五色环电阻模型，支持实时色环预览和选择预览",
    "category": "3D View"
}

# ==================== 图标管理器 ====================
class ResistorIconManager:
    """色环电阻图标管理器"""
    _icons = None
    _icon_dir = None
    if hasattr(Scene, 'resistor_icon_path'):
        _icon_dir = getattr(Scene, 'resistor_icon_path')
    
    @classmethod
    def set_icon_directory(cls, directory):
        """设置图标目录"""
        cls._icon_dir = directory
    
    @classmethod
    def load_icons(cls):
        """加载所有色环电阻图标"""
        if cls._icons is not None:
            return cls._icons
        
        # 创建图标集合
        cls._icons = previews.new()
        
        # 定义需要加载的颜色图标
        color_icons = [
            'black', 'brown', 'red', 'orange', 'yellow',
            'green', 'blue', 'violet', 'gray', 'white',
            'gold', 'silver'
        ]
        
        # 如果没有指定目录，尝试在当前目录查找
        if cls._icon_dir is None:
            # 尝试多个可能的目录
            possible_dirs = [
                os.path.join(os.path.dirname(__file__), "resistor_color_icons"),
                os.path.join(os.path.dirname(__file__), "icons"),
                os.path.join(os.path.expanduser("~"), "resistor_color_icons"),
                os.path.dirname(__file__)  # 插件目录本身
            ]
            
            for dir_path in possible_dirs:
                if os.path.exists(dir_path):
                    # 检查是否有图标文件
                    test_icon = os.path.join(dir_path, "icon_black.png")
                    if os.path.exists(test_icon):
                        cls._icon_dir = dir_path
                        break
        
        if cls._icon_dir and os.path.exists(cls._icon_dir):
            print(f"加载图标从目录: {cls._icon_dir}")
            
            for color in color_icons:
                icon_path = os.path.join(cls._icon_dir, f"icon_{color}.png")
                if os.path.exists(icon_path):
                    try:
                        cls._icons.load(color.upper(), icon_path, 'IMAGE')
                        print(f"  加载图标: {color}")
                    except Exception as e:
                        print(f"  加载图标失败 {color}: {e}")
                else:
                    print(f"  图标文件不存在: {icon_path}")
        else:
            print("警告: 未找到图标目录，将使用Blender内置图标")
        
        return cls._icons
    
    @classmethod
    def get_icon_id(cls, color_name):
        """获取颜色的图标ID"""
        icons = cls.load_icons()
        
        # 处理颜色名称（移除_tol后缀）
        base_color = color_name.replace('_tol', '').upper()
        
        if base_color in icons:
            return icons.__getattribute__(base_color).icon_id
        
        # 回退到内置图标
        return cls.get_fallback_icon(color_name)
    
    @classmethod
    def get_fallback_icon(cls, color_name):
        """获取回退图标（Blender内置）"""
        # 映射到Blender内置图标
        color_icon_map = {
            'black': 'COLORSET_01_VEC',
            'brown': 'COLORSET_02_VEC',
            'red': 'COLORSET_03_VEC',
            'orange': 'COLORSET_04_VEC',
            'yellow': 'COLORSET_05_VEC',
            'green': 'COLORSET_06_VEC',
            'blue': 'COLORSET_07_VEC',
            'violet': 'COLORSET_08_VEC',
            'gray': 'COLORSET_09_VEC',
            'white': 'COLORSET_10_VEC',
            'gold': 'COLORSET_11_VEC',
            'silver': 'COLORSET_12_VEC',
        }
        
        base_color = color_name.replace('_tol', '')
        return color_icon_map.get(base_color, 'COLORSET_01_VEC')
    
    @classmethod
    def unload_icons(cls):
        """卸载图标"""
        if cls._icons is not None:
            previews.remove(cls._icons)
            cls._icons = None

# ==================== 颜色映射 ====================
FIVE_COLOR_CODES = {
    # 数字颜色 (0-9, 乘数)
    'black':   {'rgb': (0.1, 0.1, 0.1),  'digit': 0, 'multiplier': 1},
    'brown':   {'rgb': (0.4, 0.2, 0.1),  'digit': 1, 'multiplier': 10},
    'red':     {'rgb': (0.8, 0.1, 0.1),  'digit': 2, 'multiplier': 100},
    'orange':  {'rgb': (1.0, 0.5, 0.1),  'digit': 3, 'multiplier': 1000},
    'yellow':  {'rgb': (1.0, 1.0, 0.0),  'digit': 4, 'multiplier': 10000},
    'green':   {'rgb': (0.0, 0.5, 0.0),  'digit': 5, 'multiplier': 100000},
    'blue':    {'rgb': (0.1, 0.1, 0.8),  'digit': 6, 'multiplier': 1000000},
    'violet':  {'rgb': (0.6, 0.1, 0.8),  'digit': 7, 'multiplier': 10000000},
    'gray':    {'rgb': (0.5, 0.5, 0.5),  'digit': 8, 'multiplier': 0.01},
    'white':   {'rgb': (1.0, 1.0, 1.0),  'digit': 9, 'multiplier': 0.1},
    
    # 公差颜色
    'brown_tol':   {'rgb': (0.4, 0.2, 0.1),  'tolerance': 0.01},
    'red_tol':     {'rgb': (0.8, 0.1, 0.1),  'tolerance': 0.02},
    'green_tol':   {'rgb': (0.0, 0.5, 0.0),  'tolerance': 0.005},
    'blue_tol':    {'rgb': (0.1, 0.1, 0.8),  'tolerance': 0.0025},
    'violet_tol':  {'rgb': (0.6, 0.1, 0.8),  'tolerance': 0.001},
    'gray_tol':    {'rgb': (0.5, 0.5, 0.5),  'tolerance': 0.0005},
    'gold_tol':    {'rgb': (0.8, 0.6, 0.1),  'tolerance': 0.05},
    'silver_tol':  {'rgb': (0.8, 0.8, 0.8),  'tolerance': 0.10},
    'NONE':        {'rgb': (0.9, 0.9, 0.9),  'tolerance': 0.20},
}

FOUR_COLOR_CODES = {
    # 数字颜色 (0-9, 乘数)
    'black':   {'rgb': (0.1, 0.1, 0.1),  'digit': 0, 'multiplier': 1},
    'brown':   {'rgb': (0.4, 0.2, 0.1),  'digit': 1, 'multiplier': 10},
    'red':     {'rgb': (0.8, 0.1, 0.1),  'digit': 2, 'multiplier': 100},
    'orange':  {'rgb': (1.0, 0.5, 0.1),  'digit': 3, 'multiplier': 1000},
    'yellow':  {'rgb': (1.0, 1.0, 0.0),  'digit': 4, 'multiplier': 10000},
    'green':   {'rgb': (0.0, 0.5, 0.0),  'digit': 5, 'multiplier': 100000},
    'blue':    {'rgb': (0.1, 0.1, 0.8),  'digit': 6, 'multiplier': 1000000},
    'violet':  {'rgb': (0.6, 0.1, 0.8),  'digit': 7, 'multiplier': 10000000},
    'gray':    {'rgb': (0.5, 0.5, 0.5),  'digit': 8, 'multiplier': 0.01},
    'white':   {'rgb': (1.0, 1.0, 1.0),  'digit': 9, 'multiplier': 0.1},
    
    # 公差颜色
    'red_tol':     {'rgb': (0.8, 0.1, 0.1),  'tolerance': 0.02},   # 2%
    'gold_tol':   {'rgb': (0.8, 0.6, 0.1),  'tolerance': 0.05},   # 5%
    'silver_tol':  {'rgb': (0.8, 0.8, 0.8),  'tolerance': 0.10},   # 10%
    'NONE':    {'rgb': (0.9, 0.9, 0.9),  'tolerance': 0.20},   # 20%
}


# 中文颜色名称
COLOR_NAMES_CN = {
    'black': '黑色',
    'brown': '棕色',
    'red': '红色',
    'orange': '橙色',
    'yellow': '黄色',
    'green': '绿色',
    'blue': '蓝色',
    'violet': '紫色',
    'gray': '灰色',
    'white': '白色',
    'gold': '金色',
    'silver': '银色',
}

# 四色环电阻标准值
E12_SERIES = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
E24_SERIES = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
              3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

# 五色环精密电阻标准值
E48_SERIES = [
    1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69,
    1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01,
    3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36,
    5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53
]

def get_nearest_standard_value(value: float, series: List[float] = E24_SERIES) -> Tuple[float, int]:
    """
    获取最接近的标准电阻值和对应的10的幂次
    
    考虑标准值可以乘以10的幂次
    例如：1000Ω = 1.0 * 10^3
    返回：(标准值, 指数)
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
        else:
            # 处理边界情况
            diff = abs(value - std)
            if diff < min_diff:
                min_diff = diff
                nearest_std = std
                nearest_exp = 0
    
    return nearest_std, nearest_exp


def calculate_color_bands(resistance: float, tolerance: float = 0.05, is_five_band: bool = False) -> Tuple[List[str], str]:
    """
    计算电阻的色环颜色
    
    四色环规则：两位有效数字 + 乘数 + 公差
    五色环规则：三位有效数字 + 乘数 + 公差
    
    返回: (前几个色环的颜色名列表, 公差色环颜色名)
    """
    if resistance <= 0:
        if is_five_band:
            return ['black', 'black', 'black', 'black'], 'brown_tol'
        else:
            return ['black', 'black', 'black'], 'gold'
    
    # 标准化电阻值
    if is_five_band:
        series = E48_SERIES
    else:
        series = E24_SERIES
    
    std_resistance, exp = get_nearest_standard_value(resistance, series)
    
    if is_five_band:
        # 五色环：三位有效数字
        # 确保标准值在1.00到9.99之间
        value = std_resistance
        exponent = exp
        
        # 调整到1.00-9.99之间
        while value >= 10.0:
            value /= 10.0
            exponent += 1
        
        while value < 1.0 and value > 0:
            value *= 10.0
            exponent -= 1
        
        # 获取三位有效数字
        if value >= 10.0:
            value /= 10.0
            exponent += 1
        
        if value >= 10.0:
            value /= 10.0
            exponent += 1
        
        if value < 1.0:
            value *= 10.0
            exponent -= 1
        
        # 四舍五入到两位小数（三位有效数字）
        value = round(value, 2)
        
        if value >= 10.0:
            value /= 10.0
            exponent += 1
        
        # 获取三个数字
        digit1 = int(value)
        digit2 = int((value * 10) % 10)
        digit3 = int((value * 100) % 10)
        
        # 获取乘数
        multiplier_exp = exponent - 2  # 因为有三位数字
        
        # 查找颜色
        colors = []
        for digit in [digit1, digit2, digit3]:
            color_found = None
            for color_name, data in FIVE_COLOR_CODES.items():
                if 'digit' in data and data['digit'] == digit:
                    color_found = color_name
                    break
            if color_found:
                colors.append(color_found)
            else:
                colors.append('black')  # 默认黑色
        
        # 乘数环
        color4 = None
        if -2 <= multiplier_exp <= 9:
            for color_name, data in FIVE_COLOR_CODES.items():
                if 'multiplier' in data:
                    if multiplier_exp >= 0:
                        if data['digit'] == multiplier_exp:
                            color4 = color_name
                            break
                    else:
                        if multiplier_exp == -1 and color_name == 'white':
                            color4 = color_name
                            break
                        elif multiplier_exp == -2 and color_name == 'gray':
                            color4 = color_name
                            break
        
        if color4:
            colors.append(color4)
        else:
            colors.append('black')  # 默认黑色
    else:
        # 四色环：两位有效数字
        # 确保标准值在1.0到9.9之间
        value = std_resistance
        exponent = exp
        
        # 调整到1.0-9.9之间
        while value >= 10.0:
            value /= 10.0
            exponent += 1
        
        while value < 1.0 and value > 0:
            value *= 10.0
            exponent -= 1
        
        # 获取两位有效数字
        if value >= 10.0:
            value /= 10.0
            exponent += 1
        
        if value < 1.0:
            value *= 10.0
            exponent -= 1
        
        # 四舍五入到一位小数（两位有效数字）
        value = round(value, 1)
        
        if value >= 10.0:
            value /= 10.0
            exponent += 1
        
        # 获取两个数字
        digit1 = int(value)
        digit2 = int(round((value - digit1) * 10))
        
        # 处理进位
        if digit2 == 10:
            digit1 += 1
            digit2 = 0
            if digit1 == 10:
                digit1 = 1
                exponent += 1
        
        # 获取乘数
        multiplier_exp = exponent - 1  # 因为有两位数字
        
        # 查找颜色
        colors = []
        for digit in [digit1, digit2]:
            color_found = None
            for color_name, data in FOUR_COLOR_CODES.items():
                if 'digit' in data and data['digit'] == digit:
                    color_found = color_name
                    break
            if color_found:
                colors.append(color_found)
            else:
                colors.append('black')  # 默认黑色
        
        # 乘数环
        color3 = None
        if -2 <= multiplier_exp <= 9:
            for color_name, data in FOUR_COLOR_CODES.items():
                if 'multiplier' in data:
                    if multiplier_exp >= 0:
                        if data['digit'] == multiplier_exp:
                            color3 = color_name
                            break
                    else:
                        if multiplier_exp == -1 and color_name == 'white':
                            color3 = color_name
                            break
                        elif multiplier_exp == -2 and color_name == 'gray':
                            color3 = color_name
                            break
        
        if color3:
            colors.append(color3)
        else:
            colors.append('black')  # 默认黑色
    
    # 公差环
    tolerance_color = 'gold_tol'  # 默认5%
    
    if tolerance <= 0.0005:  # 0.05%
        tolerance_color = 'gray_tol'
    elif tolerance <= 0.001:  # 0.1%
        tolerance_color = 'violet_tol'
    elif tolerance <= 0.0025:  # 0.25%
        tolerance_color = 'blue_tol'
    elif tolerance <= 0.005:  # 0.5%
        tolerance_color = 'green_tol'
    elif tolerance <= 0.01:  # 1%
        tolerance_color = 'brown_tol'
    elif tolerance <= 0.02:  # 2%
        tolerance_color = 'red_tol'
    elif tolerance <= 0.05:  # 5%
        tolerance_color = 'gold_tol'
    elif tolerance <= 0.10:  # 10%
        tolerance_color = 'silver_tol'
    
    return colors, tolerance_color


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

def get_color_display_name(color_name: str) -> str:
    """获取颜色的显示名称"""
    base_name = color_name.replace('_tol', '')
    return COLOR_NAMES_CN.get(base_name, base_name.capitalize())

def get_color_rgb(band_count: int, color_name: str) -> Tuple[float, float, float]:
    """获取颜色的RGB值"""
    if band_count == 4:
        color_codes = FOUR_COLOR_CODES
    else:
        color_codes = FIVE_COLOR_CODES
    if color_name in color_codes:
        return color_codes[color_name]['rgb']
    return (0.5, 0.5, 0.5)  # 默认灰色

# ==================== 操作类 ====================
class RESISTOR_OT_GenerateFourBand(bpy.types.Operator):
    """生成四色环电阻"""
    bl_idname = "resistor.generate_four_band"
    bl_label = "生成四色环电阻"
    bl_description = "生成四色环电阻模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 清理场景
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False, confirm=False)
        
        if context and context.scene:
            resistance = getattr(context.scene, 'four_band_resistance')
            if hasattr(context.scene, 'four_band_resistor_unit'):
                if getattr(context.scene, 'four_band_resistor_unit') == 'kΩ':
                    resistance *= 1000
                elif getattr(context.scene, 'four_band_resistor_unit') == 'MΩ':
                    resistance *= 1000000
            if hasattr(context.scene, 'four_band_tolerance'):
                tolerance = getattr(context.scene, 'four_band_tolerance')
            if hasattr(context.scene, 'four_band_rated_power'):
                rated_power = getattr(context.scene, 'four_band_rated_power')

        dims = get_dimensions_from_power(rated_power)
        # 碳膜电阻（米色体）
        dims['body_color'] = (0.9, 0.7, 0.4)
        
        # 计算色环颜色
        colors, tolerance_color = calculate_color_bands(resistance, tolerance/100.0, False)
        display_value = format_resistance(resistance)
        
        # 创建集合
        collection_name = f"四色环电阻_{display_value}"
        create_axial_resistor(collection_name, dims, colors, tolerance_color)
        
        self.report({'INFO'}, f"已生成四色环电阻: {display_value} (±{tolerance}%)")
        return {'FINISHED'}

def get_dimensions_from_power(rated_power: float) -> dict:
    """根据额定功率获取尺寸参数"""
    dims = {}
    if rated_power == '1W':
        dims['body_length'] = 12.5
        dims['body_diameter'] = 5.0
        dims['band_width'] = 1.2
        dims['band_gap'] = 0.7
        dims['start_offset'] = 1.5
        dims['lead_length'] = 25.0
        dims['lead_diameter'] = 0.8
        dims['insertion_depth'] = 0.6
    elif rated_power == '1_4W':
        dims['body_length'] = 6.5
        dims['body_diameter'] = 2.5
        dims['band_width'] = 0.45
        dims['band_gap'] = 0.3
        dims['start_offset'] = 0.6
        dims['lead_length'] = 25.0
        dims['lead_diameter'] = 0.6
        dims['insertion_depth'] = 0.4
    elif rated_power == '1_2W':
        dims['body_length'] = 8.5
        dims['body_diameter'] = 3.2
        dims['band_width'] = 0.8
        dims['band_gap'] = 0.4
        dims['start_offset'] = 0.8
        dims['lead_length'] = 25.0
        dims['lead_diameter'] = 0.7
        dims['insertion_depth'] = 0.5
    else:  # 1_8W
        dims['body_length'] = 3.5
        dims['body_diameter'] = 1.8
        dims['band_width'] = 0.25
        dims['band_gap'] = 0.18
        dims['start_offset'] = 0.4
        dims['lead_length'] = 25.0
        dims['lead_diameter'] = 0.5
        dims['insertion_depth'] = 0.3

    return dims


class RESISTOR_OT_GenerateFiveBand(bpy.types.Operator):
    """生成五色环精密电阻"""
    bl_idname = "resistor.generate_five_band"
    bl_label = "生成五色环电阻"
    bl_description = "生成五色环精密电阻模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 清理场景
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False, confirm=False)

        if context and context.scene:
            resistance = getattr(context.scene, 'five_band_resistance')
            if hasattr(context.scene, 'five_band_resistor_unit'):
                if getattr(context.scene, 'five_band_resistor_unit') == 'kΩ':
                    resistance *= 1000
                elif getattr(context.scene, 'five_band_resistor_unit') == 'MΩ':
                    resistance *= 1000000

            if hasattr(context.scene, 'five_band_tolerance'):
                tolerance = getattr(context.scene, 'five_band_tolerance')
            if hasattr(context.scene, 'five_band_resistor_type'):
                resistor_type = getattr(context.scene, 'five_band_resistor_type')
            if hasattr(context.scene, 'five_band_rated_power'):
                rated_power = getattr(context.scene, 'five_band_rated_power')

        dims = get_dimensions_from_power(rated_power)
        if resistor_type == 'metal_film':
            # 金属膜电阻（蓝色体）
            dims['body_color'] = (0.1, 0.3, 0.7)
        else:  
            # 碳膜电阻（米色体）
            dims['body_color'] = (0.9, 0.7, 0.4)

        # 计算色环颜色
        colors, tolerance_color = calculate_color_bands(resistance, tolerance/100.0, True)
        display_value = format_resistance(resistance)
        
        # 创建集合
        collection_name = f"五色环电阻_{display_value}"
        collection, obj_body = create_axial_resistor(collection_name, dims, colors, tolerance_color)

        self.report({'INFO'}, f"已生成五色环电阻: {display_value} (±{tolerance}%)")
        return {'FINISHED'}

def create_axial_resistor(collection_name, dims, colors, tolerance_color):
    """创建轴向电阻"""
    # 创建集合
    collection = bpy.data.collections.new(collection_name)
    if bpy.context:
        bpy.context.scene.collection.children.link(collection)
    
    # 创建材质
    body_mat = create_material("Resistor_Body", (0.9, 0.7, 0.4), metallic=0.0, roughness=0.7)
    end_cap_mat = create_material("End_Cap", (0.7, 0.7, 0.7), metallic=0.9, roughness=0.2)
    
    # 创建电阻体
    bm_body = bmesh.new()
    bmesh.ops.create_cone(
        bm_body,
        radius1=dims['body_diameter']/2,
        radius2=dims['body_diameter']/2,
        depth=dims['body_length'],
        segments=32,
        cap_ends=True
    )
    
    bmesh.ops.rotate(
        bm_body,
        verts=list(bm_body.verts),
        cent=(0, 0, 0),
        matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
    )
    
    mesh_body = bpy.data.meshes.new("Resistor_Body")
    bm_body.to_mesh(mesh_body)
    obj_body = bpy.data.objects.new("Resistor_Body", mesh_body)
    collection.objects.link(obj_body)
    if isinstance(obj_body.data, Mesh):
        obj_body.data.materials.append(body_mat)
    
    # 创建端帽和引线
    # 左侧端帽
    bm_left_cap = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm_left_cap,
        u_segments=32,
        v_segments=16,
        radius=dims['body_diameter']/2
    )
    
    geom = []
    geom.extend(bm_left_cap.verts)
    geom.extend(bm_left_cap.edges)
    geom.extend(bm_left_cap.faces)

    bmesh.ops.bisect_plane(
        bm_left_cap,
        geom=geom,
        plane_co=(0, 0, 0),
        plane_no=(1, 0, 0),
        clear_outer=True
    )
    
    for v in bm_left_cap.verts:
        v.co.x -= dims['body_length'] / 2
    
    mesh_left_cap = bpy.data.meshes.new("Left_Cap")
    bm_left_cap.to_mesh(mesh_left_cap)
    obj_left_cap = bpy.data.objects.new("Left_Cap", mesh_left_cap)
    collection.objects.link(obj_left_cap)
    if isinstance(obj_left_cap.data, Mesh):
        obj_left_cap.data.materials.append(end_cap_mat)
    
    # 右侧端帽
    bm_right_cap = bmesh.new()
    bmesh.ops.create_uvsphere(
        bm_right_cap,
        u_segments=32,
        v_segments=16,
        radius=dims['body_diameter']/2
    )
    
    geom = []
    geom.extend(bm_right_cap.verts)
    geom.extend(bm_right_cap.edges)
    geom.extend(bm_right_cap.faces)

    bmesh.ops.bisect_plane(
        bm_right_cap,
        geom=geom,
        plane_co=(0, 0, 0),
        plane_no=(-1, 0, 0),
        clear_outer=True
    )
    
    for v in bm_right_cap.verts:
        v.co.x += dims['body_length'] / 2
    
    mesh_right_cap = bpy.data.meshes.new("Right_Cap")
    bm_right_cap.to_mesh(mesh_right_cap)
    obj_right_cap = bpy.data.objects.new("Right_Cap", mesh_right_cap)
    collection.objects.link(obj_right_cap)
    if isinstance(obj_right_cap.data, Mesh):
        obj_right_cap.data.materials.append(end_cap_mat)
    
    # 左侧引线
    bm_left_lead = bmesh.new()
    bmesh.ops.create_cone(
        bm_left_lead,
        radius1=dims['lead_diameter']/2,
        radius2=dims['lead_diameter']/2,
        depth=dims['lead_length'],
        segments=16,
        cap_ends=True
    )
    
    bmesh.ops.rotate(
        bm_left_lead,
        verts=list(bm_left_lead.verts),
        cent=(0, 0, 0),
        matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
    )
    
    left_lead_x = -dims['body_length']/2 - dims['body_diameter']/2 - dims['lead_length']/2 + dims['insertion_depth']
    for v in bm_left_lead.verts:
        v.co.x += left_lead_x
    
    mesh_left_lead = bpy.data.meshes.new("Left_Lead")
    bm_left_lead.to_mesh(mesh_left_lead)
    obj_left_lead = bpy.data.objects.new("Left_Lead", mesh_left_lead)
    collection.objects.link(obj_left_lead)
    if isinstance(obj_left_lead.data, Mesh):
        obj_left_lead.data.materials.append(end_cap_mat)
    
    # 右侧引线
    bm_right_lead = bmesh.new()
    bmesh.ops.create_cone(
        bm_right_lead,
        radius1=dims['lead_diameter']/2,
        radius2=dims['lead_diameter']/2,
        depth=dims['lead_length'],
        segments=16,
        cap_ends=True
    )
    
    bmesh.ops.rotate(
        bm_right_lead,
        verts=list(bm_right_lead.verts),
        cent=(0, 0, 0),
        matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
    )
    
    right_lead_x = dims['body_length']/2 + dims['body_diameter']/2 + dims['lead_length']/2 - dims['insertion_depth']
    for v in bm_right_lead.verts:
        v.co.x += right_lead_x
    
    mesh_right_lead = bpy.data.meshes.new("Right_Lead")
    bm_right_lead.to_mesh(mesh_right_lead)
    obj_right_lead = bpy.data.objects.new("Right_Lead", mesh_right_lead)
    collection.objects.link(obj_right_lead)
    if isinstance(obj_right_lead.data, Mesh):
        obj_right_lead.data.materials.append(end_cap_mat)
        
    # 添加色环
    add_color_bands(collection, dims['body_length'], dims['body_diameter'], dims['band_width'], dims['band_gap'], dims['start_offset'],
                    colors, tolerance_color, dims['body_color'])
    
    # 清理
    bm_body.free()
    bm_left_cap.free()
    bm_right_cap.free() 
    bm_left_lead.free()
    bm_right_lead.free()
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
    
    if bpy.context:
        bpy.context.view_layer.objects.active = obj_body
    return collection, obj_body

def add_color_bands(collection, body_length, body_diameter, band_width, band_gap, start_offset,
                    colors, tolerance_color, body_color):
    # 创建电阻体
    bm_body = bmesh.new()
    bmesh.ops.create_cone(
        bm_body,
        radius1=body_diameter/2,
        radius2=body_diameter/2,
        depth=body_length,
        segments=32,
        cap_ends=True
    )
    
    bmesh.ops.rotate(
        bm_body,
        verts=list(bm_body.verts),
        cent=(0, 0, 0),
        matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
    )
    
    mesh_body = bpy.data.meshes.new("Resistor_Body")
    bm_body.to_mesh(mesh_body)
    obj_body = bpy.data.objects.new("Resistor_Body", mesh_body)
    collection.objects.link(obj_body)
    if isinstance(obj_body.data, Mesh):
        obj_body.data.materials.append(create_material("Resistor_Body", body_color))
    
    bm_body.free()
    
    # 创建色环
    band_diameter = body_diameter * 1.05
    all_colors = colors + [tolerance_color]
    
    for i, color_name in enumerate(all_colors):
        if i < 5:  # 五色环
            color_info = FIVE_COLOR_CODES.get(color_name, {'rgb': (0.5, 0.5, 0.5)})
            color_rgb = color_info['rgb']
            band_mat = create_material(f"Band_{color_name}", color_rgb, metallic=0.0, roughness=0.95)
            
            bm_band = bmesh.new()
            bmesh.ops.create_cone(
                bm_band,
                radius1=band_diameter/2,
                radius2=band_diameter/2,
                depth=band_width,
                segments=32,
                cap_ends=True
            )
            
            bmesh.ops.rotate(
                bm_band,
                verts=list(bm_band.verts),
                cent=(0, 0, 0),
                matrix=Matrix.Rotation(math.radians(90), 3, 'Y')
            )
            
            band_x = -body_length/2 + start_offset + i * (band_width + band_gap) + band_width/2
            for v in bm_band.verts:
                v.co.x += band_x
            
            mesh_band = bpy.data.meshes.new(f"Color_Band_{i+1}")
            bm_band.to_mesh(mesh_band)
            obj_band = bpy.data.objects.new(f"Color_Band_{i+1}", mesh_band)
            collection.objects.link(obj_band)
            if isinstance(obj_band.data, Mesh):
                obj_band.data.materials.append(band_mat)
            bm_band.free()


# ==================== 面板类 ====================
class VIEW3D_PT_ResistorGenerator(bpy.types.Panel):
    """电阻生成器主面板"""
    bl_label = "色环电阻生成器"
    bl_idname = "VIEW3D_PT_resistor_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电阻工具"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 3  # 控制面板顺序
    
    def draw(self, context):
        layout = self.layout
        
        # 四色环电阻部分
        box = layout.box()
        box.label(text="四色环电阻", icon='MESH_CYLINDER')
        
        row = box.row()
        row.label(text="电阻值:")
        if context:
            row.prop(context.scene, "four_band_resistance", text="")
        
        # 单位选择
        row = box.row()
        row.label(text="单位:")
        if context:
            row.prop(context.scene, "four_band_resistor_unit", text="")
        
        row = box.row()
        row.label(text="公差:")
        if context:
            row.prop(context.scene, "four_band_tolerance", text="")
        
        row = box.row()
        row.label(text="额定功率:")
        if context:
            row.prop(context.scene, "four_band_rated_power", text="")
        
        # 实时预览四色环
        self.draw_four_band_preview(box, context)
        
        # 生成按钮
        row = box.row()
        row.scale_y = 1.5
        row.operator("resistor.generate_four_band", text="生成四色环电阻", icon='ADD')
        
        # 五色环电阻部分
        box = layout.box()
        box.label(text="五色环精密电阻", icon='META_CUBE')
        
        # 电阻值输入
        row = box.row()
        row.label(text="电阻值:", icon='DRIVER_DISTANCE')
        row = box.row()
        if context:
            row.prop(context.scene, "five_band_resistance", text="")
        
        # 单位选择
        row = box.row()
        row.label(text="单位:")
        if context:
            row.prop(context.scene, "five_band_resistor_unit", text="")
        
        # 公差选择 - 五色环常用公差
        row = box.row()
        row.label(text="公差:")
        if context:
            row.prop(context.scene, "five_band_tolerance_enum", text="")
        
        # 如果选择"自定义"，显示自定义输入框
        if context and getattr(context.scene, "five_band_tolerance_enum", None) == 'CUSTOM':
            row = box.row()
            row.label(text="自定义公差:")
            row.prop(context.scene, "five_band_tolerance_custom", text="%")
        
        # 获取实际公差值
        tolerance_value = self.get_tolerance_value(context)
        
        # 电阻类型
        row = box.row()
        row.label(text="电阻类型:")
        if context:
            row.prop(context.scene, "five_band_resistor_type", text="")

        row = box.row()
        row.label(text="额定功率:")
        if context:
            row.prop(context.scene, "five_band_rated_power", text="")
        
        # 实时预览五色环
        self.draw_five_band_preview(box, context)
        
        # 生成按钮
        row = box.row()
        row.scale_y = 1.5
        row.operator("resistor.generate_five_band", text="生成五色环电阻", icon='ADD')
    
    def get_tolerance_value(self, context) -> float:
        """获取选择的公差值"""
        if context.scene.five_band_tolerance_enum == 'CUSTOM':
            return context.scene.five_band_tolerance_custom
        else:
            # 从枚举值中提取数字
            tol_str = context.scene.five_band_tolerance_enum
            if tol_str.endswith('%'):
                tol_str = tol_str[:-1]
            return float(tol_str)

    def draw_four_band_preview(self, layout, context):
        """绘制四色环实时预览"""
        # 计算当前参数对应的色环颜色
        tolerance = context.scene.four_band_tolerance / 100.0
        
        actual_value = context.scene.four_band_resistance
        if context.scene.four_band_resistor_unit == 'kΩ':
            actual_value *= 1000
        elif context.scene.four_band_resistor_unit == 'MΩ':
            actual_value *= 1000000

        colors, tolerance_color = calculate_color_bands(actual_value, tolerance, False)
        all_colors = colors + [tolerance_color]
        
        # 创建预览区域
        preview_box = layout.box()
        preview_box.label(text="四色环预览", icon='VIEWZOOM')
        
        # 显示电阻示意图
        self.draw_resistor_diagram(preview_box, all_colors, 4, context)
        
        # 显示色环详细说明
        row = preview_box.row(align=True)
        row.alignment = 'CENTER'
        
        for i, color_name in enumerate(all_colors):
            if i < 4:  # 只显示4个色环
                # 获取图标
                icon_id = ResistorIconManager.get_icon_id(color_name)
                
                # 创建色环预览项
                col = row.column(align=True)
                col.scale_y = 0.8
                
                # 色环图标
                if isinstance(icon_id, int) and icon_id > 0:
                    col.label(text="", icon_value=icon_id)
                else:
                    col.label(text="", icon=icon_id)
                
                color_display = get_color_display_name(color_name)
                col.label(text=f"{color_display}")

                # 色环编号
                if i < 2:
                    col.label(text=f"环{i+1}")
                elif i == 2:
                    col.label(text="乘数")
                else:
                    col.label(text="公差")
        
    def draw_five_band_preview(self, layout, context):
        """绘制五色环实时预览"""
        # 计算当前参数对应的色环颜色
        tolerance = context.scene.five_band_tolerance / 100.0

        actual_value = context.scene.five_band_resistance
        if context.scene.five_band_resistor_unit == 'kΩ':
            actual_value *= 1000
        elif context.scene.five_band_resistor_unit == 'MΩ':
            actual_value *= 1000000
        
        colors, tolerance_color = calculate_color_bands(actual_value, tolerance, True)
        all_colors = colors + [tolerance_color]
        
        # 创建预览区域
        preview_box = layout.box()
        preview_box.label(text="五色环预览", icon='VIEWZOOM')
        
        # 显示电阻示意图
        self.draw_resistor_diagram(preview_box, all_colors, 5, context)
        
        # 显示色环详细说明
        row = preview_box.row(align=True)
        row.alignment = 'CENTER'
        
        for i, color_name in enumerate(all_colors):
            if i < 5:  # 只显示5个色环
                # 获取图标
                icon_id = ResistorIconManager.get_icon_id(color_name)
                
                # 创建色环预览项
                col = row.column(align=True)
                col.scale_y = 0.8
                
                # 色环图标
                if isinstance(icon_id, int) and icon_id > 0:
                    col.label(text="", icon_value=icon_id)
                else:
                    col.label(text="", icon=icon_id)
                
                color_display = get_color_display_name(color_name)
                col.label(text=f"{color_display}")
                
                # 色环编号
                if i < 3:
                    col.label(text=f"环{i+1}",)
                elif i == 3:
                    col.label(text="乘数")
                else:
                    col.label(text="公差")
        
    
    def draw_resistor_diagram(self, layout, color_names, band_count, context):
        # 显示阻值
        if band_count == 4:
            resistance = context.scene.four_band_resistance
            tolerance = context.scene.four_band_tolerance
            if context.scene.four_band_resistor_unit == 'kΩ':
                resistance *= 1000
            elif context.scene.four_band_resistor_unit == 'MΩ':
                resistance *= 1000000
        else:
            resistance = context.scene.five_band_resistance
            tolerance = context.scene.five_band_tolerance
            if context.scene.five_band_resistor_unit == 'kΩ':
                resistance *= 1000
            elif context.scene.five_band_resistor_unit == 'MΩ':
                resistance *= 1000000

        
        display_value = format_resistance(resistance)
        row = layout.row(align=True)
        row.alignment = 'CENTER'
        row.label(text=f"阻值: {display_value} (±{tolerance}%)", icon='DRIVER_DISTANCE')


class VIEW3D_PT_ResistorCalculator(bpy.types.Panel):
    """色环电阻计算器面板"""
    bl_label = "色环电阻计算器"
    bl_idname = "VIEW3D_PT_resistor_calculator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电阻工具"
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 4  # 在最后显示
    
    def draw(self, context):
        layout = self.layout
        
        box = layout.box()
        box.label(text="色环到阻值计算", icon='DRIVER')
        
        # 选择色环数量
        row = box.row()
        row.label(text="色环数量:")
        if context:
            row.prop(context.scene, "calc_band_count", expand=True)
        
        is_five_band = context and getattr(context.scene, "calc_band_count") == 'FIVE'
        
        # 色环选择
        if is_five_band:
            # 五色环选择
            for i in range(5):
                row = box.row()
                if i < 3:
                    row.label(text=f"第{i+1}位数字:")
                elif i == 3:
                    row.label(text="乘数:")
                else:
                    row.label(text="公差:")
                
                prop_name = f"calc_color_{i}"
                if i > 2:
                    prop_name = f"calc_5color_{i}"
                
                if context:
                    row.prop(context.scene, prop_name, text="")
        
            # 计算阻值
            if context and getattr(context.scene, "calc_color_0") != 'NONE' and \
                           getattr(context.scene, "calc_color_1") != 'NONE' and \
                           getattr(context.scene, "calc_color_2") != 'NONE' and \
                           getattr(context.scene, "calc_5color_3") != 'NONE' and \
                           getattr(context.scene, "calc_5color_4") != 'NONE':
                
                # 获取数字
                digit1 = FIVE_COLOR_CODES[getattr(context.scene, "calc_color_0")]['digit']
                digit2 = FIVE_COLOR_CODES[getattr(context.scene, "calc_color_1")]['digit']
                digit3 = FIVE_COLOR_CODES[getattr(context.scene, "calc_color_2")]['digit']
                multiplier = FIVE_COLOR_CODES[getattr(context.scene, "calc_5color_3")]['multiplier']
                tolerance = FIVE_COLOR_CODES.get(f"{getattr(context.scene, 'calc_5color_4')}_tol", 
                                           FIVE_COLOR_CODES.get(getattr(context.scene, "calc_5color_4"), 
                                                          {'tolerance': 0.05}))['tolerance']
                
                # 计算阻值
                value = (digit1 * 100 + digit2 * 10 + digit3) * multiplier
                tolerance_percent = tolerance * 100
                
                row = box.row()
                row.label(text=f"阻值: {format_resistance(value)} ±{tolerance_percent:.2f}%")
        else:
            # 四色环选择
            for i in range(4):
                row = box.row()
                if i < 2:
                    row.label(text=f"第{i+1}位数字:")
                elif i == 2:
                    row.label(text="乘数:")
                else:
                    row.label(text="公差:")
                
                prop_name = f"calc_color_{i}"
                if i > 2:
                    prop_name = f"calc_4color_{i}"
                if context:
                    row.prop(context.scene, prop_name, text="")
            
            # 计算阻值
            if context and getattr(context.scene, "calc_color_0") != 'NONE' and \
                           getattr(context.scene, "calc_color_1") != 'NONE' and \
                           getattr(context.scene, "calc_color_2") != 'NONE' and \
                           getattr(context.scene, "calc_4color_3") != 'NONE':
                
                # 获取数字
                digit1 = FOUR_COLOR_CODES[getattr(context.scene, "calc_color_0")]['digit']
                digit2 = FOUR_COLOR_CODES[getattr(context.scene, "calc_color_1")]['digit']
                multiplier = FOUR_COLOR_CODES[getattr(context.scene, "calc_color_2")]['multiplier']
                tolerance = FOUR_COLOR_CODES.get(f"{getattr(context.scene, 'calc_4color_3')}_tol", 
                                           FOUR_COLOR_CODES.get(getattr(context.scene, "calc_4color_3"), 
                                                          {'tolerance': 0.05}))['tolerance']
                
                # 计算阻值
                value = (digit1 * 10 + digit2) * multiplier
                tolerance_percent = tolerance * 100
                
                row = box.row()
                row.label(text=f"阻值: {format_resistance(value)} ±{tolerance_percent:.2f}%")

# ==================== 操作类：图标管理 ====================
class RESISTOR_OT_SetIconDirectory(bpy.types.Operator):
    """设置图标目录"""
    bl_idname = "resistor.set_icon_directory"
    bl_label = "设置图标目录"
    bl_description = "设置色环电阻图标文件所在的目录"
    
    directory = bpy.props.StringProperty(
        name="图标目录",
        description="选择包含色环电阻PNG图标的目录",
        subtype='DIR_PATH'
    )
    
    def execute(self, context):
        if os.path.exists(self.directory):
            ResistorIconManager.set_icon_directory(self.directory)
            # 重新加载图标
            ResistorIconManager.unload_icons()
            ResistorIconManager.load_icons()
            self.report({'INFO'}, f"图标目录已设置为: {self.directory}")
        else:
            self.report({'ERROR'}, f"目录不存在: {self.directory}")
        return {'FINISHED'}
    
    def invoke(self, context, event):
        if context:
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class RESISTOR_OT_ReloadIcons(bpy.types.Operator):
    """重新加载图标"""
    bl_idname = "resistor.reload_icons"
    bl_label = "重新加载图标"
    bl_description = "重新加载色环电阻图标"
    
    def execute(self, context):
        ResistorIconManager.unload_icons()
        ResistorIconManager.load_icons()
        self.report({'INFO'}, "图标已重新加载")
        return {'FINISHED'}

# ==================== 注册和注销 ====================
def register():
    # 注册场景属性
    # 四色环电阻属性
    bpy.types.Scene.four_band_resistance: bpy.props.FloatProperty(
        name="电阻值",
        default=1.0,
        min=0.1,
        max=10000000,
        step=100,
        precision=2,
        update=lambda self, context: None  # 添加更新回调以触发实时预览
    ) # type: ignore
    
    bpy.types.Scene.four_band_resistor_unit: bpy.props.EnumProperty(
        name="单位",
        items=[
            ('Ω', "Ω", "欧姆"),
            ('kΩ', "kΩ", "千欧姆"),
            ('MΩ', "MΩ", "兆欧姆")
        ],
        default='kΩ'
    ) # type: ignore

    bpy.types.Scene.four_band_tolerance: bpy.props.FloatProperty(
        name="公差",
        default=5.0,
        min=0.0,
        max=20.0,
        step=5,
        precision=1,
        update=lambda self, context: None  # 添加更新回调以触发实时预览
    ) # type: ignore
    
    bpy.types.Scene.four_band_rated_power: bpy.props.EnumProperty(
        name="电阻类型",
        items=[
            ('1_8W', "1/8W", "1/8瓦碳膜电阻"),
            ('1_4W', "1/4W", "1/4瓦碳膜电阻"),
            ('1_2W', "1/2W", "1/2瓦碳膜电阻"),
            ('1W', "1W", "1瓦碳膜电阻")
        ],
        default='1_4W',
        update=lambda self, context: None  # 添加更新回调以触发实时预览
    ) # type: ignore
    
    # 五色环电阻属性
    bpy.types.Scene.five_band_resistance_value: bpy.props.FloatProperty(
        name="电阻值",
        default=1.0,
        min=0.001,
        max=100000000,
        step=100,
        precision=4,
        update=lambda self, context: None  # 添加更新回调以触发实时预览
    ) # type: ignore
    
    bpy.types.Scene.five_band_resistor_unit: bpy.props.EnumProperty(
        name="单位",
        items=[
            ('Ω', "Ω", "欧姆"),
            ('kΩ', "kΩ", "千欧姆"),
            ('MΩ', "MΩ", "兆欧姆")
        ],
        default='kΩ'
    ) # type: ignore

    bpy.types.Scene.five_band_tolerance: bpy.props.FloatProperty(
        name="公差",
        default=1.0,
        min=0.01,
        max=10.0,
        step=1,
        precision=2,
        update=lambda self, context: None  # 添加更新回调以触发实时预览
    ) # type: ignore
    
    # 计算器属性
    bpy.types.Scene.calc_band_count: bpy.props.EnumProperty(
        name="色环数量",
        items=[
            ('FOUR', "四色环", "四色环电阻"),
            ('FIVE', "五色环", "五色环精密电阻")
        ],
        default='FOUR'
    ) # type: ignore
    
    digit_color_items = [
        ('NONE', "无", "未选择"),
        ('black', "黑色", "黑色 (0)"),
        ('brown', "棕色", "棕色 (1)"),
        ('red', "红色", "红色 (2)"),
        ('orange', "橙色", "橙色 (3)"),
        ('yellow', "黄色", "黄色 (4)"),
        ('green', "绿色", "绿色 (5)"),
        ('blue', "蓝色", "蓝色 (6)"),
        ('violet', "紫色", "紫色 (7)"),
        ('gray', "灰色", "灰色 (8)"),
        ('white', "白色", "白色 (9)"),
    ]

    toleratence_4color_items = [
        ('NONE', "无色", "无色 (20%)"),
        ('brown', "棕色", "棕色 (1%)"),
        ('gold', "金色", "金色 (5%)"),
        ('silver', "银色", "银色 (10%)"),
    ]
    
    toleratence_5color_items = [
        ('NONE', "无色", "无色 (20%)"),
        ('brown', "棕色", "棕色 (1%)"),
        ('gold', "金色", "金色 (5%)"),
        ('silver', "银色", "银色 (10%)"),
        ('red', "红色", "红色 (2%)"),
        ('green', "绿色", "绿色 (0.5%)"),
        ('blue', "蓝色", "蓝色 (0.25%)"),
        ('violet', "紫色", "紫色 (0.1%)"),
        ('gray', "灰色", "灰色 (0.05%)"),
    ]

    for i in range(5):
        if i <= 2:
            setattr(bpy.types.Scene, f"calc_color_{i}", 
                    bpy.props.EnumProperty(items=digit_color_items, default='NONE'))
        elif i == 3:
            setattr(bpy.types.Scene, f"calc_4color_{i}", 
                    bpy.props.EnumProperty(items=toleratence_4color_items, default='gold'))
            setattr(bpy.types.Scene, f"calc_5color_{i}", 
                    bpy.props.EnumProperty(items=digit_color_items, default='NONE'))
        elif i == 4:
            setattr(bpy.types.Scene, f"calc_5color_{i}", 
                    bpy.props.EnumProperty(items=toleratence_5color_items, default='brown'))
    

    # 五色环常用公差枚举
    bpy.types.Scene.five_band_tolerance_enum: bpy.props.EnumProperty(
        name="公差",
        items=[
            ('0.05%', "0.05%", "0.05% 公差（灰色）"),
            ('0.1%', "0.1%", "0.1% 公差（紫色）"),
            ('0.25%', "0.25%", "0.25% 公差（蓝色）"),
            ('0.5%', "0.5%", "0.5% 公差（绿色）"),
            ('1%', "1%", "1% 公差（棕色）"),
            ('2%', "2%", "2% 公差（红色）"),
            ('CUSTOM', "自定义", "自定义公差值")
        ],
        default='1%'
    ) # type: ignore
    
    # 自定义公差
    bpy.types.Scene.five_band_tolerance_custom: bpy.props.FloatProperty(
        name="自定义公差",
        default=1.0,
        min=0.01,
        max=10.0,
        step=1,
        precision=2
    ) # type: ignore
    
    bpy.types.Scene.five_band_resistor_type: bpy.props.EnumProperty(
        name="电阻类型",
        items=[
            ('metal_film', "金属膜电阻", "金属膜精密电阻（蓝色体）"),
            ('carbon_film', "碳膜电阻", "碳膜精密电阻（米色体）"),
            # ('wire_wound', "线绕电阻", "线绕精密电阻（绿色体）"),
        ],
        default='metal_film'
    ) # type: ignore

    bpy.types.Scene.five_band_rated_power: bpy.props.EnumProperty(
        name="电阻类型",
        items=[
            ('1_8W', "1/8W", "1/8瓦碳膜电阻"),
            ('1_4W', "1/4W", "1/4瓦碳膜电阻"),
            ('1_2W', "1/2W", "1/2瓦碳膜电阻"),
            ('1W', "1W", "1瓦碳膜电阻")
        ],
        default='1_4W',
        update=lambda self, context: None  # 添加更新回调以触发实时预览
    ) # type: ignore
    
    # 注册类
    classes = [
        RESISTOR_OT_GenerateFourBand,
        RESISTOR_OT_GenerateFiveBand,
        RESISTOR_OT_SetIconDirectory,
        RESISTOR_OT_ReloadIcons,
        VIEW3D_PT_ResistorGenerator,
        VIEW3D_PT_ResistorCalculator,
    ]
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 加载图标
    ResistorIconManager.load_icons()
    
    print("色环电阻生成器插件")

def unregister():
    # 注销类
    classes = [
        RESISTOR_OT_GenerateFourBand,
        RESISTOR_OT_GenerateFiveBand,
        RESISTOR_OT_SetIconDirectory,
        RESISTOR_OT_ReloadIcons,
        VIEW3D_PT_ResistorGenerator,
        VIEW3D_PT_ResistorCalculator,
    ]
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 卸载图标
    ResistorIconManager.unload_icons()
    
    # 删除场景属性
    delattr(bpy.types.Scene, "four_band_resistance")
    delattr(bpy.types.Scene, "four_band_resistor_unit")
    delattr(bpy.types.Scene, "four_band_tolerance")
    delattr(bpy.types.Scene, "four_band_rated_power")

    delattr(bpy.types.Scene, "five_band_resistance")
    delattr(bpy.types.Scene, "five_band_resistor_unit")
    delattr(bpy.types.Scene, "five_band_tolerance")
    delattr(bpy.types.Scene, "five_band_rated_power")
    
    delattr(bpy.types.Scene, "calc_band_count")

    delattr(bpy.types.Scene, "five_band_tolerance_enum")
    delattr(bpy.types.Scene, "five_band_tolerance_custom")
    delattr(bpy.types.Scene, "five_band_resistor_type")

    
    for i in range(5):
        if i <= 2:
            delattr(bpy.types.Scene, f"calc_color_{i}")
        elif i == 3:
            delattr(bpy.types.Scene, f"calc_4color_{i}")
            delattr(bpy.types.Scene, f"calc_5color_{i}")
        elif i == 4:
            delattr(bpy.types.Scene, f"calc_5color_{i}")
    
    print("色环电阻生成器插件已注销")

# 如果直接运行，则注册插件
if __name__ == "__main__":
    register()