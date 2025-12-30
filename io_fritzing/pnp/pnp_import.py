import bpy
import os
import time
import math
import json
import re
import threading
import queue
from bpy.types import Operator, Panel, PropertyGroup, Scene, Collection
from bpy.props import (
    StringProperty, IntProperty, FloatProperty, 
    BoolProperty, EnumProperty, PointerProperty
)
from datetime import datetime
from collections import defaultdict
from io_fritzing.assets.resistors.YC164 import generate_yc164_resistor
from io_fritzing.pnp.utils.parse_resistor import parse_resistance_string
from io_fritzing.assets.switch.TS_D014 import create_ts_d014_switch
from io_fritzing.assets.switch.PB86_A0 import create_pb86_button
from io_fritzing.assets.resistors.smd_resistors import generate_smd_resistor, SMD_SIZES
from io_fritzing.assets.sod.sod123 import create_sod123_model
from io_fritzing.assets.sod.sod323 import create_sod323_model
from io_fritzing.assets.sot.sot23_3 import create_sot23_3_model
from io_fritzing.assets.sot.sot23_6 import create_sot23_6_model
from io_fritzing.assets.mx.mx125 import create_mx125_2p
from io_fritzing.assets.vqfn_hr.vqfn_hr_12 import create_vqfn_hr_12
from io_fritzing.assets.sop.sop20 import create_sop20_model
from io_fritzing.assets.esp.esp12 import create_esp12f_model
from io_fritzing.assets.buzzer.buzzer9042 import create_buzzer_9042_model
from io_fritzing.assets.type_c.usb_type_c_16pin import create_usb_type_c_16pin_model
from io_fritzing.assets.pptc.pptc0603 import create_smd0603_fuse_model
from io_fritzing.assets.esop.esop8 import create_esop8_model
from io_fritzing.assets.msop.msop10 import create_msop10_model
from io_fritzing.assets.led.led0603 import create_led0603_with_color
from io_fritzing.assets.capacitors.smd_e_cap import create_smd_ecap_model
from io_fritzing.assets.capacitors.smd_capacitor import create_smd_capacitor_model
from io_fritzing.assets.inductor.smd_inductor import create_smd_inductor_model
from io_fritzing.assets.wdfn.wdfn import create_wdfn_3x3_10_model


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
# 全局状态管理器
# ============================================================================
class PNPImportState:
    """PNP导入状态管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PNPImportState, cls).__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self):
        """初始化状态"""
        self.is_importing = False
        self.is_paused = False
        self.should_cancel = False
        self.has_errors = False
        
        # 进度信息
        self.total_lines = 0
        self.processed_lines = 0
        self.success_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.invalid_count = 0
        
        # 当前处理信息
        self.current_file = ""
        self.current_component = ""
        self.current_action = ""
        self.current_line_number = 0
        
        # 时间信息
        self.start_time = 0
        self.elapsed_time = 0
        
        # 详细记录（包含原始行）
        self.success_lines = []
        self.failed_lines = []
        self.skipped_lines = []
        self.invalid_lines = []
        
        # 原始行数据缓存
        self.original_lines = []  # 存储所有原始行
        self.error_lines_data = []  # 存储错误和跳过的行
        
        # 结果存储
        self.final_results = None
        
        # 回调函数列表
        self.update_callbacks = []
    
    def reset(self):
        """重置状态"""
        self._init()
    
    def start_import(self, filepath, total_lines):
        """开始导入"""
        self.reset()
        self.is_importing = True
        self.current_file = filepath
        self.total_lines = total_lines
        self.start_time = time.time()
        self._notify_update()
    
    def update_progress(self, line_number, component="", action=""):
        """更新进度"""
        self.processed_lines = line_number
        self.current_component = component
        self.current_action = action
        self.current_line_number = line_number
        self.elapsed_time = time.time() - self.start_time
        self._notify_update()
    
    def add_success(self, line_number, component, message, raw_line=""):
        """添加成功记录"""
        self.success_count += 1
        self.success_lines.append({
            'line': line_number,
            'component': component,
            'message': message,
            'raw_line': raw_line,
            'time': datetime.now().strftime("%H:%M:%S")
        }) 
    
    def add_failed(self, line_number, component, message, raw_line=""):
        """添加失败记录"""
        self.failed_count += 1
        self.has_errors = True
        self.failed_lines.append({
            'line': line_number,
            'component': component,
            'message': message,
            'raw_line': raw_line,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        # 同时保存到错误行数据
        self.error_lines_data.append({
            'type': 'failed',
            'line': line_number,
            'raw': raw_line,
            'error': message
        })
    
    def add_skipped(self, line_number, message, raw_line=""):
        """添加跳过记录"""
        self.skipped_count += 1
        self.skipped_lines.append({
            'line': line_number,
            'message': message,
            'raw_line': raw_line,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        # 同时保存到错误行数据
        self.error_lines_data.append({
            'type': 'skipped',
            'line': line_number,
            'raw': raw_line,
            'error': message
        })
    
    def add_invalid(self, line_number, message, raw_line=""):
        """添加无效记录"""
        self.invalid_count += 1
        self.invalid_lines.append({
            'line': line_number,
            'message': message,
            'raw_line': raw_line,
            'time': datetime.now().strftime("%H:%M:%S")
        })
        # 同时保存到错误行数据
        self.error_lines_data.append({
            'type': 'skipped',
            'line': line_number,
            'raw': raw_line,
            'error': message
        })
    
    def pause(self):
        """暂停导入"""
        self.is_paused = True
        self._notify_update()
    
    def resume(self):
        """恢复导入"""
        self.is_paused = False
        self._notify_update()
    
    def cancel(self):
        """取消导入"""
        self.should_cancel = True
        self._notify_update()
    
    def complete(self):
        """完成导入"""
        self.is_importing = False
        self.elapsed_time = time.time() - self.start_time
        
        # 保存最终结果
        self.final_results = {
            'status': 'COMPLETED',
            'total': self.total_lines,
            'success': self.success_count,
            'failed': self.failed_count,
            'skipped': self.skipped_count,
            'elapsed_time': self.elapsed_time,
            'success_items': self.success_lines,
            'failed_items': self.failed_lines,
            'skipped_items': self.skipped_lines,
            'invalid_items': self.invalid_lines,
            'file_name': os.path.basename(self.current_file) if self.current_file else "",
            'file_path': self.current_file,
            'has_errors': self.has_errors,
            'error_lines_count': len(self.error_lines_data)
        }
        self._notify_update()
    
    def get_progress(self):
        """获取进度百分比"""
        if self.total_lines == 0:
            return 0.0
        return (self.processed_lines / self.total_lines) * 100
    
    def get_eta(self):
        """获取预计剩余时间"""
        if self.processed_lines == 0:
            return 0.0
        elapsed = time.time() - self.start_time
        speed = elapsed / self.processed_lines
        remaining = (self.total_lines - self.processed_lines) * speed
        return remaining
    
    def get_summary(self):
        """获取状态摘要"""
        return {
            'is_importing': self.is_importing,
            'is_paused': self.is_paused,
            'has_errors': self.has_errors,
            'progress': self.get_progress(),
            'processed_lines': self.processed_lines,
            'total_lines': self.total_lines,
            'success_count': self.success_count,
            'failed_count': self.failed_count,
            'skipped_count': self.skipped_count,
            'elapsed_time': self.elapsed_time,
            'eta': self.get_eta(),
            'current_component': self.current_component,
            'current_action': self.current_action,
            'current_line': self.current_line_number,
            'error_lines_count': len(self.error_lines_data)
        }
    
    def get_error_data_for_export(self, format_type='WITH_COMMENTS', include_skipped=True):
        """获取错误数据用于导出"""
        export_lines = []
        
        if format_type == 'WITH_COMMENTS':
            # 添加文件头
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            export_lines.append(f"# PNP导入错误数据")
            export_lines.append(f"# 生成时间: {timestamp}")
            export_lines.append(f"# 原始文件: {os.path.basename(self.current_file) if self.current_file else '未知'}")
            export_lines.append(f"# 错误总数: {self.failed_count}")
            export_lines.append(f"# 跳过总数: {self.skipped_count}")
            export_lines.append(f"# 无效总数: {self.invalid_count}")
            export_lines.append(f"#")
            export_lines.append(f"# 格式说明:")
            export_lines.append(f"#   [失败] - 解析或创建失败的元件")
            export_lines.append(f"#   [跳过] - 被跳过的行（空行、注释、不需导入的元素等）")
            export_lines.append(f"#   [无效] - 无效的行（格式错误）")
            export_lines.append(f"#")
            
            # 按行号排序
            sorted_data = sorted(self.error_lines_data, key=lambda x: x['line'])
            
            for item in sorted_data:
                if item['type'] == 'failed' or (include_skipped and item['type'] == 'skipped'):
                    error_type = "失败" if item['type'] == 'failed' else "跳过"
                    export_lines.append(f"# [{error_type}] 行{item['line']}: {item['error']}")
                    export_lines.append(item['raw'])
                    export_lines.append("")
        
        elif format_type == 'RAW_ONLY':
            # 只导出原始行
            sorted_data = sorted(self.error_lines_data, key=lambda x: x['line'])
            
            for item in sorted_data:
                if item['type'] == 'failed' or (include_skipped and item['type'] == 'skipped'):
                    export_lines.append(item['raw'])
        
        elif format_type == 'FAILED_ONLY':
            # 只导出失败的行
            sorted_data = sorted(self.error_lines_data, key=lambda x: x['line'])
            
            for item in sorted_data:
                if item['type'] == 'failed':
                    export_lines.append(item['raw'])
        
        return "\n".join(export_lines)
    
    def register_update_callback(self, callback):
        """注册更新回调"""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
    
    def unregister_update_callback(self, callback):
        """注销更新回调"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def _notify_update(self):
        """通知所有回调更新"""
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"回调通知错误: {e}")

