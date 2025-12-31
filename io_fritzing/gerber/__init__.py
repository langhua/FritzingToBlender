# from io_fritzing.gerber.importer import register as register_gerber, unregister as unregister_gerber
# from io_fritzing.gerber.files_import import register as register_files_import, unregister as unregister_files_import
# from io_fritzing.gerber.gerber_import import register as register_gerber_regions, unregister as unregister_gerber_regions
from io_fritzing.gerber.drill_import import register as register_drill_fixed, unregister as unregister_drill_fixed

def register():
    """注册Gerber模块"""
    print("✅ 注册Gerber导入模块...")
    # register_gerber_regions()
    # register_files_import()
    register_drill_fixed()

def unregister():
    """注销Gerber模块"""
    print("注销Gerber导入模块...")
    # unregister_gerber_regions()
    # unregister_files_import()
    unregister_drill_fixed()
