from PIL import Image, ImageDraw, ImageFilter, ImageFont
import os

# 电阻色环颜色定义 (RGB)
RESISTOR_COLORS = {
    'black': (0, 0, 0),           # 黑色
    'brown': (139, 69, 19),       # 棕色
    'red': (255, 0, 0),           # 红色
    'orange': (255, 165, 0),      # 橙色
    'yellow': (255, 255, 0),      # 黄色
    'green': (0, 128, 0),         # 绿色
    'blue': (0, 0, 255),          # 蓝色
    'violet': (148, 0, 211),      # 紫色
    'gray': (128, 128, 128),      # 灰色
    'white': (255, 255, 255),     # 白色
    'gold': (255, 215, 0),        # 金色
    'silver': (192, 192, 192),    # 银色
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

# 创建图标目录
os.makedirs('icons', exist_ok=True)

def create_resistor_icon(color_name, rgb_color, size=32, border_radius=4):
    """创建电阻色环图标"""
    # 创建新图像
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制圆角矩形背景
    draw.rounded_rectangle(
        [(2, 2), (size-3, size-3)],  # 坐标
        radius=border_radius,         # 圆角半径
        fill=rgb_color,               # 填充颜色
        outline=(100, 100, 100),      # 边框颜色
        width=1                       # 边框宽度
    )
    
    # 添加一点阴影效果
    shadow_img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_img)
    shadow_draw.rounded_rectangle(
        [(0, 0), (size-1, size-1)],
        radius=border_radius,
        fill=(0, 0, 0, 30)
    )
    shadow_img = shadow_img.filter(ImageFilter.GaussianBlur(radius=1))
    
    # 合并图像
    img = Image.alpha_composite(shadow_img, img)
    
    # 保存为PNG
    filename = f"icons/icon_{color_name}.png"
    img.save(filename, 'PNG', quality=95)
    print(f"已创建: {filename}")
    
    return img

def get_chinese_font():
    """获取中文字体路径（跨平台）"""
    # Windows字体路径
    windows_fonts = [
        "C:/Windows/Fonts/simhei.ttf",  # 黑体
        "C:/Windows/Fonts/simsun.ttc",  # 宋体
        "C:/Windows/Fonts/msyh.ttc",    # 微软雅黑
    ]
    
    # macOS字体路径
    mac_fonts = [
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
    ]
    
    # Linux字体路径
    linux_fonts = [
        "/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]
    
    # 按平台尝试字体路径
    import platform
    system = platform.system()
    
    if system == "Windows":
        for font_path in windows_fonts:
            if os.path.exists(font_path):
                return font_path
    elif system == "Darwin":  # macOS
        for font_path in mac_fonts:
            if os.path.exists(font_path):
                return font_path
    elif system == "Linux":
        for font_path in linux_fonts:
            if os.path.exists(font_path):
                return font_path
    
    return None  # 没有找到中文字体

def create_resistor_color_preview():
    """创建电阻色环颜色预览图（带中文）"""
    # 创建预览图
    preview_size = 600
    preview_img = Image.new('RGB', (preview_size, 400), (240, 240, 240))
    draw = ImageDraw.Draw(preview_img)
    
    # 尝试加载中文字体
    chinese_font_path = get_chinese_font()
    if chinese_font_path:
        try:
            title_font = ImageFont.truetype(chinese_font_path, 24)
            color_font = ImageFont.truetype(chinese_font_path, 12)
        except:
            # 如果加载失败，使用默认字体
            title_font = ImageFont.load_default()
            color_font = ImageFont.load_default()
    else:
        # 没有中文字体，使用默认
        title_font = ImageFont.load_default()
        color_font = ImageFont.load_default()
    
    # 添加中文标题
    draw.text((20, 20), "电阻色环颜色预览", font=title_font, fill=(0, 0, 0))
    
    # 计算布局
    icon_size = 60
    margin = 20
    icons_per_row = 6
    rows = 2
    
    for i, (color_name, rgb_color) in enumerate(RESISTOR_COLORS.items()):
        row = i // icons_per_row
        col = i % icons_per_row
        
        x = margin + col * (icon_size + margin)
        y = 80 + row * (icon_size + margin + 30)  # 为文本留出空间
        
        # 绘制色块
        draw.rectangle(
            [x, y, x + icon_size, y + icon_size],
            fill=rgb_color,
            outline=(100, 100, 100),
            width=2
        )
        
        # 添加中文颜色名称
        chinese_name = COLOR_NAMES_CN.get(color_name, color_name)
        
        # 计算文本宽度以居中
        if chinese_font_path:
            text_bbox = draw.textbbox((0, 0), chinese_name, font=color_font)
            text_width = text_bbox[2] - text_bbox[0]
        else:
            text_width = len(chinese_name) * 6  # 近似宽度
        
        text_x = x + (icon_size - text_width) // 2
        text_y = y + icon_size + 5
        
        text_color = (0, 0, 0)  # 深色文字
        
        # 绘制背景以增强可读性
        draw.rectangle(
            [text_x - 2, text_y - 2, text_x + text_width + 2, text_y + 14],
            fill=(240, 240, 240)
        )
        
        # 绘制中文颜色名称
        draw.text((text_x, text_y), chinese_name, font=color_font, fill=text_color)
        
        # 添加英文标签（小字）
        draw.text(
            (x + 5, y + icon_size + 20),
            color_name,
            font=color_font,
            fill=(100, 100, 100)
        )
    
    # 保存预览图
    os.makedirs('icons', exist_ok=True)
    preview_img.save('icons/color_preview_cn.png', 'PNG', quality=95)
    
    # 显示字体信息
    if chinese_font_path:
        print(f"使用字体: {chinese_font_path}")
    else:
        print("警告: 未找到中文字体，中文可能显示为方框")
    
    print("预览图已保存: icons/color_preview_cn.png")
    
    # 显示图片
    preview_img.show()

if __name__ == "__main__":
    # 生成所有颜色的图标
    print("正在生成电阻色环图标...")
    for color_name, rgb_color in RESISTOR_COLORS.items():
        create_resistor_icon(color_name, rgb_color)

    print(f"\n所有图标已保存到 'icons' 文件夹中！")

    # 创建预览图
    create_resistor_color_preview()
