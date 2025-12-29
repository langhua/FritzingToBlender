import bpy
import os
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
from io_fritzing.pnp.import_pnp_report import importdata


##
# Get pnp file to import
class GetPnpFile(Operator, ImportHelper):
    bl_idname = "fritzing.select_pnp_file"
    bl_label = "Import PNP File"

    filename_ext = "_pnp.xy"
    use_filter_folder = True

    def execute(self, context):
        # 打印提示信息，表示正在获取PNP文件
        print("GetPnpFile file:")
        # 打印文件路径属性
        print(self.properties['filepath'])
        # 获取文件路径
        filename = self.properties['filepath']
        if os.path.isdir(filename):
            self.report({'ERROR'}, "Please select a file, not a folder.")
            return {"CANCELLED"}
        if os.path.exists(filename) == False:
            self.report({'ERROR'}, "File does not exist.")
            return {"CANCELLED"}
        if not filename.endswith(self.filename_ext):
            self.report({'ERROR'}, "File must end with " + self.filename_ext)
            return {"CANCELLED"}

        # 将分类后的文件名保存到importdata模块中
        importdata.filename = filename
        importdata.step_name = 'PNP_FILE_LINE_COUNT'
        # 调用PNP导入原点对话框
        getattr(getattr(bpy.ops, 'fritzing'), 'pnp_settings_dialog')("INVOKE_DEFAULT")
        return {"FINISHED"}
