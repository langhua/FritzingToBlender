def resistance_to_3digit(resistance: float) -> str:
    """
    将电阻值转换为3位代码
    
    规则：
    1. 小于0.01Ω: 四舍五入到0.01Ω，返回R01
    2. 0.01Ω-0.99Ω: 用R表示小数点，乘以100取整，如0.47Ω -> R47
    3. 1Ω-9.9Ω: XRZ格式，如4.7Ω -> 4R7
    4. 10Ω-99Ω: 直接显示数字，如47Ω -> 47R
    5. 100Ω以上: 使用标准3位代码
    """
    if resistance <= 0:
        return "000"
    
    # 处理小于0.01Ω的情况
    if resistance < 0.01:
        # 四舍五入到0.01Ω
        return "R01"
    
    # 处理0.01Ω-0.99Ω
    if resistance < 1:
        # 乘以100，四舍五入到整数
        value = round(resistance * 100)
        if value < 10:
            return f"R0{value}"
        else:
            return f"R{value}"
    
    # 处理1Ω-9.9Ω
    if resistance < 10:
        # 四舍五入到1位小数
        rounded = round(resistance, 1)
        int_part = int(rounded)
        decimal_part = int((rounded * 10) % 10)
        return f"{int_part}R{decimal_part}"
    
    # 处理10Ω-99Ω
    if resistance < 100:
        # 四舍五入到整数
        rounded = round(resistance)
        return f"{rounded}R"
    
    # 处理100Ω以上
    # 标准3位代码：ABX 表示 AB × 10^X
    value = resistance
    
    # 尝试不同的乘数
    for exp in range(0, 10):  # 乘数0-9
        base_value = value / (10 ** exp)
        if 10 <= base_value < 100:
            # 四舍五入到整数
            digits = round(base_value)
            if 10 <= digits < 100:
                digit1 = digits // 10
                digit2 = digits % 10
                return f"{digit1}{digit2}{exp}"
    
    # 如果找不到合适的乘数，使用默认
    return "000"
