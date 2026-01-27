import bpy
import bmesh
from bpy.types import Panel, Operator, PropertyGroup
from bpy.props import FloatProperty, StringProperty, EnumProperty, IntProperty, BoolProperty, PointerProperty
from .eia_96 import resistor_to_eia96
from ..utils.material import create_material
from .code_4digit import resistance_to_4digit
from .code_3digit import resistance_to_3digit

bl_info = {
    "name": "贴片电阻生成器",
    "version": (1, 10, 0),
    "blender": (4, 2, 0),
    "location": "View3D > N > 电阻工具 > 贴片电阻",
    "description": "生成带有丝印的贴片电阻模型，使用直观的电阻值转换",
    "category": "3D View"
}

# 贴片电阻封装尺寸 (单位: mm)
SMD_SIZES = {
    '0402': (1.0, 0.5, 0.35, 0.2),   # 长, 宽, 高, 焊盘长度
    '0603': (1.6, 0.8, 0.45, 0.3),   # 长, 宽, 高, 焊盘长度
    '0805': (2.0, 1.25, 0.5, 0.4),   # 长, 宽, 高, 焊盘长度
    '1206': (3.2, 1.6, 0.55, 0.5),   # 长, 宽, 高, 焊盘长度
    '1210': (3.2, 2.5, 0.55, 0.5),   # 长, 宽, 高, 焊盘长度
    '1812': (4.5, 3.2, 0.55, 0.6),   # 长, 宽, 高, 焊盘长度
    '2010': (5.0, 2.5, 0.55, 0.6),   # 长, 宽, 高, 焊盘长度
    '2512': (6.3, 3.2, 0.55, 0.7),   # 长, 宽, 高, 焊盘长度
}

# ==================== 工具函数 ====================
def format_resistance(value: float) -> str:
    """格式化电阻值显示"""
    if value >= 1000000:  # 1MΩ以上
        return f"{value/1000000:.4f}MΩ"
    elif value >= 1000:   # 1kΩ以上
        return f"{value/1000:.4f}kΩ"
    elif value >= 1:      # 1Ω以上
        return f"{value:.4f}Ω"
    elif value >= 0.001:  # 1mΩ以上
        return f"{value*1000:.4f}mΩ"
    else:                 # 小于1mΩ
        return f"{value*1000000:.4f}μΩ"

def get_tolerance_value(tolerance_enum: str) -> float:
    """从枚举值获取公差百分比的小数形式"""
    tolerance_map = {
        '1%': 0.01,
        '5%': 0.05,
    }
    return tolerance_map.get(tolerance_enum, 0.01)  # 默认1%

# ==================== 属性组 ====================
class SMDResistorProperties(PropertyGroup):
    """贴片电阻属性组"""
    
    # 基本参数
    resistance: FloatProperty(
        name="电阻值",
        description="电阻值 (单位: Ω)",
        default=4700.0,
        min=0.001,
        max=10000000.0,
        precision=4,
        step=100
    )  # type: ignore
    
    # 公差
    tolerance: EnumProperty(
        name="公差",
        description="选择电阻公差百分比",
        items=[
            ('1%', "1%", "1% 公差"),
            ('5%', "5%", "5% 公差"),
        ],
        default='1%',
        update=lambda self, context: self.update_code_type(context)
    )  # type: ignore
    
    # 封装选择
    package_size: EnumProperty(
        name="封装尺寸",
        description="选择贴片电阻封装尺寸",
        items=[
            ('0402', "0402 (1.0×0.5mm)", "超小型封装"),
            ('0603', "0603 (1.6×0.8mm)", "常用小型封装"),
            ('0805', "0805 (2.0×1.25mm)", "常用标准封装"),
            ('1206', "1206 (3.2×1.6mm)", "标准功率封装"),
            ('1210', "1210 (3.2×2.5mm)", "中功率封装"),
            ('1812', "1812 (4.5×3.2mm)", "大功率封装"),
            ('2010', "2010 (5.0×2.5mm)", "大功率封装"),
            ('2512', "2512 (6.3×3.2mm)", "超大功率封装"),
        ],
        default='0805',
        update=lambda self, context: self.update_code_type(context)
    )  # type: ignore
    
    # 编码类型（根据封装尺寸和公差自动确定，用户可查看但不可编辑）
    code_type: StringProperty(
        name="编码类型",
        description="根据封装尺寸和公差自动确定的丝印编码类型",
        default="4位编码"
    )  # type: ignore
    
    def update_code_type(self, context):
        """根据封装尺寸和公差更新编码类型"""
        package = self.package_size
        tol = self.tolerance

        self.code_type = get_code_type(package, tol)
        
        # 同时更新编码值
        self.update_code_value()

    def update_code_value(self):
        """根据电阻值和编码类型计算编码值"""
        if self.code_type is None:
            self.code_value = "无"
        elif self.code_type != "3位编码" and self.code_type != "4位编码" and self.code_type != "EIA-96":
            self.code_value = "未知"

