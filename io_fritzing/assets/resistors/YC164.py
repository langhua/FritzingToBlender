import bpy
import math
from io_fritzing.assets.utils.material import create_material
from io_fritzing.assets.utils.scene import clear_scene

# 清理场景
# 根据设计图定义YC164的尺寸
dimensions = {
    # 从设计图表格中取值
    'B': 0.30,    # 引脚宽度: 0.30±0.15mm
    'L': 3.20,    # 总长度: 3.20±0.15mm
    'W2': 1.60,   # 总宽度: 1.60±0.15mm
    'H': 0.65,    # 两侧引脚长度: 0.65±0.05mm
    'H2': 0.50,   # 中间引脚长度: 0.50±0.15mm
    'T': 0.60,    # 引脚厚度: 0.60±0.10mm
    'W1': 0.30,   # 底面引脚宽度: 0.30±0.15mm
    'P': 0.80,    # 引脚间距: 0.80±0.05mm
    
    # 其他计算尺寸
    'num_pins': 8,             # 引脚数量: 4个电阻，每个电阻2个引脚
    'resistor_count': 4,       # 电阻数量
    
    # 计算引脚位置
    'pin_spacing': 0.80,                   # 引脚中心距
    'total_pin_length': 1.60,              # 引脚总长度
    
    # 倒角参数
    'chamfer_size': 0.05,
    'chamfer_segments': 6,
    
    # 材质参数
    'body_color': (0.3, 0.3, 0.3, 1.0),     # 深灰色主体
    'cover_color': (0.1, 0.1, 0.1, 1.0),    # 表层黑色树脂
    'pin_color': (0.9, 0.9, 0.95, 1.0),     # 银白色引脚
    'marking_color': (1.0, 1.0, 1.0, 1.0),  # 白色标记
}

# 定义UI面板属性
class YC164Properties(bpy.types.PropertyGroup):
    resistor_value: bpy.props.StringProperty(
        name="电阻值",
        description="电阻值标记 (如: 103 表示10kΩ)",
        default="103"
    ) # type: ignore
    
    auto_clear_scene: bpy.props.BoolProperty(
        name="自动清理场景",
        description="创建前自动清理场景",
        default=True
    ) # type: ignore

