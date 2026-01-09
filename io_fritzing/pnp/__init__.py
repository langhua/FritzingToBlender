import bpy
from io_fritzing.pnp.ui_labels import langs
from io_fritzing.pnp.pnp_import import register as register_pnp_settings, unregister as unregister_pnp_settings

classes = (
)


def register():
    bpy.app.translations.register(__name__, langs)
    for cls in classes:
        bpy.utils.register_class(cls)
    register_pnp_settings()


def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
    unregister_pnp_settings()
    bpy.app.translations.unregister(__name__)


# Allow the add-on to be ran directly without installation.
if __name__ == "__main__":
    register()