def get_code_type(package_size: str, tolerance: str) -> str | None:
    # 根据规则确定编码类型
    if package_size == '0402':
        code_type = "无"
    elif package_size == '0603':
        if tolerance == '1%':
            code_type = "EIA-96"
        else:  # 5%
            code_type = "3位编码"
    else:  # 0805及以上
        if tolerance == '1%':
            code_type = "4位编码"
        else:  # 5%
            code_type = "3位编码"
        
    return code_type


# ==================== 操作类 ====================
class SMD_OT_GenerateResistor(Operator):
    """生成带有丝印的贴片电阻"""
    bl_idname = "smd.generate_resistor"
    bl_label = "生成贴片电阻"
    bl_description = "生成带有丝印的贴片电阻模型"
    bl_options = {'REGISTER', 'UNDO'}
    
    def execute(self, context):
        if context:
            props = getattr(context.scene, "smd_resistor_props")
        
        # 计算电阻代码
        if props.code_type == 'EIA-96':
            code_dict = resistor_to_eia96(props.resistance)
            code_to_show = code_dict['eia96_mark']
        elif props.code_type == '4位编码':
            code_to_show = resistance_to_4digit(props.resistance)
        elif props.code_type == '3位编码':
            # 3DIGIT
            code_to_show = resistance_to_3digit(props.resistance)
        elif props.code_type == '无':
            code_to_show = "无"
        else:
            code_to_show = "未知"
        
        # 创建电阻集合
        if code_to_show != "无":
            collection_name = f"SMD_Resistor_{props.package_size}"
        else:
            collection_name = f"SMD_Resistor_{props.package_size}_{code_to_show}"
        
        collection = bpy.data.collections.new(collection_name)
        if context:
            context.scene.collection.children.link(collection)
        
        generate_smd_resistor_with_code(collection, props.package_size, code_to_show)

        # 选择所有生成的对象
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.objects:
            obj.select_set(True)
        if context and collection.objects:
            context.view_layer.objects.active = collection.objects[0]
        
        # 报告结果
        self.report({'INFO'}, f"已生成{props.package_size}电阻: {format_resistance(props.resistance)} 丝印: {code_to_show}")
        return {'FINISHED'}

def create_resistor_body(collection, length_mm, width_mm, height_mm):
    """创建电阻主体"""
    # 创建材质
    body_mat = create_material("Resistor_Body", (0.9, 0.9, 0.9), metallic=0.0, roughness=0.8)
    
    # 创建网格
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    
    # 缩放
    for v in bm.verts:
        v.co.x *= length_mm
        v.co.y *= width_mm
        v.co.z *= height_mm
    
    # 创建网格对象
    mesh = bpy.data.meshes.new("Resistor_Body")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("Resistor_Body", mesh)
    collection.objects.link(obj)
    
    # 应用材质
    getattr(obj.data, "materials").append(body_mat)
    obj.location.z += height_mm * 1.05/2
    
    return obj
    
def create_pads(collection, length_mm, width_mm, height_mm, pad_length_mm):
    """创建焊盘"""
    # 创建材质
    pad_mat = create_material("Resistor_Pad", (0.9, 0.9, 0.95, 1.0), metallic=0.8, roughness=0.3)
    
    # 左焊盘
    bm_left = bmesh.new()
    bmesh.ops.create_cube(bm_left, size=1.0)
    
    for v in bm_left.verts:
        v.co.x *= pad_length_mm
        v.co.y *= width_mm * 1.1
        v.co.z *= height_mm * 1.05
        v.co.x -= (length_mm/2 + pad_length_mm/2)
    
    mesh_left = bpy.data.meshes.new("Left_Pad")
    bm_left.to_mesh(mesh_left)
    bm_left.free()
    
    obj_left = bpy.data.objects.new("Left_Pad", mesh_left)
    collection.objects.link(obj_left)
    getattr(obj_left.data, "materials").append(pad_mat)
    obj_left.location.z += height_mm * 1.05/2
    
    # 右焊盘
    bm_right = bmesh.new()
    bmesh.ops.create_cube(bm_right, size=1.0)
    
    for v in bm_right.verts:
        v.co.x *= pad_length_mm
        v.co.y *= width_mm * 1.1
        v.co.z *= height_mm * 1.05
        v.co.x += (length_mm/2 + pad_length_mm/2)
    
    mesh_right = bpy.data.meshes.new("Right_Pad")
    bm_right.to_mesh(mesh_right)
    bm_right.free()
    
    obj_right = bpy.data.objects.new("Right_Pad", mesh_right)
    collection.objects.link(obj_right)
    getattr(obj_right.data, "materials").append(pad_mat)
    obj_right.location.z += height_mm * 1.05/2
    
    return [obj_left, obj_right]
    
