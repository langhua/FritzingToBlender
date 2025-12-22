from typing import List, Dict
from io_fritzing.assets.resistors.band_colors import RESISTOR_COLORS, TOLERANCE_COLORS

def resistance_tolerance_to_5bands(resistance: float, tolerance_percent: float = 1) -> List[Dict]:
    """
    计算任意电阻值的五色色环，包括容差色环
    参数：
    resistance: 电阻值（单位：欧姆）
    tolerance_percent: 容差百分比（默认：1%）
    返回：
    包含5个字典的列表，每个字典表示一个色环，包含颜色、位置和值
    """
    if resistance <= 0:
        return []
    
    bands = []
    
    # 处理非常小的电阻值 (<1Ω)
    if resistance < 1:
        exp = 0
        while resistance < 1 and exp > -3:
            resistance *= 10
            exp -= 1
        
        digits = round(resistance * 10)
        digit1 = digits // 100
        digit2 = (digits // 10) % 10
        digit3 = digits % 10
        
        multiplier_exp = exp - 2
        
        bands.append({
            'color': RESISTOR_COLORS.get(digit1, RESISTOR_COLORS[0]),
            'position': 1,
            'value': digit1
        })
        
        bands.append({
            'color': RESISTOR_COLORS.get(digit2, RESISTOR_COLORS[0]),
            'position': 2,
            'value': digit2
        })
        
        bands.append({
            'color': RESISTOR_COLORS.get(digit3, RESISTOR_COLORS[0]),
            'position': 3,
            'value': digit3
        })
        
        if multiplier_exp < -2:
            multiplier_exp = -2
        elif multiplier_exp > 9:
            multiplier_exp = 9
        bands.append({
            'color': RESISTOR_COLORS.get(multiplier_exp, RESISTOR_COLORS[0]),
            'position': 4,
            'value': multiplier_exp
        })
    else:
        exp = 0
        temp_value = resistance
        
        while temp_value >= 1000:
            temp_value /= 10
            exp += 1
        while temp_value < 100 and exp > -3:
            temp_value *= 10
            exp -= 1
        
        digits = round(temp_value)
        digit1 = digits // 100
        digit2 = (digits // 10) % 10
        digit3 = digits % 10
        
        bands.append({
            'color': RESISTOR_COLORS.get(digit1, RESISTOR_COLORS[0]),
            'position': 1,
            'value': digit1
        })
        
        bands.append({
            'color': RESISTOR_COLORS.get(digit2, RESISTOR_COLORS[0]),
            'position': 2,
            'value': digit2
        })
        
        bands.append({
            'color': RESISTOR_COLORS.get(digit3, RESISTOR_COLORS[0]),
            'position': 3,
            'value': digit3
        })
        
        if exp < -2:
            exp = -2
        elif exp > 9:
            exp = 9
        bands.append({
            'color': RESISTOR_COLORS.get(exp, RESISTOR_COLORS[0]),
            'position': 4,
            'value': exp
        })
    
    tolerance_keys = list(TOLERANCE_COLORS.keys())
    closest_tolerance = min(tolerance_keys, key=lambda x: abs(x - tolerance_percent))
    
    bands.append({
        'color': TOLERANCE_COLORS[closest_tolerance],
        'position': len(bands) + 1,
        'value': closest_tolerance
    })
    
    return bands

