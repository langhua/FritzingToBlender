import bpy
import os
from bpy.types import Operator, Panel, Scene
from bpy.props import (FloatProperty, StringProperty, EnumProperty)
from io_fritzing.pnp.import_pnp_report import importdata

# ============================================================================
# 场景属性定义
# ============================================================================
def update_origin_preview(self, context):
    """坐标属性更新时的回调，更新预览对象"""
    scene = context.scene
    
    # 查找预览对象
    preview_name = "PNP_Origin_Preview"
    if preview_name in bpy.data.objects:
        preview_obj = bpy.data.objects[preview_name]
        preview_obj.location = (
            scene.pnp_origin_x,
            scene.pnp_origin_y,
            scene.pnp_origin_z
        )
    
    # 强制UI更新
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

def update_origin_from_mode(self, context):
    """原点模式变化时的回调"""
    scene = context.scene
    
    if scene.pnp_origin_mode == 'CURSOR':
        cursor_loc = context.scene.cursor.location
        scene.pnp_origin_x = cursor_loc.x
        scene.pnp_origin_y = cursor_loc.y
        scene.pnp_origin_z = cursor_loc.z
    
    elif scene.pnp_origin_mode == 'SELECTED':
        if context.selected_objects and context.active_object:
            obj = context.active_object
            scene.pnp_origin_x = obj.location.x
            scene.pnp_origin_y = obj.location.y
            scene.pnp_origin_z = obj.location.z
        else:
            scene.pnp_origin_x = 0.0
            scene.pnp_origin_y = 0.0
            scene.pnp_origin_z = 0.0
    
    elif scene.pnp_origin_mode == 'WORLD':
        scene.pnp_origin_x = 0.0
        scene.pnp_origin_y = 0.0
        scene.pnp_origin_z = 0.0
    
    update_origin_preview(self, context)


# ============================================================================
# 2. 操作符定义
# ============================================================================
class IMPORT_OT_update_from_cursor_scene(Operator):
    """从光标更新原点坐标（场景属性版本）"""
    bl_idname = "fritzing.pnp_update_from_cursor_scene"
    bl_label = "从光标更新"
    bl_description = "将原点坐标更新为当前3D光标位置"
    
    def execute(self, context):
        if context:
            scene = context.scene
            cursor_loc = context.scene.cursor.location
        
            # 更新场景属性
            setattr(scene, "pnp_origin_x", cursor_loc.x)
            setattr(scene, "pnp_origin_y", cursor_loc.y)
            setattr(scene, "pnp_origin_z", cursor_loc.z)
            
            # 设置模式为手动
            setattr(scene, "pnp_origin_mode", 'MANUAL')
            
            self.report({'INFO'}, f"已更新原点为光标位置: {cursor_loc}")
        return {'FINISHED'}

class IMPORT_OT_update_from_selected_scene(Operator):
    """从选中对象更新原点坐标"""
    bl_idname = "fritzing.pnp_update_from_selected_scene"
    bl_label = "从选中对象更新"
    bl_description = "将原点坐标更新为选中对象的位置"
    
    def execute(self, context):
        if context is None:
            return
        if not context.selected_objects:
            self.report({'WARNING'}, "没有选中任何对象")
            return {'CANCELLED'}
        
        obj = context.active_object
        if not obj:
            self.report({'WARNING'}, "没有活动的选中对象")
            return {'CANCELLED'}
        
        scene = context.scene
        
        # 更新场景属性
        setattr(scene, "pnp_origin_x", obj.location.x)
        setattr(scene, "pnp_origin_y", obj.location.y)
        setattr(scene, "pnp_origin_z", obj.location.z)
        
        # 设置模式为手动
        setattr(scene, "pnp_origin_mode", 'MANUAL')
        
        self.report({'INFO'}, f"已更新原点为对象位置: {obj.location}")
        return {'FINISHED'}

