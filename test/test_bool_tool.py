import bpy
from bpy.props import FloatProperty, StringProperty
from bpy.types import Operator, Scene
import time


# a variable where we can store the original draw funtion
info_header_draw = lambda s,c: None

def update(self, context):
    areas = context.window.screen.areas
    for area in areas:
        if area.type == 'VIEW_3D':
            area.tag_redraw()


class TestBoolTool(Operator):
    bl_idname = 'fritzing.test_bool_tool'
    bl_label = 'Test Bool Tool'

    def modal(self, context, event):
        if event.type == 'TIMER':
            self.ticks += 1
            if self.step_name is None:
                context.scene.test_progress_indicator_text = 'Creating 1 cube and 2 cylinders ...'
                bpy.ops.mesh.primitive_cube_add(size = 2,
                                                location = (0, 0, 0))
                
                self.test_cube = bpy.context.active_object
                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.mesh.primitive_cylinder_add(radius = 0.5,
                                                    depth = 3,
                                                    location = (-0.2, 0, 0),
                                                    rotation = (0, 0, 0))
                self.test_cylinder1 = context.active_object

                bpy.ops.object.select_all(action='DESELECT')
                bpy.ops.mesh.primitive_cylinder_add(radius = 0.5,
                                                    depth = 3,
                                                    location = (0.2, 0, 0),
                                                    rotation = (0, 0, 0))
                self.test_cylinder2 = context.active_object
                self.step_name = 'pause'
            elif self.step_name == 'pause':
                time.sleep(1)
                self.step_name = 'bool_tool'
            elif self.step_name == 'bool_tool':
                context.scene.test_progress_indicator_text = 'Using bool tool ...'
                bpy.ops.object.select_all(action='DESELECT')
                self.test_cube.select_set(True)
                bpy.context.view_layer.objects.active = self.test_cube
                self.test_cylinder1.select_set(True)
                self.test_cylinder2.select_set(True)
                bpy.ops.object.boolean_auto_difference()
                self.step_name = 'finished'

        if self.ticks > 3:
            context.scene.test_progress_indicator = 101 # done
            context.window_manager.event_timer_remove(self.timer)
            return {'CANCELLED'}

        # total steps = 1
        context.scene.test_progress_indicator = self.ticks*25

        return {'RUNNING_MODAL'}
    
    def invoke(self, context, event):
        self.ticks = 0
        self.step_name = None
        wm = context.window_manager
        self.timer = wm.event_timer_add(1.0, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


def register():
    # a value between [0,100] will show the slider
    Scene.test_progress_indicator = FloatProperty(
                                    default=-1,
                                    subtype='PERCENTAGE',
                                    precision=1,
                                    min=-1,
                                    soft_min=0,
                                    soft_max=100,
                                    max=101,
                                    update=update)

    # the label in front of the slider can be configured
    Scene.test_progress_indicator_text = StringProperty(
                                    default="Start to test Bool Tool ...",
                                    update=update)

    # save the original draw method of the Info header
    global info_header_draw
    info_header_draw = bpy.types.VIEW3D_HT_tool_header.draw

    # create a new draw function
    def newdraw(self, context):
        # first call the original stuff
        global info_header_draw
        info_header_draw(self, context)
        # then add the prop that acts as a progress indicator
        if context.scene.test_progress_indicator >= 0 and context.scene.test_progress_indicator <= 100:
            layout = self.layout
            layout.ui_units_x = 40
            layout.alert = True
            layout.separator()
            text = context.scene.test_progress_indicator_text
            layout.prop(context.scene,
                             property='test_progress_indicator',
                             text=text,
                             slider=True)

    # replace it
    bpy.types.VIEW3D_HT_tool_header.draw = newdraw
    bpy.types.VIEW3D_HT_tool_header.draw = newdraw


def unregister():
    global info_header_draw
    bpy.types.VIEW3D_HT_tool_header.draw = info_header_draw