# 创建全局状态管理器
import_state = PNPImportState()

# ============================================================================
# UI更新辅助函数
# ============================================================================
def update_ui_display():
    """更新UI显示"""
    # 标记所有3D视图区域需要重绘
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()
    
    # 尝试请求一次重绘
    try:
        bpy.ops.wm.redraw_timer(type='DRAW', iterations=1)
    except:
        pass

# 注册更新回调
import_state.register_update_callback(update_ui_display)

# ============================================================================
# 模态导入操作符
# ============================================================================
class IMPORT_OT_pnp_live_import(Operator):
    """实时PNP导入 - 在面板显示实时进度"""
    bl_idname = "fritzing.pnp_live_import"
    bl_label = "PNP实时导入"
    bl_description = "导入PNP文件并在面板实时显示进度"
    bl_options = {'REGISTER', 'UNDO'}
    
    # 文件路径
    filepath: StringProperty(
        name="PNP文件",
        subtype='FILE_PATH',
        default=""
    ) # type: ignore
    
    # 导入设置
    batch_size: IntProperty(
        name="每批数量",
        default=1,
        min=1,
        max=10
    ) # type: ignore
    
    delay_time: FloatProperty(
        name="延迟时间",
        default=0.05,
        min=0.01,
        max=1.0
    ) # type: ignore
    
    # 线程和模态变量
    _import_thread = None
    _timer = None
    _stop_event = threading.Event()
    
    def invoke(self, context, event):
        """调用对话框"""
        if not self.filepath or not os.path.exists(self.filepath):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        
        return self.execute(context)
    
    def execute(self, context):
        """开始导入"""
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({'ERROR'}, "请选择有效的PNP文件")
            return {'CANCELLED'}
        
        # 检查是否已经在导入
        if import_state.is_importing:
            self.report({'WARNING'}, "已有导入任务在进行中")
            return {'CANCELLED'}
        
        # 读取文件
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                lines = [line.strip() for line in f.readlines()]
        except Exception as e:
            self.report({'ERROR'}, f"读取文件失败: {e}")
            return {'CANCELLED'}
        
        if not lines:
            self.report({'WARNING'}, "PNP文件为空")
            return {'CANCELLED'}
        
        # 重置停止事件
        self._stop_event.clear()
        
        # 启动导入线程
        self._import_thread = threading.Thread(
            target=self._import_thread_func,
            args=(context, self.filepath, lines),
            daemon=True
        )
        self._import_thread.start()
        
        # 启动模态定时器用于监控线程
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.1, window=context.window)
        wm.modal_handler_add(self)
        
        print(f"🚀 开始导入 {len(lines)} 行数据")
        return {'RUNNING_MODAL'}
    
    def modal(self, context, event):
        """模态处理 - 监控导入线程"""
        if event.type == 'TIMER':
            # 检查导入线程是否还在运行
            if self._import_thread and self._import_thread.is_alive():
                # 更新UI显示
                update_ui_display()
                return {'RUNNING_MODAL'}
            else:
                # 导入完成
                self._finish_import(context)
                return {'FINISHED'}
        
        elif event.type in {'ESC'}:
            # 用户取消
            self._cancel_import()
            return {'CANCELLED'}
        
        elif event.type == 'P' and event.value == 'PRESS':
            # 暂停/继续快捷键
            if import_state.is_importing:
                if import_state.is_paused:
                    import_state.resume()
                else:
                    import_state.pause()
        
        return {'PASS_THROUGH'}
    
    def _import_thread_func(self, context, filepath, lines):
        """导入线程函数"""
        try:
            # 获取原点
            scene = context.scene
            origin = (
                getattr(scene, 'pnp_origin_x', 0.0),
                getattr(scene, 'pnp_origin_y', 0.0),
                getattr(scene, 'pnp_origin_z', 0.0)
            )
            
            # 开始导入
            import_state.start_import(filepath, len(lines))
            
            # 保存原始行
            import_state.original_lines = lines
            
            # 处理每一行
            for i, line in enumerate(lines):
                # 检查是否应该停止
                if self._stop_event.is_set() or import_state.should_cancel:
                    break
                
                # 检查是否暂停
                while import_state.is_paused and not self._stop_event.is_set():
                    time.sleep(0.1)
                
                line_num = i + 1
                raw_line = line
                
                # 更新进度
                import_state.update_progress(line_num, action="解析行数据")
                
                # 处理单行
                result, designator = self._process_line(line, line_num, origin, context)
                
                # 记录结果
                if result == 'success':
                    import_state.add_success(line_num, designator, f"行{line_num}导入成功", raw_line)
                elif result == 'failed':
                    import_state.add_failed(line_num, designator, f"行{line_num}导入失败", raw_line)
                elif result == 'skipped':
                    import_state.add_skipped(line_num, f"行{line_num}被跳过", raw_line)
                
                # 延迟
                time.sleep(self.delay_time)
            
            # 完成导入
            if not self._stop_event.is_set():
                import_state.complete()
            
        except Exception as e:
            print(f"导入线程错误: {e}")
            import_state.add_failed(0, "", f"导入过程错误: {str(e)}", "")
    
    def _process_line(self, line, line_num, origin, context):
        """处理单行数据"""
        # 跳过空行
        if not line.strip():
            return 'skipped', ""
        
        # 跳过注释行
        if line.strip().startswith('#'):
            return 'skipped', "注释行"

        # 跳过过孔(Via)
        if line.strip().startswith('Via'):
            return 'skipped', "过孔"
        
        # 跳过焊盘(Pad)
        if line.strip().startswith('Pad') or re.match(r'^P[0-9]', line.strip()):
            return 'skipped', "焊盘"
        
        # 跳过Description数据格式说明行
        if line.strip().startswith('Description:'):
            return 'skipped', "描述行"
        
        # 跳过数据格式说明行
        if line.strip().startswith('RefDes,Description,Package,X,Y,Rotation,Side,Mount'):
            return 'skipped', "格式说明行"

        clean_line = line.replace('"', '')
        for s in ['[SMD, multilayer]', '[SMD]', 'SandFlower', 'sandflower', '[SMD, electrolytic]']:
            clean_line = clean_line.replace(s, '')
        parts = clean_line.strip().split(',')

        # 格式错误
        if len(parts) != 8:
            return 'failed', "格式错误，不是8列"
        
        designator = parts[0]
        description = parts[1]
        package = parts[2]
        center_x = parts[3]
        center_y = parts[4]
        # mil to mm
        center_x = round(float(center_x) * 25.4 / 1000, 4)
        center_y = round(float(center_y) * 25.4 / 1000, 4)

        rotation = parts[5]
        layer = parts[6]
        mount = parts[7]
        
        try:
            # 设置当前正在处理的元件
            import_state.current_component = designator
            import_state.current_action = f"导入行 {line_num}"
            
            # 在主线程中创建元件
            bpy.app.timers.register(
                lambda: self._create_component_in_main_thread(
                    context, line_num, line, designator, description, package, center_x, center_y, rotation, layer, mount
                ),
                first_interval=0.0
            )
            
            return 'success', designator
            
        except ValueError as e:
            return 'failed', f"数值转换错误: {e}"
        except Exception as e:
            return 'failed', f"解析错误: {e}"
    
    def _create_component_in_main_thread(self, context, line_number, line, designator, description, package, center_x, center_y, rotation, layer, mount):
        component = None
        # 处理每一行数据的逻辑
        # 这里可以添加将数据添加到Blender场景中的代码
        print(f" ** Processing line: {designator},{description},{package},{center_x},{center_y},{rotation},{layer},{mount}")
        # 分号分割description
        description_parts = description.split(';')
        if description_parts[0].strip() != '':
            # 如果description第一个分号前有内容，作为电阻导入
            print(f" ** Resistor: {description_parts[0].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
            resistance, unit, resistance_str = parse_resistance_string(description_parts[0].strip())
            print(f"   -> 电阻阻值：{resistance}")
            if resistance is None:
                resistance = 0
            if SMD_SIZES[package.strip()] is not None:
                collection = generate_smd_resistor(resistance=resistance, tolerance=description_parts[6].strip(), package_size=package.strip())
                component = collection.objects[0]
                bpy.ops.object.select_all(action='DESELECT')
                for obj in collection.objects:
                    obj.select_set(True)
                bpy.context.view_layer.objects.active = component
                bpy.ops.object.join()
        elif description_parts[1].strip() != '':
            # 如果description第二个分号前有内容，作为电容导入
            print(f" ** Capacitor: {description_parts[1].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
            if package.strip() == '0605':
                component = create_smd_ecap_model(package.strip())
            elif package.strip() == '0603' or package.strip() == '0805':
                component = create_smd_capacitor_model(package.strip())
            else:
                print(f" !!!! Unknown !!!!")
                import_state.add_failed(line_number, line, "Unknown")
                return None
        elif description_parts[2].strip() != '':
            # 如果description第三个分号前有内容，作为电感导入
            print(f" ** Inductor: {description_parts[2].strip()},{package},{center_x},{center_y},{rotation},{layer},{mount}")
            component = create_smd_inductor_model(size_name=package.strip())
            print(f" **** SMD Inductor {package.strip()} ****")
        else:
            # 依据package类型进行导入
            component = None
            mpn = description_parts[6].strip()
            package = package.strip()
            if package.capitalize().startswith('Pb86-a0'):
                component = create_pb86_button(color=description)
            elif package.capitalize().startswith('Usb-typec'):
                print(f" **** USB-TYPE-C ****")
                if mpn.find('蓝') != -1:
                    plastic_color = 'blue'
                elif mpn.find('绿') != -1:
                    plastic_color = 'green'
                elif mpn.find('橙') != -1 or mpn.find('橘') != -1:
                    plastic_color = 'orange'
                elif mpn.find('白') != -1:
                    plastic_color = 'white'
                else:
                    plastic_color = 'black'
                component = create_usb_type_c_16pin_model(plastic_color=plastic_color)
            elif package.capitalize().startswith('Yc164'):
                resistance, unit, resistance_str = parse_resistance_string(description)
                if resistance is None:
                    resistance = 0
                component = generate_yc164_resistor(resistance)
            elif package.capitalize().startswith('Sot23-3'):
                print(f" **** SOT23-3 ****")
                component = create_sot23_3_model(text=mpn)
            elif package.capitalize().startswith('Sot23-6'):
                print(f" **** SOT23-6 ****")
                component = create_sot23_6_model(text=mpn)
            elif package.capitalize().startswith('Sop20'):
                print(f" **** SOP20 ****")
                component = create_sop20_model(description_parts[6])
            elif package.capitalize().startswith('Sod323'):
                print(f" **** SOD323 ****")
                component = create_sod323_model()
            elif package.capitalize().startswith('Sod123fl'):
                print(f" **** SOD123FL ****")
                component = create_sod123_model()
            elif package.capitalize().startswith('Esop8'):
                print(f" **** ESOP8 ****")
                component = create_esop8_model(text=mpn)
            elif package.capitalize().startswith('Msop-10'):
                print(f" **** msop-10 ****")
                component = create_msop10_model(text=mpn)
            elif package.capitalize().startswith('Wdfn3x3-10'):
                print(f" **** WDFN3X3-10 ****")
                component = create_wdfn_3x3_10_model(text=mpn)
            elif package.capitalize().startswith('Ts-d014'):
                component = create_ts_d014_switch()
            elif package.capitalize().startswith('Vqfn-hr-12'):
                print(f" **** VQFN-HR-12 ****")
                component = create_vqfn_hr_12(description_parts[6])
            elif package.lower().find('mx1.25') > 0:
                print(f" **** MX1.25 ****")
                component = create_mx125_2p()
            elif package == '0603':
                if mpn != '':
                    print(f" **** 0603 mpn: {mpn}")
                    if mpn.capitalize().startswith('0.5a '):
                        component = create_smd0603_fuse_model(text='5')
                        print(f" **** PPTC 0603 ****")
                    elif mpn.capitalize().find('Led') != -1 or mpn.capitalize().find('led') != -1:
                        component = create_led0603_with_color(color_name=mpn)
                        print(f" **** LED 0603 ****")
                    elif mpn.find('μH') != -1:
                        component = create_smd_inductor_model(size_name='0603')
                        print(f" **** SMD Inductor 0603 ****")
                    else:
                        print(f" !!!! Unknown !!!!")
                        import_state.add_failed(line_number, line, "Unknown")
                    return None
                else:
                    print(f" !!!! Unknown !!!!")
                    import_state.add_failed(line_number, line, "Unknown")
                    return None
            else:
                if mpn != '':
                    if mpn.capitalize().startswith('Esp-12'):
                        component = create_esp12f_model()
                        component.rotation_euler.z += math.pi / 2
                    elif mpn.startswith('9*4无源蜂鸣器'):
                        component = create_buzzer_9042_model()
                    else:
                        print(f" !!!! Unknown !!!!")
                        import_state.add_failed(line_number, line, "Unknown")
                        return None
                else:
                    print(f" !!!! Unknown !!!!")
                    import_state.add_failed(line_number, line, "Unknown")
                    return None

        # 调整元件位置
        if component is not None:
            if isinstance(component, object):
                self.post_parse(context, component=component, center_x=center_x, center_y=center_y, rotation=rotation, layer=layer)
            elif isinstance(component, Collection):
                for obj in component.objects:
                    self.post_parse(context, component=obj, center_x=center_x, center_y=center_y, rotation=rotation, layer=layer)

        return None
    
    def post_parse(self, context, component, center_x, center_y, rotation, layer):
        # 先旋转
        if float(rotation) != 0.0:
            print(f"   -> 旋转：{rotation}")
            component.rotation_euler.z += -float(rotation) * math.pi / 180
        if layer == 'Bottom':
            component.rotation_euler.y -= math.pi
        else:
            component.location.z += float(context.scene.pnp_pcb_thickness)
        # 再移动
        if center_x != 0.0:
            component.location.x += center_x
        if center_y != 0.0:
            component.location.y += center_y


    def _apply_component_color(self, obj, line_num):
        """为元件应用颜色"""
        mat_name = f"PNP_Mat_{line_num % 10}"
        
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.use_nodes = True
            
            # 简化材质节点
            nodes = mat.node_tree.nodes
            nodes.clear()
            
            bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
            output = nodes.new(type='ShaderNodeOutputMaterial')
            
            # 设置随机颜色
            import random
            hue = (line_num * 0.6180339887) % 1.0  # 黄金比例分布
            bsdf.inputs[0].default_value = (hue, 0.8, 0.6, 1.0)
            bsdf.inputs[7].default_value = 0.2  # 粗糙度
            
            # 连接节点
            links = mat.node_tree.links
            links.new(bsdf.outputs[0], output.inputs[0])
        
        # 应用材质
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    
    def _cancel_import(self):
        """取消导入"""
        self._stop_event.set()
        if self._import_thread and self._import_thread.is_alive():
            self._import_thread.join(timeout=2.0)
        
        import_state.cancel()
        print("❌ 导入已取消")
    
    def _finish_import(self, context):
        """完成导入"""
        # 移除定时器
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        
        # 保存结果到场景
        scene = context.scene
        scene['pnp_import_results'] = import_state.final_results
        
        # 记录导入时间
        scene.pnp_last_import_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        print(f"✅ 导入完成")
        
        # 如果导入失败，自动弹出结果对话框
        if import_state.has_errors:
            bpy.ops.fritzing.show_pnp_results_complete('INVOKE_DEFAULT')

# ============================================================================
# 控制操作符
# ============================================================================
class IMPORT_OT_pnp_pause_import(Operator):
    """暂停导入"""
    bl_idname = "fritzing.pnp_pause_import"
    bl_label = "暂停导入"
    
    def execute(self, context):
        import_state.pause()
        self.report({'INFO'}, "导入已暂停")
        return {'FINISHED'}

class IMPORT_OT_pnp_resume_import(Operator):
    """恢复导入"""
    bl_idname = "fritzing.pnp_resume_import"
    bl_label = "恢复导入"
    
    def execute(self, context):
        import_state.resume()
        self.report({'INFO'}, "导入已恢复")
        return {'FINISHED'}

class IMPORT_OT_pnp_cancel_import(Operator):
    """取消导入"""
    bl_idname = "fritzing.pnp_cancel_import"
    bl_label = "取消导入"
    
    def execute(self, context):
        import_state.cancel()
        self.report({'INFO'}, "导入已取消")
        return {'FINISHED'}

# ============================================================================
# 错误数据导出操作符
# ============================================================================
class IMPORT_OT_export_error_data(Operator):
    """导出错误数据为文本文件"""
    bl_idname = "fritzing.export_error_data"
    bl_label = "导出错误数据"
    bl_description = "将导入失败和跳过的行导出为文本文件，方便修改后重新导入"
    
    filepath: StringProperty(
        name="保存路径",
        description="选择保存错误数据的文件",
        subtype='FILE_PATH',
        default="pnp_errors.txt"
    ) # type: ignore
    
    export_format: EnumProperty(
        name="导出格式",
        description="选择导出数据的格式",
        items=[
            ('WITH_COMMENTS', "带注释", "在每行前添加错误原因注释"),
            ('RAW_ONLY', "仅原始行", "只导出原始行数据，适合直接修改后导入"),
            ('FAILED_ONLY', "仅失败行", "只导出导入失败的行，跳过注释行"),
        ],
        default='WITH_COMMENTS'
    ) # type: ignore
    
    include_skipped: BoolProperty(
        name="包含跳过的行",
        description="是否包含跳过的行（空行、注释行等）",
        default=True
    ) # type: ignore
    
    def invoke(self, context, event):
        # 设置默认文件名
        if not self.filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.filepath = f"pnp_errors_{timestamp}.txt"
        
        # 弹出文件选择对话框
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        # 获取错误数据
        error_data = import_state.get_error_data_for_export(
            format_type=self.export_format,
            include_skipped=self.include_skipped
        )
        
        if not error_data.strip():
            self.report({'WARNING'}, "没有错误数据可导出")
            return {'CANCELLED'}
        
        try:
            # 写入文件
            with open(self.filepath, 'w', encoding='utf-8') as f:
                f.write(error_data)
            
            # 显示成功信息
            lines = error_data.strip().split('\n')
            data_lines = [l for l in lines if l and not l.startswith('#')]
            comment_lines = [l for l in lines if l.startswith('#')]
            
            message = f"已导出 {len(data_lines)} 行错误数据"
            if comment_lines:
                message += f"（包含 {len(comment_lines)} 条注释）"
            
            self.report({'INFO'}, message)
            
            # 在控制台显示保存路径
            print(f"✅ 错误数据已导出到: {os.path.abspath(self.filepath)}")
            
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"导出失败: {str(e)}")
            return {'CANCELLED'}
    
    def draw(self, context):
        layout = self.layout
        
        # 文件路径
        col = layout.column(align=True)
        col.label(text="保存为:", icon='FILE')
        col.prop(self, "filepath", text="")
        
        # 导出选项
        box = layout.box()
        box.label(text="导出选项", icon='SETTINGS')
        
        box.prop(self, "export_format", text="格式")
        
        if self.export_format == 'WITH_COMMENTS':
            box.prop(self, "include_skipped", text="包含跳过的行")
        
        # 预览
        preview = import_state.get_error_data_for_export(
            format_type=self.export_format,
            include_skipped=self.include_skipped
        )
        
        if preview:
            box = layout.box()
            box.label(text="预览（前10行）:", icon='VIEWZOOM')
            
            preview_box = box.box()
            lines = preview.split('\n')[:10]
            for line in lines:
                if line.strip():
                    preview_box.label(text=line)
            
            if len(preview.split('\n')) > 10:
                preview_box.label(text="...")

# ============================================================================
# 快速重新导入操作符
# ============================================================================
class IMPORT_OT_import_error_data(Operator):
    """快速重新导入错误数据"""
    bl_idname = "fritzing.import_error_data"
    bl_label = "重新导入错误数据"
    bl_description = "创建临时错误文件并重新导入"
    
    def execute(self, context):
        # 检查是否有错误数据
        if not import_state.error_lines_data:
            self.report({'WARNING'}, "没有可用的错误数据")
            return {'CANCELLED'}
        
        try:
            # 创建临时错误文件
            temp_dir = bpy.app.tempdir
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = os.path.join(temp_dir, f"pnp_errors_{timestamp}.txt")
            
            # 获取错误数据
            error_data = import_state.get_error_data_for_export(
                format_type='FAILED_ONLY',
                include_skipped=False
            )
            
            if not error_data.strip():
                self.report({'WARNING'}, "无法提取原始行数据")
                return {'CANCELLED'}
            
            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(error_data)
            
            # 设置场景文件路径
            context.scene.pnp_file_path = temp_file
            
            # 开始导入
            bpy.ops.fritzing.pnp_live_import('INVOKE_DEFAULT')
            
            # 统计失败行数
            failed_lines = error_data.strip().split('\n')
            failed_count = len([l for l in failed_lines if l.strip()])
            
            self.report({'INFO'}, f"正在重新导入 {failed_count} 个失败元件")
            return {'FINISHED'}
            
        except Exception as e:
            self.report({'ERROR'}, f"重新导入失败: {str(e)}")
            return {'CANCELLED'}

# ============================================================================
# 清除操作符
# ============================================================================
class IMPORT_OT_clear_import_results(Operator):
    """清除导入结果"""
    bl_idname = "fritzing.clear_import_results"
    bl_label = "清除结果"
    
    def execute(self, context):
        scene = context.scene
        
        # 重置状态管理器
        import_state.reset()
        
        # 清除场景属性
        scene.pnp_import_status = 'IDLE'
        scene.pnp_import_progress = 0.0
        scene.pnp_current_line = 0
        scene.pnp_total_lines = 0
        scene.pnp_success_count = 0
        scene.pnp_failed_count = 0
        scene.pnp_skipped_count = 0
        scene.pnp_current_component = ""
        scene.pnp_current_action = ""
        
        # 清除结果
        if 'pnp_import_results' in scene:
            del scene['pnp_import_results']
        
        self.report({'INFO'}, "已清除导入结果")
        return {'FINISHED'}

class IMPORT_OT_clear_successful_components(Operator):
    """清除成功导入的元件"""
    bl_idname = "fritzing.clear_successful_components"
    bl_label = "清除成功元件"
    
    confirm: BoolProperty(default=False)
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=300)
    
    def draw(self, context):
        layout = self.layout
        
        if not self.confirm:
            layout.label(text="确定要删除所有成功导入的元件吗？", icon='ERROR')
            layout.label(text="此操作不可撤销！")
            layout.prop(self, "confirm", text="我确定要删除")
        else:
            layout.label(text="请再次确认：", icon='QUESTION')
            layout.label(text="点击确认将删除所有PNP导入的元件")
    
    def execute(self, context):
        if not self.confirm:
            return {'CANCELLED'}
        
        deleted_count = 0
        
        # 查找并删除所有PNP导入的元件
        for obj in bpy.data.objects:
            if obj.name.startswith("PNP_") or "pnp_line" in obj:
                bpy.data.objects.remove(obj, do_unlink=True)
                deleted_count += 1
        
        self.report({'INFO'}, f"已删除 {deleted_count} 个元件")
        return {'FINISHED'}

