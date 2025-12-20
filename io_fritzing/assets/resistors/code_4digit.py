def resistance_to_4digit(resistance: float) -> str:
    """
    将电阻值转换为4位代码
    
    规则：
    1. 小于0.001Ω: 四舍五入到0.001Ω，返回R001
    2. 0.001Ω-0.999Ω: 用R表示小数点，乘以1000取整，如0.047Ω -> R047
    3. 1Ω-9.99Ω: XRZZ格式，如4.7Ω -> 4R70
    4. 10Ω-99.9Ω: XXRZ格式，如47Ω -> 47R0
    5. 100Ω以上: 使用标准4位代码
    """
    if resistance <= 0:
        return "0000"
    
    # 处理小于0.001Ω的情况
    if resistance < 0.001:
        # 四舍五入到0.001Ω
        return "R001"
    
    # 处理0.001Ω-0.999Ω
    if resistance < 1:
        # 乘以1000，四舍五入到整数
        value = round(resistance * 1000)
        if value < 10:
            return f"R00{value}"
        elif value < 100:
            return f"R0{value}"
        else:
            return f"R{value}"
    
    # 处理1Ω-9.99Ω
    if resistance < 10:
        # 四舍五入到2位小数
        rounded = round(resistance, 2)
        int_part = int(rounded)
        decimal_part = int((rounded * 100) % 100)
        return f"{int_part}R{decimal_part:02d}"
    
    # 处理10Ω-99.9Ω
    if resistance < 100:
        # 四舍五入到1位小数
        rounded = round(resistance, 1)
        
        # 分离整数和小数部分
        int_part = int(rounded)
        decimal_part = int((rounded * 10) % 10)
        
        # 格式化为 XXRZ，其中XX是两位整数，Z是小数位
        # 注意：整数部分可能是1位或2位，我们需要确保总是输出4位字符
        if int_part < 10:
            # 整数部分1位，补0变成两位
            return f"0{int_part}R{decimal_part}"
        else:
            # 整数部分2位
            return f"{int_part}R{decimal_part}"
    
    # 处理100Ω以上
    # 标准4位代码：ABCX 表示 ABC × 10^X
    value = resistance
    
    # 尝试不同的乘数
    for exp in range(0, 10):  # 乘数0-9
        base_value = value / (10 ** exp)
        if 100 <= base_value < 1000:
            # 四舍五入到整数
            digits = round(base_value)
            if 100 <= digits < 1000:
                digit1 = digits // 100
                digit2 = (digits // 10) % 10
                digit3 = digits % 10
                return f"{digit1}{digit2}{digit3}{exp}"
    
    # 如果找不到合适的乘数，使用默认
    return "0000"

def test_resistance_4digit_calculations():
    """测试4位电阻值计算"""
    test_cases_4digit = [
        (0.0047, "0.0047Ω → R005"),
        (0.047, "0.047Ω → R047"),
        (0.47, "0.47Ω → R470"),
        (4.7, "4.7Ω → 4R70"),
        (47, "47Ω → 47R0"),
        (470, "470Ω → 4700"),
        (4700, "4.7kΩ → 4701"),
        (10000, "10kΩ → 1002"),
        (100, "100Ω → 1000"),
        (2200, "2.2kΩ → 2201"),
    ]
    
    print("=" * 60)
    print("贴片电阻4位代码计算测试")
    print("=" * 60)
    
    all_passed_4digit = True
    for resistance, description in test_cases_4digit:
        code_4digit = resistance_to_4digit(resistance)
        expected = description.split("→ ")[1]
        
        status = "✓" if code_4digit == expected else "✗"
        
        if code_4digit != expected:
            all_passed_4digit = False
        
        print(f"{status} {description}")
        print(f"  计算值: {code_4digit}")
        
        if code_4digit != expected:
            print(f"  错误: 期望 {expected}, 得到 {code_4digit}")
    
    print("-" * 40)
    
    if all_passed_4digit:
        print("✓ 所有4位测试通过！")
    else:
        print("✗ 有4位测试失败")
    
    print("=" * 60)
    
    return all_passed_4digit

if __name__ == "__main__":
    test_resistance_4digit_calculations()