class IMPORT_OT_use_cursor_as_origin(Operator):
    """使用光标作为原点"""
    bl_idname = "fritzing.pnp_use_cursor_as_origin"
    bl_label = "使用光标原点"
    
    def execute(self, context):
        if context is None:
            return
        scene = context.scene
        
        # 设置模式
        setattr(scene, "pnp_origin_mode", 'CURSOR')
        
        # 立即更新一次坐标
        cursor_loc = context.scene.cursor.location
        setattr(scene, "pnp_origin_x", cursor_loc.x)
        setattr(scene, "pnp_origin_y", cursor_loc.y)
        setattr(scene, "pnp_origin_z", cursor_loc.z)
        
        self.report({'INFO'}, "已启用光标模式，原点将实时跟随光标")
        return {'FINISHED'}

class IMPORT_OT_use_selected_as_origin(Operator):
    """使用选中对象作为原点（不更新坐标，只改模式）"""
    bl_idname = "fritzing.pnp_use_selected_as_origin"
    bl_label = "使用选中对象原点"
    bl_description = "使用选中对象位置作为原点（实时更新）"
    
    def execute(self, context):
        if context is None:
            return
        if not context.selected_objects:
            self.report({'WARNING'}, "没有选中任何对象")
            return {'CANCELLED'}
        
        scene = context.scene
        
        # 设置模式为选中对象模式
        setattr(scene, "pnp_origin_mode", 'SELECTED')
        
        # 立即更新一次坐标
        obj = context.active_object
        if obj:
            setattr(scene, 'pnp_origin_x', obj.location.x)
            setattr(scene, 'pnp_origin_y', obj.location.y)
            setattr(scene, 'pnp_origin_z', obj.location.z)
        
        self.report({'INFO'}, "已设为选中对象模式")
        return {'FINISHED'}

class IMPORT_OT_use_world_as_origin(Operator):
    """使用世界原点"""
    bl_idname = "fritzing.pnp_use_world_as_origin"
    bl_label = "使用世界原点"
    
    def execute(self, context):
        if context is None:
            return
        scene = context.scene
        
        # 设置模式为世界原点
        setattr(scene, 'pnp_origin_mode', 'WORLD')

        # 更新坐标
        setattr(scene, 'pnp_origin_x', 0.0)
        setattr(scene, 'pnp_origin_y', 0.0)
        setattr(scene, 'pnp_origin_z', 0.0)
        
        self.report({'INFO'}, "已设为世界原点模式 (0, 0, 0)")
        return {'FINISHED'}


class IMPORT_OT_start_pnp_import_scene(Operator):
    """开始导入PNP（使用场景属性）"""
    bl_idname = "fritzing.pnp_start_import_scene"
    bl_label = "导入PNP"
    bl_description = "使用设置的原点导入PNP文件"
    
    def execute(self, context):
        if context is None:
            return
        scene = context.scene
        
        # 检查文件夹路径
        if not hasattr(scene, 'pnp_file_path') or not getattr(scene, 'pnp_file_path'):
            self.report({'ERROR'}, "请先选择PNP文件夹")
            return {'CANCELLED'}
        
        file_path = getattr(scene, 'pnp_file_path')
        if not os.path.isfile(file_path):
            self.report({'ERROR'}, f"文件不存在: {file_path}")
            return {'CANCELLED'}
        
        # 获取原点坐标
        if getattr(scene, 'pnp_origin_mode') == 'CURSOR':
            origin = context.scene.cursor.location
        elif getattr(scene, 'pnp_origin_mode') == 'SELECTED':
            if context.selected_objects and context.active_object:
                origin = context.active_object.location
            else:
                origin = (0, 0, 0)
        elif getattr(scene, 'pnp_origin_mode') == 'WORLD':
            origin = (0, 0, 0)
        else:  # MANUAL
            origin = (
                getattr(scene, 'pnp_origin_x'),
                getattr(scene, 'pnp_origin_y'),
                getattr(scene, 'pnp_origin_z')
            )
        
        # 获取PNP文件
        print(f"开始导入PNP，原点: {origin}")
        importdata.filename = file_path
        
        try:
            # 强制UI更新
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP', iterations=1)
            
            # 导入PNP
            getattr(getattr(bpy.ops, 'fritzing'), 'pnp_count_lines')("INVOKE_DEFAULT")
            
            # 短暂延迟
            import time
            time.sleep(0.1)
            
        except Exception as e:
            self.report({'ERROR'}, f"导入失败 {os.path.basename(file_path)}: {str(e)}")
        
        self.report({'INFO'}, f"以 {origin} 为原点，成功导入 {importdata.successed} 个元件")
        return {'FINISHED'}


