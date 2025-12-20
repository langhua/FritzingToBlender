import bpy
import math
from typing import Dict

bl_info = {
    "name": "EIA-96贴片电阻丝印计算器",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N > 电阻工具",
    "description": "EIA-96标准精密贴片电阻丝印与阻值计算器",
    "category": "3D View"
}

# ==================== EIA-96 标准定义 ====================
# EIA-96 有效数字代码表 (01-96 对应 100-976)
EIA96_DIGIT_CODES = {
    '01': 100, '02': 102, '03': 105, '04': 107, '05': 110, '06': 113, '07': 115, 
    '08': 118, '09': 121, '10': 124, '11': 127, '12': 130, '13': 133, '14': 137, 
    '15': 140, '16': 143, '17': 147, '18': 150, '19': 154, '20': 158, '21': 162, 
    '22': 165, '23': 169, '24': 174, '25': 178, '26': 182, '27': 187, '28': 191, 
    '29': 196, '30': 200, '31': 205, '32': 210, '33': 215, '34': 221, '35': 226, 
    '36': 232, '37': 237, '38': 243, '39': 249, '40': 255, '41': 261, '42': 267, 
    '43': 274, '44': 280, '45': 287, '46': 294, '47': 301, '48': 309, '49': 316, 
    '50': 324, '51': 332, '52': 340, '53': 348, '54': 357, '55': 365, '56': 374, 
    '57': 383, '58': 392, '59': 402, '60': 412, '61': 422, '62': 432, '63': 442, 
    '64': 453, '65': 464, '66': 475, '67': 487, '68': 499, '69': 511, '70': 523, 
    '71': 536, '72': 549, '73': 562, '74': 576, '75': 590, '76': 604, '77': 619, 
    '78': 634, '79': 649, '80': 665, '81': 681, '82': 698, '83': 715, '84': 732, 
    '85': 750, '86': 768, '87': 787, '88': 806, '89': 825, '90': 845, '91': 866, 
    '92': 887, '93': 909, '94': 931, '95': 953, '96': 976
}

# EIA-96 乘数字母代码表
EIA96_MULTIPLIER_CODES = {
    'Z': 0.001,  # 10^-3
    'Y': 0.01,   # 10^-2
    'X': 0.1,    # 10^-1
    'A': 1,      # 10^0
    'B': 10,     # 10^1
    'C': 100,    # 10^2
    'D': 1000,   # 10^3
    'E': 10000,  # 10^4
    'F': 100000, # 10^5
}

# 反向查找表：从有效数字到代码
DIGITS_TO_CODE = {value: code for code, value in EIA96_DIGIT_CODES.items()}
MULTIPLIER_TO_CODE = {value: code for code, value in EIA96_MULTIPLIER_CODES.items()}

