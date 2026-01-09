import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import bpy
from io_fritzing.gerber.excellon_parser import register as register_excellon_parser, unregister as unregister_excellon_parser
from io_fritzing.gerber.gerber_rs274x_parser import register as register_gerber_parser, unregister as unregister_gerber_parser
from io_fritzing.gerber.get_files import GerberGetFiles
from io_fritzing.gerber.board_settings import GerberBoardSettings
from io_fritzing.gerber.report import register as register_report, unregister as unregister_report
from io_fritzing.gerber.ui_labels import langs
from io_fritzing.gerber.extrude import GerberExtrude
from io_fritzing.gerber.merge_layers import GerberMergeLayers
from io_fritzing.gerber.create_materials import GerberCreateMaterials
from io_fritzing.gerber.error_dialog import GerberErrorDialog
from io_fritzing.gerber.drill_holes import GerberDrillHoles

def menu_import(self, _):
    """
    Calls the Fritzing Gerber import operator from the menu item.
    """
    self.layout.operator(GerberGetFiles.bl_idname)

classes = (
    GerberGetFiles,
    GerberBoardSettings,
    GerberExtrude,
    GerberMergeLayers,
    GerberCreateMaterials,
    GerberErrorDialog,
    GerberDrillHoles,
)

def register():
    try:
        # 先尝试注销
        bpy.app.translations.unregister(__name__)
    except (ValueError, KeyError, RuntimeError) as e:
        # 如果没有注册，忽略错误
        pass

    # 注册翻译
    try:
        bpy.app.translations.register(__name__, langs)
    except ValueError as e:
        # 如果仍然失败，可能是其他问题
        print(f"Warning: Could not register translations: {e}")
    
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)

    """注册Gerber模块"""
    print("✅ 注册Gerber导入模块...")
    register_report()
    register_gerber_parser()
    register_excellon_parser()


def unregister():
    # 注销翻译
    try:
        bpy.app.translations.unregister(__name__)
    except (ValueError, KeyError, RuntimeError) as e:
        # 如果没有注册，忽略错误
        pass

    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)

    """注销Gerber模块"""
    print("注销Gerber导入模块...")
    unregister_report()
    unregister_gerber_parser()
    unregister_excellon_parser()

# Allow the add-on to be ran directly without installation.
if __name__ == "__main__":
    register()
