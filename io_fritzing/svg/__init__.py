# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import sys
import os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

import bpy
from .import_single_svg import ImportSingleSVG
from .get_files import GetFiles
from .report import register as FritzingIORegister, unregister as FritzingIOUnregister
from .error_dialog import ErrorDialog
from .clean_drill_holes import CleanDrillHoles
from .create_materials import CreateMaterials
from .drill_holes import DrillHoles
from .extrude import Extrude
from .merge_layers import MergeLayers
from .remove_extra_verts import RemoveExtraVerts
from .ui_labels import langs
from .board_settings import BoardSettings, register as BoardSettingsRegister, unregister as BoardSettingsUnregister

# from .test.test_bool_tool import TestBoolTool, register as TestBoolToolRegister, unregister as TestBoolToolUnregister

def menu_import(self, _):
    """
    Calls the Fritzing PCB import operator from the menu item.
    """
    self.layout.operator(GetFiles.bl_idname)
    # self.layout.operator(ErrorDialog.bl_idname)
    # self.layout.operator(TestBoolTool.bl_idname)
    # self.layout.operator(BoardSettings.bl_idname)

classes = (
    GetFiles,
    ImportSingleSVG,
    ErrorDialog,
    CleanDrillHoles,
    CreateMaterials,
    DrillHoles,
    Extrude,
    MergeLayers,
    RemoveExtraVerts,
    BoardSettings,
    # TestBoolTool,
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
    FritzingIORegister()
    BoardSettingsRegister()
    # TestBoolToolRegister()

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
    FritzingIOUnregister()
    BoardSettingsUnregister()
    # TestBoolToolUnregister()

# Allow the add-on to be ran directly without installation.
if __name__ == "__main__":
    register()