# 常见贴片电阻封装尺寸
SMD_SIZES = {
    '0201': (0.6, 0.3, 0.23),   # 长, 宽, 高 (mm)
    '0402': (1.0, 0.5, 0.35),   # 长, 宽, 高 (mm)
    '0603': (1.6, 0.8, 0.45),   # 长, 宽, 高 (mm)
    '0805': (2.0, 1.25, 0.5),   # 长, 宽, 高 (mm)
    '1206': (3.2, 1.6, 0.55),   # 长, 宽, 高 (mm)
    '1210': (3.2, 2.5, 0.55),   # 长, 宽, 高 (mm)
    '1812': (4.5, 3.2, 0.55),   # 长, 宽, 高 (mm)
    '2010': (5.0, 2.5, 0.55),   # 长, 宽, 高 (mm)
    '2512': (6.4, 3.2, 0.55),   # 长, 宽, 高 (mm)
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

def resistor_to_eia96(resistance: float) -> Dict:
    """
    计算EIA-96标准丝印代码
    
    返回字典包含:
    - digit_code: 两位数字代码 (01-96)
    - multiplier_code: 乘数字母代码
    - standard_value: 标准电阻值
    - eia96_mark: EIA-96丝印代码 (如: 01C)
    - digits: 三位有效数字
    - multiplier: 乘数值
    - relative_error: 相对误差百分比
    """
    if resistance <= 0:
        return {
            'digit_code': '01',
            'multiplier_code': 'A',
            'standard_value': 100.0,
            'eia96_mark': '01A',
            'digits': 100,
            'multiplier': 1,
            'relative_error': 0.0
        }
    
    # 计算最接近的标准值
    min_diff = float('inf')
    best_digit_code = '01'
    best_multiplier_code = 'A'
    best_std_value = 100.0
    
    # 遍历所有可能的组合
    for digit_code, digits in EIA96_DIGIT_CODES.items():
        for multiplier_code, multiplier in EIA96_MULTIPLIER_CODES.items():
            std_value = digits * multiplier
            diff = abs(math.log10(resistance) - math.log10(std_value))
            
            if diff < min_diff:
                min_diff = diff
                best_digit_code = digit_code
                best_multiplier_code = multiplier_code
                best_std_value = std_value
    
    # 计算相对误差
    if resistance > 0:
        relative_error = ((best_std_value - resistance) / resistance) * 100
    else:
        relative_error = 0.0
    
    return {
        'digit_code': best_digit_code,
        'multiplier_code': best_multiplier_code,
        'standard_value': best_std_value,
        'eia96_mark': f"{best_digit_code}{best_multiplier_code}",
        'digits': EIA96_DIGIT_CODES[best_digit_code],
        'multiplier': EIA96_MULTIPLIER_CODES[best_multiplier_code],
        'relative_error': relative_error
    }

def decode_eia96_code(code_str: str) -> Dict:
    """
    解码EIA-96丝印代码
    
    参数:
    - code_str: EIA-96代码 (如: "01C", "96F")
    
    返回字典包含:
    - resistance: 电阻值
    - digits: 三位有效数字
    - multiplier: 乘数
    - digit_code: 数字代码
    - multiplier_code: 乘数字母代码
    """
    if len(code_str) != 3:
        return {
            'resistance': 0,
            'digits': 0,
            'multiplier': 1,
            'digit_code': '01',
            'multiplier_code': 'A',
            'error': '代码长度必须为3位'
        }
    
    digit_code = code_str[:2]
    multiplier_code = code_str[2]
    
    if digit_code not in EIA96_DIGIT_CODES:
        return {
            'resistance': 0,
            'digits': 0,
            'multiplier': 1,
            'digit_code': digit_code,
            'multiplier_code': multiplier_code,
            'error': f'无效的数字代码: {digit_code}'
        }
    
    if multiplier_code not in EIA96_MULTIPLIER_CODES:
        return {
            'resistance': 0,
            'digits': 0,
            'multiplier': 1,
            'digit_code': digit_code,
            'multiplier_code': multiplier_code,
            'error': f'无效的乘数字母: {multiplier_code}'
        }
    
    digits = EIA96_DIGIT_CODES[digit_code]
    multiplier = EIA96_MULTIPLIER_CODES[multiplier_code]
    resistance = digits * multiplier
    
    return {
        'resistance': resistance,
        'digits': digits,
        'multiplier': multiplier,
        'digit_code': digit_code,
        'multiplier_code': multiplier_code,
        'error': None
    }

def get_smd_power_rating(size_code: str) -> float:
    """获取贴片电阻的额定功率"""
    power_ratings = {
        '0201': 0.05,    # 1/20W
        '0402': 0.0625,  # 1/16W
        '0603': 0.1,     # 1/10W
        '0805': 0.125,   # 1/8W
        '1206': 0.25,    # 1/4W
        '1210': 0.33,    # 1/3W
        '1812': 0.5,     # 1/2W
        '2010': 0.75,    # 3/4W
        '2512': 1.0,     # 1W
    }
    
    return power_ratings.get(size_code, 0.1)  # 默认1/10W

# ==================== 操作类 ====================
class EIA96_OT_GenerateCode(bpy.types.Operator):
    """生成EIA-96代码"""
    bl_idname = "eia96.generate_code"
    bl_label = "生成EIA-96代码"
    bl_description = "从电阻值生成EIA-96丝印代码"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 获取当前参数
        if context:
            resistance = getattr(context.scene, "eia96_resistance")
            size_code = getattr(context.scene, "eia96_size")
        
        # 计算EIA-96代码
        result = resistor_to_eia96(resistance)
        
        # 获取封装尺寸
        if size_code in SMD_SIZES:
            size = SMD_SIZES[size_code]
            power_rating = get_smd_power_rating(size_code)
        else:
            size = (1.6, 0.8, 0.45)  # 默认0603
            power_rating = 0.1
        
        # 创建信息字符串
        info = f"""
=== EIA-96 贴片电阻代码 ===
输入电阻值: {format_resistance(resistance)}
标准电阻值: {format_resistance(result['standard_value'])}
EIA-96丝印代码: {result['eia96_mark']}
数字代码: {result['digit_code']} = {result['digits']}
乘数字母: {result['multiplier_code']} = ×{result['multiplier']}
计算: {result['digits']} × {result['multiplier']} = {result['standard_value']}Ω
相对误差: {result['relative_error']:.2f}%
封装: {size_code} ({size[0]}×{size[1]}×{size[2]}mm)
功率: {power_rating}W
公差: ±1% (EIA-96标准)
"""
        
        # 在文本编辑器显示结果
        self.show_in_text_editor(info, f"EIA96_{result['eia96_mark']}")
        
        self.report({'INFO'}, f"已生成EIA-96代码: {result['eia96_mark']}")
        return {'FINISHED'}
    
    def show_in_text_editor(self, text, name="EIA96_Code"):
        """在文本编辑器中显示结果"""
        # 查找或创建文本数据块
        if name in bpy.data.texts:
            text_data = bpy.data.texts[name]
        else:
            text_data = bpy.data.texts.new(name)
        
        # 清除旧内容并添加新内容
        text_data.clear()
        text_data.write(text)
        
        # 尝试切换到文本编辑器
        if bpy.context:
            for area in getattr(bpy.context.screen, "areas"):
                if area.type == 'TEXT_EDITOR':
                    setattr(area.spaces.active, "text", text_data)
                    break

class EIA96_OT_DecodeCode(bpy.types.Operator):
    """解码EIA-96代码"""
    bl_idname = "eia96.decode_code"
    bl_label = "解码EIA-96代码"
    bl_description = "从EIA-96丝印代码解码电阻值"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        # 获取输入的代码
        if context:
            code_str = getattr(context.scene, "eia96_decode_code").upper().strip()
        
        if len(code_str) != 3:
            self.report({'ERROR'}, "EIA-96代码必须是3位字符")
            return {'CANCELLED'}
        
        # 解码代码
        result = decode_eia96_code(code_str)
        
        if result['error']:
            self.report({'ERROR'}, result['error'])
            return {'CANCELLED'}
        
        # 创建信息字符串
        info = f"""
=== EIA-96 代码解码 ===
输入代码: {code_str}
数字代码: {result['digit_code']} = {result['digits']}
乘数字母: {result['multiplier_code']} = ×{result['multiplier']}
电阻值: {result['digits']} × {result['multiplier']} = {format_resistance(result['resistance'])}
计算: {result['digits']} × {result['multiplier']} = {result['resistance']}Ω
EIA-96标准: ±1% 公差
"""
        
        # 在文本编辑器显示结果
        self.show_in_text_editor(info, f"Decode_{code_str}")
        
        self.report({'INFO'}, f"解码结果: {format_resistance(result['resistance'])}")
        return {'FINISHED'}
    
    def show_in_text_editor(self, text, name="EIA96_Decode"):
        """在文本编辑器中显示结果"""
        # 查找或创建文本数据块
        if name in bpy.data.texts:
            text_data = bpy.data.texts[name]
        else:
            text_data = bpy.data.texts.new(name)
        
        # 清除旧内容并添加新内容
        text_data.clear()
        text_data.write(text)
        
        # 尝试切换到文本编辑器
        if bpy.context:
            for area in getattr(bpy.context.screen, "areas"):
                if area.type == 'TEXT_EDITOR':
                    setattr(area.spaces.active, "text", text_data)
                    break

# ==================== 面板类 ====================
class VIEW3D_PT_EIA96Calculator(bpy.types.Panel):
    """EIA-96贴片电阻计算器面板"""
    bl_label = "EIA-96丝印计算器"
    bl_idname = "VIEW3D_PT_eia96_calculator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电阻工具"
    bl_order = 2
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        
        # 编码部分：从电阻值到代码
        encode_box = layout.box()
        encode_box.label(text="编码：电阻值 → EIA-96代码")
        
        # 电阻值输入
        row = encode_box.row()
        row.label(text="电阻值:")
        if context:
            row.prop(context.scene, "eia96_resistance", text="")
        
        # 实时计算结果
        if context:
            result = resistor_to_eia96(getattr(context.scene, "eia96_resistance"))
        
        result_box = encode_box.box()
        result_box.label(text="实时计算结果", icon='DRIVER')
        
        # 显示标准值和代码
        row = result_box.row()
        row.label(text="标准值:")
        row.label(text=f"{format_resistance(result['standard_value'])}")
        
        row = result_box.row()
        row.label(text="EIA-96代码:")
        row.label(text=f"{result['digit_code']}{result['multiplier_code']}")
        
        # 解码部分：从代码到电阻值
        decode_box = layout.box()
        decode_box.label(text="解码：EIA-96代码 → 电阻值")
        
        # 代码输入
        row = decode_box.row()
        row.label(text="EIA-96代码:")
        if context:
            row.prop(context.scene, "eia96_decode_code", text="")
        
        # 解码按钮
        row = decode_box.row()
        row.scale_y = 1.5
        row.operator("eia96.decode_code", text="解码EIA-96代码")
        

# ==================== 注册和注销 ====================
def register():
    """注册插件"""
    # 注册类
    classes = [
        VIEW3D_PT_EIA96Calculator,
        EIA96_OT_GenerateCode,
        EIA96_OT_DecodeCode,
    ]
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
        except ValueError:
            # 如果已经注册，先注销再注册
            try:
                bpy.utils.unregister_class(cls)
            except RuntimeError:
                pass
            bpy.utils.register_class(cls)
    
    # 注册场景属性
    from bpy.types import Scene
    
    # 电阻值
    Scene.eia96_resistance = bpy.props.FloatProperty(
        name="电阻值",
        default=10000.0,  # 10kΩ
        min=0.001,
        max=1000000000,
        step=100,
        precision=4,
        description="输入电阻值，计算EIA-96代码",
        update=lambda self, context: None
    )
    
    # 封装尺寸
    Scene.eia96_size = bpy.props.EnumProperty(
        name="封装尺寸",
        items=[
            ('0201', "0201 (0.6×0.3mm)", "超小型封装"),
            ('0402', "0402 (1.0×0.5mm)", "小型封装"),
            ('0603', "0603 (1.6×0.8mm)", "常用封装"),
            ('0805', "0805 (2.0×1.25mm)", "常用封装"),
            ('1206', "1206 (3.2×1.6mm)", "标准封装"),
            ('1210', "1210 (3.2×2.5mm)", "大功率封装"),
            ('1812', "1812 (4.5×3.2mm)", "大功率封装"),
            ('2010', "2010 (5.0×2.5mm)", "大功率封装"),
            ('2512', "2512 (6.4×3.2mm)", "超大功率封装"),
        ],
        default='0603',
        description="贴片电阻封装尺寸"
    )
    
    # 解码代码
    Scene.eia96_decode_code = bpy.props.StringProperty(
        name="EIA-96代码",
        default="01C",
        description="输入EIA-96代码 (如: 01C, 68D)",
        maxlen=3
    )
    
    print("EIA-96贴片电阻计算器已注册")

def unregister():
    """注销插件"""
    # 注销类
    classes = [
        VIEW3D_PT_EIA96Calculator,
        EIA96_OT_GenerateCode,
        EIA96_OT_DecodeCode,
    ]
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError:
            pass
    
    # 注销场景属性
    from bpy.types import Scene
    
    try:
        delattr(Scene, "eia96_resistance")
    except AttributeError:
        pass
    
    try:
        delattr(Scene, "eia96_size")
    except AttributeError:
        pass
    
    try:
        delattr(Scene, "eia96_decode_code")
    except AttributeError:
        pass
    
    print("EIA-96贴片电阻计算器已注销")

# 如果直接运行，则注册插件
if __name__ == "__main__":
    register()