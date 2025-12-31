"""
Gerber图元完整解析器 - 支持所有图元类型
"""

import bpy
import os
import sys
import math
import time
import traceback
from bpy.types import Operator, Panel, Scene
from bpy.props import (
    StringProperty, IntProperty, FloatProperty, 
    BoolProperty, EnumProperty, PointerProperty
)
from mathutils import Vector, Matrix
import numpy as np


# ============================================================================
# 添加pcb_tools到Python路径
# ============================================================================
def setup_pcb_tools_path():
    """设置pcb_tools路径"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    pcb_tools_path = os.path.join(project_root, "pcb_tools")
    
    if os.path.exists(pcb_tools_path) and pcb_tools_path not in sys.path:
        sys.path.insert(0, pcb_tools_path)
        print("✅ 已将pcb_tools添加到Python路径")
        return True
    
    try:
        import pcb_tools
        print("✅ 已从系统路径导入pcb_tools")
        return True
    except ImportError:
        print("❌ 未找到pcb_tools")
        return False

# 设置路径
PCB_TOOLS_AVAILABLE = setup_pcb_tools_path()

if PCB_TOOLS_AVAILABLE:
    try:
        from pcb_tools import read
        print("✅ pcb_tools库导入成功")
        GERBER_LIB_AVAILABLE = True
    except ImportError as e:
        print(f"❌ pcb_tools库导入失败: {e}")
        GERBER_LIB_AVAILABLE = False
else:
    GERBER_LIB_AVAILABLE = False

# ============================================================================
# 增强的Gerber图元解析器
# ============================================================================
class GerberCompleteParser:
    """完整的Gerber图元解析器 - 支持所有图元类型"""
    
    def __init__(self):
        self.primitives = []
        self.file_info = {}
        self.unknown_count = 0
    
    def parse_file(self, filepath, debug=False):
        """解析Gerber文件"""
        if not GERBER_LIB_AVAILABLE:
            return {
                'success': False, 
                'error': '缺少pcb-tools库'
            }
        
        try:
            print(f"🔍 开始解析Gerber文件: {os.path.basename(filepath)}")
            start_time = time.time()
            
            # 读取Gerber文件
            gerber = read(filepath)
            
            # 获取文件信息
            self.file_info = self._get_file_info(gerber, filepath)
            print(f"📄 文件信息: {self.file_info}")
            
            # 提取图元
            self.primitives = self._extract_all_primitives(gerber, debug)
            
            processing_time = time.time() - start_time
            
            # 统计图元类型
            type_stats = self._analyze_primitive_types()
            
            result = {
                'success': True,
                'file_info': self.file_info,
                'primitives': self.primitives,
                'primitive_count': len(self.primitives),
                'type_stats': type_stats,
                'processing_time': processing_time,
                'message': f"成功解析 {len(self.primitives)} 个图元"
            }
            
            print(f"\n📊 解析统计:")
            print(f"  - 总图元数: {len(self.primitives)}")
            for prim_type, count in type_stats.items():
                print(f"  - {prim_type}: {count} 个")
            
            if self.unknown_count > 0:
                print(f"⚠️  有 {self.unknown_count} 个未知图元需要进一步分析")
            
            print(f"⏱️  耗时: {processing_time:.2f} 秒")
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
            'units': gerber.units if hasattr(gerber, 'units') else 'metric',
        }
        
        # 获取边界框
        if hasattr(gerber, 'bounds') and gerber.bounds:
            try:
                bounds = gerber.bounds
                if bounds and len(bounds) >= 2:
                    min_x, min_y = bounds[0]
                    max_x, max_y = bounds[1]
                    
                    info.update({
                        'bounds': bounds,
                        'min_x': min_x,
                        'min_y': min_y,
                        'max_x': max_x,
                        'max_y': max_y,
                        'width': max_x - min_x,
                        'height': max_y - min_y,
                    })
            except Exception as e:
                print(f"⚠️ 获取边界框失败: {e}")
        
        return info
    
    def _extract_all_primitives(self, gerber, debug=False):
        """提取所有图元"""
        primitives = []
        
        try:
            # 方法1: 从primitives属性提取
            if hasattr(gerber, 'primitives') and gerber.primitives:
                print(f"🔍 从primitives属性提取图元: {len(gerber.primitives)} 个")
                
                for i, primitive in enumerate(gerber.primitives):
                    primitive_data = self._parse_primitive_complete(primitive, i, debug)
                    if primitive_data:
                        primitives.append(primitive_data)
                        if primitive_data.get('type') == 'unknown':
                            self.unknown_count += 1
                
                return primitives
            
            print("⚠️ 未找到可提取的图元")
            return []
            
        except Exception as e:
            print(f"❌ 提取图元失败: {e}")
            traceback.print_exc()
            return []
    
    def _parse_primitive_complete(self, primitive, index, debug=False):
        """完整解析单个图元"""
        try:
            class_name = primitive.__class__.__name__
            
            # 调试信息
            # if debug and index < 5:  # 只显示前5个的详细信息
            self._debug_primitive_details(primitive, index)
            
            # 根据类名分派到相应的解析方法
            if class_name == 'Line':
                return self._parse_line_detailed(primitive, index)
            elif class_name == 'Circle':
                return self._parse_circle_detailed(primitive, index)
            elif class_name == 'Rectangle':
                return self._parse_rectangle_detailed(primitive, index)
            elif class_name == 'Obround':
                return self._parse_obround_detailed(primitive, index)
            elif class_name == 'AMGroup':
                return self._parse_amgroup_detailed(primitive, index)
            elif class_name == 'Arc':
                return self._parse_arc_detailed(primitive, index)
            elif class_name == 'Region':
                return self._parse_region_detailed(primitive, index)
            elif class_name == 'Polygon':
                return self._parse_polygon_detailed(primitive, index)
            elif class_name == 'TestRecord':
                return self._parse_test_record(primitive, index)
            elif class_name == 'Flash':
                return self._parse_flash(primitive, index)
            elif class_name == 'StepRepeat':
                return self._parse_step_repeat(primitive, index)
            else:
                # 尝试通用解析方法
                return self._parse_generic_primitive(primitive, index, debug)
                
        except Exception as e:
            print(f"❌ 解析图元 {index} ({primitive.__class__.__name__}) 失败: {e}")
            if debug:
                traceback.print_exc()
            return self._create_fallback_primitive(primitive, index)
    
    def _debug_primitive_details(self, primitive, index):
        """调试打印图元详细信息"""
        print(f"\n🔬 图元 {index} 详细信息:")
        print(f"  类名: {primitive.__class__.__name__}")
        print(f"  模块: {primitive.__class__.__module__}")
        
        # 打印所有公共属性
        for attr in dir(primitive):
            if not attr.startswith('_') and not callable(getattr(primitive, attr)):
                try:
                    value = getattr(primitive, attr)
                    # 避免打印过长的值
                    value_str = str(value)
                    if len(value_str) > 100:
                        value_str = value_str[:100] + "..."
                    print(f"  {attr}: {type(value).__name__} = {value_str}")
                except Exception as e:
                    print(f"  {attr}: 无法访问")
    
    def _parse_region_detailed(self, region, index):
        """详细解析区域"""
        try:
            # 获取区域的所有点
            points = []
            if hasattr(region, 'points'):
                for point in region.points:
                    if hasattr(point, '__len__') and len(point) >= 2:
                        points.append((point[0], point[1]))
            
            # 计算区域中心
            if points:
                x_coords = [p[0] for p in points]
                y_coords = [p[1] for p in points]
                center_x = sum(x_coords) / len(points)
                center_y = sum(y_coords) / len(points)
                width = max(x_coords) - min(x_coords) if x_coords else 0
                height = max(y_coords) - min(y_coords) if y_coords else 0
            else:
                center_x, center_y, width, height = 0, 0, 0, 0
            
            return {
                'id': index,
                'type': 'region',
                'x': center_x,
                'y': center_y,
                'width': width,
                'height': height,
                'points': points,
                'point_count': len(points),
                'is_closed': getattr(region, 'is_closed', False),
                'area': self._calculate_polygon_area(points) if len(points) >= 3 else 0,
            }
        except Exception as e:
            print(f"❌ 解析区域失败: {e}")
            return self._create_fallback_primitive(region, index)
    
    def _parse_polygon_detailed(self, polygon, index):
        """详细解析多边形"""
        try:
            # 获取多边形属性
            position = getattr(polygon, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            # 获取多边形参数
            diameter = getattr(polygon, 'diameter', 0)
            vertices = getattr(polygon, 'vertices', 4)
            rotation = getattr(polygon, 'rotation', 0)
            
            return {
                'id': index,
                'type': 'polygon',
                'x': x,
                'y': y,
                'diameter': diameter,
                'vertices': vertices,
                'rotation': rotation,
                'radius': diameter / 2,
            }
        except Exception as e:
            print(f"❌ 解析多边形失败: {e}")
            return self._create_fallback_primitive(polygon, index)
    
    def _parse_amgroup_detailed(self, amgroup, index):
        """详细解析光圈组"""
        try:
            # 获取位置
            position = getattr(amgroup, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            # 获取光圈信息
            aperture = getattr(amgroup, 'aperture', None)
            aperture_id = getattr(aperture, 'd', 'unknown') if aperture else 'unknown'
            
            return {
                'id': index,
                'type': 'amgroup',
                'x': x,
                'y': y,
                'aperture_id': aperture_id,
                'size': 0.1,
            }
        except Exception as e:
            print(f"❌ 解析光圈组失败: {e}")
            return self._create_fallback_primitive(amgroup, index)
    
    def _parse_arc_detailed(self, arc, index):
        """详细解析圆弧"""
        try:
            # 获取圆弧属性
            position = getattr(arc, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            # 获取圆弧参数
            start_angle = getattr(arc, 'start_angle', 0)
            end_angle = getattr(arc, 'end_angle', 360)
            radius = getattr(arc, 'radius', 1.0)
            
            return {
                'id': index,
                'type': 'arc',
                'x': x,
                'y': y,
                'radius': radius,
                'start_angle': start_angle,
                'end_angle': end_angle,
                'sweep_angle': (end_angle - start_angle) % 360,
            }
        except Exception as e:
            print(f"❌ 解析圆弧失败: {e}")
            return self._create_fallback_primitive(arc, index)
    
    def _parse_test_record(self, test_record, index):
        """解析测试记录"""
        try:
            # 测试记录通常是标记点
            x = getattr(test_record, 'x', 0)
            y = getattr(test_record, 'y', 0)
            
            return {
                'id': index,
                'type': 'test_record',
                'x': x,
                'y': y,
                'size': 0.05,  # 测试点通常较大
            }
        except Exception as e:
            print(f"❌ 解析测试记录失败: {e}")
            return self._create_fallback_primitive(test_record, index)
    
    def _parse_flash(self, flash, index):
        """解析闪光（Flash）操作"""
        try:
            # 闪光操作通常有位置和光圈
            x = getattr(flash, 'x', 0)
            y = getattr(flash, 'y', 0)
            aperture = getattr(flash, 'aperture', None)
            aperture_id = getattr(aperture, 'd', 'unknown') if aperture else 'unknown'
            
            return {
                'id': index,
                'type': 'flash',
                'x': x,
                'y': y,
                'aperture_id': aperture_id,
                'size': 0.1,
            }
        except Exception as e:
            print(f"❌ 解析闪光操作失败: {e}")
            return self._create_fallback_primitive(flash, index)
    
    def _parse_step_repeat(self, step_repeat, index):
        """解析步进重复"""
        try:
            # 步进重复有多个实例
            x = getattr(step_repeat, 'x', 0)
            y = getattr(step_repeat, 'y', 0)
            x_repeat = getattr(step_repeat, 'x_repeat', 1)
            y_repeat = getattr(step_repeat, 'y_repeat', 1)
            x_step = getattr(step_repeat, 'x_step', 0)
            y_step = getattr(step_repeat, 'y_step', 0)
            
            return {
                'id': index,
                'type': 'step_repeat',
                'x': x,
                'y': y,
                'x_repeat': x_repeat,
                'y_repeat': y_repeat,
                'x_step': x_step,
                'y_step': y_step,
                'instance_count': x_repeat * y_repeat,
            }
        except Exception as e:
            print(f"❌ 解析步进重复失败: {e}")
            return self._create_fallback_primitive(step_repeat, index)
    
    def _parse_generic_primitive(self, primitive, index, debug=False):
        """通用解析方法"""
        try:
            # 尝试各种可能的方法获取位置和尺寸
            x, y = 0, 0
            size = 0.1
            
            # 尝试常见的属性名
            for attr_name in ['x', 'y', 'position', 'start', 'end', 'center']:
                if hasattr(primitive, attr_name):
                    value = getattr(primitive, attr_name)
                    if hasattr(value, '__len__') and len(value) >= 2:
                        x, y = value[0], value[1]
                        break
                    elif attr_name in ['x', 'y']:
                        if attr_name == 'x':
                            x = value
                        else:
                            y = value
            
            # 尝试获取尺寸信息
            for size_attr in ['width', 'height', 'diameter', 'radius', 'size']:
                if hasattr(primitive, size_attr):
                    size = getattr(primitive, size_attr)
                    break
            
            # 获取类名
            class_name = primitive.__class__.__name__
            
            return {
                'id': index,
                'type': class_name.lower(),
                'x': x,
                'y': y,
                'size': size,
                'class_name': class_name,
            }
        except Exception as e:
            print(f"❌ 通用解析失败: {e}")
            return self._create_fallback_primitive(primitive, index)
    
    def _create_fallback_primitive(self, primitive, index):
        """创建回退图元"""
        class_name = primitive.__class__.__name__
        
        return {
            'id': index,
            'type': 'unknown',
            'x': 0,
            'y': 0,
            'size': 0.001,
            'class_name': class_name,
        }
    
    def _parse_line_detailed(self, line, index):
        """详细解析线段"""
        try:
            start = getattr(line, 'start', (0, 0))
            end = getattr(line, 'end', (0, 0))
            
            if hasattr(start, '__len__') and len(start) >= 2:
                start_x, start_y = start[0], start[1]
            else:
                start_x, start_y = 0, 0
            
            if hasattr(end, '__len__') and len(end) >= 2:
                end_x, end_y = end[0], end[1]
            else:
                end_x, end_y = 0, 0
            
            return {
                'id': index,
                'type': 'line',
                'start_x': start_x,
                'start_y': start_y,
                'end_x': end_x,
                'end_y': end_y,
                'length': math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2),
                'angle': getattr(line, 'angle', 0),
            }
        except Exception as e:
            print(f"❌ 解析线段失败: {e}")
            return self._create_fallback_primitive(line, index)
    
    def _parse_circle_detailed(self, circle, index):
        """详细解析圆形"""
        try:
            position = getattr(circle, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            diameter = getattr(circle, 'diameter', 1.0)
            radius = diameter / 2.0
            
            return {
                'id': index,
                'type': 'circle',
                'x': x,
                'y': y,
                'radius': radius,
                'diameter': diameter,
            }
        except Exception as e:
            print(f"❌ 解析圆形失败: {e}")
            return self._create_fallback_primitive(circle, index)
    
    def _parse_rectangle_detailed(self, rectangle, index):
        """详细解析矩形"""
        try:
            position = getattr(rectangle, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            width = getattr(rectangle, 'width', 1.0)
            height = getattr(rectangle, 'height', 1.0)
            rotation = getattr(rectangle, 'rotation', 0.0)
            
            return {
                'id': index,
                'type': 'rectangle',
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'rotation': rotation,
            }
        except Exception as e:
            print(f"❌ 解析矩形失败: {e}")
            return self._create_fallback_primitive(rectangle, index)
    
    def _parse_obround_detailed(self, obround, index):
        """详细解析椭圆形"""
        try:
            position = getattr(obround, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            width = getattr(obround, 'width', 1.0)
            height = getattr(obround, 'height', 1.0)
            rotation = getattr(obround, 'rotation', 0.0)
            
            return {
                'id': index,
                'type': 'obround',
                'x': x,
                'y': y,
                'width': width,
                'height': height,
                'rotation': rotation,
            }
        except Exception as e:
            print(f"❌ 解析椭圆形失败: {e}")
            return self._create_fallback_primitive(obround, index)
    
    def _calculate_polygon_area(self, points):
        """计算多边形面积"""
        if len(points) < 3:
            return 0
        
        # 使用鞋带公式计算多边形面积
        area = 0
        for i in range(len(points)):
            j = (i + 1) % len(points)
            area += points[i][0] * points[j][1]
            area -= points[j][0] * points[i][1]
        
        return abs(area) / 2.0
    
    def _analyze_primitive_types(self):
        """分析图元类型统计"""
        type_stats = {}
        for primitive in self.primitives:
            prim_type = primitive.get('type', 'unknown')
            type_stats[prim_type] = type_stats.get(prim_type, 0) + 1
        return type_stats

# ============================================================================
# 增强的几何生成器
# ============================================================================
class EnhancedGeometryGenerator:
    """增强的几何生成器 - 支持所有图元类型"""
    
    def __init__(self):
        self.collection = None
        self.created_objects = []
    
    def create_enhanced_geometry(self, primitives, file_info, debug=False):
        """创建增强的几何体"""
        if not primitives:
            print("⚠️ 没有图元数据，创建边界框")
            return self._create_bounding_box_only(file_info, "Gerber_Empty")
        
        try:
            print(f"🛠️ 开始创建几何体，共 {len(primitives)} 个图元")
            
            # 获取单位转换因子
            units = file_info.get('units', 'metric')
            unit_factor = 0.0254 if units == 'inch' else 0.001
            print(f"📏 单位系统: {units}, 转换因子: {unit_factor}")
            
            # 生成唯一集合名称
            base_name = f"Gerber_{os.path.basename(file_info['filename']).replace('.', '_')}"
            timestamp = int(time.time())
            final_name = f"{base_name}_{timestamp}"
            
            # 创建集合
            self._create_collection_safe(final_name)
            
            # 创建图元
            created_count = 0
            for i, primitive in enumerate(primitives):
                if self._create_primitive_enhanced(primitive, i, unit_factor, debug):
                    created_count += 1
                
                # 显示进度
                if i % 20 == 0 and i > 0:
                    print(f"📊 进度: {i}/{len(primitives)}")
            
            result = {
                'success': True,
                'object_count': created_count,
                'collection': final_name,
                'message': f"创建了 {created_count} 个对象"
            }
            
            print(f"\n✅ 几何创建完成: {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"创建几何体失败: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _create_collection_safe(self, name):
        """安全创建集合"""
        try:
            # 创建新集合
            self.collection = bpy.data.collections.new(name)
            bpy.context.scene.collection.children
            # 继续从上一行开始
            bpy.context.scene.collection.children.link(self.collection)
            print(f"📁 创建集合: {name}")
            
        except Exception as e:
            print(f"创建集合失败: {e}")
    
    def _create_primitive_enhanced(self, primitive, index, unit_factor, debug=False):
        """创建增强的图元"""
        primitive_type = primitive.get('type', 'unknown')
        
        try:
            if primitive_type == 'line':
                return self._create_line_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'circle':
                return self._create_circle_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'rectangle':
                return self._create_rectangle_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'obround':
                return self._create_obround_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'polygon':
                return self._create_polygon_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'region':
                return self._create_region_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'arc':
                return self._create_arc_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'amgroup':
                return self._create_amgroup_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'test_record':
                return self._create_test_record_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'flash':
                return self._create_flash_enhanced(primitive, index, unit_factor)
            elif primitive_type == 'step_repeat':
                return self._create_step_repeat_enhanced(primitive, index, unit_factor)
            else:
                return self._create_point_enhanced(primitive, index, unit_factor, debug)
        except Exception as e:
            print(f"创建图元 {index} 失败: {e}")
            traceback.print_exc()
            return False
    
    def _create_line_enhanced(self, primitive, index, unit_factor):
        """创建增强的线段"""
        try:
            start_x = primitive.get('start_x', 0) * unit_factor
            start_y = primitive.get('start_y', 0) * unit_factor
            end_x = primitive.get('end_x', 0) * unit_factor
            end_y = primitive.get('end_y', 0) * unit_factor
            
            # 创建曲线
            curve_data = bpy.data.curves.new(name=f"Gerber_Line_{index:05d}", type='CURVE')
            curve_data.dimensions = '3D'
            
            # 创建样条
            spline = curve_data.splines.new('POLY')
            spline.points.add(1)
            
            # 设置起点和终点
            spline.points[0].co = (start_x, start_y, 0, 1)
            spline.points[1].co = (end_x, end_y, 0, 1)
            
            # 创建对象
            curve_obj = bpy.data.objects.new(f"Gerber_Line_{index:05d}", curve_data)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Line_Mat")
            mat.diffuse_color = (0.2, 0.2, 0.8, 1.0)  # 蓝色
            
            if curve_obj.data.materials:
                curve_obj.data.materials[0] = mat
            else:
                curve_obj.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(curve_obj)
            
            self.created_objects.append(curve_obj)
            return True
            
        except Exception as e:
            print(f"创建线段失败: {e}")
            return False
    
    def _create_circle_enhanced(self, primitive, index, unit_factor):
        """创建增强的圆形"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            radius = primitive.get('radius', 0.001) * unit_factor
            
            # 创建圆形
            bpy.ops.mesh.primitive_circle_add(
                vertices=32,
                radius=radius,
                fill_type='NGON',
                location=(x, y, 0)
            )
            circle = bpy.context.active_object
            circle.name = f"Gerber_Circle_{index:05d}"
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Circle_Mat")
            mat.diffuse_color = (0.8, 0.2, 0.2, 1.0)  # 红色
            
            if circle.data.materials:
                circle.data.materials[0] = mat
            else:
                circle.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(circle)
            
            # 从场景集合中移除
            if circle.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(circle)
            
            self.created_objects.append(circle)
            return True
            
        except Exception as e:
            print(f"创建圆形失败: {e}")
            return False
    
    def _create_rectangle_enhanced(self, primitive, index, unit_factor):
        """创建增强的矩形"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            height = primitive.get('height', 0.001) * unit_factor
            rotation = primitive.get('rotation', 0)
            
            # 创建平面
            bpy.ops.mesh.primitive_plane_add(
                size=1.0,
                location=(x, y, 0)
            )
            plane = bpy.context.active_object
            plane.name = f"Gerber_Rect_{index:05d}"
            
            # 旋转
            plane.rotation_euler.z = math.radians(rotation)
            
            # 缩放
            plane.scale = (width, height, 1)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Rect_Mat")
            mat.diffuse_color = (0.2, 0.8, 0.2, 1.0)  # 绿色
            
            if plane.data.materials:
                plane.data.materials[0] = mat
            else:
                plane.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(plane)
            
            # 从场景集合中移除
            if plane.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(plane)
            
            self.created_objects.append(plane)
            return True
            
        except Exception as e:
            print(f"创建矩形失败: {e}")
            return False
    
    def _create_obround_enhanced(self, primitive, index, unit_factor):
        """创建增强的椭圆形"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            height = primitive.get('height', 0.001) * unit_factor
            rotation = primitive.get('rotation', 0)
            
            # 创建圆形（简化处理）
            radius = min(width, height) / 2
            bpy.ops.mesh.primitive_circle_add(
                vertices=32,
                radius=radius,
                fill_type='NGON',
                location=(x, y, 0)
            )
            circle = bpy.context.active_object
            circle.name = f"Gerber_Obround_{index:05d}"
            
            # 旋转
            circle.rotation_euler.z = math.radians(rotation)
            
            # 缩放为椭圆形
            if width != height:
                circle.scale = (width/height, 1, 1)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Obround_Mat")
            mat.diffuse_color = (0.8, 0.5, 0.2, 1.0)  # 橙色
            
            if circle.data.materials:
                circle.data.materials[0] = mat
            else:
                circle.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(circle)
            
            # 从场景集合中移除
            if circle.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(circle)
            
            self.created_objects.append(circle)
            return True
            
        except Exception as e:
            print(f"创建椭圆形失败: {e}")
            return False
    
    def _create_polygon_enhanced(self, primitive, index, unit_factor):
        """创建增强的多边形"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            vertices = primitive.get('vertices', 6)
            diameter = primitive.get('diameter', 0.001) * unit_factor
            rotation = primitive.get('rotation', 0)
            radius = diameter / 2
            
            # 创建多边形
            bpy.ops.mesh.primitive_circle_add(
                vertices=vertices,
                radius=radius,
                fill_type='NGON',
                location=(x, y, 0)
            )
            polygon = bpy.context.active_object
            polygon.name = f"Gerber_Polygon_{index:05d}"
            
            # 旋转
            polygon.rotation_euler.z = math.radians(rotation)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Polygon_Mat")
            mat.diffuse_color = (0.8, 0.2, 0.8, 1.0)  # 紫色
            
            if polygon.data.materials:
                polygon.data.materials[0] = mat
            else:
                polygon.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(polygon)
            
            # 从场景集合中移除
            if polygon.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(polygon)
            
            self.created_objects.append(polygon)
            return True
            
        except Exception as e:
            print(f"创建多边形失败: {e}")
            return False
    
    def _create_region_enhanced(self, primitive, index, unit_factor):
        """创建增强的区域"""
        try:
            points = primitive.get('points', [])
            if not points or len(points) < 3:
                # 如果没有足够点，创建点表示
                return self._create_point_enhanced(primitive, index, unit_factor, False)
            
            # 转换点到Blender坐标
            converted_points = []
            for point in points:
                x, y = point[0] * unit_factor, point[1] * unit_factor
                converted_points.append((x, y, 0))
            
            # 创建网格
            mesh = bpy.data.meshes.new(f"Gerber_Region_{index:05d}")
            
            # 创建面
            vertices = converted_points
            faces = []
            
            # 如果是凸多边形，创建单个面
            if len(vertices) >= 3:
                # 创建三角形扇
                for i in range(1, len(vertices)-1):
                    faces.append([0, i, i+1])
            
            # 创建网格
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            
            # 创建对象
            region_obj = bpy.data.objects.new(f"Gerber_Region_{index:05d}", mesh)
            region_obj.location = (0, 0, 0)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Region_Mat")
            mat.diffuse_color = (0.2, 0.8, 0.8, 0.5)  # 青色，半透明
            
            if region_obj.data.materials:
                region_obj.data.materials[0] = mat
            else:
                region_obj.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(region_obj)
            
            # 从场景集合中移除
            if region_obj.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(region_obj)
            
            self.created_objects.append(region_obj)
            return True
            
        except Exception as e:
            print(f"创建区域失败: {e}")
            return self._create_point_enhanced(primitive, index, unit_factor, False)
    
    def _create_arc_enhanced(self, primitive, index, unit_factor):
        """创建增强的圆弧"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            radius = primitive.get('radius', 0.001) * unit_factor
            start_angle = primitive.get('start_angle', 0)
            end_angle = primitive.get('end_angle', 360)
            
            # 创建圆弧曲线
            curve_data = bpy.data.curves.new(name=f"Gerber_Arc_{index:05d}", type='CURVE')
            curve_data.dimensions = '3D'
            
            # 创建圆弧样条
            spline = curve_data.splines.new('NURBS')
            spline.use_endpoint_u = True
            spline.use_endpoint_v = True
            
            # 计算圆弧点
            points_count = 32
            angle_range = end_angle - start_angle
            if angle_range < 0:
                angle_range += 360
            
            points = []
            for i in range(points_count + 1):
                angle = start_angle + (angle_range * i / points_count)
                rad = math.radians(angle)
                px = x + radius * math.cos(rad)
                py = y + radius * math.sin(rad)
                points.append((px, py, 0))
            
            spline.points.add(len(points) - 1)
            for i, point in enumerate(points):
                spline.points[i].co = (point[0], point[1], point[2], 1)
            
            # 创建对象
            arc_obj = bpy.data.objects.new(f"Gerber_Arc_{index:05d}", curve_data)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Arc_Mat")
            mat.diffuse_color = (0.8, 0.8, 0.2, 1.0)  # 黄色
            
            if arc_obj.data.materials:
                arc_obj.data.materials[0] = mat
            else:
                arc_obj.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(arc_obj)
            
            self.created_objects.append(arc_obj)
            return True
            
        except Exception as e:
            print(f"创建圆弧失败: {e}")
            return self._create_point_enhanced(primitive, index, unit_factor, False)
    
    def _create_amgroup_enhanced(self, primitive, index, unit_factor):
        """创建增强的光圈组"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            aperture_id = primitive.get('aperture_id', 'unknown')
            
            # 创建标记对象
            bpy.ops.mesh.primitive_cone_add(
                vertices=8,
                radius1=0.0005,
                radius2=0.0003,
                depth=0.001,
                location=(x, y, 0)
            )
            cone = bpy.context.active_object
            cone.name = f"Gerber_AMGroup_{index:05d}_{aperture_id}"
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_AMGroup_Mat")
            mat.diffuse_color = (0.5, 0.2, 0.8, 1.0)  # 深紫色
            
            if cone.data.materials:
                cone.data.materials[0] = mat
            else:
                cone.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(cone)
            
            # 从场景集合中移除
            if cone.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(cone)
            
            self.created_objects.append(cone)
            return True
            
        except Exception as e:
            print(f"创建光圈组失败: {e}")
            return self._create_point_enhanced(primitive, index, unit_factor, False)
    
    def _create_test_record_enhanced(self, primitive, index, unit_factor):
        """创建增强的测试记录"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            size = primitive.get('size', 0.001) * unit_factor
            
            # 创建测试点（十字标记）
            # 创建水平线
            curve_data = bpy.data.curves.new(name=f"Gerber_Test_{index:05d}", type='CURVE')
            curve_data.dimensions = '3D'
            
            # 创建十字标记
            spline_h = curve_data.splines.new('POLY')
            spline_h.points.add(1)
            spline_h.points[0].co = (x - size/2, y, 0, 1)
            spline_h.points[1].co = (x + size/2, y, 0, 1)
            
            spline_v = curve_data.splines.new('POLY')
            spline_v.points.add(1)
            spline_v.points[0].co = (x, y - size/2, 0, 1)
            spline_v.points[1].co = (x, y + size/2, 0, 1)
            
            # 创建对象
            test_obj = bpy.data.objects.new(f"Gerber_Test_{index:05d}", curve_data)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Test_Mat")
            mat.diffuse_color = (1.0, 0.5, 0.0, 1.0)  # 橙色
            
            if test_obj.data.materials:
                test_obj.data.materials[0] = mat
            else:
                test_obj.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(test_obj)
            
            self.created_objects.append(test_obj)
            return True
            
        except Exception as e:
            print(f"创建测试记录失败: {e}")
            return self._create_point_enhanced(primitive, index, unit_factor, False)
    
    def _create_flash_enhanced(self, primitive, index, unit_factor):
        """创建增强的闪光操作"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            aperture_id = primitive.get('aperture_id', 'unknown')
            
            # 创建闪光标记（星形）
            bpy.ops.mesh.primitive_circle_add(
                vertices=6,
                radius=0.0005,
                fill_type='TRIFAN',
                location=(x, y, 0)
            )
            flash = bpy.context.active_object
            flash.name = f"Gerber_Flash_{index:05d}_{aperture_id}"
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Flash_Mat")
            mat.diffuse_color = (1.0, 0.0, 1.0, 1.0)  # 洋红色
            
            if flash.data.materials:
                flash.data.materials[0] = mat
            else:
                flash.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(flash)
            
            # 从场景集合中移除
            if flash.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(flash)
            
            self.created_objects.append(flash)
            return True
            
        except Exception as e:
            print(f"创建闪光操作失败: {e}")
            return self._create_point_enhanced(primitive, index, unit_factor, False)
    
    def _create_step_repeat_enhanced(self, primitive, index, unit_factor):
        """创建增强的步进重复"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            instance_count = primitive.get('instance_count', 1)
            
            # 创建步进重复标记
            bpy.ops.mesh.primitive_cube_add(
                size=0.0003,
                location=(x, y, 0)
            )
            step_repeat = bpy.context.active_object
            step_repeat.name = f"Gerber_StepRepeat_{index:05d}_{instance_count}"
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_StepRepeat_Mat")
            mat.diffuse_color = (0.5, 0.5, 0.0, 1.0)  # 橄榄色
            
            if step_repeat.data.materials:
                step_repeat.data.materials[0] = mat
            else:
                step_repeat.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(step_repeat)
            
            # 从场景集合中移除
            if step_repeat.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(step_repeat)
            
            self.created_objects.append(step_repeat)
            return True
            
        except Exception as e:
            print(f"创建步进重复失败: {e}")
            return self._create_point_enhanced(primitive, index, unit_factor, False)
    
    def _create_point_enhanced(self, primitive, index, unit_factor, debug=False):
        """创建增强的点"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            size = primitive.get('size', 0.0001)  # 更小的点
            primitive_type = primitive.get('type', 'unknown')
            class_name = primitive.get('class_name', 'unknown')
            
            if debug:
                print(f"  ⚫ 创建点: 类型={primitive_type}, 类={class_name}, 位置=({x:.6f}, {y:.6f})")
            
            # 创建立方体
            bpy.ops.mesh.primitive_cube_add(
                size=size,
                location=(x, y, 0)
            )
            cube = bpy.context.active_object
            cube.name = f"Gerber_{class_name}_{index:05d}"
            
            # 根据类型设置颜色
            color_map = {
                'unknown': (0.5, 0.5, 0.5, 1.0),  # 灰色
                'amgroup': (0.5, 0.2, 0.8, 1.0),  # 紫色
                'arc': (0.8, 0.8, 0.2, 1.0),      # 黄色
                'region': (0.2, 0.8, 0.8, 0.5),   # 青色，半透明
                'test_record': (1.0, 0.5, 0.0, 1.0),  # 橙色
                'flash': (1.0, 0.0, 1.0, 1.0),    # 洋红色
                'step_repeat': (0.5, 0.5, 0.0, 1.0),  # 橄榄色
            }
            
            color = color_map.get(primitive_type, (0.8, 0.2, 0.8, 1.0))  # 粉色
            
            # 创建材质
            mat = bpy.data.materials.new(name=f"Gerber_{primitive_type}_Mat")
            mat.diffuse_color = color
            
            if cube.data.materials:
                cube.data.materials[0] = mat
            else:
                cube.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(cube)
            
            # 从场景集合中移除
            if cube.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(cube)
            
            self.created_objects.append(cube)
            return True
            
        except Exception as e:
            print(f"创建点失败: {e}")
            return False
    
    def _create_bounding_box_only(self, file_info, collection_name):
        """只创建边界框"""
        try:
            # 创建集合
            if collection_name in bpy.data.collections:
                collection = bpy.data.collections[collection_name]
            else:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            
            # 创建立方体表示边界框
            bpy.ops.mesh.primitive_cube_add(size=0.05)
            cube = bpy.context.active_object
            cube.name = f"{collection_name}_Bounds"
            cube.location = (0, 0, 0)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Bounds_Mat")
            mat.diffuse_color = (0.5, 0.5, 0.5, 0.5)
            
            if cube.data.materials:
                cube.data.materials[0] = mat
            else:
                cube.data.materials.append(mat)
            
            # 链接到集合
            collection.objects.link(cube)
            
            self.created_objects.append(cube)
            
            return {
                'success': True,
                'object_count': 1,
                'collection': collection_name,
                'message': f"创建了边界框"
            }
            
        except Exception as e:
            print(f"创建边界框失败: {e}")
            return {'success': False, 'error': str(e)}

# ============================================================================
# 主导入操作符
# ============================================================================
class IMPORT_OT_gerber_complete(Operator):
    """完整的Gerber导入"""
    bl_idname = "io_fritzing.import_gerber_complete"
    bl_label = "导入Gerber文件（完整版）"
    bl_description = "支持所有Gerber图元类型的完整导入"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="Gerber文件",
        subtype='FILE_PATH',
        default=""
    )
    
    debug_mode: BoolProperty(
        name="调试模式",
        description="显示详细的调试信息",
        default=False
    )
    
    def invoke(self, context, event):
        """调用对话框"""
        if not self.filepath or not os.path.exists(self.filepath):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return self.execute(context)
    
    def execute(self, context):
        """执行导入"""
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({'ERROR'}, "请选择有效的Gerber文件")
            return {'CANCELLED'}
        
        if not GERBER_LIB_AVAILABLE:
            self.report({'ERROR'}, "python-gerber库不可用")
            return {'CANCELLED'}
        
        try:
            # 解析Gerber文件
            parser = GerberCompleteParser()
            result = parser.parse_file(self.filepath, debug=self.debug_mode)
            
            if not result.get('success', False):
                self.report({'ERROR'}, f"解析失败: {result.get('error', '未知错误')}")
                return {'CANCELLED'}
            
            # 创建几何体
            generator = EnhancedGeometryGenerator()
            primitives = result.get('primitives', [])
            file_info = result.get('file_info', {})
            
            create_result = generator.create_enhanced_geometry(
                primitives, 
                file_info,
                debug=self.debug_mode
            )
            
            if not create_result.get('success', False):
                self.report({'ERROR'}, f"创建几何体失败: {create_result.get('error', '未知错误')}")
                return {'CANCELLED'}
            
            # 显示统计信息
            type_stats = result.get('type_stats', {})
            stats_text = ", ".join([f"{k}:{v}" for k, v in type_stats.items()])
            message = f"导入完成: {create_result.get('object_count', 0)} 个对象 [{stats_text}]"
            self.report({'INFO'}, message)
            return {'FINISHED'}
            
        except Exception as e:
            error_msg = f"导入过程错误: {str(e)}"
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}

# ============================================================================
# 设置面板
# ============================================================================
class VIEW3D_PT_gerber_complete(Panel):
    """Gerber导入设置面板 - 完整版"""
    bl_label = "Gerber导入（完整版）"
    bl_idname = "VIEW3D_PT_gerber_complete"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing工具"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 标题
        box = layout.box()
        box.label(text="Gerber文件导入（完整版）", icon='IMPORT')
        
        # 文件选择
        row = box.row(align=True)
        row.prop(scene, "gerber_file_complete", text="")
        row.operator("io_fritzing.browse_gerber_complete", 
                    text="", 
                    icon='FILEBROWSER')
        
        # 文件信息
        if scene.gerber_file_complete and os.path.exists(scene.gerber_file_complete):
            try:
                file_size = os.path.getsize(scene.gerber_file_complete)
                ext = os.path.splitext(scene.gerber_file_complete)[1].lower()
                
                col = box.column(align=True)
                col.label(text=f"文件大小: {file_size/1024:.1f} KB", icon='INFO')
                
                if ext in ['.gtl', '.gbl', '.gto', '.gts', '.gtp', '.gm1']:
                    layer_names = {
                        '.gtl': '顶层铜层',
                        '.gbl': '底层铜层',
                        '.gto': '顶层丝印',
                        '.gts': '顶层阻焊',
                        '.gtp': '顶层焊膏',
                        '.gm1': '板框层'
                    }
                    col.label(text=f"图层: {layer_names.get(ext, '未知')}", icon='MESH_GRID')
            except:
                pass
        
        # 导入选项
        layout.separator()
        box = layout.box()
        box.label(text="导入选项", icon='SETTINGS')
        box.prop(scene, "gerber_debug_mode_complete", text="启用调试模式")
        
        # 工具状态
        layout.separator()
        box = layout.box()
        box.label(text="工具状态", icon='INFO')
        
        if GERBER_LIB_AVAILABLE:
            box.label(text="✅ python-gerber: 可用", icon='CHECKMARK')
        else:
            box.label(text="❌ python-gerber: 不可用", icon='ERROR')
        
        # 导入按钮
        layout.separator()
        col = layout.column(align=True)
        
        if not GERBER_LIB_AVAILABLE:
            col.label(text="无法导入，依赖库缺失", icon='ERROR')
            return
        
        if scene.gerber_file_complete and os.path.exists(scene.gerber_file_complete):
            op = col.operator("io_fritzing.import_gerber_complete", 
                             text="导入Gerber文件（完整版）", 
                             icon='IMPORT')
            op.filepath = scene.gerber_file_complete
            op.debug_mode = scene.gerber_debug_mode_complete
        else:
            col.label(text="请先选择Gerber文件", icon='ERROR')

# ============================================================================
# 辅助操作符
# ============================================================================
class IMPORT_OT_browse_gerber_complete(Operator):
    """浏览Gerber文件"""
    bl_idname = "io_fritzing.browse_gerber_complete"
    bl_label = "浏览"
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(default="*.gbr;*.ger;*.gbx;*.gtl;*.gbl;*.gto;*.gts;*.gtp;*.gm1;*.gko", options={'HIDDEN'})
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if self.filepath:
            context.scene.gerber_file_complete = self.filepath
        return {'FINISHED'}

# ============================================================================
# 注册
# ============================================================================
classes = [
    IMPORT_OT_gerber_complete,
    IMPORT_OT_browse_gerber_complete,
    VIEW3D_PT_gerber_complete,
]

def register():
    """注册插件"""
    print("注册Gerber完整导入插件...")
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ 注册类: {cls.__name__}")
        except Exception as e:
            print(f"❌ 注册类 {cls.__name__} 失败: {e}")
    
    # 注册场景属性
    Scene.gerber_file_complete = StringProperty(
        name="Gerber File",
        description="Gerber文件路径",
        subtype='FILE_PATH',
        default=""
    )
    
    Scene.gerber_debug_mode_complete = BoolProperty(
        name="Gerber Debug Mode",
        description="启用调试模式显示详细信息",
        default=False
    )
    
    print("✅ Gerber完整导入插件注册完成")

def unregister():
    """注销插件"""
    print("注销Gerber完整导入插件...")
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ 注销类: {cls.__name__}")
        except:
            pass

if __name__ == "__main__":
    register()