# 操作符类 - 创建YC164排阻
class OBJECT_OT_create_yc164(bpy.types.Operator):
    bl_idname = "object.create_yc164"
    bl_label = "创建YC164排阻"
    bl_description = "创建YC164 4位0603贴片排阻3D模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    def apply_all_modifiers(self, obj=None):
        """应用所有修改器"""
        if bpy.context and bpy.context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        if obj:
            objects = [obj]
        else:
            if bpy.context:
                objects = bpy.context.scene.objects
        
        for obj in objects:
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            if bpy.context:
                bpy.context.view_layer.objects.active = obj
            
            for modifier in list(obj.modifiers):
                try:
                    bpy.ops.object.modifier_apply(modifier=modifier.name)
                except:
                    obj.modifiers.remove(modifier)

    def create_resistor_body(self):
        """创建排阻主体"""
        length = dimensions['L']   # 3.20mm
        width = dimensions['W2'] - dimensions['B']   # 1.60mm
        height = dimensions['T']
        base_height = height * 0.9
        cover_height = height * 0.1 + 0.01
        
        # 创建base立方体
        bpy.ops.mesh.primitive_cube_add(
            size=1,
            location=(0, 0, height/2)  # 放置在z=0平面以上
        )
        if bpy.context:
            base = bpy.context.active_object
            setattr(base, "name", "YC164_Body_Base")
            
            # 设置尺寸
            setattr(base, "scale", (length, width, base_height))
            bpy.ops.object.transform_apply(scale=True)
        
            # 设置base材质
            if base:
                getattr(base.data, "materials").clear()
                mat_base = create_material("Ceramic_Body", dimensions['body_color'][:4], metallic=0.2, roughness=0.7, weight=0.1, ior=1.5)
                getattr(base.data, "materials").append(mat_base)
            
            # 创建cover立方体
            bpy.ops.mesh.primitive_cube_add(
                size=1,
                location=(0, 0, base_height + cover_height/2)  # 放置在base上方
            )
            cover = bpy.context.active_object
            setattr(cover, "name", "YC164_Body_Cover")
            
            # 设置尺寸
            setattr(cover, "scale", (length, width, cover_height))
            bpy.ops.object.transform_apply(scale=True)

            # 设置cover材质
            if cover:
                getattr(cover.data, "materials").clear()
                mat_cover = create_material("Resin_Cover", dimensions['cover_color'][:4], metallic=0.0, roughness=0.8, weight=0.1, ior=1.5)
                getattr(cover.data, "materials").append(mat_cover)
            
            # 合并base和cover两部分
            bpy.ops.object.select_all(action='DESELECT')
            getattr(base, "select_set")(True)
            getattr(cover, "select_set")(True)
            bpy.context.view_layer.objects.active = base
            bpy.ops.object.join()
            
            # 重命名合并后的对象
            setattr(base, "name", "YC164_Body")
            
            # 添加倒角修改器
            bevel_mod = getattr(base, "modifiers").new(name="Bevel", type='BEVEL')
            setattr(bevel_mod, "width", dimensions['chamfer_size'])
            setattr(bevel_mod, "segments", dimensions['chamfer_segments'])
            setattr(bevel_mod, "limit_method", 'ANGLE')
            setattr(bevel_mod, "angle_limit", math.radians(30))
            
            # 应用修改器
            self.apply_all_modifiers(base)
        
        return base

    def create_single_pin(self, pin_name, x_pos, y_pos, pin_width, pin_length, pin_height):
        """创建单个引脚"""
        # 引脚中心位置
        z_pos = pin_height / 2  # 引脚底部在z=0平面
        
        # 创建引脚立方体
        bpy.ops.mesh.primitive_cube_add(size=1.0)
        pin = getattr(bpy.context, "active_object")
        setattr(pin, "name", pin_name)

        # 设置尺寸
        setattr(pin, "dimensions", (pin_length, pin_width, pin_height))
        setattr(pin, "location", (x_pos, y_pos, z_pos))
        bpy.ops.object.transform_apply(scale=True)
        
        # 设置材质
        pin.data.materials.clear()
        mat_pin = create_material("Metal_Silver", dimensions['pin_color'][:4], metallic=0.9, roughness=0.3)
        pin.data.materials.append(mat_pin)
        
        return pin

    def create_pins(self):
        """创建8个引脚，4个电阻，每个电阻2个"""
        pins = []
        
        # 引脚尺寸
        side_pin_length = dimensions['H']
        center_pin_length = dimensions['H2']
        pin_width = dimensions['B']
        pin_height = dimensions['T']
        
        # 引脚间距
        pin_spacing = dimensions['pin_spacing']  # 0.80mm
        
        # 总长度
        total_length = dimensions['L']  # 3.20mm
        
        # 计算引脚位置
        # 8个引脚，平均分布在两侧
        # 左侧4个引脚，右侧4个引脚
        
        # 一排4个引脚x坐标
        left_x = -total_length / 2 + side_pin_length / 2
        left_center_x = -pin_spacing/2
        right_x = total_length / 2 - side_pin_length / 2
        right_center_x = pin_spacing/2
        
        # 一排引脚y坐标
        top_y = dimensions['W2'] / 2 - pin_width / 2
        bottom_y = -top_y
        
        # 创建上排引脚
        pin_name = f"Pin_Top_Left"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=left_x,
            y_pos=top_y,
            pin_width=pin_width,
            pin_length=side_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)
        
        pin_name = f"Pin_Top_Left_Center"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=left_center_x,
            y_pos=top_y,
            pin_width=pin_width,
            pin_length=center_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)
        
        pin_name = f"Pin_Top_Right_Center"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=right_center_x,
            y_pos=top_y,
            pin_width=pin_width,
            pin_length=center_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)
        
        pin_name = f"Pin_Top_Right"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=right_x,
            y_pos=top_y,
            pin_width=pin_width,
            pin_length=side_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)
        
        # 创建下排引脚
        pin_name = f"Pin_Bottom_Left"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=left_x,
            y_pos=bottom_y,
            pin_width=pin_width,
            pin_length=side_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)
        
        pin_name = f"Pin_Bottom_Left_Center"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=left_center_x,
            y_pos=bottom_y,
            pin_width=pin_width,
            pin_length=center_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)
        
        pin_name = f"Pin_Bottom_Right_Center"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=right_center_x,
            y_pos=bottom_y,
            pin_width=pin_width,
            pin_length=center_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)
        
        pin_name = f"Pin_Bottom_Right"
        pin = self.create_single_pin(
            pin_name=pin_name,
            x_pos=right_x,
            y_pos=bottom_y,
            pin_width=pin_width,
            pin_length=side_pin_length,
            pin_height=pin_height,
        )
        pins.append(pin)

        return pins

    def create_marking(self, value):
        """在主体上创建单个标记"""
        # 创建文本对象
        text_size = dimensions['W2'] * 0.6
        bpy.ops.object.text_add(location=(0, 0, dimensions['T'] + 0.01))
        text_obj = getattr(bpy.context, "active_object")
        setattr(text_obj, "name", f"Text_{value}")
        setattr(text_obj.data, "body", value)
        setattr(text_obj.data, "size", text_size)
        setattr(text_obj.data, "extrude", 0.001)
        setattr(text_obj.data, "align_x", 'CENTER')
        setattr(text_obj.data, "align_y", 'CENTER')

        # 设置材质
        text_obj.data.materials.clear()
        mat_text = create_material("Text_White", dimensions['marking_color'][:4], metallic=0.0, roughness=0.8)
        text_obj.data.materials.append(mat_text)
        
        return text_obj

    def create_collection_and_organize(self, body, pins, marking):
        """将所有对象组织到一个组合中"""
        # 创建新的组合
        collection = bpy.data.collections.new("YC164_Resistor_Array")
        if bpy.context:
            bpy.context.scene.collection.children.link(collection)
        
        # 收集所有对象
        objects_to_move = [body]
        objects_to_move.extend(pins)
        objects_to_move.append(marking)
        
        # 从主场景移除并添加到新组合
        if bpy.context:
            for obj in objects_to_move:
                if obj.name in bpy.context.scene.collection.objects:
                    bpy.context.scene.collection.objects.unlink(obj)
                collection.objects.link(obj)
        
        # 选择所有对象
        bpy.ops.object.select_all(action='DESELECT')
        for obj in objects_to_move:
            obj.select_set(True)
        
        return collection

    def execute(self, context):
        # 获取属性
        if context:
            props = getattr(context.scene, "yc164_props")
        
        # 清理场景（如果启用）
        if props.auto_clear_scene:
            clear_scene()
        
        # 创建YC164排阻模型
        body = self.create_resistor_body()
        pins = self.create_pins()
        marking = self.create_marking(value=props.resistor_value)
        
        # 确保所有修改器都被应用
        self.apply_all_modifiers()
        
        # 将所有对象组织到一个组合中
        self.create_collection_and_organize(body, pins, marking)
        
        # 设置视图显示
        if context:
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    shading = getattr(area.spaces[0], "shading")
                    setattr(shading, "type", 'SOLID')
                    setattr(shading, "color_type", 'MATERIAL')
                    setattr(shading, "show_object_outline", True)
                    setattr(shading, "object_outline_color", (0, 0, 0))
        
        self.report({'INFO'}, f"YC164排阻创建完成! 电阻值: {props.resistor_value}")
        return {'FINISHED'}

