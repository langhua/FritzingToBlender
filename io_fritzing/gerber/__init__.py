from io_fritzing.gerber.excellon_parser import register as register_excellon_parser, unregister as unregister_excellon_parser
from io_fritzing.gerber.gerber_rs274x_parser import register as register_gerber_parser, unregister as unregister_gerber_parser

def register():
    """注册Gerber模块"""
    print("✅ 注册Gerber导入模块...")
    register_gerber_parser()
    register_excellon_parser()


def unregister():
    """注销Gerber模块"""
    print("注销Gerber导入模块...")
    unregister_gerber_parser()
    unregister_excellon_parser()