def create_resistor_cover(collection, length_mm, width_mm, height_mm, thickness_mm):
    """创建电阻表面涂层"""
    # 创建材质
    cover_mat = create_material("Resistor_Cover", (0.1, 0.1, 0.1), metallic=0.0, roughness=0.8, weight=0.1, ior=1.5)
    
    # 创建网格
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    
    # 缩放
    for v in bm.verts:
        v.co.x *= length_mm
        v.co.y *= width_mm
        v.co.z *= thickness_mm
    
    # 创建网格对象
    mesh = bpy.data.meshes.new("Resistor_Cover")
    bm.to_mesh(mesh)
    bm.free()
    
    obj = bpy.data.objects.new("Resistor_Cover", mesh)
    collection.objects.link(obj)
    
    # 应用材质
    getattr(obj.data, "materials").clear()
    getattr(obj.data, "materials").append(cover_mat)
    obj.location.z += height_mm * 1.025

    return obj
    
def create_silk_screen(collection, code, height_mm, width_mm, thickness_mm):
    """创建丝印"""
    # 获取丝印颜色
    silk_mat = create_material("Silk_Screen", (1.0, 1.0, 1.0, 1.0), metallic=0.0, roughness=0.9)
    
    # 创建文本曲线
    curve_data = bpy.data.curves.new(type="FONT", name="Silk_Screen_Text")
    setattr(curve_data, "body", code)
    setattr(curve_data, "align_x", 'CENTER')
    setattr(curve_data, "align_y", 'CENTER')
    setattr(curve_data, "size", width_mm * 0.5)
    
    # 尝试使用默认字体
    if bpy.data.fonts:
        setattr(curve_data, "font", bpy.data.fonts[0])
    
    # 创建文本对象
    text_obj = bpy.data.objects.new("Silk_Screen_Text", curve_data)
    collection.objects.link(text_obj)
    setattr(text_obj.data, "extrude", thickness_mm * 0.5)
    
    # 设置文本对象的位置、旋转和缩放
    text_obj.scale = (1, 1, 0.1)
    bpy.ops.object.transform_apply(scale=True)
    text_obj.location.z = height_mm * 1.025 + 0.0175 + 0.005

    # 转换为网格
    if bpy.context:
        bpy.context.view_layer.objects.active = text_obj
    text_obj.select_set(True)
    
    # 转换曲线为网格
    bpy.ops.object.convert(target='MESH')
    
    # 获取转换后的网格对象
    if bpy.context:
        mesh_obj = bpy.context.active_object
    
    # 重命名
    if mesh_obj:
        mesh_obj.name = "Silk_Screen"
        getattr(mesh_obj.data, "materials").append(silk_mat)  # 应用材质
    
    return mesh_obj

