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

import bpy
from .io_fritzing.import_single_svg import ImportSingleSVG
from .io_fritzing.get_files import GetFiles
from .io_fritzing.report import register as FritzingIORegister, unregister as FritzingIOUnregister
from .io_fritzing.report import ProgressReport
from .io_fritzing.error_dialog import ErrorDialog
from .io_fritzing.clean_drill_holes import CleanDrillHoles
from .io_fritzing.create_materials import CreateMaterials
from .io_fritzing.drill_holes import DrillHoles
from .io_fritzing.extrude import Extrude
from .io_fritzing.merge_layers import MergeLayers
from .io_fritzing.remove_extra_verts import RemoveExtraVerts
from .io_fritzing.ui_labels import langs


def menu_import(self, _):
    """
    Calls the Fritzing PCB import operator from the menu item.
    """
    self.layout.operator(GetFiles.bl_idname, text="Fritzing PCB SVG Folder (.svg)")
    # self.layout.operator(ProgressReport.bl_idname)
    # self.layout.operator(ErrorDialog.bl_idname)


classes = (
    GetFiles,
    ImportSingleSVG,
    ErrorDialog,
    ProgressReport,
    CleanDrillHoles,
    CreateMaterials,
    DrillHoles,
    Extrude,
    MergeLayers,
    RemoveExtraVerts,
)

def register():
    bpy.app.translations.register(__name__, langs)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)
    FritzingIORegister()

def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    FritzingIOUnregister()
    bpy.app.translations.unregister(__name__)


# Allow the add-on to be ran directly without installation.
if __name__ == "__main__":
    register()