# UI面板类
class VIEW3D_PT_yc164_panel(bpy.types.Panel):
    bl_label = "YC164 排阻生成器"
    bl_idname = "VIEW3D_PT_yc164_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电阻工具"
    bl_context = "objectmode"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        if context:
            props = getattr(context.scene, "yc164_props")
        
        # 面板标题
        box = layout.box()
        box.label(text="YC164 4位0603排阻", icon='MOD_ARRAY')
        
        # 参数设置
        layout.label(text="参数设置:")
        layout.prop(props, "resistor_value")
        layout.prop(props, "auto_clear_scene")
        
        # 分隔线
        layout.separator()
        
        # 创建按钮
        layout.operator("object.create_yc164", text="创建YC164排阻", icon='ADD')
        
        # 规格信息
        box = layout.box()
        box.label(text="规格信息:", icon='INFO')
        
        col = box.column(align=True)
        col.label(text=f"尺寸: {dimensions['L']}mm × {dimensions['W2']}mm × {dimensions['T']}mm")
        col.label(text=f"引脚数: {dimensions['num_pins']} (4个独立电阻)")
        col.label(text=f"引脚间距: {dimensions['P']}mm")
        
        # 分隔线
        layout.separator()
        
        # 应用说明
        box = layout.box()
        box.label(text="应用说明:", icon='SCRIPT')
        
        col = box.column(align=True)
        col.label(text="• 用于PCB电路板的电阻网络")
        col.label(text="• 节省空间，提高电路密度")
        col.label(text="• 适合高频电路")
        col.label(text="• 适用于自动贴片机")

