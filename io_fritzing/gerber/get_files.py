import bpy
from bpy.types import Operator
from bpy.props import StringProperty
from bpy_extras.io_utils import ImportHelper
import os
import glob
from io_fritzing.gerber.report import importdata

##
# Get import files
class GerberGetFiles(Operator, ImportHelper):
    bl_idname = "fritzing.select_gerber_folder"
    bl_label = "Import Gerber Folder"

    use_filter_folder = True

    filter_glob: StringProperty(
        default="*.gm1;*.gbl;*.gtl;*drill.txt;*.gbo;*.gto;",
        options={'HIDDEN'}
    ) # type: ignore

    def execute(self, context):
        directory = self.properties['filepath']
        cut = directory.rindex(os.path.sep[0])
        directory = directory[0:cut]
        tmp_filenames = glob.glob(os.path.join(directory, '*.*'))
        # get filenames dictionary contains outline, bottom, top, bottomsilk, topsilk, drill
        filenames = dict()
        for filename in tmp_filenames:
            if filename.endswith('.gm1'):
                filenames['outline'] = filename
            elif filename.endswith('.gbl'):
                filenames['bottom'] = filename
            elif filename.endswith('.gtl'):
                filenames['top'] = filename
            elif filename.endswith('_drill.txt'):
                filenames['drill'] = filename
            elif filename.endswith('.gbo'):
                filenames['bottomsilk'] = filename
            elif filename.endswith('.gto'):
                filenames['topsilk'] = filename

        importdata.filenames = filenames
        importdata.total = len(filenames.items()) + 5 # total steps
        importdata.current = 1
        importdata.step_name = 'IMPORTING_GERBER_FILES'
        getattr(getattr(bpy.ops, 'fritzing'), 'gerber_board_settings')("INVOKE_DEFAULT")
        return {"FINISHED"}
