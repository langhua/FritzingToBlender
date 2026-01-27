from bpy.types import Operator, Scene
import bpy
from bpy.props import EnumProperty
from ..svg.commondata import Board_Black, Board_Blue, Board_Green, Board_Purple, Board_Red, Board_White, Board_Yellow
from ..svg.commondata import Copper, Copper2, Silk_Black, Silk_White, Silk_White2
import os
import bpy.utils.previews as previews
from .report import importdata

##
# Dialog box to handle error messages
class GerberBoardSettings(Operator):
    bl_idname = "fritzing.gerber_board_settings"
    bl_label = "Fritzing Gerber PCB Settings"

    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "object"

    def draw(self, context):
        layout = self.layout
        # top margin
        row = layout.row()

        # board thickness
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.4
        col1.label(text='Board Thickness:')
        col2 = row.column()
        col2.scale_x = 0.6
        if context:
            col2.prop(context.scene, text='', property='gerber_board_thickness_setting')

        # board color
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.3
        col1.scale_y = 2
        col1.label(text='Board Color:')
        col2 = row.column()
        if context:
            col2.template_icon_view(context.scene, 'gerber_board_color_setting', scale=2)

        # copper color
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.3
        col1.scale_y = 2
        col1.label(text='Copper Color:')
        col2 = row.column()
        if context:
            col2.template_icon_view(context.scene, 'gerber_copper_color_setting', scale=2)

        # silk color
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.3
        col1.scale_y = 2
        col1.label(text='Silk Color:')
        col2 = row.column()
        if context:
            col2.template_icon_view(context.scene, 'gerber_silk_color_setting', scale=2)

        # drill cylinder filter
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.4
        col1.label(text='Cylinder Filter:')
        col2 = row.column()
        col2.scale_x = 0.6
        if context:
            col2.prop(context.scene, text='', property='gerber_cylinder_filter_setting')

        # drill algorithm
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.4
        col1.label(text='Drill Algorithm:')
        col2 = row.column()
        col2.scale_x = 0.6
        if context:
            col2.prop(context.scene, text='', property='gerber_drill_algorithm_setting')

        # bottom margin
        row = layout.row()


    def execute(self, context):
        if context:
            importdata.silk_color = getattr(context.scene, 'gerber_silk_color_setting')
            importdata.board_color = getattr(context.scene, 'gerber_board_color_setting')
            importdata.board_thickness = float(getattr(context.scene, 'gerber_board_thickness_setting'))
        getattr(getattr(bpy.ops, 'fritzing'), 'gerber_progress_report')("INVOKE_DEFAULT")
        return {"FINISHED"}
    
    def invoke(self, context, event):
        area_3d = None
        if bpy.context is not None:
            for area in bpy.context.screen.areas:
                if area.type == "VIEW_3D":
                    area_3d = area
                    break
            if area_3d:
                screen_width = area_3d.width
                screen_height = area_3d.height
                center_x = int(screen_width / 2) - 50
                center_y = int(screen_height / 2) + 300
                # Warp the cursor to the center of the 3D Viewport
                if context:
                    context.window.cursor_warp(center_x, center_y)
        if context:
            return context.window_manager.invoke_props_dialog(self)


board_color_items = []
copper_color_items = []
silk_color_items = []
board_thickness_items = []
drill_algorithm_items = []
cylinder_filter_items = []
global pcoll
pcoll = None

def register():
    global pcoll
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, '../../icons')

    bpy.utils.register_class(GerberBoardSettings)

    if len(board_thickness_items) == 0:
        board_thickness_items.extend([
            ('0.00154', '1.6mm', '', 0),
            ('0.00134', '1.4mm', '', 1),
            ('0.00114', '1.2mm', '', 2),
            ('0.00094', '1.0mm', '', 3),
        ])

        setattr(Scene, 'gerber_board_thickness_setting', EnumProperty(
            items=board_thickness_items,
            default='0.00154'  # Set the default value to 1.6mm, which is the most common PCB thickness
        ))

    if pcoll is None:
        pcoll = previews.new()

    if len(board_color_items) == 0:
        board_configs = [
            (Board_Green, 0),
            (Board_Red, 1),
            (Board_Blue, 2),
            (Board_White, 3),
            (Board_Black, 4),
            (Board_Yellow, 5),
            (Board_Purple, 6)
        ]

        for config, index in board_configs:
            icon = pcoll.load(config['name'], os.path.join(icons_dir, config['icon']), 'IMAGE')
            board_color_items.append((config['name'], config['name'], '', icon.icon_id, index))

        setattr(Scene, 'gerber_board_color_setting', EnumProperty(
            items=board_color_items,
            default=Board_Green['name']  # Set the default value to green
        ))

    if len(copper_color_items) == 0:
        copper_configs = [
            (Copper, 0),
            (Copper2, 1)
        ]

        for config, index in copper_configs:
            icon = pcoll.load(config['name'], os.path.join(icons_dir, config['icon']), 'IMAGE')
            copper_color_items.append((config['name'], config['name'], '', icon.icon_id, index))

        setattr(Scene, 'gerber_copper_color_setting', EnumProperty(
            items=copper_color_items,
            default=Copper['name']  # Set the default value to the first copper color
        ))

    if len(silk_color_items) == 0:
        silk_configs = [
                (Silk_White2, 0),
                (Silk_White, 1),
                (Silk_Black, 2)
            ]

        for config, index in silk_configs:
            icon = pcoll.load(config['name'], os.path.join(icons_dir, config['icon']), 'IMAGE')
            silk_color_items.append((config['name'], config['name'], '', icon.icon_id, index))

        setattr(Scene, 'gerber_silk_color_setting', EnumProperty(
            items=silk_color_items,
            default=Silk_White['name']  # Set the default value to white
        ))
  
    if len(drill_algorithm_items) == 0:
        drill_algorithm_items.extend([
            ('None', 'No Drill', '', 0),
            ('BooleanModifier', 'Boolean Modifier', '', 1),
            ('AutoBoolean', 'Auto Boolean (Fast)', '', 2),
            ('NonDestructiveDifference', 'Booltron Non-Destructive Difference', '', 3),
        ])

        setattr(Scene, 'gerber_drill_algorithm_setting', EnumProperty(
            items=drill_algorithm_items,
            default='None'
        ))

    if len(cylinder_filter_items) == 0:
        cylinder_filter_items.extend([
            ('0.0015', '>=1.5mm', '', 0),
            ('0.0012', '>=1.2mm', '', 1),
            ('0.0009', '>=0.9mm', '', 2),
            ('0.0005', '>=0.5mm', '', 3),
            ('0.0', 'No Filter', '', 4)
        ])

        setattr(Scene, 'gerber_cylinder_filter_setting', EnumProperty(
            items=cylinder_filter_items,
            default='0.0015'  # Set the default value to 1.5mm. Cylinders with a drill diameter >= 1.5mm will be drilled (boolean operation).
        ))

def unregister():
    bpy.utils.unregister_class(GerberBoardSettings)

    global pcoll
    if pcoll is not None:
        previews.remove(pcoll)
        pcoll = None

    delattr(Scene, 'gerber_board_color_setting')
    delattr(Scene, 'gerber_copper_color_setting')
    delattr(Scene, 'gerber_silk_color_setting')
    delattr(Scene, 'gerber_board_thickness_setting')
    delattr(Scene, 'gerber_drill_algorithm_setting')
    delattr(Scene, 'gerber_cylinder_filter_setting')

    board_color_items.clear()
    copper_color_items.clear()
    silk_color_items.clear()
    board_thickness_items.clear()
    drill_algorithm_items.clear()
    cylinder_filter_items.clear()
