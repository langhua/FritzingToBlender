from bpy.types import Operator, Scene
import bpy
from bpy.props import EnumProperty
from io_fritzing.svg.commondata import Board_Black, Board_Blue, Board_Green, Board_Purple, Board_Red, Board_White, Board_Yellow
from io_fritzing.svg.commondata import Copper, Copper2, Silk_Black, Silk_White, Silk_White2
import os
import bpy.utils.previews

##
# Dialog box to handle error messages
class BoardSettings(Operator):
    bl_idname = "fritzing.board_settings"
    bl_label = "Fritzing Board Settings"

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
        col1.scale_y = 4
        col1.label(text='Board Thickness:')
        col2 = row.column()
        if context:
            col2.prop_tabs_enum(context.scene, property='board_thickness_setting')

        # board color
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.3
        col1.scale_y = 2
        col1.label(text='Board Color:')
        col2 = row.column()
        if context:
            col2.template_icon_view(context.scene, 'board_color_setting', scale=2)

        # copper color
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.3
        col1.scale_y = 2
        col1.label(text='Copper Color:')
        col2 = row.column()
        if context:
            col2.template_icon_view(context.scene, 'copper_color_setting', scale=2)

        # silk color
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_x = 0.3
        col1.scale_y = 2
        col1.label(text='Silk Color:')
        col2 = row.column()
        if context:
            col2.template_icon_view(context.scene, 'silk_color_setting', scale=2)

        # drill algorithm
        box = layout.box()
        row = box.row()
        col1 = row.column()
        col1.scale_y = 2
        col1.label(text='Drill Algorithm:')
        col2 = row.column()
        if context:
            col2.prop_tabs_enum(context.scene, property='drill_algorithm_setting')

        # bottom margin
        row = layout.row()


    def execute(self, context):
        getattr(getattr(bpy.ops, 'fritzing'), 'progress_report')("INVOKE_DEFAULT")
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
pcoll = bpy.utils.previews.new()

def register():
    addon_path = os.path.dirname(__file__)
    icons_dir = os.path.join(addon_path, '..', 'icons')

    if len(board_thickness_items) == 0:
        board_thickness_items.append(('0.0016', '1.6mm', '', 0))
        board_thickness_items.append(('0.0014', '1.4mm', '', 1))
        board_thickness_items.append(('0.0012', '1.2mm', '', 2))
        board_thickness_items.append(('0.001', '1.0mm', '', 3))
        setattr(Scene, 'board_thickness_setting', EnumProperty(items=board_thickness_items))

    if len(board_color_items) == 0:
        board_green = pcoll.load(Board_Green['name'], os.path.join(icons_dir, Board_Green['icon']), 'IMAGE')
        board_color_items.append((Board_Green['name'], Board_Green['name'], '', board_green.icon_id, 0))
        
        board_red = pcoll.load(Board_Red['name'], os.path.join(icons_dir, Board_Red['icon']), 'IMAGE')
        board_color_items.append((Board_Red['name'], Board_Red['name'], '', board_red.icon_id, 1))

        board_blue = pcoll.load(Board_Blue['name'], os.path.join(icons_dir, Board_Blue['icon']), 'IMAGE')
        board_color_items.append((Board_Blue['name'], Board_Blue['name'], '', board_blue.icon_id, 2))

        board_white = pcoll.load(Board_White['name'], os.path.join(icons_dir, Board_White['icon']), 'IMAGE')
        board_color_items.append((Board_White['name'], Board_White['name'], '', board_white.icon_id, 3))

        board_black = pcoll.load(Board_Black['name'], os.path.join(icons_dir, Board_Black['icon']), 'IMAGE')
        board_color_items.append((Board_Black['name'], Board_Black['name'], '', board_black.icon_id, 4))

        board_yellow = pcoll.load(Board_Yellow['name'], os.path.join(icons_dir, Board_Yellow['icon']), 'IMAGE')
        board_color_items.append((Board_Yellow['name'], Board_Yellow['name'], '', board_yellow.icon_id, 5))

        board_purple = pcoll.load(Board_Purple['name'], os.path.join(icons_dir, Board_Purple['icon']), 'IMAGE')
        board_color_items.append((Board_Purple['name'], Board_Purple['name'], '', board_purple.icon_id, 6))

        setattr(Scene, 'board_color_setting', EnumProperty(items=board_color_items))

    if len(copper_color_items) == 0:
        copper = pcoll.load(Copper['name'], os.path.join(icons_dir, Copper['icon']), 'IMAGE')
        copper_color_items.append((Copper['name'], Copper['name'], '', copper.icon_id, 0))
        
        copper2 = pcoll.load(Copper2['name'], os.path.join(icons_dir, Copper2['icon']), 'IMAGE')
        copper_color_items.append((Copper2['name'], Copper2['name'], '', copper2.icon_id, 1))

        setattr(Scene, 'copper_color_setting', EnumProperty(items=copper_color_items))

    if len(silk_color_items) == 0:
        silk_white2 = pcoll.load(Silk_White2['name'], os.path.join(icons_dir, Silk_White2['icon']), 'IMAGE')
        silk_color_items.append((Silk_White2['name'], Silk_White2['name'], '', silk_white2.icon_id, 0))
        
        silk_white = pcoll.load(Silk_White['name'], os.path.join(icons_dir, Silk_White['icon']), 'IMAGE')
        silk_color_items.append((Silk_White['name'], Silk_White['name'], '', silk_white.icon_id, 1))

        silk_black = pcoll.load(Silk_Black['name'], os.path.join(icons_dir, Silk_Black['icon']), 'IMAGE')
        silk_color_items.append((Silk_Black['name'], Silk_Black['name'], '', silk_black.icon_id, 2))

        setattr(Scene, 'silk_color_setting', EnumProperty(items=silk_color_items))

    if len(drill_algorithm_items) == 0:
        drill_algorithm_items.append(('BooleanModifier', 'Boolean Modifier', '', 0))
        drill_algorithm_items.append(('AutoBoolean', 'Auto Boolean', '', 1))
        setattr(Scene, 'drill_algorithm_setting', EnumProperty(items=drill_algorithm_items))


def unregister():
    bpy.utils.previews.remove(pcoll)
    board_color_items.clear()
    copper_color_items.clear()
    silk_color_items.clear()
    board_thickness_items.clear()
    drill_algorithm_items.clear()
