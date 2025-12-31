"""
gerber_importer_complete.py
完整的Gerber文件导入插件
基于python-gerber库直接解析Gerber文件
"""

import bpy
import os
import time
import math
import threading
import traceback
from bpy.types import Operator, Panel, PropertyGroup, Scene
from bpy.props import (
    StringProperty, IntProperty, FloatProperty, 
    BoolProperty, EnumProperty, PointerProperty
)
from mathutils import Vector, Matrix
import numpy as np

# ============================================================================
# 依赖检查
# ============================================================================
def check_dependencies():
    """检查所需的Python库"""
    try:
        from pcb_tools import read
        from pcb_tools.render import RenderSettings, theme
        from pcb_tools.primitives import Circle, Rectangle, Obround, AMGroup
        from pcb_tools.utils import inch, metric
        print("✅ python-gerber库导入成功 (从已安装的包)")
        return True
    except ImportError as e:
        print(f"❌ python-gerber库导入失败: {e}")
# 检查依赖
GERBER_LIB_AVAILABLE = check_dependencies()

# ============================================================================
# Gerber解析器
# ============================================================================
class GerberParser:
    """Gerber文件解析器"""
    
    def __init__(self):
        self.scale_factor = 0.001  # 毫米到米
        self.max_primitives = 10000  # 最大图元数
        self.current_progress = 0
        self.total_primitives = 0
        self.is_cancelled = False
    
    def parse_file(self, filepath, progress_callback=None):
        """解析Gerber文件"""
        if not GERBER_LIB_AVAILABLE:
            return {
                'success': False, 
                'error': '缺少python-gerber库，请先安装',
                'install_hint': '在Blender的Python中运行: python -m pip install pcb-tools'
            }
        
        try:
            print(f"📁 开始解析Gerber文件: {os.path.basename(filepath)}")
            start_time = time.time()
            
            # 加载Gerber文件
            from pcb_tools import read
            gerber = read(filepath)
            
            # 获取文件信息
            file_info = self._get_file_info(gerber, filepath)
            
            # 提取图元
            primitives = self._extract_primitives(gerber, progress_callback)
            
            if self.is_cancelled:
                return {'success': False, 'error': '用户取消解析'}
            
            processing_time = time.time() - start_time
            
            result = {
                'success': True,
                'file_info': file_info,
                'primitives': primitives,
                'primitive_count': len(primitives),
                'processing_time': processing_time,
                'units': file_info.get('units', 'metric'),
                'bounds': file_info.get('bounds', None)
            }
            
            print(f"✅ 解析完成: {len(primitives)} 个图元, 耗时 {processing_time:.2f} 秒")
            return result
            
        except Exception as e:
            error_msg = f"解析Gerber文件失败: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _get_file_info(self, gerber, filepath):
        """获取文件信息"""
        info = {
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'format': str(gerber.notation) if hasattr(gerber, 'notation') else 'unknown',
            'units': gerber.units if hasattr(gerber, 'units') else 'metric',
            'apertures': len(gerber.apertures) if hasattr(gerber, 'apertures') else 0,
        }
        
        # 获取边界框
        if hasattr(gerber, 'bounds') and gerber.bounds:
            bounds = gerber.bounds
            min_x, min_y = bounds[0]
            max_x, max_y = bounds[1]
            info.update({
                'width_mm': (max_x - min_x),
                'height_mm': (max_y - min_y),
                'width': (max_x - min_x) * self.scale_factor,
                'height': (max_y - min_y) * self.scale_factor,
                'bounds': bounds,
                'center_x': (min_x + max_x) / 2 * self.scale_factor,
                'center_y': (min_y + max_y) / 2 * self.scale_factor,
            })
        
        return info
    
    def _extract_primitives(self, gerber, progress_callback=None):
        """提取图元"""
        primitives = []
        
        try:
            # 方法1: 从primitives属性提取
            if hasattr(gerber, 'primitives') and gerber.primitives:
                self.total_primitives = len(gerber.primitives)
                
                for i, primitive in enumerate(gerber.primitives):
                    if i >= self.max_primitives:
                        print(f"⚠️ 达到最大图元数限制 {self.max_primitives}")
                        break
                    
                    if self.is_cancelled:
                        break
                    
                    primitive_data = self._parse_primitive(primitive, i)
                    if primitive_data:
                        primitives.append(primitive_data)
                    
                    # 更新进度
                    if progress_callback and i % 100 == 0:
                        progress_callback(i, self.total_primitives)
                
                return primitives
            
            # 方法2: 从语句提取
            if hasattr(gerber, 'statements'):
                return self._extract_from_statements(gerber, progress_callback)
            
            return []
            
        except Exception as e:
            print(f"❌ 提取图元失败: {e}")
            traceback.print_exc()
            return []
    
    def _extract_from_statements(self, gerber, progress_callback):
        """从语句提取图元"""
        primitives = []
        
        try:
            from gerber.primitives import Circle, Rectangle, Obround, AMGroup
            from gerber.rs274x import Region
            
            statement_count = len(gerber.statements) if hasattr(gerber, 'statements') else 0
            self.total_primitives = min(statement_count, 10000)
            
            for i, stmt in enumerate(gerber.statements):
                if i >= self.max_primitives:
                    break
                
                if self.is_cancelled:
                    break
                
                # 解析不同类型的语句
                primitive_data = None
                
                if isinstance(stmt, Circle):
                    primitive_data = self._parse_circle(stmt, i)
                elif isinstance(stmt, Rectangle):
                    primitive_data = self._parse_rectangle(stmt, i)
                elif isinstance(stmt, Obround):
                    primitive_data = self._parse_obround(stmt, i)
                elif isinstance(stmt, Region):
                    primitive_data = self._parse_region(stmt, i)
                elif hasattr(stmt, 'x') and hasattr(stmt, 'y'):
                    # 基本位置语句
                    primitive_data = self._parse_basic_statement(stmt, i)
                
                if primitive_data:
                    primitives.append(primitive_data)
                
                # 更新进度
                if progress_callback and i % 100 == 0:
                    progress_callback(i, self.total_primitives)
            
            return primitives
            
        except Exception as e:
            print(f"❌ 从语句提取失败: {e}")
            return []
    
    def _parse_primitive(self, primitive, index):
        """解析单个图元"""
        try:
            from gerber.primitives import Circle, Rectangle, Obround, AMGroup
            
            primitive_type = type(primitive).__name__
            
            if isinstance(primitive, Circle):
                return self._parse_circle(primitive, index)
            elif isinstance(primitive, Rectangle):
                return self._parse_rectangle(primitive, index)
            elif isinstance(primitive, Obround):
                return self._parse_obround(primitive, index)
            elif hasattr(primitive, 'position'):
                return self._parse_basic_primitive(primitive, index)
            else:
                return None
                
        except Exception as e:
            print(f"❌ 解析图元 {index} 失败: {e}")
            return None
    
    def _parse_circle(self, circle, index):
        """解析圆形"""
        try:
            position = getattr(circle, 'position', (0, 0))
            diameter = getattr(circle, 'diameter', 1.0)
            radius = diameter / 2.0
            
            return {
                'id': index,
                'type': 'circle',
                'x': position[0] * self.scale_factor,
                'y': position[1] * self.scale_factor,
                'z': 0.0,
                'radius': radius * self.scale_factor,
                'diameter': diameter * self.scale_factor,
                'rotation': 0.0,
            }
        except Exception as e:
            print(f"❌ 解析圆形失败: {e}")
            return None
    
    def _parse_rectangle(self, rectangle, index):
        """解析矩形"""
        try:
            position = getattr(rectangle, 'position', (0, 0))
            width = getattr(rectangle, 'width', 1.0)
            height = getattr(rectangle, 'height', 1.0)
            
            return {
                'id': index,
                'type': 'rectangle',
                'x': position[0] * self.scale_factor,
                'y': position[1] * self.scale_factor,
                'z': 0.0,
                'width': width * self.scale_factor,
                'height': height * self.scale_factor,
                'rotation': getattr(rectangle, 'rotation', 0.0),
            }
        except Exception as e:
            print(f"❌ 解析矩形失败: {e}")
            return None
    
    def _parse_obround(self, obround, index):
        """解析椭圆形"""
        try:
            position = getattr(obround, 'position', (0, 0))
            width = getattr(obround, 'width', 1.0)
            height = getattr(obround, 'height', 1.0)
            
            return {
                'id': index,
                'type': 'obround',
                'x': position[0] * self.scale_factor,
                'y': position[1] * self.scale_factor,
                'z': 0.0,
                'width': width * self.scale_factor,
                'height': height * self.scale_factor,
                'rotation': getattr(obround, 'rotation', 0.0),
            }
        except Exception as e:
            print(f"❌ 解析椭圆形失败: {e}")
            return None
    
    def _parse_region(self, region, index):
        """解析区域"""
        try:
            # 区域可以包含多个点
            points = getattr(region, 'points', [])
            
            if not points:
                return None
            
            # 计算区域中心
            x_coords = [p[0] for p in points]
            y_coords = [p[1] for p in points]
            center_x = (min(x_coords) + max(x_coords)) / 2
            center_y = (min(y_coords) + max(y_coords)) / 2
            
            return {
                'id': index,
                'type': 'region',
                'x': center_x * self.scale_factor,
                'y': center_y * self.scale_factor,
                'z': 0.0,
                'points': [(p[0] * self.scale_factor, p[1] * self.scale_factor) for p in points],
                'width': (max(x_coords) - min(x_coords)) * self.scale_factor,
                'height': (max(y_coords) - min(y_coords)) * self.scale_factor,
            }
        except Exception as e:
            print(f"❌ 解析区域失败: {e}")
            return None
    
    def _parse_basic_primitive(self, primitive, index):
        """解析基本图元"""
        try:
            position = getattr(primitive, 'position', (0, 0))
            
            return {
                'id': index,
                'type': 'primitive',
                'x': position[0] * self.scale_factor,
                'y': position[1] * self.scale_factor,
                'z': 0.0,
                'size': 0.001,
            }
        except Exception as e:
            print(f"❌ 解析基本图元失败: {e}")
            return None
    
    def _parse_basic_statement(self, stmt, index):
        """解析基本语句"""
        try:
            return {
                'id': index,
                'type': 'statement',
                'x': getattr(stmt, 'x', 0) * self.scale_factor,
                'y': getattr(stmt, 'y', 0) * self.scale_factor,
                'z': 0.0,
                'size': 0.001,
            }
        except Exception as e:
            return None
    
    def cancel(self):
        """取消解析"""
        self.is_cancelled = True