# ============================================================================
# 3. 面板定义
# ============================================================================
class VIEW3D_PT_pnp_origin_scene(Panel):
    """PNP导入原点设置面板（场景属性版本）"""
    bl_label = "PNP导入原点设置"
    bl_idname = "VIEW3D_PT_pnp_origin_scene"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PNP导入"
    
    def draw(self, context):
        layout = self.layout
        if context is None:
            return
        scene = context.scene
        
        # 标题
        layout.label(text="原点设置", icon='PIVOT_BOUNDBOX')
        
        # 实时坐标显示
        box = layout.box()
        box.label(text="实时坐标:", icon='ORIENTATION_GLOBAL')
        
        # 光标位置
        cursor_loc = context.scene.cursor.location
        if getattr(scene, 'pnp_origin_mode') == 'CURSOR':
            box.label(text=f"3D光标:")
            box.label(text=f"  X: {cursor_loc.x:.3f}  Y: {cursor_loc.y:.3f}  Z: {cursor_loc.z:.3f}")
        elif getattr(scene, 'pnp_origin_mode') == 'SELECTED':        
            # 选中对象位置
            if context.selected_objects and context.active_object:
                obj = context.active_object
                obj_loc = obj.location
                box.label(text=f"选中对象 ({obj.name}):")
                box.label(text=f"  X: {obj_loc.x:.3f}  Y: {obj_loc.y:.3f}  Z: {obj_loc.z:.3f}")
            else:
                box.label(text="选中对象: 无")
        elif getattr(scene, 'pnp_origin_mode') == 'WORLD':
            box.label(text="世界原点: ")
            box.label(text=f"  X: {getattr(scene, 'pnp_origin_x'):.3f}  Y: {getattr(scene, 'pnp_origin_y'):.3f}  Z: {getattr(scene, 'pnp_origin_z'):.3f}")
        elif getattr(scene, 'pnp_origin_mode') == 'MANUAL':
            box.label(text="手动坐标: ")
            box.label(text=f"  X: {getattr(scene, 'pnp_origin_x'):.3f}  Y: {getattr(scene, 'pnp_origin_y'):.3f}  Z: {getattr(scene, 'pnp_origin_z'):.3f}")

        # 分隔线
        layout.separator()
        
        # 原点模式选择
        box = layout.box()
        box.label(text="原点模式:", icon='PIVOT_ACTIVE')
        
        # 模式选择按钮
        row = box.row(align=True)
        op = row.operator("fritzing.pnp_use_cursor_as_origin", 
                         text="光标", 
                         icon='CURSOR',
                         depress=(getattr(scene, 'pnp_origin_mode') == 'CURSOR'))
        
        if context.selected_objects:
            op = row.operator("fritzing.pnp_use_selected_as_origin", 
                             text="选中对象", 
                             icon='OBJECT_DATA',
                             depress=(getattr(scene, 'pnp_origin_mode') == 'SELECTED'))
        
        op = row.operator("fritzing.pnp_use_world_as_origin", 
                         text="世界原点", 
                         icon='WORLD',
                         depress=(getattr(scene, 'pnp_origin_mode') == 'WORLD'))
        
        # 手动坐标输入
        box = layout.box()
        box.label(text="手动坐标:", icon='GRID')
        
        col = box.column(align=True)
        row = col.row(align=True)
        
        # 在CURSOR模式下，手动坐标框应该显示为不可编辑
        if getattr(scene, 'pnp_origin_mode') == 'CURSOR':
            # 显示为只读标签
            row.label(text=f"X: {getattr(scene, 'pnp_origin_x'):.3f}")
            row.label(text=f"Y: {getattr(scene, 'pnp_origin_y'):.3f}")
            row.label(text=f"Z: {getattr(scene, 'pnp_origin_z'):.3f}")
        else:
            # 手动模式下可编辑
            row.prop(scene, "pnp_origin_x", text="X")
            row.prop(scene, "pnp_origin_y", text="Y")
            row.prop(scene, "pnp_origin_z", text="Z")
        
        # 同步按钮
        row = box.row(align=True)
        op = row.operator("fritzing.pnp_update_from_cursor_scene", 
                         text="从光标同步", 
                         icon='CURSOR')
        
        if context.selected_objects:
            op = row.operator("fritzing.pnp_update_from_selected_scene", 
                             text="从选中对象同步", 
                             icon='OBJECT_DATA')
        
        # 文件选择
        layout.separator()
        box = layout.box()
        box.label(text="选择PNP文件:", icon='FILE')
        
        row = box.row(align=True)
        row.prop(scene, "pnp_file_path", text="")
        
        # 导入按钮
        row = box.row(align=True)
        row.operator("fritzing.pnp_start_import_scene", 
                    text="开始导入PNP", 
                    icon='MOD_UVPROJECT')


