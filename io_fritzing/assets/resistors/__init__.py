import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import bpy
from bpy.types import Panel, Scene
from bpy.utils import register_class, unregister_class
from io_fritzing.assets.resistors.smd_resistor import SMD_RESISTOR_OT_Generate, ResistorTypes as SMDResisterTypes
from io_fritzing.assets.resistors.color_bands import register as register_resistor_color_bands, unregister as unregister_resistor_color_bands
from io_fritzing.assets.resistors.eia_96 import register as register_resistor_eia_96, unregister as unregister_resistor_eia_96

# 定义插件信息
bl_info = {
    "name": "电阻",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N > 电子元件 > 电阻",
    "description": "生成各种类型的电阻3D模型",
    "category": "3D View"
}

# 定义操作类
class VIEW3D_PT_CompactResistorGenerator(Panel):
    """紧凑版电阻生成器面板"""
    bl_label = "电阻"
    bl_idname = "VIEW3D_PT_compact_resistor_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电子元件模型"
    
    def draw(self, context):
        layout = self.layout
        
        if context:
            # 轴向电阻部分
            box = layout.box()
            spliter = box.split(factor=0.5)
            col_left = spliter.column()
            col_left.label(text="色环电阻")
            row = col_left.row()
            row.prop(context.scene, "axial_resistor_type", text="")
            row = col_left.row()
            row.operator("resistor.generate_axial", text="生成色环电阻")
            
            # 贴片电阻部分
            col_right = spliter.column()
            col_right.label(text="贴片电阻")
            row = col_right.row()
            row.prop(context.scene, "smd_resistor_size", text="")
            row = col_right.row()
            row.operator("resistor.generate_smd", text="生成贴片电阻")

# 注册函数
def register():
    # 定义场景属性
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, 'icons')
    print(f"Icon directory: {icons_dir}")
    setattr(Scene, "resistor_icon_path", icons_dir)
    setattr(Scene, "smd_resistor_size", SMDResisterTypes)
    
    # 注册类
    register_class(SMD_RESISTOR_OT_Generate)
    register_class(VIEW3D_PT_CompactResistorGenerator)

    register_resistor_color_bands()
    register_resistor_eia_96()
    
    print("电阻模型生成器插件已注册")

def unregister():
    # 注销类
    unregister_resistor_color_bands()
    unregister_resistor_eia_96()
    unregister_class(VIEW3D_PT_CompactResistorGenerator)
    unregister_class(SMD_RESISTOR_OT_Generate)
    
    # 删除场景属性
    delattr(Scene, "smd_resistor_size")
    
    print("注销了电阻模型生成器插件")

