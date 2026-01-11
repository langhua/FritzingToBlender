import bpy
import os
import winsound
from bpy.props import FloatProperty, StringProperty
from bpy.types import Operator, Scene
from io_fritzing.svg.commondata import PCBImportData


# a variable where we can store the original draw funtion
info_header_draw = lambda s, c: None

def update(self, context):
    areas = context.window.screen.areas
    for area in areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

importdata = PCBImportData(filenames=dict(),
                            svgLayers=dict(),
                            total=0,
                            current=0,
                            step_name = 'IMPORTING_GERBER_FILES',
                            error_msg=None,
                            current_file='',
                            board_thickness=0.0018,
                            board_color='',
                            silk_color='',
                            diameter_summary={})


class GerberProgressReport(Operator):
    bl_idname = 'fritzing.gerber_progress_report'
    bl_label = 'Fritzing Gerber Import Progress Report'
    bl_options = {'REGISTER'}

    ticks = 0

    def modal(self, context, event):
        if event.type == 'TIMER' and importdata.step_name == 'IMPORTING_GERBER_FILES':
            self.ticks += 1
            getattr(getattr(bpy.ops, 'fritzing'), 'import_single_gerber')("INVOKE_DEFAULT")
        elif event.type == 'TIMER' and importdata.step_name and importdata.step_name.startswith('POST_'):
            self.ticks += 1
            if importdata.step_name == 'POST_GERBER_EXTRUDE':
                if context and hasattr(context.scene, 'gerber_progress_indicator_text'):
                    setattr(context.scene, 'gerber_progress_indicator_text', 'Extruding ...')
                    update(self, context)
                getattr(getattr(bpy.ops, 'fritzing'), 'gerber_extrude')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_GERBER_CREATE_MATERIAL':
                print('--POST_GERBER_CREATE_MATERIAL')
                if context and hasattr(context.scene, 'gerber_progress_indicator_text'):
                    setattr(context.scene, 'gerber_progress_indicator_text', 'Creating materials ...')
                    update(self, context)
                getattr(getattr(bpy.ops, 'fritzing'), 'gerber_create_materials')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_GERBER_DRILL_HOLES':
                print('--POST_GERBER_DRILL_HOLES')
                if context and hasattr(context.scene, 'gerber_progress_indicator_text'):
                    setattr(context.scene, 'gerber_progress_indicator_text', 'Drilling holes ...')
                    update(self, context)
                getattr(getattr(bpy.ops, 'fritzing'), 'gerber_drill_holes')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_GERBER_CLEAN_DRILL':
                print('--POST_GERBER_CLEAN_DRILL')
                if context and hasattr(context.scene, 'gerber_progress_indicator_text'):
                    setattr(context.scene, 'gerber_progress_indicator_text', 'Cleaning drilled holes ...')
                    update(self, context)
                getattr(getattr(bpy.ops, 'fritzing'), 'gerber_clean_drill_holes')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_GERBER_MERGE_LAYERS':
                print('--POST_GERBER_MERGE_LAYERS')
                if context and hasattr(context.scene, 'gerber_progress_indicator_text'):
                    setattr(context.scene, 'gerber_progress_indicator_text', 'Merging layers ...')
                    update(self, context)
                getattr(getattr(bpy.ops, 'fritzing'), 'gerber_merge_layers')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_GERBER_MERGE_CYLINDERS':
                print('--POST_GERBER_DRILL_CYLINDERS')
                if context and hasattr(context.scene, 'gerber_progress_indicator_text'):
                    setattr(context.scene, 'gerber_progress_indicator_text', 'Merging drill cylinders ...')
                    update(self, context)
                getattr(getattr(bpy.ops, 'fritzing'), 'gerber_merge_cylinders')("INVOKE_DEFAULT")
        elif event.type == 'TIMER' and importdata.step_name == 'FINISHED':
            update(self, context)
            self.ticks += 1

        if self.ticks > 12:
            if context and hasattr(context.scene, 'gerber_progress_indicator'):
                setattr(context.scene, 'gerber_progress_indicator', 101)  # done
            if context:
                context.window_manager.event_timer_remove(self.timer)
            if os.name == 'nt':
                frequency = 1500
                # Set Duration To 1000 ms == 1 second
                duration = 1000
                winsound.Beep(frequency, duration)
            return {'CANCELLED'}

        # total steps = 12
        if context and hasattr(context.scene, 'gerber_progress_indicator'):
            setattr(context.scene, 'gerber_progress_indicator', self.ticks*100/12)

        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        self.ticks = 0
        if context:
            wm = context.window_manager
            self.timer = wm.event_timer_add(1.0, window=context.window)
            wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def register():
    bpy.utils.register_class(GerberProgressReport)

    # a value between [0,100] will show the slider
    setattr(Scene, 'gerber_progress_indicator', FloatProperty(
                                    default=-1,
                                    subtype='PERCENTAGE',
                                    precision=1,
                                    min=-1,
                                    soft_min=0,
                                    soft_max=100,
                                    max=101,
                                    update=update))

    # the label in front of the slider can be configured
    setattr(Scene, 'gerber_progress_indicator_text', StringProperty(
                                    default="Starting Gerber import ...",
                                    update=update))

    # save the original draw method of the Info header
    global info_header_draw
    info_header_draw = bpy.types.VIEW3D_HT_tool_header.draw

    # create a new draw function
    def newdraw(self, context):
        # first call the original stuff
        # global info_header_draw
        # info_header_draw(self, context)
        # then add the prop that acts as a progress indicator
        if context.scene.gerber_progress_indicator >= 0 and context.scene.gerber_progress_indicator <= 100:
            layout = self.layout
            layout.ui_units_x = 40
            layout.alert = True
            layout.separator()
            text = context.scene.gerber_progress_indicator_text
            layout.prop(context.scene,
                             property='gerber_progress_indicator',
                             text=text,
                             slider=True)

    # replace it
    bpy.types.VIEW3D_HT_tool_header.draw = newdraw


def unregister():
    global info_header_draw
    bpy.types.VIEW3D_HT_tool_header.draw = info_header_draw
    bpy.utils.unregister_class(GerberProgressReport)
    delattr(Scene, 'gerber_progress_indicator_text')
    delattr(Scene, 'gerber_progress_indicator')
