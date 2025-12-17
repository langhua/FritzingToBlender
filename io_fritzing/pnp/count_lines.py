import bpy
from bpy.types import Operator
from io_fritzing.pnp.import_pnp_report import importdata


##
# 统计行数
class CountLines(Operator):
    bl_idname = "fritzing.count_pnp_lines"
    bl_label = "Count PNP Lines"

    def execute(self, context):
        print("开始统计行数...")
        lines = simple_count_lines(importdata.filename)
        print(f"文件 {importdata.filename} 共有 {lines} 行")
        importdata.total_lines = lines
        importdata.current_line = 0

        importdata.step_name = 'PNP_PARSE_LINE_BY_LINE'
        getattr(getattr(bpy.ops, 'fritzing'), 'pnp_parse_line_by_line')("INVOKE_DEFAULT")
        return {"FINISHED"}

def simple_count_lines(filepath):
    """这里用的是最简单的方法：一次性读取所有行"""
    try:
        # 转换为绝对路径（处理Blender相对路径）
        abs_path = bpy.path.abspath(filepath)
        
        with open(abs_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            return len(lines)
    except Exception as e:
        print(f"读取文件失败: {e}")
        importdata.error_msg = str(e)
        getattr(getattr(bpy.ops, 'fritzing'), 'pnp_import_error')("INVOKE_DEFAULT")
        return 0
