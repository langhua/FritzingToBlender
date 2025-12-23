import re
from typing import Optional, Tuple

def parse_resistance_string(resistance_str: str) -> Tuple[Optional[float], Optional[str], str]:
    """
    从字符串中解析电阻值
    
    参数:
        resistance_str: 包含电阻值的字符串，例如："排阻100kΩ"
    
    返回:
        tuple: (电阻值(欧姆), 单位, 原始匹配字符串)
    
    示例:
        "排阻100kΩ" -> (100000.0, "kΩ", "100kΩ")
        "10k" -> (10000.0, "k", "10k")
        "1.2MΩ" -> (1200000.0, "MΩ", "1.2MΩ")
    """
    if not resistance_str:
        return None, None, ""
    
    # 定义电阻单位映射
    unit_multiplier = {
        'R': 1,      # 欧姆
        'Ω': 1,      # 欧姆符号
        'k': 1000,   # 千欧
        'K': 1000,   # 千欧
        'kΩ': 1000,  # 千欧符号
        'KΩ': 1000,  # 千欧符号
        'M': 1000000,  # 兆欧
        'MΩ': 1000000, # 兆欧符号
        'G': 1000000000,  # 吉欧
        'GΩ': 1000000000,  # 吉欧符号
    }
    
    # 移除空格和特殊字符
    resistance_str = resistance_str.strip()
    
    # 尝试不同的正则表达式模式
    patterns = [
        # 模式1: 数字 + 可选小数点 + 数字 + 单位
        r'([\d\.]+)([a-zA-ZΩ]+)',
        # 模式2: 只有数字
        r'([\d\.]+)(?!.*[a-zA-ZΩ])',
        # 模式3: 数字 + 单位 + 中文
        r'([\d\.]+)([a-zA-ZΩ]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, resistance_str)
        if match:
            value_part = match.group(1)
            unit_part = match.group(2) if len(match.groups()) > 1 else ''
            
            try:
                # 解析数值部分
                if '.' in value_part:
                    value = float(value_part)
                else:
                    value = float(value_part)
                
                # 解析单位
                unit = unit_part.upper() if unit_part else 'Ω'
                
                # 标准化单位表示
                unit_key = unit
                if unit in ['K', 'k']:
                    unit_key = 'kΩ' if 'Ω' in resistance_str else 'k'
                elif unit in ['M']:
                    unit_key = 'MΩ' if 'Ω' in resistance_str else 'M'
                elif unit in ['G']:
                    unit_key = 'GΩ' if 'Ω' in resistance_str else 'G'
                elif unit in ['R', 'Ω']:
                    unit_key = 'Ω'
                
                # 计算实际电阻值
                if unit_key in unit_multiplier:
                    actual_value = value * unit_multiplier[unit_key]
                elif not unit_key:  # 没有单位，默认为欧姆
                    actual_value = value
                    unit_key = 'Ω'
                else:
                    # 尝试从字符串中提取单位
                    for unit_str, multiplier in unit_multiplier.items():
                        if unit_str in resistance_str.upper():
                            actual_value = value * multiplier
                            unit_key = unit_str
                            break
                    else:
                        # 如果没有找到已知单位，默认欧姆
                        actual_value = value
                        unit_key = 'Ω'
                
                return actual_value, unit_key, match.group(0)
                
            except (ValueError, AttributeError) as e:
                print(f"解析电阻值失败: {resistance_str}, 错误: {e}")
                continue
    
    return None, None, ""