# ============================================================================
# 4. 注册和取消注册
# ============================================================================
classes = [
    # 操作符
    IMPORT_OT_update_from_cursor_scene,
    IMPORT_OT_update_from_selected_scene,
    IMPORT_OT_use_cursor_as_origin,
    IMPORT_OT_use_selected_as_origin,
    IMPORT_OT_use_world_as_origin,
    IMPORT_OT_start_pnp_import_scene,
    
    # 面板
    VIEW3D_PT_pnp_origin_scene,
]

def register():
    """注册所有类和属性"""
    # 注册类
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册场景属性
    setattr(Scene, "pnp_origin_x", FloatProperty(
        name="Origin X",
        description="PNP导入原点的X坐标",
        default=0.0,
        update=update_origin_preview
    ))
    
    setattr(Scene, "pnp_origin_y", FloatProperty(
        name="Origin Y",
        description="PNP导入原点的Y坐标",
        default=0.0,
        update=update_origin_preview
    ))
    
    setattr(Scene, "pnp_origin_z", FloatProperty(
        name="Origin Z",
        description="PNP导入原点的Z坐标",
        default=0.0,
        update=update_origin_preview
    ))
    
    setattr(Scene, "pnp_origin_mode", EnumProperty(
        name="Origin Mode",
        description="原点选择模式",
        items=[
            ('MANUAL', "手动", "手动设置坐标"),
            ('CURSOR', "光标", "使用3D光标位置"),
            ('SELECTED', "选中对象", "使用选中对象位置"),
            ('WORLD', "世界原点", "使用世界原点"),
        ],
        default='CURSOR',
        update=update_origin_from_mode
    ))
    
    setattr(Scene, "pnp_file_path", StringProperty(
        name="PNP File",
        description="PNP文件路径",
        subtype='FILE_PATH',
        default=""
    ))
    
    print("PNP导入插件（场景属性版）已注册")

def unregister():
    """注销所有类和属性"""
    # 注销类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 删除场景属性
    delattr(Scene, "pnp_origin_x")
    delattr(Scene, "pnp_origin_y")
    delattr(Scene, "pnp_origin_z")
    delattr(Scene, "pnp_origin_mode")
    delattr(Scene, "pnp_file_path")
    
    print("PNP导入插件（场景属性版）已注销")

# 自动注册
if __name__ == "__main__":
    register()