# ==================== 面板类 ====================
class VIEW3D_PT_SMDResistorGenerator(Panel):
    """贴片电阻生成器面板"""
    bl_label = "贴片电阻"
    bl_idname = "VIEW3D_PT_smd_resistor_generator"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "电阻工具"
    bl_order = 1
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        layout = self.layout
        if context:
            props = getattr(context.scene, "smd_resistor_props")
        
        # 输入参数部分
        box = layout.box()
        box.label(text="电阻参数", icon='SETTINGS')
        
        # 电阻值
        row = box.row()
        row.label(text="电阻值:")
        row.prop(props, "resistance", text="")
        
        # 公差
        row = box.row()
        row.label(text="公差:")
        row.prop(props, "tolerance", text="")
        
        # 封装尺寸
        row = box.row()
        row.label(text="封装尺寸:")
        row.prop(props, "package_size", text="")
        
        # 代码类型
        row = box.row()
        row.label(text="代码类型:")
        row.label(text=props.code_type)
        
        layout.separator()
        
        # 实时计算结果
        result_box = layout.box()
        result_box.label(text="计算结果", icon='DRIVER')
        
        standard_value = props.resistance
        if props.code_type == 'EIA-96':
            result = resistor_to_eia96(props.resistance)
            code_to_show = result['eia96_mark']
            standard_value = result['standard_value']
        elif props.code_type == '4位编码':
            code_to_show = resistance_to_4digit(props.resistance)
        else:
            code_to_show = resistance_to_3digit(props.resistance)
        
        # 显示标准值
        row = result_box.row()
        if standard_value != props.resistance:
            row.label(text="标准值:", icon='INFO')
        else:
            row.label(text="电阻值:", icon='CHECKMARK')
        row.label(text=f"{format_resistance(standard_value)}")
        
        # 显示丝印代码
        row = result_box.row()
        row.label(text="丝印代码:", icon='SORTBYEXT')
        row.label(text=code_to_show, icon='TEXT')

        # 显示标准值与输入值的偏差
        row = result_box.row()
        if standard_value != props.resistance:
            row.label(text="偏差:", icon='MODIFIER')
            row.label(text=f"{(standard_value - props.resistance) / standard_value * 100:.2f}%")
        
        # 操作按钮
        action_box = layout.box()
        row = action_box.row()
        row.scale_y = 1.5
        row.operator("smd.generate_resistor", text="生成电阻", icon='ADD')

def generate_smd_resistor(resistance: float, tolerance: str, package_size: str) -> bpy.types.Collection:
    """生成贴片电阻模型"""
    code_type = get_code_type(package_size, tolerance)
    # 计算电阻代码
    code_to_show = None
    if code_type == 'EIA-96':
        code_dict = resistor_to_eia96(resistance)
        print(f"   -> 相对误差：{code_dict['relative_error']}")
        if code_dict['relative_error'] >= 0.01:
            code_to_show = resistance_to_3digit(resistance)
        else:
            code_to_show = code_dict['eia96_mark']
    elif code_type == '4位编码':
        code_to_show = resistance_to_4digit(resistance)
    elif code_type == '3位编码':
        # 3DIGIT
        code_to_show = resistance_to_3digit(resistance)
    print(f'   -> 代码：{code_to_show}')
 
    # 创建电阻集合
    if code_to_show == "无" or code_to_show == "未知":
        collection_name = f"SMD_Resistor_{package_size}"
    else:
        collection_name = f"SMD_Resistor_{package_size}_{code_to_show}"
    
    collection = bpy.data.collections.new(collection_name)
    if bpy.context:
        bpy.context.scene.collection.children.link(collection)
        
    return generate_smd_resistor_with_code(collection, package_size, code_to_show)

def generate_smd_resistor_with_code(collection: bpy.types.Collection, package_size: str, silk_code: str|None) -> bpy.types.Collection:
    # 获取封装尺寸
    if package_size in SMD_SIZES:
        length_mm, width_mm, height_mm, pad_length_mm = SMD_SIZES[package_size]
    else:
        # 默认0805封装
        length_mm, width_mm, height_mm, pad_length_mm = SMD_SIZES['0805']
    
    # 创建电阻主体
    create_resistor_body(collection, length_mm, width_mm, height_mm)
    
    # # 创建焊盘
    create_pads(collection, length_mm, width_mm, height_mm, pad_length_mm)
            
    # 创建树脂层
    create_resistor_cover(collection, length_mm, width_mm, height_mm, 0.035)

    # 创建丝印
    create_silk_screen(collection, silk_code, height_mm, width_mm, 0.0175)
    
    return collection

        
# ==================== 注册和注销 ====================
classes = [
    SMDResistorProperties,
    SMD_OT_GenerateResistor,
    VIEW3D_PT_SMDResistorGenerator,
]

def register():
    """注册插件"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册属性组
    setattr(bpy.types.Scene, "smd_resistor_props", bpy.props.PointerProperty(type=SMDResistorProperties))
    
    print("贴片电阻生成器已注册")
    
def unregister():
    """注销插件"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 清理属性组
    try:
        delattr(bpy.types.Scene, "smd_resistor_props")
    except AttributeError:
        pass
    
    print("贴片电阻生成器已注销")

# 如果直接运行，则注册插件
if __name__ == "__main__":
    register()