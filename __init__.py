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
from .import_pcb import ImportPCB, ErrorDialog

def menu_import(self, _):
    """
    Calls the Fritzing PCB import operator from the menu item.
    """
    self.layout.operator(ImportPCB.bl_idname, text="Fritzing PCB SVG Folder (.svg)")


classes = (
    ImportPCB,
    ErrorDialog
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)


# Allow the add-on to be ran directly without installation.
if __name__ == "__main__":
    register()