# 注册类
classes = (
    YC164Properties,
    OBJECT_OT_create_yc164,
    VIEW3D_PT_yc164_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册场景属性
    setattr(bpy.types.Scene, "yc164_props", bpy.props.PointerProperty(type=YC164Properties))

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 删除场景属性
    try:
        delattr(bpy.types.Scene, "yc164_props")
    except AttributeError:
        pass

# 保留原有的main函数（可选）
def main():
    """主函数（保留原有功能）"""
    # 清理场景
    clear_scene()
    
    # 创建YC164排阻模型
    operator = OBJECT_OT_create_yc164()
    operator.execute(bpy.context)
    
    # 打印规格信息
    print("YC164 4位0603贴片排阻3D模型创建完成！")
    print("=" * 60)
    print("产品信息:")
    print("  型号: YC164 贴片排阻")
    print("  封装: 0603×4 (4电阻网络)")
    print("  尺寸: 3.2mm × 1.6mm × 0.65mm")
    print("  引脚数: 8 (4个独立电阻)")
    print("  引脚间距: 0.8mm")
    print("")
    print("尺寸参数 (单位:mm):")
    print(f"  B (引脚宽度): {dimensions['B']}mm (±0.15mm)")
    print(f"  H (总高度): {dimensions['H']}mm (±0.05mm)")
    print(f"  H2 (主体高度): {dimensions['H2']}mm (±0.15mm)")
    print(f"  L (总长度): {dimensions['L']}mm (±0.15mm)")
    print(f"  T (引脚厚度): {dimensions['T']}mm (±0.10mm)")
    print(f"  W1 (引脚内部宽度): {dimensions['W1']}mm (±0.15mm)")
    print(f"  W2 (总宽度): {dimensions['W2']}mm (±0.15mm)")
    print(f"  P (引脚间距): {dimensions['P']}mm (±0.05mm)")
    print("")
    print("结构特性:")
    print("  - 黑色陶瓷主体")
    print("  - 银白色金属引脚")
    print("  - 4个独立电阻，共8个引脚")
    print("  - 引脚间距0.8mm")
    print("  - 0603封装尺寸")
    print("  - 标记: 电阻值标记")
    print("")
    print("电阻值 (示例):")
    print("  103 (10kΩ)")
    print("")
    print("应用说明:")
    print("  - 用于PCB电路板的电阻网络")
    print("  - 节省空间，提高电路密度")
    print("  - 适合高频电路")
    print("  - 适用于自动贴片机")
    print("=" * 60)

if __name__ == "__main__":
    register()
    # 可以选择是否自动运行main函数
    # main()