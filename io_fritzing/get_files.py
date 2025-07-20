import bpy
from bpy.types import Operator
from bpy_extras.io_utils import ImportHelper
import os
import glob
from .report import importdata

##
# Get import files
class GetFiles(Operator, ImportHelper):
    bl_idname = "fritzing.select_svg_folder"
    bl_label = "Import SVG Folder"

    filename_ext = "."
    use_filter_folder = True

    def execute(self, context):
        directory = self.properties['filepath']
        cut = directory.rindex(os.path.sep[0])
        directory = directory[0:cut]
        tmp_filenames = glob.glob(os.path.join(directory, '*.svg'))
        # get filenames dictionary contains outline, bottom, top, bottomsilk, topsilk, drill
        filenames = dict()
        for filename in tmp_filenames:
            if filename.endswith('.gm1.svg'):
                filenames['outline'] = filename
            elif filename.endswith('.gbl.svg'):
                filenames['bottom'] = filename
            elif filename.endswith('.gtl.svg'):
                filenames['top'] = filename
            elif filename.endswith('_drill.txt.svg'):
                filenames['drill'] = filename
            elif filename.endswith('.gbo.svg'):
                filenames['bottomsilk'] = filename
            elif filename.endswith('.gto.svg'):
                filenames['topsilk'] = filename

        importdata.filenames = filenames
        importdata.total = len(filenames.items()) + 5 # total steps
        importdata.current = 1
        importdata.step_name = 'IMPORTING_SVG_FILES'
        bpy.ops.fritzing.board_settings("INVOKE_DEFAULT")
        return {"FINISHED"}
