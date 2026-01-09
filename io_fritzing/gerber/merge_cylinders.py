import bpy
import re
import os
from collections import defaultdict
from mathutils import Vector
from bpy.props import BoolProperty, FloatProperty, StringProperty, EnumProperty
from bpy.types import Panel, Operator, PropertyGroup

# 插件信息
bl_info = {
    "name": "Fritzing钻孔工具管理器",
    "version": (2, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Fritzing工具 > 钻孔工具",
    "description": "合并钻孔圆柱体并生成直径汇总报告",
    "category": "Fritzing",
}

# 全局变量用于存储统计信息
pre_merge_stats = None
merge_operation_performed = False

# 自定义属性组
class DrillToolsProperties(PropertyGroup):
    # 选项
    auto_create_labels: BoolProperty(
        name="自动创建直径标签",
        description="合并后自动在3D视图中创建直径标签",
        default=True
    ) # type: ignore
    
    # 显示选项
    show_details: BoolProperty(
        name="显示详细信息",
        description="显示每个工具组的详细信息",
        default=True
    ) # type: ignore
    
    # 合并选项
    merge_selected_only: BoolProperty(
        name="仅处理选中对象",
        description="只处理选中的Drill_Cylinder对象",
        default=False
    ) # type: ignore
    
    rename_single_objects: BoolProperty(
        name="重名单个对象",
        description="即使只有一个圆柱体，也重命名为规范名称",
        default=True
    ) # type: ignore

# 合并操作符
class DRILLTOOLS_OT_MergeCylinders(Operator):
    bl_idname = "drilltools.merge_cylinders"
    bl_label = "合并钻孔工具"
    bl_description = "合并相同工具编号的钻孔圆柱体并生成直径汇总"
    
    def execute(self, context):
        global pre_merge_stats, merge_operation_performed
        
        props = context.scene.drill_tools_props
        
        # 获取设置
        selected_only = props.merge_selected_only
        auto_create_labels = props.auto_create_labels
        rename_single_objects = props.rename_single_objects
        
        # 保存合并前的统计信息
        pre_merge_stats = get_current_stats(selected_only)
        
        # 执行合并
        merged_objects, diameter_summary = merge_drill_cylinders_with_simple_diameter(
            selected_only, 
            rename_single_objects
        )
        
        if not merged_objects:
            self.report({'WARNING'}, "没有找到Drill_Cylinder对象")
            return {'CANCELLED'}
        
        # 设置合并操作标志
        merge_operation_performed = True
        
        # 在控制台打印汇总
        print_simple_diameter_summary(diameter_summary)
        
        # 选中所有处理后的对象
        bpy.ops.object.select_all(action='DESELECT')
        for obj in merged_objects:
            if obj and obj.name in bpy.data.objects:
                obj.select_set(True)
        if merged_objects and merged_objects[0].name in bpy.data.objects:
            context.view_layer.objects.active = merged_objects[0]
        
        # 显示统计信息
        stats = get_diameter_statistics(diameter_summary)
        self.report({'INFO'}, f"完成! 处理了 {stats['total_tools']} 种工具, {stats['total_holes']} 个钻孔")
        
        return {'FINISHED'}

# 查看汇总操作符
class DRILLTOOLS_OT_ShowSummary(Operator):
    bl_idname = "drilltools.show_summary"
    bl_label = "查看直径汇总"
    bl_description = "在控制台显示钻孔工具直径汇总"
    
    def execute(self, context):
        global merge_operation_performed
        
        # 获取设置
        props = context.scene.drill_tools_props
        selected_only = props.merge_selected_only
        
        # 获取当前统计信息
        stats = get_current_stats(selected_only)
        
        if not stats['drill_objects']:
            self.report({'WARNING'}, "没有找到Drill_Cylinder对象")
            return {'CANCELLED'}
        
        # 在控制台显示汇总
        print("\n" + "="*50)
        print("当前钻孔工具统计")
        print("="*50)
        print(f"钻孔圆柱体总数: {stats['total_holes']} 个")
        print(f"工具种类: {stats['total_groups']} 种")
        
        # 显示每个组的详细信息
        sorted_groups = sorted(stats['cylinder_groups'].items(), key=lambda x: int(x[0]))
        print(f"\n{'工具编号':<10} {'孔数':<8} {'直径(m)':<12}")
        print("-" * 40)
        
        for cylinder_number, objects in sorted_groups:
            if objects:
                diameter = objects[0].dimensions.x
                print(f"T{cylinder_number:<9} {len(objects):<8} {diameter:<12.6f}")
        
        # 显示合并状态
        if merge_operation_performed:
            print("\n⚠ 注意: 此统计显示的是当前场景中的对象状态")
            print("  如果已执行合并操作，请查看合并后的汇总报告以获取详细直径信息")
        
        self.report({'INFO'}, f"汇总完成: {stats['total_groups']} 种工具, {stats['total_holes']} 个钻孔")
        return {'FINISHED'}

# 清理工具编号操作符
class DRILLTOOLS_OT_CleanupToolNumbers(Operator):
    bl_idname = "drilltools.cleanup_tool_numbers"
    bl_label = "清理工具编号"
    bl_description = "清理和重新编号工具，确保编号从1开始连续"
    
    def execute(self, context):
        global merge_operation_performed
        
        all_objects = bpy.data.objects
        cylinder_groups = defaultdict(list)
        
        # 匹配所有可能的Drill_Cylinder格式
        patterns = [
            re.compile(r'^Drill_Cylinder_(\d+)(?:_Mat)?(?:\.\d{3})?$'),
            re.compile(r'^Drill_Cylinder_(\d+)_\d+$'),
            re.compile(r'^Drill_Cylinder_(\d+)\.\d+$'),
        ]
        
        for obj in all_objects:
            if obj.type != 'MESH':
                continue
            
            for pattern in patterns:
                match = pattern.match(obj.name)
                if match:
                    cylinder_number = int(match.group(1))
                    cylinder_groups[cylinder_number].append(obj)
                    break
        
        if not cylinder_groups:
            self.report({'WARNING'}, "没有找到Drill_Cylinder对象")
            return {'CANCELLED'}
        
        # 重新编号
        sorted_numbers = sorted(cylinder_groups.keys())
        renumber_map = {}
        
        for i, old_number in enumerate(sorted_numbers, 1):
            renumber_map[old_number] = i
        
        renamed_count = 0
        for old_number, objects in cylinder_groups.items():
            new_number = renumber_map[old_number]
            
            for obj in objects:
                # 构建新的名称
                if old_number != new_number or not obj.name.startswith(f"Drill_Cylinder_{old_number}"):
                    obj.name = f"Drill_Cylinder_{new_number}"
                    renamed_count += 1
        
        # 重置合并标志
        merge_operation_performed = False
        
        self.report({'INFO'}, f"重新编号完成: {len(cylinder_groups)} 种工具, 重命名了 {renamed_count} 个对象")
        return {'FINISHED'}

# 面板
class DRILLTOOLS_PT_MainPanel(Panel):
    bl_label = "钻孔合并工具"
    bl_idname = "DRILLTOOLS_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing工具"
    bl_context = "objectmode"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        global pre_merge_stats, merge_operation_performed
        
        layout = self.layout
        scene = context.scene
        props = scene.drill_tools_props
        
        # 主操作按钮
        box = layout.box()
        box.label(text="主操作", icon='TOOL_SETTINGS')
        
        row = box.row()
        row.scale_y = 1.5
        row.operator("drilltools.merge_cylinders", text="合并钻孔工具", icon='AUTOMERGE_OFF')
        
        # 选项
        box = layout.box()
        box.label(text="选项", icon='PREFERENCES')
        
        box.prop(props, "merge_selected_only")
        box.prop(props, "rename_single_objects")
        box.prop(props, "show_details")
        
        # 工具按钮
        box = layout.box()
        box.label(text="工具", icon='TOOL_SETTINGS')
        
        col = box.column(align=True)
        col.operator("drilltools.show_summary", icon='VIEWZOOM')
        col.operator("drilltools.cleanup_tool_numbers", icon='SORTALPHA')
        
        # 状态信息
        if props.show_details:
            box = layout.box()
            box.label(text="状态", icon='INFO')
            
            # 根据是否执行过合并操作显示不同的状态信息
            if merge_operation_performed and pre_merge_stats:
                # 显示合并前的统计信息
                stats = pre_merge_stats
                if merge_operation_performed:
                    box.label(text="*已执行合并操作*", icon='INFO')
                    box.label(text="以下是合并前的统计信息:")
            else:
                # 获取当前实时统计
                stats = get_current_stats(props.merge_selected_only)
            
            if stats['drill_objects']:
                box.label(text=f"共 {stats['total_holes']} 个钻孔圆柱体", icon='MESH_CYLINDER')
                box.label(text=f"共 {stats['total_groups']} 种工具编号", icon='LINENUMBERS_ON')
                
                # 显示工具列表
                sorted_groups = sorted(stats['cylinder_groups'].items(), key=lambda x: int(x[0]))
                for i, (num, objects) in enumerate(sorted_groups[:6]):  # 最多显示6个
                    if objects:
                        diameter = objects[0].dimensions.x
                        box.label(text=f"  T{num}: {len(objects)}孔, {diameter:.3f}m")
                
                if len(stats['cylinder_groups']) > 6:
                    box.label(text=f"  ... 还有 {len(stats['cylinder_groups']) - 6} 种工具")
                
                # 如果已合并，添加说明
                if merge_operation_performed:
                    box.separator()
                    box.label(text="合并后，每个工具组已合并为单个对象", icon='INFO')
                    current_stats = get_current_stats(props.merge_selected_only)
                    if current_stats['total_objects'] != stats['total_groups']:
                        box.label(text=f"当前有 {current_stats['total_objects']} 个Drill_Cylinder对象", icon='OUTLINER_OB_MESH')
            else:
                box.label(text="未找到Drill_Cylinder", icon='ERROR')

# 工具函数
def get_current_stats(selected_only=False):
    """获取当前场景中的Drill_Cylinder统计信息"""
    # 获取对象
    if selected_only:
        all_objects = bpy.context.selected_objects
    else:
        all_objects = bpy.data.objects
    
    # 按数字分组存储Drill_Cylinder
    cylinder_groups = defaultdict(list)
    
    # 使用多个模式匹配
    patterns = [
        re.compile(r'^Drill_Cylinder_(\d+)(?:_Mat)?(?:\.\d{3})?$'),
        re.compile(r'^Drill_Cylinder_(\d+)_\d+$'),  # 匹配 Drill_Cylinder_1_001
        re.compile(r'^Drill_Cylinder_(\d+)\.\d+$'),  # 匹配 Drill_Cylinder_1.001
    ]
    
    drill_objects = []
    for obj in all_objects:
        if obj.type != 'MESH':
            continue
        
        for pattern in patterns:
            match = pattern.match(obj.name)
            if match:
                cylinder_number = match.group(1)
                cylinder_groups[cylinder_number].append(obj)
                drill_objects.append(obj)
                break
    
    # 计算统计信息
    total_holes = len(drill_objects)
    total_groups = len(cylinder_groups)
    total_objects = len([obj for obj in drill_objects])
    
    stats = {
        'drill_objects': drill_objects,
        'cylinder_groups': cylinder_groups,
        'total_holes': total_holes,
        'total_groups': total_groups,
        'total_objects': total_objects
    }
    
    return stats

def merge_drill_cylinders_with_simple_diameter(selected_only=False, rename_single_objects=True):
    """简化版：合并Drill_Cylinder并提取直径信息"""
    
    print("开始合并Drill_Cylinder并提取直径信息...")
    
    # 获取对象
    if selected_only:
        all_objects = bpy.context.selected_objects
    else:
        all_objects = bpy.data.objects
    
    # 按数字分组存储Drill_Cylinder
    cylinder_groups = defaultdict(list)
    
    # 使用多个模式匹配
    patterns = [
        re.compile(r'^Drill_Cylinder_(\d+)(?:_Mat)?(?:\.\d{3})?$'),
        re.compile(r'^Drill_Cylinder_(\d+)_\d+$'),  # 匹配 Drill_Cylinder_1_001
        re.compile(r'^Drill_Cylinder_(\d+)\.\d+$'),  # 匹配 Drill_Cylinder_1.001
    ]
    
    for obj in all_objects:
        if obj.type != 'MESH':
            continue
        
        for pattern in patterns:
            match = pattern.match(obj.name)
            if match:
                cylinder_number = match.group(1)
                cylinder_groups[cylinder_number].append(obj)
                break
    
    if not cylinder_groups:
        print("没有找到Drill_Cylinder对象")
        return [], {}
    
    print(f"找到 {len(cylinder_groups)} 组Drill_Cylinder")
    
    # 合并每组，并记录直径信息
    merged_objects = []
    diameter_summary = {}
    
    for cylinder_number, objects in cylinder_groups.items():
        if not objects:
            continue
            
        # 简化直径计算：取第一个对象的X维度作为直径
        first_obj = objects[0]
        diameter = first_obj.dimensions.x
        
        # 处理单个或多个对象
        if len(objects) > 1:
            print(f"合并第 {cylinder_number} 组 ({len(objects)} 个对象, 直径: {diameter:.6f}m):")
            merged_obj = merge_cylinder_group_safe(objects, cylinder_number)
            if merged_obj:
                merged_objects.append(merged_obj)
                current_obj = merged_obj
            else:
                # 如果合并失败，使用第一个对象
                current_obj = first_obj
                if rename_single_objects:
                    current_obj.name = f"Drill_Cylinder_{cylinder_number}"
        else:
            # 只有一个对象
            print(f"第 {cylinder_number} 组只有1个对象 (直径: {diameter:.6f}m)")
            current_obj = first_obj
            if rename_single_objects:
                if not current_obj.name.startswith(f"Drill_Cylinder_{cylinder_number}"):
                    current_obj.name = f"Drill_Cylinder_{cylinder_number}"
            merged_objects.append(current_obj)
        
        # 记录直径信息
        diameter_summary[cylinder_number] = {
            'object': current_obj,
            'diameter': diameter,
            'object_count': len(objects),  # 注意：这是合并前的孔数
            'tool_number': cylinder_number
        }
    
    print(f"处理完成! 共处理 {len(merged_objects)} 个圆柱体")
    return merged_objects, diameter_summary

def merge_cylinder_group_safe(objects, cylinder_number):
    """安全地合并同一组的圆柱体，避免引用已删除的对象"""
    if len(objects) < 2:
        return objects[0] if objects else None
    
    # 保存当前选择和激活状态（只保存名称，而不是对象引用）
    original_selected_names = [obj.name for obj in bpy.context.selected_objects]
    original_active_name = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
    
    try:
        # 取消选择所有对象
        bpy.ops.object.select_all(action='DESELECT')
        
        # 选择要合并的所有对象
        for obj in objects:
            obj.select_set(True)
        
        # 设置第一个对象为激活对象
        bpy.context.view_layer.objects.active = objects[0]
        
        # 执行合并
        bpy.ops.object.join()
        
        # 获取合并后的对象
        merged_obj = bpy.context.active_object
        
        # 重命名为 Drill_Cylinder_数字
        new_name = f"Drill_Cylinder_{cylinder_number}"
        merged_obj.name = new_name
        
        print(f"  ✓ 合并为: {new_name}")
        
        return merged_obj
        
    except Exception as e:
        print(f"  ✗ 合并第 {cylinder_number} 组时出错: {e}")
        return None
        
    finally:
        # 恢复原始选择状态（通过名称查找对象）
        bpy.ops.object.select_all(action='DESELECT')
        
        # 恢复选择状态
        for obj_name in original_selected_names:
            if obj_name in bpy.data.objects:
                bpy.data.objects[obj_name].select_set(True)
        
        # 恢复激活对象
        if original_active_name and original_active_name in bpy.data.objects:
            bpy.context.view_layer.objects.active = bpy.data.objects[original_active_name]

def print_simple_diameter_summary(diameter_summary):
    """打印简化的直径汇总表"""
    if not diameter_summary:
        print("没有直径数据可汇总")
        return
    
    print("\n" + "="*50)
    print("钻孔工具直径汇总表")
    print("="*50)
    
    # 按工具编号排序
    sorted_summary = sorted(diameter_summary.items(), key=lambda x: int(x[0]))
    
    # 打印表格标题
    print(f"{'工具编号':<10} {'直径(m)':<15} {'孔数':<8} {'状态':<10}")
    print("-" * 60)
    
    total_holes = 0
    total_objects = 0
    
    # 打印每行数据
    for tool_number, data in sorted_summary:
        diameter = data['diameter']
        count = data['object_count']
        status = "已合并" if data['object_count'] > 1 else "单孔"
        
        print(f"T{tool_number:<9} {diameter:<15.6f} {count:<8} {status:<10}")
        total_holes += count
        total_objects += 1
    
    # 统计信息
    print("-" * 60)
    unique_diameters = len(set(round(data['diameter'], 6) for data in diameter_summary.values()))
    
    print(f"工具种类: {len(diameter_summary)} 种")
    print(f"合并前钻孔总数: {total_holes} 个")
    print(f"合并后对象数: {len(diameter_summary)} 个")
    print(f"唯一直径: {unique_diameters} 种")
    
    # 按直径分组显示
    if unique_diameters > 1:
        print("\n直径分布:")
        diameter_groups = defaultdict(list)
        for tool_num, data in diameter_summary.items():
            rounded_diameter = round(data['diameter'], 6)
            diameter_groups[rounded_diameter].append(f"T{tool_num}")
        
        for diameter, tools in sorted(diameter_groups.items()):
            print(f"  {diameter:.6f}m: {len(tools)} 种工具 ({', '.join(tools)})")
    
    # 检查是否有编号不连续
    tool_numbers = [int(num) for num in diameter_summary.keys()]
    min_num = min(tool_numbers) if tool_numbers else 0
    max_num = max(tool_numbers) if tool_numbers else 0
    expected_count = max_num - min_num + 1 if tool_numbers else 0
    missing_count = expected_count - len(tool_numbers)
    
    if missing_count > 0:
        print(f"\n⚠ 注意: 工具编号不连续")
        print(f"  最小编号: T{min_num}")
        print(f"  最大编号: T{max_num}")
        print(f"  应有工具数: {expected_count}")
        print(f"  实际工具数: {len(tool_numbers)}")
        print(f"  缺失工具数: {missing_count}")
        
        # 找出缺失的编号
        all_numbers = set(range(min_num, max_num + 1))
        existing_numbers = set(tool_numbers)
        missing_numbers = sorted(all_numbers - existing_numbers)
        if missing_numbers:
            print(f"  缺失的编号: {', '.join([f'T{num}' for num in missing_numbers[:10]])}")
            if len(missing_numbers) > 10:
                print(f"  ... 还有 {len(missing_numbers) - 10} 个")

def export_diameter_summary_to_text(diameter_summary, filename="钻孔工具汇总报告.txt"):
    """将直径汇总数据导出为文本文件"""
    try:
        # 获取Blender文件所在目录
        blend_file_path = bpy.data.filepath
        if blend_file_path:
            directory = os.path.dirname(blend_file_path)
            file_path = os.path.join(directory, filename)
        else:
            file_path = filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("钻孔工具直径汇总报告\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"生成时间: {bpy.utils.time_to_datetime_string()}\n")
            f.write(f"Blender文件: {os.path.basename(blend_file_path) if blend_file_path else '未保存'}\n\n")
            
            # 按工具编号排序
            sorted_summary = sorted(diameter_summary.items(), key=lambda x: int(x[0]))
            
            # 写入表格
            f.write(f"{'工具编号':<10} {'直径(m)':<15} {'孔数':<8} {'状态':<10}\n")
            f.write("-" * 50 + "\n")
            
            for tool_number, data in sorted_summary:
                diameter = data['diameter']
                count = data['object_count']
                status = "已合并" if data['object_count'] > 1 else "单孔"
                f.write(f"T{tool_number:<9} {diameter:<15.6f} {count:<8} {status:<10}\n")
            
            f.write("\n" + "=" * 50 + "\n")
            
            # 统计信息
            total_holes = sum(data['object_count'] for data in diameter_summary.values())
            unique_diameters = len(set(round(data['diameter'], 6) for data in diameter_summary.values()))
            
            f.write("统计信息:\n")
            f.write(f"  工具总数: {len(diameter_summary)}\n")
            f.write(f"  合并前钻孔总数: {total_holes}\n")
            f.write(f"  合并后对象数: {len(diameter_summary)}\n")
            f.write(f"  唯一直径数: {unique_diameters}\n")
            
            # 直径分布
            if unique_diameters > 1:
                f.write("\n直径分布:\n")
                diameter_groups = defaultdict(list)
                for tool_num, data in diameter_summary.items():
                    rounded_diameter = round(data['diameter'], 6)
                    diameter_groups[rounded_diameter].append(f"T{tool_num}")
                
                for diameter, tools in sorted(diameter_groups.items()):
                    f.write(f"  {diameter:.6f}m: {len(tools)} 种工具 ({', '.join(tools)})\n")
            
            f.write("\n" + "=" * 50 + "\n")
            f.write("报告结束\n")
        
        print(f"钻孔工具汇总已导出到: {file_path}")
        return file_path
        
    except Exception as e:
        print(f"导出文本文件时出错: {e}")
        return None

def get_diameter_statistics(diameter_summary):
    """获取直径统计信息"""
    if not diameter_summary:
        return {}
    
    diameters = [data['diameter'] for data in diameter_summary.values()]
    counts = [data['object_count'] for data in diameter_summary.values()]
    
    stats = {
        'total_tools': len(diameter_summary),
        'total_holes': sum(counts),
        'total_objects': len(diameter_summary),  # 合并后的对象数
        'avg_diameter': sum(diameters) / len(diameters) if diameters else 0,
        'min_diameter': min(diameters) if diameters else 0,
        'max_diameter': max(diameters) if diameters else 0,
        'diameter_range': (max(diameters) - min(diameters)) if diameters else 0,
        'unique_diameters': len(set(round(d, 6) for d in diameters)) if diameters else 0
    }
    
    return stats

# 注册/注销函数
classes = [
    DrillToolsProperties,
    DRILLTOOLS_OT_MergeCylinders,
    DRILLTOOLS_OT_ShowSummary,
    DRILLTOOLS_OT_CleanupToolNumbers,
    DRILLTOOLS_PT_MainPanel,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册自定义属性
    bpy.types.Scene.drill_tools_props = bpy.props.PointerProperty(type=DrillToolsProperties)
    
    print("Fritzing钻孔工具管理器已注册 (版本 2.1.0)")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 删除自定义属性
    del bpy.types.Scene.drill_tools_props
    
    print("Fritzing钻孔工具管理器已注销")

# 如果作为独立脚本运行
if __name__ == "__main__":
    # 临时注册以进行测试
    try:
        unregister()
    except:
        pass
    register()