# ============================================================================
# 设置面板
# ============================================================================
class VIEW3D_PT_pnp_settings(Panel):
    """PNP导入设置面板"""
    bl_label = "PNP导入设置"
    bl_idname = "VIEW3D_PT_pnp_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PNP工具"
    bl_order = 0
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 文件选择
        box = layout.box()
        box.label(text="PNP文件", icon='FILE')
        
        row = box.row(align=True)
        row.prop(scene, "pnp_file_path", text="")
        row.operator("fritzing.browse_pnp_file", 
                    text="", 
                    icon='FILEBROWSER')
        
        # 文件信息
        if scene.pnp_file_path and os.path.exists(scene.pnp_file_path):
            try:
                with open(scene.pnp_file_path, 'r') as f:
                    lines = [line.strip() for line in f if line.strip()]
                box.label(text=f"行数: {len(lines)} 个", icon='LINENUMBERS_ON')
            except:
                pass
        
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
        
        # PCB厚度设置
        layout.separator()
        box = layout.box()
        box.label(text="PCB厚度设置", icon='FILE')
        
        row = box.row(align=True)
        row.prop(scene, "pnp_pcb_thickness", text="厚度")

        # # 原点设置
        # layout.separator()
        # box = layout.box()
        # box.label(text="原点设置", icon='PIVOT_CURSOR')
        
        # col = box.column(align=True)
        # col.prop(scene, "pnp_origin_x", text="X")
        # col.prop(scene, "pnp_origin_y", text="Y")
        # col.prop(scene, "pnp_origin_z", text="Z")
        
        # # 快速设置按钮
        # row = box.row(align=True)
        # row.operator("fritzing.set_origin_to_cursor", 
        #             text="设为光标", 
        #             icon='CURSOR')
        
        # if context.selected_objects:
        #     row.operator("fritzing.set_origin_to_selected", 
        #                 text="设为选中", 
        #                 icon='OBJECT_DATA')
        
        # 导入设置
        layout.separator()
        box = layout.box()
        box.label(text="导入设置", icon='SETTINGS')
        
        box.prop(scene, "pnp_batch_size", text="每批数量")
        box.prop(scene, "pnp_delay_time", text="延迟时间(秒)")
        
        # 导入按钮
        layout.separator()
        col = layout.column(align=True)
        
        if scene.pnp_file_path and os.path.exists(scene.pnp_file_path):
            op = col.operator("fritzing.pnp_live_import", 
                             text="开始实时导入", 
                             icon='PLAY')
            op.filepath = scene.pnp_file_path
            op.batch_size = scene.pnp_batch_size
            op.delay_time = scene.pnp_delay_time
        else:
            col.label(text="请先选择PNP文件", icon='ERROR')

