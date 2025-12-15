import bpy
from io_fritzing.pnp.import_single_pnp import GetPnpFile
from io_fritzing.pnp.ui_labels import langs

def menu_import(self, _):
    """
    Calls the Fritzing PNP import operator from the menu item.
    """
    self.layout.operator(GetPnpFile.bl_idname)


classes = (
    GetPnpFile,
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

