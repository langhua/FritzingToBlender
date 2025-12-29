import bpy
from bpy.types import Operator

class IMPORT_OT_update_dialog_from_cursor_scene(Operator):
    """从光标更新原点坐标（场景属性版本）"""
    bl_idname = "fritzing.pnp_update_dialog_from_cursor_scene"
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
            
            # 强制UI刷新（对话框需要）
            if context.area:
                context.area.tag_redraw()
            
            self.report({'INFO'}, f"已更新原点为光标位置: {cursor_loc}")
        return {'FINISHED'}

# 对其他操作符也添加类似的刷新逻辑
class IMPORT_OT_dialog_use_cursor_as_origin(Operator):
    """使用光标作为原点"""
    bl_idname = "fritzing.pnp_dialog_use_cursor_as_origin"
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
        
        # 强制UI刷新
        if context.area:
            context.area.tag_redraw()
        
        self.report({'INFO'}, "已启用光标模式，原点将实时跟随光标")
        return {'FINISHED'}
    

# ============================================================================
# 3. 对话框
# ============================================================================
class IMPORT_OT_pnp_settings_dialog(Operator):
    """PNP导入对话框"""
    bl_idname = "fritzing.pnp_settings_dialog"
    bl_label = "PNP导入设置"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 对话框尺寸
    width: bpy.props.IntProperty(
                            name="Width",
                            description="Dialog width",
                            default=400
                            ) # type: ignore
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=self.width)
    
    def execute(self, context):
        # 对话框确认按钮的操作
        # 这里可以添加一些确认后的操作
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 将原面板的UI内容复制到这里
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
        
        if getattr(scene, 'pnp_origin_mode') == 'CURSOR':
            row.label(text=f"X: {getattr(scene, 'pnp_origin_x'):.3f}")
            row.label(text=f"Y: {getattr(scene, 'pnp_origin_y'):.3f}")
            row.label(text=f"Z: {getattr(scene, 'pnp_origin_z'):.3f}")
        else:
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

classes = [
    # 操作符
    IMPORT_OT_update_dialog_from_cursor_scene,
    IMPORT_OT_dialog_use_cursor_as_origin,
    
    # 对话框操作符
    IMPORT_OT_pnp_settings_dialog,
]

def register():
    """注册所有类和属性"""
    # 注册类
    for cls in classes:
        bpy.utils.register_class(cls)
    
    print("PNP导入插件（对话框属性版）已注册")

def unregister():
    """注销所有类和属性"""
    # 注销类
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    print("PNP导入插件（场景属性版）已注销")

# 自动注册
if __name__ == "__main__":
    register()