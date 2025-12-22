import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from bpy.types import Scene
from io_fritzing.assets.resistors.color_band_resistors import register as register_resistor_color_bands, unregister as unregister_resistor_color_bands
from io_fritzing.assets.resistors.eia_96 import register as register_resistor_eia_96, unregister as unregister_resistor_eia_96
from io_fritzing.assets.resistors.smd_resistors import register as register_resistor_smd, unregister as unregister_resistor_smd
from io_fritzing.assets.resistors.YC164 import register as register_resistor_YC164, unregister as unregister_resistor_YC164

# 注册函数
def register():
    # 定义场景属性
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, 'icons')
    setattr(Scene, "resistor_icon_path", icons_dir)
    
    # 注册类
    register_resistor_color_bands()
    register_resistor_eia_96()
    register_resistor_smd()
    register_resistor_YC164()
    
    print("电阻模型生成器插件已注册")

def unregister():
    # 注销类
    unregister_resistor_smd()
    unregister_resistor_color_bands()
    unregister_resistor_eia_96()
    unregister_resistor_YC164()
    
    # 删除场景属性
    delattr(Scene, "resistor_icon_path")
    
    print("注销了电阻模型生成器插件")