# ============================================================================
# 实时进度面板
# ============================================================================
class VIEW3D_PT_pnp_progress(Panel):
    """PNP导入进度面板"""
    bl_label = "PNP导入状态"
    bl_idname = "VIEW3D_PT_pnp_progress"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PNP工具"
    bl_order = 1
    
    def draw(self, context):
        layout = self.layout
        
        # 获取当前状态
        summary = import_state.get_summary()
        
        if not summary['is_importing'] and not hasattr(context.scene, 'pnp_import_results'):
            # 没有导入活动
            box = layout.box()
            box.label(text="当前没有导入活动", icon='INFO')
            return
        
        # 标题栏
        box = layout.box()
        
        # 状态指示
        row = box.row(align=True)
        if summary['is_importing']:
            if summary['is_paused']:
                row.label(text="", icon='PAUSE')
                row.label(text="状态: 已暂停")
            else:
                row.label(text="", icon='PLAY')
                row.label(text="状态: 导入中...")
        else:
            row.label(text="", icon='CHECKMARK')
            row.label(text="状态: 已完成")
        
        # 进度条
        if summary['is_importing'] and not summary['is_paused']:
            progress = summary['progress']
            row = box.row()
            row.prop(context.scene, "pnp_import_progress", 
                    slider=True, 
                    text=f"{progress:.1f}%")
        
        # 基本信息
        col = box.column(align=True)
        
        # 文件信息
        if import_state.current_file:
            row = col.row(align=True)
            row.label(text="文件:", icon='FILE')
            row.label(text=os.path.basename(import_state.current_file))
        
        # 进度信息
        row = col.row(align=True)
        row.label(text="进度:", icon='LINENUMBERS_ON')
        row.label(text=f"{summary['processed_lines']}/{summary['total_lines']}")
        
        # 统计信息
        row = col.row(align=True)
        row.label(text="成功:", icon='CHECKMARK')
        row.label(text=str(summary['success_count']))
        
        row = col.row(align=True)
        row.label(text="失败:", icon='CANCEL')
        row.label(text=str(summary['failed_count']))
        
        row = col.row(align=True)
        row.label(text="跳过:", icon='BLANK1')
        row.label(text=str(summary['skipped_count']))
        
        # 时间信息
        if summary['elapsed_time'] > 0:
            row = col.row(align=True)
            row.label(text="已用时间:", icon='TIME')
            row.label(text=self._format_time(summary['elapsed_time']))
        
        if summary['eta'] > 0 and summary['is_importing'] and not summary['is_paused']:
            row = col.row(align=True)
            row.label(text="预计剩余:", icon='TIME')
            row.label(text=self._format_time(summary['eta']))
        
        # 当前操作
        if summary['current_action'] or summary['current_component']:
            subbox = box.box()
            subbox.label(text="当前操作:", icon='NONE')
            
            if summary['current_component']:
                row = subbox.row(align=True)
                row.label(text="元件:")
                row.label(text=summary['current_component'])
            
            if summary['current_action']:
                row = subbox.row(align=True)
                row.label(text="操作:")
                row.label(text=summary['current_action'])
            
            if summary['current_line'] > 0:
                row = subbox.row(align=True)
                row.label(text="行号:")
                row.label(text=str(summary['current_line']))
        
        # 控制按钮
        self._draw_control_buttons(layout, summary)
    
    def _draw_control_buttons(self, layout, summary):
        """绘制控制按钮"""
        col = layout.column(align=True)
        
        if summary['is_importing']:
            if summary['is_paused']:
                # 已暂停：显示继续和取消
                row = col.row(align=True)
                row.operator("fritzing.pnp_resume_import", 
                            text="继续", 
                            icon='PLAY')
                row.operator("fritzing.pnp_cancel_import", 
                            text="取消", 
                            icon='CANCEL')
            else:
                # 运行中：显示暂停和取消
                row = col.row(align=True)
                row.operator("fritzing.pnp_pause_import", 
                            text="暂停", 
                            icon='PAUSE')
                row.operator("fritzing.pnp_cancel_import", 
                            text="取消", 
                            icon='CANCEL')
            
            # 提示
            box = col.box()
            box.label(text="提示:", icon='INFO')
            box.label(text="• 按ESC键可随时取消")
            box.label(text="• 按P键可暂停/继续")
        
        elif summary['has_errors']:
            # 有错误：显示错误处理按钮
            box = col.box()
            box.label(text="检测到错误:", icon='ERROR')
            
            row = box.row(align=True)
            row.operator("fritzing.export_error_data", 
                        text="导出错误数据", 
                        icon='EXPORT')
            row.operator("fritzing.import_error_data", 
                        text="重新导入失败项", 
                        icon='FILE_REFRESH')
        
        else:
            # 已完成：显示清除和重新导入
            if hasattr(bpy.context.scene, 'pnp_file_path') and bpy.context.scene.pnp_file_path:
                row = col.row(align=True)
                row.operator("fritzing.clear_import_results", 
                            text="清除结果", 
                            icon='X')
                
                op = row.operator("fritzing.pnp_live_import", 
                                text="重新导入", 
                                icon='FILE_REFRESH')
                op.filepath = bpy.context.scene.pnp_file_path
    
    def _format_time(self, seconds):
        """格式化时间显示"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"

# ============================================================================
# 批量工具面板
# ============================================================================
class VIEW3D_PT_pnp_tools(Panel):
    """PNP批量工具面板"""
    bl_label = "PNP批量工具"
    bl_idname = "VIEW3D_PT_pnp_tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "PNP工具"
    bl_order = 2
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 错误处理工具
        box = layout.box()
        box.label(text="错误处理工具", icon='ERROR')
        
        col = box.column(align=True)
        
        # 导出工具
        row = col.row(align=True)
        row.operator("fritzing.export_error_data", 
                    text="导出错误数据", 
                    icon='EXPORT')
        
        # 重新导入
        if import_state.has_errors:
            row = col.row(align=True)
            row.operator("fritzing.import_error_data", 
                        text="重新导入失败项", 
                        icon='FILE_REFRESH')
        
        # 清除工具
        layout.separator()
        box = layout.box()
        box.label(text="清理工具", icon='BRUSH_DATA')
        
        col = box.column(align=True)
        col.operator("fritzing.clear_import_results", 
                    text="清除导入结果", 
                    icon='X')
        col.operator("fritzing.clear_successful_components", 
                    text="清除成功导入的元件", 
                    icon='TRASH')
        
        # 最后导入信息
        if hasattr(scene, 'pnp_last_import_time'):
            layout.separator()
            box = layout.box()
            box.label(text="最新导入", icon='TIME')
            box.label(text=f"时间: {scene.pnp_last_import_time}")
            
            if 'pnp_import_results' in scene:
                results = scene['pnp_import_results']
                box.label(text=f"文件: {results.get('file_name', '未知')}")
                box.label(text=f"成功: {results.get('success', 0)}")
                box.label(text=f"失败: {results.get('failed', 0)}")

# ============================================================================
# 结果对话框
# ============================================================================
class IMPORT_OT_show_pnp_results_complete(Operator):
    """显示PNP导入结果（完整版）"""
    bl_idname = "fritzing.show_pnp_results_complete"
    bl_label = "PNP导入结果"
    bl_options = {'REGISTER', 'UNDO'}
    
    width: IntProperty(default=600)
    show_tab: EnumProperty(
        name="显示标签",
        items=[
            ('SUMMARY', "摘要", "显示导入摘要"),
            ('SUCCESS', "成功", "显示成功项"),
            ('FAILED', "失败", "显示失败项"),
            ('SKIPPED', "跳过", "显示跳过的行"),
        ],
        default='SUMMARY'
    )
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=self.width)
    
    def execute(self, context):
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 获取结果
        results = scene.get('pnp_import_results', {})
        
        if not results:
            layout.label(text="没有导入结果", icon='INFO')
            return
        
        # 标题
        layout.label(text="PNP导入详细结果", icon='INFO')
        
        # 标签页
        row = layout.row(align=True)
        row.prop(self, "show_tab", expand=True)
        
        # 根据标签显示内容
        if self.show_tab == 'SUMMARY':
            self._draw_summary(layout, results)
        elif self.show_tab == 'SUCCESS':
            self._draw_success(layout, results)
        elif self.show_tab == 'FAILED':
            self._draw_failed(layout, results)
        elif self.show_tab == 'SKIPPED':
            self._draw_skipped(layout, results)
        
        # 错误处理按钮
        if results.get('failed', 0) > 0:
            layout.separator()
            box = layout.box()
            box.label(text="错误处理", icon='ERROR')
            
            col = box.column(align=True)
            row = col.row(align=True)
            row.operator("fritzing.export_error_data", 
                        text="导出错误数据", 
                        icon='EXPORT')
            row.operator("fritzing.import_error_data", 
                        text="重新导入失败项", 
                        icon='FILE_REFRESH')
    
    def _draw_summary(self, layout, results):
        """绘制摘要"""
        box = layout.box()
        
        # 基本信息
        col = box.column(align=True)
        
        if 'file_name' in results:
            row = col.row(align=True)
            row.label(text="文件:")
            row.label(text=results['file_name'])
        
        if 'elapsed_time' in results:
            row = col.row(align=True)
            row.label(text="总用时:")
            row.label(text=f"{results['elapsed_time']:.1f}秒")
        
        # 统计卡片
        box = layout.box()
        box.label(text="导入统计", icon='LINENUMBERS_ON')
        
        col = box.column(align=True)
        
        row = col.row(align=True)
        row.label(text="总计:", icon='FILE')
        row.label(text=str(results.get('total', 0)))
        
        row = col.row(align=True)
        row.label(text="成功:", icon='CHECKMARK')
        row.label(text=str(results.get('success', 0)))
        
        row = col.row(align=True)
        row.label(text="失败:", icon='CANCEL')
        row.label(text=str(results.get('failed', 0)))
        
        row = col.row(align=True)
        row.label(text="跳过:", icon='BLANK1')
        row.label(text=str(results.get('skipped', 0)))
    
    def _draw_success(self, layout, results):
        """绘制成功项"""
        success_items = results.get('success_items', [])
        
        if not success_items:
            layout.label(text="没有成功项", icon='INFO')
            return
        
        layout.label(text=f"成功导入 {len(success_items)} 项:", icon='CHECKMARK')
        
        box = layout.box()
        for i, item in enumerate(success_items[:20]):  # 最多显示20个
            row = box.row(align=True)
            row.label(text="", icon='CHECKMARK')
            row.label(text=f"行{item['line']}: {item.get('component', '未知')}")
            
            if 'message' in item:
                subrow = box.row(align=True)
                subrow.label(text="", icon='BLANK1')
                subrow.label(text=item['message'])
            
            if i < len(success_items[:20]) - 1:
                box.separator(factor=0.5)
        
        if len(success_items) > 20:
            box.label(text=f"... 还有 {len(success_items) - 20} 个成功项")
    
    def _draw_failed(self, layout, results):
        """绘制失败项"""
        failed_items = results.get('failed_items', [])
        
        if not failed_items:
            layout.label(text="没有失败项", icon='INFO')
            return
        
        layout.label(text=f"导入失败 {len(failed_items)} 项:", icon='CANCEL')
        
        box = layout.box()
        for i, item in enumerate(failed_items[:20]):
            row = box.row(align=True)
            row.label(text="", icon='CANCEL')
            row.label(text=f"行{item['line']}: {item.get('component', '未知')}")
            
            if 'message' in item:
                subrow = box.row(align=True)
                subrow.label(text="", icon='BLANK1')
                subrow.label(text=item['message'], icon='ERROR')
            
            if 'raw_line' in item and item['raw_line']:
                subrow = box.row(align=True)
                subrow.label(text="", icon='BLANK1')
                subrow.label(text=f"原始行: {item['raw_line']}")
            
            if i < len(failed_items[:20]) - 1:
                box.separator(factor=0.5)
        
        if len(failed_items) > 20:
            box.label(text=f"... 还有 {len(failed_items) - 20} 个失败项")
    
    def _draw_skipped(self, layout, results):
        """绘制跳过项"""
        skipped_items = results.get('skipped_items', [])
        
        if not skipped_items:
            layout.label(text="没有跳过的行", icon='INFO')
            return
        
        layout.label(text=f"跳过 {len(skipped_items)} 行:", icon='BLANK1')
        
        box = layout.box()
        for i, item in enumerate(skipped_items[:20]):
            row = box.row(align=True)
            row.label(text="", icon='BLANK1')
            row.label(text=f"行{item['line']}")
            
            if 'message' in item:
                subrow = box.row(align=True)
                subrow.label(text="", icon='BLANK1')
                subrow.label(text=item['message'], icon='INFO')
            
            if 'raw_line' in item and item['raw_line']:
                subrow = box.row(align=True)
                subrow.label(text="", icon='BLANK1')
                subrow.label(text=f"原始行: {item['raw_line']}")
            
            if i < len(skipped_items[:20]) - 1:
                box.separator(factor=0.5)
        
        if len(skipped_items) > 20:
            box.label(text=f"... 还有 {len(skipped_items) - 20} 个跳过项")

# ============================================================================
# 辅助操作符
# ============================================================================
class IMPORT_OT_browse_pnp_file(Operator):
    """浏览PNP文件"""
    bl_idname = "fritzing.browse_pnp_file"
    bl_label = "浏览"
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*_pnp.xy", options={'HIDDEN'})
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if self.filepath:
            context.scene.pnp_file_path = self.filepath
        return {'FINISHED'}

class IMPORT_OT_set_origin_to_cursor(Operator):
    """设置原点为光标位置"""
    bl_idname = "fritzing.set_origin_to_cursor"
    bl_label = "设为光标位置"
    
    def execute(self, context):
        scene = context.scene
        cursor = context.scene.cursor.location
        
        scene.pnp_origin_x = cursor.x
        scene.pnp_origin_y = cursor.y
        scene.pnp_origin_z = cursor.z
        
        return {'FINISHED'}

class IMPORT_OT_set_origin_to_selected(Operator):
    """设置原点为选中对象位置"""
    bl_idname = "fritzing.set_origin_to_selected"
    bl_label = "设为选中对象位置"
    
    def execute(self, context):
        if not context.selected_objects:
            return {'CANCELLED'}
        
        scene = context.scene
        obj = context.active_object
        
        if obj:
            scene.pnp_origin_x = obj.location.x
            scene.pnp_origin_y = obj.location.y
            scene.pnp_origin_z = obj.location.z
        
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


# ============================================================================
# 注册
# ============================================================================
classes = [
    # 导入操作符
    IMPORT_OT_pnp_live_import,
    
    # 控制操作符
    IMPORT_OT_pnp_pause_import,
    IMPORT_OT_pnp_resume_import,
    IMPORT_OT_pnp_cancel_import,
    
    # 错误处理操作符
    IMPORT_OT_export_error_data,
    IMPORT_OT_import_error_data,
    
    # 清除操作符
    IMPORT_OT_clear_import_results,
    IMPORT_OT_clear_successful_components,
    
    # 面板
    VIEW3D_PT_pnp_settings,
    VIEW3D_PT_pnp_progress,
    VIEW3D_PT_pnp_tools,
    
    # 结果显示
    IMPORT_OT_show_pnp_results_complete,
    
    # 辅助操作符
    IMPORT_OT_browse_pnp_file,
    IMPORT_OT_set_origin_to_cursor,
    IMPORT_OT_set_origin_to_selected,
    IMPORT_OT_update_from_selected_scene,
    IMPORT_OT_use_world_as_origin,
    IMPORT_OT_use_cursor_as_origin,
    IMPORT_OT_update_from_cursor_scene,
    IMPORT_OT_use_selected_as_origin,
]

def register():
    """注册插件"""
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册场景属性
    Scene.pnp_file_path = StringProperty(
        name="PNP File",
        description="PNP文件路径",
        subtype='FILE_PATH',
        default=""
    )
    
    Scene.pnp_origin_x = FloatProperty(
        name="Origin X",
        description="PNP导入原点的X坐标",
        default=0.0
    )
    
    Scene.pnp_origin_y = FloatProperty(
        name="Origin Y", 
        description="PNP导入原点的Y坐标",
        default=0.0
    )
    
    Scene.pnp_origin_z = FloatProperty(
        name="Origin Z",
        description="PNP导入原点的Z坐标", 
        default=0.0
    )
    
    Scene.pnp_batch_size = IntProperty(
        name="Batch Size",
        description="每批导入的行数",
        default=1,
        min=1,
        max=10
    )
    
    Scene.pnp_delay_time = FloatProperty(
        name="Delay Time",
        description="元件间的延迟时间",
        default=0.05,
        min=0.01,
        max=1.0
    )
    
    Scene.pnp_import_progress = FloatProperty(
        name="Import Progress",
        description="导入进度",
        default=0.0,
        min=0.0,
        max=100.0
    )
    
    Scene.pnp_import_status = EnumProperty(
        name="Import Status",
        items=[
            ('IDLE', "空闲", "未在导入"),
            ('RUNNING', "运行中", "正在导入"),
            ('PAUSED', "已暂停", "导入已暂停"),
            ('COMPLETED', "已完成", "导入完成"),
            ('CANCELLED', "已取消", "导入已取消"),
        ],
        default='IDLE'
    )
    
    Scene.pnp_current_line = IntProperty(
        name="Current Line",
        default=0
    )
    
    Scene.pnp_total_lines = IntProperty(
        name="Total Lines",
        default=0
    )
    
    Scene.pnp_success_count = IntProperty(
        name="Success Count",
        default=0
    )
    
    Scene.pnp_failed_count = IntProperty(
        name="Failed Count",
        default=0
    )
    
    Scene.pnp_skipped_count = IntProperty(
        name="Skipped Count",
        default=0
    )
    
    Scene.pnp_current_component = StringProperty(
        name="Current Component",
        default=""
    )
    
    Scene.pnp_current_action = StringProperty(
        name="Current Action",
        default=""
    )
    
    Scene.pnp_last_import_time = StringProperty(
        name="Last Import Time",
        default=""
    )
    
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
    
    pcb_thickness_items = []
    pcb_thickness_items.append(('1.6', '1.6mm', '', 0))
    pcb_thickness_items.append(('1.4', '1.4mm', '', 1))
    pcb_thickness_items.append(('1.2', '1.2mm', '', 2))
    pcb_thickness_items.append(('1.0', '1.0mm', '', 3))
    setattr(Scene, 'pnp_pcb_thickness', EnumProperty(items=pcb_thickness_items))
    
    print("✅ PNP完整导入插件已注册")

def unregister():
    """注销插件"""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # 注销更新回调
    import_state.unregister_update_callback(update_ui_display)
    
    print("✅ PNP完整导入插件已注销")

# 运行注册
if __name__ == "__main__":
    register()