# ============================================================================
# Blender几何生成器
# ============================================================================
class BlenderGeometryGenerator:
    """Blender几何生成器"""
    
    def __init__(self):
        self.collection = None
        self.object_count = 0
        self.max_objects = 5000
        self.is_cancelled = False
    
    def create_geometry(self, primitives, collection_name="GerberImport", progress_callback=None):
        """从图元创建几何体"""
        if not primitives:
            return {'success': False, 'error': '没有图元数据'}
        
        try:
            # 创建集合
            self.collection = self._create_collection(collection_name)
            
            # 创建图元对象
            created_objects = []
            total_primitives = len(primitives)
            
            for i, primitive in enumerate(primitives):
                if self.object_count >= self.max_objects:
                    print(f"⚠️ 达到最大对象限制 {self.max_objects}，停止创建")
                    break
                
                if self.is_cancelled:
                    break
                
                # 创建对象
                obj = self._create_primitive_object(primitive, i)
                if obj:
                    created_objects.append(obj)
                    self.object_count += 1
                
                # 更新进度
                if progress_callback and i % 100 == 0:
                    progress_callback(i, total_primitives)
            
            if self.is_cancelled:
                return {'success': False, 'error': '用户取消创建'}
            
            result = {
                'success': True,
                'object_count': len(created_objects),
                'collection': self.collection.name,
                'message': f"创建了 {len(created_objects)} 个对象"
            }
            
            print(f"✅ 几何创建完成: {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"创建几何体失败: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _create_collection(self, name):
        """创建集合"""
        # 清理现有集合
        if name in bpy.data.collections:
            old_collection = bpy.data.collections[name]
            for obj in old_collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            bpy.data.collections.remove(old_collection)
        
        # 创建新集合
        collection = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(collection)
        return collection
    
    def _create_primitive_object(self, primitive, index):
        """创建图元对象"""
        primitive_type = primitive.get('type', 'primitive')
        
        try:
            if primitive_type == 'circle':
                return self._create_circle(primitive, index)
            elif primitive_type == 'rectangle':
                return self._create_rectangle(primitive, index)
            elif primitive_type == 'obround':
                return self._create_obround(primitive, index)
            elif primitive_type == 'region':
                return self._create_region(primitive, index)
            else:
                return self._create_default_primitive(primitive, index)
                
        except Exception as e:
            print(f"❌ 创建图元 {index} 失败: {e}")
            return None
    
    def _create_circle(self, primitive, index):
        """创建圆形"""
        x = primitive.get('x', 0)
        y = primitive.get('y', 0)
        radius = primitive.get('radius', 0.001)
        
        # 创建圆形曲线
        bpy.ops.curve.primitive_bezier_circle_add(radius=radius)
        circle_obj = bpy.context.active_object
        circle_obj.name = f"Gerber_Circle_{index:05d}"
        circle_obj.location = (x, y, 0)
        
        # 设置颜色
        self._set_object_color(circle_obj, 'circle')
        
        # 添加到集合
        self.collection.objects.link(circle_obj)
        bpy.context.scene.collection.objects.unlink(circle_obj)
        
        return circle_obj
    
    def _create_rectangle(self, primitive, index):
        """创建矩形"""
        x = primitive.get('x', 0)
        y = primitive.get('y', 0)
        width = primitive.get('width', 0.001)
        height = primitive.get('height', 0.001)
        rotation = primitive.get('rotation', 0)
        
        # 创建平面
        bpy.ops.mesh.primitive_plane_add(size=1.0)
        plane_obj = bpy.context.active_object
        plane_obj.name = f"Gerber_Rect_{index:05d}"
        plane_obj.location = (x, y, 0)
        plane_obj.rotation_euler.z = math.radians(rotation)
        
        # 缩放
        plane_obj.scale = (width, height, 1)
        
        # 设置颜色
        self._set_object_color(plane_obj, 'rectangle')
        
        # 添加到集合
        self.collection.objects.link(plane_obj)
        bpy.context.scene.collection.objects.unlink(plane_obj)
        
        return plane_obj
    
    def _create_obround(self, primitive, index):
        """创建椭圆形"""
        x = primitive.get('x', 0)
        y = primitive.get('y', 0)
        width = primitive.get('width', 0.001)
        height = primitive.get('height', 0.001)
        rotation = primitive.get('rotation', 0)
        
        # 创建圆形（简化为圆形）
        radius = min(width, height) / 2
        bpy.ops.curve.primitive_bezier_circle_add(radius=radius)
        circle_obj = bpy.context.active_object
        circle_obj.name = f"Gerber_Obround_{index:05d}"
        circle_obj.location = (x, y, 0)
        circle_obj.rotation_euler.z = math.radians(rotation)
        
        # 非圆形时需要特殊处理，这里简化
        if width != height:
            circle_obj.scale = (width/height, 1, 1)
        
        # 设置颜色
        self._set_object_color(circle_obj, 'obround')
        
        # 添加到集合
        self.collection.objects.link(circle_obj)
        bpy.context.scene.collection.objects.unlink(circle_obj)
        
        return circle_obj
    
    def _create_region(self, primitive, index):
        """创建区域"""
        points = primitive.get('points', [])
        
        if len(points) < 3:
            return None
        
        try:
            # 创建网格
            mesh = bpy.data.meshes.new(f"Gerber_Region_{index:05d}")
            
            # 添加顶点
            vertices = [(p[0], p[1], 0) for p in points]
            
            # 创建面（三角形扇）
            faces = []
            for i in range(1, len(vertices) - 1):
                faces.append([0, i, i + 1])
            
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            
            # 创建对象
            obj = bpy.data.objects.new(f"Gerber_Region_{index:05d}", mesh)
            
            # 设置颜色
            self._set_object_color(obj, 'region')
            
            # 添加到集合
            self.collection.objects.link(obj)
            
            return obj
            
        except Exception as e:
            print(f"❌ 创建区域失败: {e}")
            return None
    
    def _create_default_primitive(self, primitive, index):
        """创建默认图元"""
        x = primitive.get('x', 0)
        y = primitive.get('y', 0)
        size = primitive.get('size', 0.001)
        
        # 创建立方体
        bpy.ops.mesh.primitive_cube_add(size=size)
        cube_obj = bpy.context.active_object
        cube_obj.name = f"Gerber_Prim_{index:05d}"
        cube_obj.location = (x, y, 0)
        
        # 设置颜色
        self._set_object_color(cube_obj, 'primitive')
        
        # 添加到集合
        self.collection.objects.link(cube_obj)
        bpy.context.scene.collection.objects.unlink(cube_obj)
        
        return cube_obj
    
    def _set_object_color(self, obj, primitive_type):
        """设置对象颜色"""
        color_map = {
            'circle': (0.8, 0.2, 0.2, 1.0),    # 红色
            'rectangle': (0.2, 0.8, 0.2, 1.0), # 绿色
            'obround': (0.2, 0.2, 0.8, 1.0),  # 蓝色
            'region': (0.8, 0.5, 0.2, 1.0),   # 橙色
            'primitive': (0.8, 0.8, 0.2, 1.0), # 黄色
        }
        
        color = color_map.get(primitive_type, (0.5, 0.5, 0.5, 1.0))
        
        # 创建材质
        mat_name = f"Gerber_{primitive_type}_Mat"
        if mat_name in bpy.data.materials:
            mat = bpy.data.materials[mat_name]
        else:
            mat = bpy.data.materials.new(name=mat_name)
            mat.diffuse_color = color
        
        # 应用材质
        if obj.data.materials:
            obj.data.materials[0] = mat
        else:
            obj.data.materials.append(mat)
    
    def cancel(self):
        """取消创建"""
        self.is_cancelled = True

# ============================================================================
# 导入状态管理器
# ============================================================================
class GerberImportState:
    """Gerber导入状态管理器"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GerberImportState, cls).__new__(cls)
            cls._instance.reset()
        return cls._instance
    
    def reset(self):
        """重置状态"""
        self.is_importing = False
        self.is_parsing = False
        self.is_creating = False
        self.should_cancel = False
        
        # 进度信息
        self.total_steps = 0
        self.current_step = 0
        self.current_progress = 0.0
        
        # 文件信息
        self.current_file = ""
        self.current_action = ""
        self.parser_result = None
        self.creator_result = None
        
        # 时间信息
        self.start_time = 0
        self.elapsed_time = 0
        
        # 回调函数
        self.update_callbacks = []
    
    def start_import(self, filepath, total_steps=100):
        """开始导入"""
        self.reset()
        self.is_importing = True
        self.current_file = filepath
        self.total_steps = total_steps
        self.start_time = time.time()
        self._notify_update()
    
    def start_parsing(self):
        """开始解析"""
        self.is_parsing = True
        self.current_action = "解析Gerber文件..."
        self._notify_update()
    
    def start_creating(self):
        """开始创建几何体"""
        self.is_creating = True
        self.current_action = "创建几何体..."
        self._notify_update()
    
    def update_progress(self, current, total, action=""):
        """更新进度"""
        self.current_step = current
        self.total_steps = total
        self.current_progress = (current / total) * 100 if total > 0 else 0
        self.elapsed_time = time.time() - self.start_time
        
        if action:
            self.current_action = action
        
        self._notify_update()
    
    def set_parser_result(self, result):
        """设置解析结果"""
        self.parser_result = result
        self.is_parsing = False
    
    def set_creator_result(self, result):
        """设置创建结果"""
        self.creator_result = result
        self.is_creating = False
    
    def complete(self):
        """完成导入"""
        self.is_importing = False
        self.elapsed_time = time.time() - self.start_time
        self._notify_update()
    
    def cancel(self):
        """取消导入"""
        self.should_cancel = True
        self._notify_update()
    
    def get_summary(self):
        """获取状态摘要"""
        return {
            'is_importing': self.is_importing,
            'is_parsing': self.is_parsing,
            'is_creating': self.is_creating,
            'progress': self.current_progress,
            'current_step': self.current_step,
            'total_steps': self.total_steps,
            'elapsed_time': self.elapsed_time,
            'current_action': self.current_action,
            'has_parser_result': self.parser_result is not None,
            'has_creator_result': self.creator_result is not None,
        }
    
    def register_update_callback(self, callback):
        """注册更新回调"""
        if callback not in self.update_callbacks:
            self.update_callbacks.append(callback)
    
    def unregister_update_callback(self, callback):
        """注销更新回调"""
        if callback in self.update_callbacks:
            self.update_callbacks.remove(callback)
    
    def _notify_update(self):
        """通知更新"""
        for callback in self.update_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"回调通知错误: {e}")

# 创建全局状态管理器
import_state = GerberImportState()

# ============================================================================
# UI更新
# ============================================================================
def update_ui_display():
    """更新UI显示"""
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

# 注册更新回调
import_state.register_update_callback(update_ui_display)

# ============================================================================
# 主导入操作符
# ============================================================================
class IMPORT_OT_gerber_complete(Operator):
    """导入Gerber文件（完整版）"""
    bl_idname = "fritzing.import_gerber_complete"
    bl_label = "导入Gerber文件"
    bl_description = "使用python-gerber库解析Gerber文件并创建几何体"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="Gerber文件",
        subtype='FILE_PATH',
        default=""
    )
    
    max_primitives: IntProperty(
        name="最大图元数",
        default=5000,
        min=100,
        max=50000
    )
    
    create_geometry: BoolProperty(
        name="创建几何体",
        description="将Gerber图元转换为Blender几何体",
        default=True
    )
    
    def invoke(self, context, event):
        if not self.filepath or not os.path.exists(self.filepath):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return self.execute(context)
    
    def execute(self, context):
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({'ERROR'}, "请选择有效的Gerber文件")
            return {'CANCELLED'}
        
        # 检查文件扩展名
        valid_extensions = ['.gbr', '.ger', '.gbx', '.gtl', '.gbl', '.gto', '.gts', '.gtp', '.gm1', '.gko']
        file_ext = os.path.splitext(self.filepath)[1].lower()
        
        if file_ext not in valid_extensions:
            self.report({'WARNING'}, f"文件扩展名 {file_ext} 可能不是标准Gerber文件")
        
        # 启动导入线程
        import_thread = threading.Thread(
            target=self._import_thread,
            args=(context, self.filepath),
            daemon=True
        )
        import_thread.start()
        
        # 启动UI监控
        bpy.app.timers.register(
            self._ui_monitor,
            persistent=True
        )
        
        print(f"🚀 开始导入Gerber文件: {os.path.basename(self.filepath)}")
        return {'FINISHED'}
    
    def _import_thread(self, context, filepath):
        """导入线程"""
        try:
            # 开始导入
            import_state.start_import(filepath, 100)
            
            # 创建解析器
            parser = GerberParser()
            parser.max_primitives = self.max_primitives
            
            # 进度回调
            def progress_callback(current, total):
                if import_state.should_cancel:
                    parser.cancel()
                import_state.update_progress(current, total, f"解析图元: {current}/{total}")
            
            # 开始解析
            import_state.start_parsing()
            parser_result = parser.parse_file(filepath, progress_callback)
            import_state.set_parser_result(parser_result)
            
            if import_state.should_cancel:
                import_state.complete()
                return
            
            if not parser_result.get('success', False):
                self._show_error(f"解析失败: {parser_result.get('error', '未知错误')}")
                import_state.complete()
                return
            
            # 检查是否需要创建几何体
            if not self.create_geometry:
                self._show_success(f"解析完成: {parser_result.get('primitive_count', 0)} 个图元")
                import_state.complete()
                return
            
            # 开始创建几何体
            import_state.start_creating()
            primitives = parser_result.get('primitives', [])
            
            # 创建几何生成器
            generator = BlenderGeometryGenerator()
            generator.max_objects = self.max_primitives
            
            # 进度回调
            def create_progress_callback(current, total):
                if import_state.should_cancel:
                    generator.cancel()
                import_state.update_progress(current, total, f"创建几何体: {current}/{total}")
            
            # 生成几何体
            creator_result = generator.create_geometry(
                primitives, 
                f"Gerber_{os.path.basename(filepath)}",
                create_progress_callback
            )
            
            import_state.set_creator_result(creator_result)
            
            if import_state.should_cancel:
                import_state.complete()
                return
            
            if not creator_result.get('success', False):
                self._show_error(f"创建几何体失败: {creator_result.get('error', '未知错误')}")
            else:
                self._show_success(creator_result.get('message', '导入完成'))
            
            import_state.complete()
            
        except Exception as e:
            error_msg = f"导入过程错误: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            self._show_error(error_msg)
            import_state.complete()
    
    def _show_success(self, message):
        """显示成功消息"""
        def show_in_main_thread():
            bpy.ops.fritzing.gerber_import_success('INVOKE_DEFAULT', message=message)
        
        bpy.app.timers.register(
            lambda: show_in_main_thread(),
            first_interval=0.5
        )
    
    def _show_error(self, error_message):
        """显示错误消息"""
        def show_in_main_thread():
            bpy.ops.fritzing.gerber_import_error('INVOKE_DEFAULT', error_message=error_message)
        
        bpy.app.timers.register(
            lambda: show_in_main_thread(),
            first_interval=0.5
        )
    
    def _ui_monitor(self):
        """UI监控"""
        if not import_state.is_importing:
            return None
        
        update_ui_display()
        return 0.1

# ============================================================================
# 控制操作符
# ============================================================================
class IMPORT_OT_gerber_cancel(Operator):
    """取消导入"""
    bl_idname = "fritzing.gerber_cancel"
    bl_label = "取消导入"
    
    def execute(self, context):
        import_state.cancel()
        self.report({'INFO'}, "导入已取消")
        return {'FINISHED'}

# ============================================================================
# 结果对话框
# ============================================================================
class IMPORT_OT_gerber_import_success(Operator):
    """导入成功对话框"""
    bl_idname = "fritzing.gerber_import_success"
    bl_label = "Gerber导入成功"
    bl_options = {'REGISTER', 'UNDO'}
    
    message: StringProperty(default="导入成功")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)
    
    def execute(self, context):
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="✅ Gerber导入成功", icon='INFO')
        layout.separator()
        
        box = layout.box()
        box.label(text=self.message, icon='CHECKMARK')
        
        if import_state.parser_result:
            parser_result = import_state.parser_result
            if parser_result.get('success', False):
                col = box.column(align=True)
                col.label(text=f"文件: {parser_result.get('file_info', {}).get('filename', '')}")
                col.label(text=f"图元数: {parser_result.get('primitive_count', 0)}")
                col.label(text=f"耗时: {parser_result.get('processing_time', 0):.2f}秒")
        
        if import_state.creator_result:
            creator_result = import_state.creator_result
            if creator_result.get('success', False):
                col = box.column(align=True)
                col.label(text=f"创建对象: {creator_result.get('object_count', 0)}")
                col.label(text=f"集合: {creator_result.get('collection', '')}")

class IMPORT_OT_gerber_import_error(Operator):
    """导入错误对话框"""
    bl_idname = "fritzing.gerber_import_error"
    bl_label = "Gerber导入错误"
    bl_options = {'REGISTER', 'UNDO'}
    
    error_message: StringProperty(default="导入错误")
    
    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=500)
    
    def execute(self, context):
        return {'FINISHED'}
    
    def draw(self, context):
        layout = self.layout
        layout.label(text="❌ Gerber导入错误", icon='ERROR')
        layout.separator()
        
        box = layout.box()
        box.label(text=self.error_message, icon='CANCEL')
        
        # 如果是依赖错误，显示安装提示
        if "缺少python-gerber库" in self.error_message:
            layout.separator()
            box = layout.box()
            box.label(text="💡 安装提示:", icon='QUESTION')
            box.label(text="1. 找到Blender的Python路径:")
            box.label(text="   blender --python-expr \"import sys; print(sys.executable)\"")
            box.label(text="2. 使用该Python运行:")
            box.label(text="   python -m pip install pcb-tools")

# ============================================================================
# 设置面板
# ============================================================================
class VIEW3D_PT_gerber_complete_settings(Panel):
    """Gerber导入设置面板（完整版）"""
    bl_label = "Gerber导入设置"
    bl_idname = "VIEW3D_PT_gerber_complete_settings"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Gerber工具"
    bl_order = 0
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 标题
        box = layout.box()
        box.label(text="Gerber文件导入", icon='IMPORT')
        
        # 文件选择
        row = box.row(align=True)
        row.prop(scene, "gerber_file_path", text="")
        row.operator("fritzing.browse_gerber_file_complete", 
                    text="", 
                    icon='FILEBROWSER')
        
        # 文件信息
        if scene.gerber_file_path and os.path.exists(scene.gerber_file_path):
            file_size = os.path.getsize(scene.gerber_file_path)
            box.label(text=f"文件大小: {file_size/1024:.1f} KB", icon='INFO')
        
        # 导入设置
        layout.separator()
        box = layout.box()
        box.label(text="导入设置", icon='SETTINGS')
        
        box.prop(scene, "gerber_max_primitives", text="最大图元数")
        box.prop(scene, "gerber_create_geometry", text="创建几何体")
        
        # 依赖状态
        layout.separator()
        box = layout.box()
        box.label(text="工具状态", icon='INFO')
        
        col = box.column(align=True)
        
        if GERBER_LIB_AVAILABLE:
            col.label(text="✅ python-gerber: 已安装", icon='CHECKMARK')
        else:
            col.label(text="❌ python-gerber: 未安装", icon='ERROR')
            col.label(text="请先安装python-gerber库", icon='ERROR')
        
        # 导入按钮
        layout.separator()
        col = layout.column(align=True)
        
        if not GERBER_LIB_AVAILABLE:
            col.label(text="请先安装python-gerber库", icon='ERROR')
            return
        
        if scene.gerber_file_path and os.path.exists(scene.gerber_file_path):
            op = col.operator("fritzing.import_gerber_complete", 
                             text="导入Gerber文件", 
                             icon='IMPORT')
            op.filepath = scene.gerber_file_path
            op.max_primitives = scene.gerber_max_primitives
            op.create_geometry = scene.gerber_create_geometry
        else:
            col.label(text="请先选择Gerber文件", icon='ERROR')

# ============================================================================
# 进度面板
# ============================================================================
class VIEW3D_PT_gerber_complete_progress(Panel):
    """Gerber导入进度面板（完整版）"""
    bl_label = "Gerber导入状态"
    bl_idname = "VIEW3D_PT_gerber_complete_progress"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Gerber工具"
    bl_order = 1
    
    def draw(self, context):
        layout = self.layout
        
        # 获取状态
        summary = import_state.get_summary()
        
        if not summary['is_importing'] and not import_state.parser_result:
            box = layout.box()
            box.label(text="当前没有导入活动", icon='INFO')
            return
        
        # 标题栏
        box = layout.box()
        
        # 状态指示
        row = box.row(align=True)
        if summary['is_importing']:
            if summary['is_parsing']:
                row.label(text="", icon='TIME')
                row.label(text="状态: 解析中...")
            elif summary['is_creating']:
                row.label(text="", icon='MESH_DATA')
                row.label(text="状态: 创建中...")
            else:
                row.label(text="", icon='PLAY')
                row.label(text="状态: 导入中...")
        else:
            row.label(text="", icon='CHECKMARK')
            row.label(text="状态: 已完成")
        
        # 进度条
        if summary['is_importing']:
            progress = summary['progress']
            row = box.row()
            row.prop(context.scene, "gerber_import_progress", 
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
        row.label(text=f"{summary['current_step']}/{summary['total_steps']}")
        
        # 时间信息
        if summary['elapsed_time'] > 0:
            row = col.row(align=True)
            row.label(text="已用时间:", icon='TIME')
            row.label(text=self._format_time(summary['elapsed_time']))
        
        # 当前操作
        if summary['current_action']:
            subbox = box.box()
            subbox.label(text="当前操作:", icon='NONE')
            subbox.label(text=summary['current_action'])
        
        # 控制按钮
        if summary['is_importing']:
            col = layout.column(align=True)
            col.operator("fritzing.gerber_cancel", 
                        text="取消导入", 
                        icon='CANCEL')
        
        # 结果信息
        if not summary['is_importing'] and import_state.parser_result:
            self._draw_results(layout, context)
    
    def _draw_results(self, layout, context):
        """绘制结果信息"""
        box = layout.box()
        box.label(text="导入结果", icon='INFO')
        
        if import_state.parser_result and import_state.parser_result.get('success', False):
            parser_result = import_state.parser_result
            
            col = box.column(align=True)
            col.label(text=f"图元数: {parser_result.get('primitive_count', 0)}")
            col.label(text=f"单位: {parser_result.get('units', 'metric')}")
            col.label(text=f"解析耗时: {parser_result.get('processing_time', 0):.2f}秒")
            
            if import_state.creator_result and import_state.creator_result.get('success', False):
                creator_result = import_state.creator_result
                col.label(text=f"创建对象: {creator_result.get('object_count', 0)}")
                col.label(text=f"集合: {creator_result.get('collection', '')}")
        
        elif import_state.parser_result and not import_state.parser_result.get('success', False):
            box.label(text=f"❌ 错误: {import_state.parser_result.get('error', '未知错误')}", icon='ERROR')
    
    def _format_time(self, seconds):
        """格式化时间"""
        if seconds < 60:
            return f"{seconds:.1f}秒"
        elif seconds < 3600:
            minutes = seconds / 60
            return f"{minutes:.1f}分钟"
        else:
            hours = seconds / 3600
            return f"{hours:.1f}小时"

# ============================================================================
# 辅助操作符
# ============================================================================
class IMPORT_OT_browse_gerber_file_complete(Operator):
    """浏览Gerber文件"""
    bl_idname = "fritzing.browse_gerber_file_complete"
    bl_label = "浏览"
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.gbr;*.ger;*.gbx;*.gtl;*.gbl;*.gto;*.gts;*.gtp;*.gm1;*.gko", options={'HIDDEN'})
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if self.filepath:
            context.scene.gerber_file_path = self.filepath
        return {'FINISHED'}

# ============================================================================
# 注册
# ============================================================================
def register():
    """注册插件"""
    classes = [
        # 导入操作符
        IMPORT_OT_gerber_complete,
        
        # 控制操作符
        IMPORT_OT_gerber_cancel,
        
        # 结果对话框
        IMPORT_OT_gerber_import_success,
        IMPORT_OT_gerber_import_error,
        
        # 面板
        VIEW3D_PT_gerber_complete_settings,
        VIEW3D_PT_gerber_complete_progress,
        
        # 辅助操作符
        IMPORT_OT_browse_gerber_file_complete,
    ]
    
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # 注册场景属性
    Scene.gerber_file_path = StringProperty(
        name="Gerber File",
        description="Gerber文件路径",
        subtype='FILE_PATH',
        default=""
    )
    
    Scene.gerber_max_primitives = IntProperty(
        name="Gerber Max Primitives",
        description="最大解析图元数",
        default=5000,
        min=100,
        max=50000
    )
    
    Scene.gerber_create_geometry = BoolProperty(
        name="Gerber Create Geometry",
        description="将Gerber图元转换为Blender几何体",
        default=True
    )
    
    Scene.gerber_import_progress = FloatProperty(
        name="Gerber Import Progress",
        description="Gerber导入进度",
        default=0.0,
        min=0.0,
        max=100.0
    )
    
    print("✅ Gerber导入插件（完整版）已注册")

def unregister():
    """注销插件"""
    classes = [
        IMPORT_OT_browse_gerber_file_complete,
        VIEW3D_PT_gerber_complete_progress,
        VIEW3D_PT_gerber_complete_settings,
        IMPORT_OT_gerber_import_error,
        IMPORT_OT_gerber_import_success,
        IMPORT_OT_gerber_cancel,
        IMPORT_OT_gerber_complete,
    ]
    
    for cls in classes:
        bpy.utils.unregister_class(cls)
    
    # 注销更新回调
    import_state.unregister_update_callback(update_ui_display)
    
    print("✅ Gerber导入插件（完整版）已注销")

# 运行注册
if __name__ == "__main__":
    register()