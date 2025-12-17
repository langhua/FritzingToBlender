import bpy
from .import_single_pnp import GetPnpFile
from .count_lines import CountLines
from .error_dialog import ErrorDialog
from io_fritzing.pnp.parse_line_by_line import PnpParseLineByLine
from io_fritzing.pnp.import_pnp_report import PnpImportProgressReport
from io_fritzing.pnp.ui_labels import langs

def menu_import(self, _):
    """
    Calls the Fritzing PNP import operator from the menu item.
    """
    self.layout.operator(GetPnpFile.bl_idname)


classes = (
    GetPnpFile,
    CountLines,
    ErrorDialog,
    PnpImportProgressReport,
    PnpParseLineByLine,
)


def register():
    bpy.app.translations.register(__name__, langs)
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.TOPBAR_MT_file_import.append(menu_import)


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    bpy.types.TOPBAR_MT_file_import.remove(menu_import)
    bpy.app.translations.unregister(__name__)


# Allow the add-on to be ran directly without installation.
if __name__ == "__main__":
    register()

