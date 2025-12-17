import bpy
from bpy.props import FloatProperty, StringProperty
from bpy.types import Operator, Scene
from io_fritzing.pnp.pnp_import_data import PnpImportData


# a variable where we can store the original draw funtion
info_header_draw = lambda s, c: None

def update(self, context):
    areas = context.window.screen.areas
    for area in areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()

importdata = PnpImportData(filename='',
                            step_name='',
                            total_lines=0,
                            current_line=0,
                            error_msg=None,
                            step_part='',
                            successed=0,
                            failed=0,
                            skipped=0,
                            invalid=0,
                            failed_lines=[],
                            invalid_lines=[])


class PnpImportProgressReport(Operator):
    bl_idname = 'fritzing.pnp_import_progress_report'
    bl_label = 'Fritzing PNP Import Progress Report'
    bl_options = {'REGISTER'}

    def modal(self, context, event):
        if event.type == 'TIMER' and importdata.step_name == 'IMPORTING_PNP_FILE':
            self.ticks += 1
            getattr(getattr(bpy.ops, 'fritzing'), 'import_single_pnp')("INVOKE_DEFAULT")
        elif event.type == 'TIMER' and importdata.step_name and importdata.step_name.startswith('POST_'):
            self.ticks += 1
            if importdata.step_name == 'POST_REMOVE_EXTRA_VERTS':
                if context and hasattr(context.scene, 'progress_indicator_text'):
                    setattr(context.scene, 'progress_indicator_text', 'Removing extra verts ...')
                getattr(getattr(bpy.ops, 'fritzing'), 'remove_extra_verts')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_EXTRUDE':
                if context and hasattr(context.scene, 'progress_indicator_text'):
                    setattr(context.scene, 'progress_indicator_text', 'Extruding ...')
                getattr(getattr(bpy.ops, 'fritzing'), 'extrude')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_CREATE_MATERIAL':
                if context and hasattr(context.scene, 'progress_indicator_text'):
                    setattr(context.scene, 'progress_indicator_text', 'Creating materials ...')
                getattr(getattr(bpy.ops, 'fritzing'), 'create_materials')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_DRILL_HOLES':
                if context and hasattr(context.scene, 'progress_indicator_text'):
                    setattr(context.scene, 'progress_indicator_text', 'Drilling holes ...')
                getattr(getattr(bpy.ops, 'fritzing'), 'drill_holes')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_CLEAN_DRILL':
                if context and hasattr(context.scene, 'progress_indicator_text'):
                    setattr(context.scene, 'progress_indicator_text', 'Cleaning drilled holes ...')
                getattr(getattr(bpy.ops, 'fritzing'), 'clean_drill_holes')("INVOKE_DEFAULT")
            elif importdata.step_name == 'POST_MERGE_LAYERS':
                if context and hasattr(context.scene, 'progress_indicator_text'):
                    setattr(context.scene, 'progress_indicator_text', 'Merging layers ...')
                getattr(getattr(bpy.ops, 'fritzing'), 'merge_layers')("INVOKE_DEFAULT")
        elif event.type == 'TIMER' and importdata.step_name == 'FINISHED':
            self.ticks += 1

        if self.ticks > 12:
            if context and hasattr(context.scene, 'progress_indicator'):
                setattr(context.scene, 'progress_indicator', 101)  # done
            if context:
                context.window_manager.event_timer_remove(self.timer)
            return {'CANCELLED'}

        # total steps = 12
        if context and hasattr(context.scene, 'progress_indicator'):
            setattr(context.scene, 'progress_indicator', self.ticks*100/12)

        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        self.ticks = 0
        if context:
            wm = context.window_manager
            self.timer = wm.event_timer_add(1.0, window=context.window)
            wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def register():
    # a value between [0,100] will show the slider
    setattr(Scene, 'progress_indicator', FloatProperty(
                                    default=-1,
                                    subtype='PERCENTAGE',
                                    precision=1,
                                    min=-1,
                                    soft_min=0,
                                    soft_max=100,
                                    max=101,
                                    update=update))

    # the label in front of the slider can be configured
    setattr(Scene, 'progress_indicator_text', StringProperty(
                                    default="Starting SVG import ...",
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
        if context.scene.progress_indicator >= 0 and context.scene.progress_indicator <= 100:
            layout = self.layout
            layout.ui_units_x = 40
            layout.alert = True
            layout.separator()
            text = context.scene.progress_indicator_text
            layout.prop(context.scene,
                             property='progress_indicator',
                             text=text,
                             slider=True)

    # replace it
    bpy.types.VIEW3D_HT_tool_header.draw = newdraw


def unregister():
    global info_header_draw
    bpy.types.VIEW3D_HT_tool_header.draw = info_header_draw
