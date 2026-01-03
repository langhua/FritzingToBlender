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
import gc
from mathutils import Vector, Matrix

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
        print("❌ 未找到pcb_tools，请确保已下载pcb_tools源代码")
        return False

# 设置路径
PCB_TOOLS_AVAILABLE = setup_pcb_tools_path()

# 导入检测
GERBER_LIB_AVAILABLE = False
EXCELLON_LIB_AVAILABLE = False

if PCB_TOOLS_AVAILABLE:
    try:
        from pcb_tools import read
        print("✅ pcb_tools库导入成功")
        GERBER_LIB_AVAILABLE = True
    except ImportError as e:
        print(f"❌ pcb_tools库导入失败: {e}")
    
    try:
        from pcb_tools.excellon import read as read_excellon
        print("✅ pcb_tools.excellon库导入成功")
        EXCELLON_LIB_AVAILABLE = True
    except ImportError as e:
        print(f"❌ pcb_tools.excellon库导入失败: {e}")

# 计算总库可用性
ALL_LIB_AVAILABLE = GERBER_LIB_AVAILABLE or EXCELLON_LIB_AVAILABLE


# ============================================================================
# 性能优化工具
# ============================================================================
class PerformanceOptimizer:
    """性能优化工具类"""
    
    @staticmethod
    def batch_process(primitives, batch_size=50):
        """批量处理图元，提高性能"""
        for i in range(0, len(primitives), batch_size):
            yield primitives[i:i + batch_size]
    
    @staticmethod
    def clear_unused_data():
        """清理未使用的数据"""
        try:
            # 清理未使用的网格
            for mesh in bpy.data.meshes:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            
            # 清理未使用的材质
            for mat in bpy.data.materials:
                if mat.users == 0:
                    bpy.data.materials.remove(mat)
            
            # 清理未使用的曲线
            for curve in bpy.data.curves:
                if curve.users == 0:
                    bpy.data.curves.remove(curve)
            
            # 强制垃圾回收
            gc.collect()
            
            print("🧹 已清理未使用的数据")
            return True
        except Exception as e:
            print(f"清理数据失败: {e}")
            return False

# ============================================================================
# 修复的Gerber解析器
# ============================================================================
class FixedGerberParser:
    """修复的Gerber解析器"""
    
    def __init__(self):
        self.primitives = []
        self.file_info = {}
    
    def parse_gerber_fixed(self, filepath, debug=False):
        """解析Gerber文件 - 修复版"""
        if not GERBER_LIB_AVAILABLE:
            return {
                'success': False, 
                'error': '缺少python-gerber库',
                'install_hint': '请确保pcb_tools已正确安装'
            }
        
        try:
            print(f"🔍 开始解析Gerber文件: {os.path.basename(filepath)}")
            start_time = time.time()
            
            # 读取Gerber文件
            gerber = read(filepath)
            
            # 获取单位
            units = 'metric' if hasattr(gerber, 'units') and gerber.units == 'metric' else 'inch'
            unit_factor = 0.001 if units == 'metric' else 0.0254

            # 获取文件信息
            self.file_info = self._get_gerber_info(gerber, filepath)
            print(f"📄 Gerber文件信息: {self.file_info}")
            
            # 提取图元
            # self.primitives = self._extract_primitives_fixed(gerber, debug)

            if hasattr(gerber, 'primitives'):
                for i, prim in enumerate(gerber.primitives):
                    prim_data = self._extract_primitive_data(prim, i, units)
                    if prim_data:
                        self.primitives.append(prim_data)

            processing_time = time.time() - start_time
            
            # 统计图元类型
            type_stats = self._analyze_primitive_types()
            
            result = {
                'success': True,
                'file_type': 'gerber',
                'file_info': self.file_info,
                'primitives': self.primitives,
                'primitive_count': len(self.primitives),
                'type_stats': type_stats,
                'processing_time': processing_time,
                'units': units,
                'unit_factor': unit_factor,
                'message': f"成功解析 {len(self.primitives)} 个图元"
            }
            
            print(f"\n📊 Gerber解析统计:")
            print(f"  - 总图元数: {len(self.primitives)}")
            for prim_type, count in type_stats.items():
                print(f"  - {prim_type}: {count} 个")
            
            print(f"⏱️  耗时: {processing_time:.2f} 秒")
            return result
            
        except Exception as e:
            error_msg = f"解析Gerber文件失败: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _get_gerber_info(self, gerber, filepath):
        """获取Gerber文件信息"""
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
    
    def _extract_primitive_data(self, primitive, index, units):
        """提取图元数据"""
        try:
            prim_type = primitive.__class__.__name__.lower()
            
            if prim_type == 'line':
                return self._extract_line_data(primitive, index)
            elif prim_type == 'circle':
                return self._extract_circle_data(primitive, index)
            elif prim_type == 'region':
                return self._extract_region_data(primitive, index)
            elif prim_type == 'rectangle':
                return self._extract_rectangle_data(primitive, index)
            elif prim_type == 'obround':
                return self._extract_obround_data(primitive, index)
            else:
                print(f"未知图元类型: {prim_type}")
                return None
                
        except Exception as e:
            print(f"提取图元{index}数据失败: {e}")
            return None
    
    def _extract_line_data(self, line, index):
        """提取线段数据"""
        try:
            start = getattr(line, 'start', (0, 0))
            end = getattr(line, 'end', (0, 0))
            
            if hasattr(start, '__len__') and len(start) >= 2:
                x1, y1 = start[0], start[1]
            else:
                x1, y1 = 0, 0
            
            if hasattr(end, '__len__') and len(end) >= 2:
                x2, y2 = end[0], end[1]
            else:
                x2, y2 = 0, 0
            
            # 获取线宽
            width = 0.001
            if hasattr(line, 'width'):
                width = line.width
            elif hasattr(line, 'aperture'):
                aperture = line.aperture
                if aperture and hasattr(aperture, 'diameter'):
                    width = aperture.diameter
            
            return {
                'type': 'line',
                'x1': x1,
                'y1': y1,
                'x2': x2,
                'y2': y2,
                'width': width
            }
        except Exception as e:
            print(f"提取线段数据失败: {e}")
            return None
    
    def _extract_region_data(self, region, index):
        """提取Region数据"""
        try:
            # 获取边界框
            bbox = getattr(region, 'bounding_box', None)
            
            if bbox and len(bbox) >= 2:
                min_x, min_y = bbox[0]
                max_x, max_y = bbox[1]
                
                width = max_x - min_x
                height = max_y - min_y
                
                # 计算中心
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
            else:
                # 尝试从属性获取
                center_x = getattr(region, 'x', 0)
                center_y = getattr(region, 'y', 0)
                width = getattr(region, 'width', 0.001)
                height = getattr(region, 'height', 0.001)
            
            return {
                'type': 'region',
                'x': center_x,
                'y': center_y,
                'width': width,
                'height': height
            }
        except Exception as e:
            print(f"提取Region数据失败: {e}")
            return None
    
    def _extract_circle_data(self, circle, index):
        """提取圆形数据"""
        try:
            # 尝试多种可能的属性名
            x = 0
            y = 0
            radius = 0.001
            
            # 尝试各种可能的中心坐标属性
            if hasattr(circle, 'position'):
                pos = circle.position
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(circle, 'center'):
                pos = circle.center
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(circle, 'x') and hasattr(circle, 'y'):
                x = circle.x
                y = circle.y
            
            # 获取半径
            if hasattr(circle, 'radius'):
                radius = circle.radius
            elif hasattr(circle, 'diameter'):
                radius = circle.diameter / 2
            
            return {
                'type': 'circle',
                'x': x,
                'y': y,
                'radius': radius
            }
        except Exception as e:
            print(f"提取圆形数据失败: {e}")
            return None
    
    def _extract_rectangle_data(self, rectangle, index):
        """提取矩形数据"""
        try:
            x = 0
            y = 0
            width = 0.001
            height = 0.001
            
            # 尝试各种可能的中心坐标属性
            if hasattr(rectangle, 'position'):
                pos = rectangle.position
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(rectangle, 'center'):
                pos = rectangle.center
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(rectangle, 'x') and hasattr(rectangle, 'y'):
                x = rectangle.x
                y = rectangle.y
            
            # 获取尺寸
            if hasattr(rectangle, 'width'):
                width = rectangle.width
            if hasattr(rectangle, 'height'):
                height = rectangle.height
            
            return {
                'type': 'rectangle',
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }
        except Exception as e:
            print(f"提取矩形数据失败: {e}")
            return None
    
    def _extract_obround_data(self, obround, index):
        """提取椭圆形数据"""
        try:
            x = 0
            y = 0
            width = 0.001
            height = 0.001
            
            # 尝试各种可能的中心坐标属性
            if hasattr(obround, 'position'):
                pos = obround.position
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(obround, 'center'):
                pos = obround.center
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(obround, 'x') and hasattr(obround, 'y'):
                x = obround.x
                y = obround.y
            
            # 获取尺寸
            if hasattr(obround, 'width'):
                width = obround.width
            if hasattr(obround, 'height'):
                height = obround.height
            
            return {
                'type': 'obround',
                'x': x,
                'y': y,
                'width': width,
                'height': height
            }
        except Exception as e:
            print(f"提取椭圆形数据失败: {e}")
            return None
    
    def _extract_primitives_fixed(self, gerber, debug=False):
        """提取图元 - 修复版"""
        primitives = []
        
        try:
            if hasattr(gerber, 'primitives') and gerber.primitives:
                print(f"🔍 从primitives属性提取图元: {len(gerber.primitives)} 个")
                
                for i, primitive in enumerate(gerber.primitives):
                    primitive_data = self._parse_primitive_fixed(primitive, i, debug and i < 5)
                    if primitive_data:
                        primitives.append(primitive_data)
                
                return primitives
            
            return []
            
        except Exception as e:
            print(f"❌ 提取图元失败: {e}")
            traceback.print_exc()
            return []
    
    def _parse_primitive_fixed(self, primitive, index, debug=False):
        """解析单个图元 - 修复版"""
        try:
            class_name = primitive.__class__.__name__
            
            if debug:
                print(f"  🔍 解析图元 {index}: {class_name}")
            
            if class_name == 'Line':
                return self._parse_line_fixed(primitive, index, debug)
            elif class_name == 'Circle':
                return self._parse_circle_fixed(primitive, index, debug)
            elif class_name == 'Rectangle':
                return self._parse_rectangle_fixed(primitive, index, debug)
            elif class_name == 'Obround':
                return self._parse_obround_fixed(primitive, index, debug)
            elif class_name == 'Region':
                return self._parse_region_fixed(primitive, index, debug)
            else:
                return self._parse_unknown_fixed(primitive, index, debug)
                
        except Exception as e:
            print(f"❌ 解析图元 {index} 失败: {e}")
            return None
    
    def _parse_line_fixed(self, line, index, debug=False):
        """解析线段 - 修复版"""
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
            
            # 获取线段宽度
            width = 0.001  # 默认宽度
            
            # 尝试多种方法获取宽度
            if hasattr(line, 'width'):
                width = line.width
            elif hasattr(line, 'aperture'):
                aperture = line.aperture
                if aperture and hasattr(aperture, 'width'):
                    width = aperture.width
                elif aperture and hasattr(aperture, 'diameter'):
                    width = aperture.diameter
            
            if debug:
                print(f"    线段: ({start_x:.3f}, {start_y:.3f}) -> ({end_x:.3f}, {end_y:.3f}), 宽度: {width:.6f}")
            
            return {
                'id': index,
                'type': 'line',
                'start_x': start_x,
                'start_y': start_y,
                'end_x': end_x,
                'end_y': end_y,
                'width': width,
                'length': math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2),
            }
        except Exception as e:
            print(f"解析线段失败: {e}")
            return None
    
    def _parse_circle_fixed(self, circle, index, debug=False):
        """解析圆形 - 修复版"""
        try:
            position = getattr(circle, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            diameter = getattr(circle, 'diameter', 0.1)
            radius = diameter / 2
            
            if debug:
                print(f"    圆形: 中心({x:.3f}, {y:.3f}), 直径: {diameter:.6f}")
            
            return {
                'id': index,
                'type': 'circle',
                'x': x,
                'y': y,
                'radius': radius,
                'diameter': diameter,
            }
        except Exception as e:
            print(f"解析圆形失败: {e}")
            return None
    
    def _parse_rectangle_fixed(self, rectangle, index, debug=False):
        """解析矩形 - 修复版"""
        try:
            position = getattr(rectangle, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            width = getattr(rectangle, 'width', 0.1)
            height = getattr(rectangle, 'height', 0.1)
            rotation = getattr(rectangle, 'rotation', 0.0)
            
            if debug:
                print(f"    矩形: 中心({x:.3f}, {y:.3f}), 尺寸: {width:.6f}x{height:.6f}")
            
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
            print(f"解析矩形失败: {e}")
            return None
    
    def _parse_obround_fixed(self, obround, index, debug=False):
        """解析椭圆形 - 修复版"""
        try:
            position = getattr(obround, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            width = getattr(obround, 'width', 0.1)
            height = getattr(obround, 'height', 0.1)
            rotation = getattr(obround, 'rotation', 0.0)
            
            if debug:
                print(f"    椭圆形: 中心({x:.3f}, {y:.3f}), 尺寸: {width:.6f}x{height:.6f}")
            
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
            print(f"解析椭圆形失败: {e}")
            return None
    
    def _parse_region_fixed(self, region, index, debug=False):
        """解析区域 - 修复版"""
        try:
            bounding_box = getattr(region, 'bounding_box', ((0, 0), (0, 0)))
            
            if bounding_box and len(bounding_box) >= 2:
                min_x, min_y = bounding_box[0]
                max_x, max_y = bounding_box[1]
                
                width = max_x - min_x
                height = max_y - min_y
                
                # 计算中心点
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
            else:
                min_x, min_y, max_x, max_y = 0, 0, 0, 0
                width, height = 0, 0
                center_x, center_y = 0, 0
            
            if debug:
                print(f"    区域: 边界框({min_x:.3f}, {min_y:.3f}) -> ({max_x:.3f}, {max_y:.3f})")
                print(f"          尺寸: {width:.6f}x{height:.6f}")
            
            return {
                'id': index,
                'type': 'region',
                'x': center_x,
                'y': center_y,
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y,
                'width': width,
                'height': height,
                'is_valid': width > 0 and height > 0,
            }
        except Exception as e:
            print(f"解析区域失败: {e}")
            return None
    
    def _parse_unknown_fixed(self, primitive, index, debug=False):
        """解析未知图元 - 修复版"""
        try:
            return {
                'id': index,
                'type': 'unknown',
                'x': 0,
                'y': 0,
                'size': 0.001,
            }
        except Exception as e:
            return None
    
    def _analyze_primitive_types(self):
        """分析图元类型统计"""
        type_stats = {}
        for primitive in self.primitives:
            prim_type = primitive.get('type', 'unknown')
            type_stats[prim_type] = type_stats.get(prim_type, 0) + 1
        return type_stats

# ============================================================================
# 修复的Gerber几何生成器
# ============================================================================
class FixedGerberGenerator:
    """修复的Gerber几何生成器"""
    
    def __init__(self):
        self.collection = None
        self.created_objects = []
        self.optimizer = PerformanceOptimizer()
    
    def create_gerber_geometry_fixed(self, primitives, file_info, debug=False, optimize=True):
        """创建Gerber几何体 - 修复版"""
        if not primitives:
            print("⚠️ 没有图元数据")
            return {
                'success': True,
                'object_count': 0,
                'collection': None,
                'message': "没有图元数据"
            }
        
        try:
            print(f"🛠️ 开始创建几何体，共 {len(primitives)} 个图元")
            
            # 获取单位转换因子
            units = file_info.get('units', 'metric')
            unit_factor = 0.0254 if units == 'inch' else 0.001
            print(f"📏 单位系统: {units}, 转换因子: {unit_factor}")
            
            # 生成唯一集合名称
            base_name = f"Gerber_Fixed_{os.path.basename(file_info['filename']).replace('.', '_')}"
            timestamp = int(time.time())
            final_name = f"{base_name}_{timestamp}"
            
            # 创建集合
            self._create_collection_safe(final_name)
            
            # 清理内存
            if optimize:
                self.optimizer.clear_unused_data()
            
            # 批量处理图元
            created_count = 0
            batch_index = 0
            
            for batch in self.optimizer.batch_process(primitives, batch_size=50):
                print(f"📦 处理批次 {batch_index + 1}, 大小: {len(batch)}")
                
                for primitive in batch:
                    if self._create_primitive(primitive, created_count, unit_factor, debug and created_count < 5):
                        created_count += 1
                
                batch_index += 1
                
                # 清理内存
                if optimize and batch_index % 5 == 0:
                    self.optimizer.clear_unused_data()
            
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
            bpy.context.scene.collection.children.link(self.collection)
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[name]
            print(f"📁 创建集合: {name}")
        except Exception as e:
            print(f"创建集合失败: {e}")
    
    def _create_primitive(self, primitive, index, unit_factor, debug=False):
        """创建修复的图元"""
        primitive_type = primitive.get('type', 'unknown')
        
        try:
            if primitive_type == 'line':
                return self._create_line_connected(primitive, index, unit_factor, debug)
            elif primitive_type == 'circle':
                return self._create_circle_fixed(primitive, index, unit_factor, debug)
            elif primitive_type == 'rectangle':
                return self._create_rectangle_fixed(primitive, index, unit_factor, debug)
            elif primitive_type == 'obround':
                return self._create_obround_fixed(primitive, index, unit_factor, debug)
            elif primitive_type == 'region':
                return self._create_region_fixed(primitive, index, unit_factor, True)
            else:
                return self._create_point_fixed(primitive, index, unit_factor, debug)
        except Exception as e:
            print(f"创建图元 {index} 失败: {e}")
            return False
    
    def _create_line_connected(self, primitive, index, unit_factor, debug=False):
        """创建连接的线段"""
        try:
            start_x = primitive.get('start_x', 0) * unit_factor
            start_y = primitive.get('start_y', 0) * unit_factor
            end_x = primitive.get('end_x', 0) * unit_factor
            end_y = primitive.get('end_y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            
            if debug:
                print(f"  🔧 创建连接线段 {index}:")
                print(f"    起点: ({start_x:.6f}, {start_y:.6f})")
                print(f"    终点: ({end_x:.6f}, {end_y:.6f})")
                print(f"    线宽: {width:.6f}")
            
            # 计算线段的方向和长度
            dx = end_x - start_x
            dy = end_y - start_y
            length = math.sqrt(dx*dx + dy*dy)
            
            if length == 0:
                return False
            
            # 创建有厚度的线段（矩形）
            # 计算矩形的四个角点
            half_width = width / 2
            
            # 计算垂直方向
            if dx == 0:
                # 垂直线段
                perp_x = half_width
                perp_y = 0
            elif dy == 0:
                # 水平线段
                perp_x = 0
                perp_y = half_width
            else:
                # 斜线段
                # 计算垂直向量
                perp_length = math.sqrt(dx*dx + dy*dy)
                perp_x = -dy * half_width / perp_length
                perp_y = dx * half_width / perp_length
            
            # 创建矩形顶点
            vertices = [
                (start_x - perp_x, start_y - perp_y, 0),  # 起点左下
                (start_x + perp_x, start_y + perp_y, 0),  # 起点右下
                (end_x + perp_x, end_y + perp_y, 0),     # 终点右下
                (end_x - perp_x, end_y - perp_y, 0),     # 终点左下
            ]
            
            # 创建面
            faces = [(0, 1, 2, 3)]
            
            # 创建网格
            mesh = bpy.data.meshes.new(f"Gerber_Line_Conn_{index:05d}")
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            
            # 创建对象
            line_obj = bpy.data.objects.new(f"Gerber_Line_Conn_{index:05d}", mesh)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Line_Mat")
            mat.diffuse_color = (0.2, 0.2, 0.8, 1.0)  # 蓝色
            
            if line_obj.data.materials:
                line_obj.data.materials[0] = mat
            else:
                line_obj.data.materials.append(mat)
            
            try:
                self.collection.objects.link(line_obj)
            except:
                pass
            self.created_objects.append(line_obj)
            return True
            
        except Exception as e:
            print(f"创建连接线段失败: {e}")
            return False
    
    def _create_circle_fixed(self, primitive, index, unit_factor, debug=False):
        """创建圆形 - 修复版"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            diameter = primitive.get('diameter', 0.001) * unit_factor
            radius = diameter / 2
            
            if diameter <= 0:
                if debug:
                    print(f"  ⚠️  圆形 {index}: 无效直径 {diameter}")
                return False
            
            if debug:
                print(f"  🔧 创建圆形 {index}:")
                print(f"    中心: ({x:.6f}, {y:.6f})")
                print(f"    直径: {diameter:.6f}")
            
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
    
    def _create_rectangle_fixed(self, primitive, index, unit_factor, debug=False):
        """创建矩形 - 修复版"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            height = primitive.get('height', 0.001) * unit_factor
            rotation = primitive.get('rotation', 0)
            
            if width <= 0 or height <= 0:
                if debug:
                    print(f"  ⚠️  矩形 {index}: 无效尺寸 {width}x{height}")
                return False
            
            if debug:
                print(f"  🔧 创建矩形 {index}:")
                print(f"    中心: ({x:.6f}, {y:.6f})")
                print(f"    尺寸: {width:.6f}x{height:.6f}")
            
            # 创建平面
            bpy.ops.mesh.primitive_plane_add(
                size=1.0,
                location=(x, y, 0)
            )
            plane = bpy.context.active_object
            plane.name = f"Gerber_Rect_{index:05d}"
            
            # 旋转
            if rotation != 0:
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
            
            self.created_objects.append(plane)
            return True
            
        except Exception as e:
            print(f"创建矩形失败: {e}")
            return False
    
    def _create_obround_fixed(self, primitive, index, unit_factor, debug=False):
        """创建椭圆形 - 修复版"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            height = primitive.get('height', 0.001) * unit_factor
            rotation = primitive.get('rotation', 0)
            
            if width <= 0 or height <= 0:
                if debug:
                    print(f"  ⚠️  椭圆形 {index}: 无效尺寸 {width}x{height}")
                return False
            
            if debug:
                print(f"  🔧 创建椭圆形 {index}:")
                print(f"    中心: ({x:.6f}, {y:.6f})")
                print(f"    尺寸: {width:.6f}x{height:.6f}")
            
            # 创建圆形
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
            if rotation != 0:
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
            
            self.created_objects.append(circle)
            return True
            
        except Exception as e:
            print(f"创建椭圆形失败: {e}")
            return False
    
    def _create_region_fixed(self, primitive, index, unit_factor, debug=False):
        """创建区域 - 修复版"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0) * unit_factor
            height = primitive.get('height', 0) * unit_factor
            is_valid = primitive.get('is_valid', False)
            
            if not is_valid or width <= 0 or height <= 0:
                if debug:
                    print(f"  ⚠️  区域 {index}: 无效尺寸 {width}x{height}")
                return False
            
            if debug:
                print(f"  🔧 创建区域 {index}:")
                print(f"    中心: ({x:.6f}, {y:.6f})")
                print(f"    尺寸: {width:.6f}x{height:.6f}")
            
            # 创建较小的区域（原尺寸的1/10，避免过大）
            scale_factor = 0.1
            scaled_width = width * scale_factor
            scaled_height = height * scale_factor
            
            # 创建平面表示区域
            bpy.ops.mesh.primitive_plane_add(
                size=1.0,
                location=(x, y, 0)
            )
            plane = bpy.context.active_object
            plane.name = f"Gerber_Region_Fixed_{index:05d}"
            
            # 缩放
            plane.scale = (scaled_width, scaled_height, 1)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Region_Fixed_Mat")
            mat.diffuse_color = (0.2, 0.8, 0.8, 0.3)  # 青色，更透明
            
            if plane.data.materials:
                plane.data.materials[0] = mat
            else:
                plane.data.materials.append(mat)
            
            self.created_objects.append(plane)
            return True
            
        except Exception as e:
            print(f"创建区域失败: {e}")
            return False
    
    def _create_point_fixed(self, primitive, index, unit_factor, debug=False):
        """创建点 - 修复版"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            
            # 创建立方体
            bpy.ops.mesh.primitive_cube_add(
                size=0.0005,
                location=(x, y, 0)
            )
            if bpy.context is None:
                return False
            cube = bpy.context.active_object
            setattr(cube, 'name', f"Gerber_Point_{index:05d}")
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Point_Mat")
            mat.diffuse_color = (0.8, 0.8, 0.2, 1.0)  # 黄色
            
            if cube and cube.data and hasattr(cube.data, 'materials'):
                getattr(cube.data, 'materials')[0] = mat
            elif cube and cube.data:
                getattr(cube.data, 'materials').append(mat)
            
            self.created_objects.append(cube)
            return True
            
        except Exception as e:
            print(f"创建点失败: {e}")
            return False

# ============================================================================
# 清理操作符
# ============================================================================
class IMPORT_OT_clear_all_objects(Operator):
    """清理所有导入的对象"""
    bl_idname = "io_fritzing.clear_all_objects"
    bl_label = "清理所有导入的对象"
    bl_description = "清理所有导入的对象，提高性能"
    
    def execute(self, context):
        try:
            # 清理未使用的数据
            optimizer = PerformanceOptimizer()
            optimizer.clear_unused_data()
            
            # 统计清理前的对象数量
            meshes_before = len(bpy.data.meshes)
            materials_before = len(bpy.data.materials)
            
            # 清理集合
            collections_to_remove = []
            for collection in bpy.data.collections:
                if collection.name.startswith(("Gerber_", "Drill_", "PCB_")):
                    collections_to_remove.append(collection)
            
            for collection in collections_to_remove:
                # 删除集合中的所有对象
                for obj in collection.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                # 删除集合
                bpy.data.collections.remove(collection)
            
            # 清理独立的Gerber对象
            objects_to_remove = []
            for obj in bpy.data.objects:
                if obj.name.startswith(("Gerber_", "Drill_")):
                    objects_to_remove.append(obj)
            
            for obj in objects_to_remove:
                bpy.data.objects.remove(obj, do_unlink=True)
            
            # 强制垃圾回收
            gc.collect()
            
            # 统计清理后的对象数量
            meshes_after = len(bpy.data.meshes)
            materials_after = len(bpy.data.materials)
            
            message = f"清理完成: 删除了 {len(collections_to_remove)} 个集合, {len(objects_to_remove)} 个对象"
            message += f"\n网格减少: {meshes_before} -> {meshes_after}"
            message += f"\n材质减少: {materials_before} -> {materials_after}"
            
            self.report({'INFO'}, message)
            return {'FINISHED'}
            
        except Exception as e:
            error_msg = f"清理失败: {str(e)}"
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}

# ============================================================================
# 主导入操作符
# ============================================================================
class IMPORT_OT_gerber_fixed(Operator):
    """修复的Gerber导入"""
    bl_idname = "io_fritzing.import_gerber_file"
    bl_label = "导入Gerber文件"
    bl_description = "修复线段断开、Region尺寸和性能问题的导入"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="Gerber文件",
        subtype='FILE_PATH',
        default=""
    ) # type: ignore
    
    debug_mode: BoolProperty(
        name="调试模式",
        description="显示详细的调试信息",
        default=False
    ) # type: ignore
    
    optimize_performance: BoolProperty(
        name="性能优化",
        description="启用性能优化（批量处理和内存清理）",
        default=True
    ) # type: ignore
    
    def invoke(self, context, event):
        """调用对话框"""
        if not self.filepath or not os.path.exists(self.filepath):
            if context:
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
            parser = FixedGerberParser()
            result = parser.parse_gerber_fixed(self.filepath, debug=self.debug_mode)
            
            if not result.get('success', False):
                self.report({'ERROR'}, f"解析失败: {result.get('error', '未知错误')}")
                return {'CANCELLED'}
            
            # 创建主集合
            collection_name = os.path.basename(self.filepath).replace('.', '_')
            if collection_name.endswith('_'):
                collection_name = collection_name[:-1]
            collection_name = f"Gerber_{collection_name[:20]}"
            
            main_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(main_collection)

            result_stats = self._create_gerber_mesh_filled(
                result.get('primitives', []), 
                main_collection,
                result.get('unit_factor', 0.001)
            )
            
            # 报告结果
            message = f"导入完成: {result_stats['total_prims']}个图元, {result_stats['total_verts']}个顶点, {result_stats['total_faces']}个面"
            self.report({'INFO'}, message)
            print(f"导入结果: {message}")
            print(f"集合名称: {collection_name}")
            return {'FINISHED'}
            
        except Exception as e:
            error_msg = f"导入过程错误: {str(e)}"
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}

    def _create_gerber_mesh_filled(self, primitives, collection, unit_factor):
        """创建Gerber网格 - 2D填充模式核心函数"""
        stats = {
            'total_prims': len(primitives),
            'total_verts': 0,
            'total_faces': 0,
            'meshes_created': 0
        }
        
        print(f"开始创建Gerber网格: {len(primitives)} 个图元")
        print(f"单位转换比例: {unit_factor}")
        
        # 创建铜箔材质
        # copper_material = self._create_copper_material()
        
        # 将所有图元合并到一个网格中
        all_verts = []
        all_faces = []
        
        # 处理每个图元
        for i, prim in enumerate(primitives):
            if i < 5 or self.debug_mode:  # 显示前几个的调试信息
                print(f"  处理图元 {i+1}/{len(primitives)}: {prim.get('type', 'unknown')}")
            
            # 为每个图元创建网格数据
            verts, faces = self._create_mesh_from_primitive(prim, i, unit_factor)
            
            if verts and faces:
                # 调整面索引，因为我们要合并到同一个网格
                vert_offset = len(all_verts)
                for face in faces:
                    all_faces.append([v_idx + vert_offset for v_idx in face])
                
                all_verts.extend(verts)
                
                stats['total_verts'] += len(verts)
                stats['total_faces'] += len(faces)
        
        if not all_verts:
            print("警告: 没有创建任何网格数据")
            return stats
        
        # 创建合并后的网格
        mesh_name = f"Copper_Layer"
        mesh_data = bpy.data.meshes.new(mesh_name)
        mesh_data.from_pydata(all_verts, [], all_faces)
        mesh_data.update()
        
        # 创建网格对象
        mesh_obj = bpy.data.objects.new(mesh_name, mesh_data)
        # mesh_obj.data.materials.append(copper_material)
        
        # 确保对象是2D平面（Z坐标为0）
        mesh_obj.location.z = 0
        
        # 添加到集合
        collection.objects.link(mesh_obj)
        
        # 设置为活动对象
        bpy.context.view_layer.objects.active = mesh_obj
        mesh_obj.select_set(True)
        
        # 更新场景
        bpy.context.view_layer.update()
        
        # 视图调整
        # self._adjust_viewport(mesh_obj)
        
        stats['meshes_created'] = 1
        
        print(f"网格创建完成: {len(all_verts)}个顶点, {len(all_faces)}个面")
        print(f"网格尺寸: {mesh_obj.dimensions}")
        
        return stats

    def _create_mesh_from_primitive(self, prim, index, unit_factor):
        """从图元创建样条线"""
        prim_type = prim.get('type', '')
        
        try:
            if prim_type == 'line':
                return self._create_line_mesh(prim, index, unit_factor)
            elif prim_type == 'circle':
                return self._create_circle_mesh(prim, index, unit_factor)
            elif prim_type == 'rectangle':
                return self._create_rectangle_mesh(prim, index, unit_factor)
            elif prim_type == 'obround':
                return self._create_obround_mesh(prim, index, unit_factor)
            elif prim_type == 'region':
                return self._create_region_mesh(prim, index, unit_factor)
            else:
                return None
        except Exception as e:
            print(f"创建样条线 {index} 失败: {e}")
            return None
    
    def _create_line_mesh(self, line_data, index, unit_factor):
        """创建线段网格（有宽度的矩形）"""
        # 应用偏移和单位转换
        x1 = line_data.get('x1', 0) * unit_factor
        y1 = line_data.get('y1', 0) * unit_factor
        x2 = line_data.get('x2', 0) * unit_factor
        y2 = line_data.get('y2', 0) * unit_factor
        width = line_data.get('width', 0.1) * unit_factor
        
        # 计算线段方向和垂直方向
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < 0.000001 or width < 0.000001:  # 忽略过短的线段
            if self.debug_mode:
                print(f"    忽略过短线: 长度={length}, 宽度={width}")
            return [], []
        
        # 计算单位向量
        ux = dx / length
        uy = dy / length
        
        # 计算垂直向量
        vx = -uy * (width * 0.5)
        vy = ux * (width * 0.5)
        
        # 计算矩形的四个角点
        verts = [
            (x1 - vx, y1 - vy, 0.0),  # 左下
            (x1 + vx, y1 + vy, 0.0),  # 右下
            (x2 + vx, y2 + vy, 0.0),  # 右上
            (x2 - vx, y2 - vy, 0.0)   # 左上
        ]
        
        # 创建两个三角形面
        faces = [[0, 1, 2], [0, 2, 3]]

        # 在两个端点创建两个直径为线宽的圆
        circle_verts, circle_faces = self._create_line_terminal_circle_mesh(x1, y1, x2, y2, width/2)
        vert_offset = len(verts)
        for face in circle_faces:
            faces.append([v_idx + vert_offset for v_idx in face])
        verts.extend(circle_verts)

        if self.debug_mode and index < 5:
            print(f"    创建线段网格: 起点=({x1:.6f}, {y1:.6f}), 终点=({x2:.6f}, {y2:.6f}), 宽度={width:.6f}")
        
        return verts, faces
    
    def  _create_line_terminal_circle_mesh(self, x1, y1, x2, y2, radius):
        segments = 32
        
        # 1. 以(x1, y1)为圆心，radius为半径，创建一个圆
        verts = []
        faces = []

        # 中心点
        verts.append((x1, y1, 0.0))
        
        # 圆周上的点
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x1 + radius * math.cos(angle)
            py = y1 + radius * math.sin(angle)
            verts.append((px, py, 0.0))
        
        # 创建三角形扇
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([0, i + 1, next_i + 1])

        # 2. 以(x2, y2)为圆心，radius为半径，创建一个圆
        # 中心点
        verts.append((x2, y2, 0.0))
        
        # 圆周上的点
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x2 + radius * math.cos(angle)
            py = y2 + radius * math.sin(angle)
            verts.append((px, py, 0.0))
        
        # 创建三角形扇
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([segments + 1, i + 2 + segments, next_i + 2 + segments])
        
        return verts, faces
    
    def _create_circle_mesh(self, circle_data, index, unit_factor):
        """创建圆形网格（实心圆）"""
        x = circle_data.get('x', 0) * unit_factor
        y = circle_data.get('y', 0) * unit_factor
        radius = circle_data.get('radius', 0.05) * unit_factor
        
        if radius < 0.000001:  # 忽略过小的圆形
            if self.debug_mode:
                print(f"    忽略过小圆: 半径={radius}")
            return [], []
        
        # 创建圆形网格
        segments = 32
        verts = []
        faces = []
        
        # 中心点
        verts.append((x, y, 0.0))
        
        # 圆周上的点
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            verts.append((px, py, 0.0))
        
        # 创建三角形扇
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([0, i + 1, next_i + 1])
        
        if self.debug_mode and index < 5:
            print(f"    创建圆形网格: 中心=({x:.6f}, {y:.6f}), 半径={radius:.6f}")
        
        return verts, faces
    
    def _create_rectangle_mesh(self, rect_data, index, unit_factor):
        """创建矩形网格（实心矩形）"""
        x = rect_data.get('x', 0) * unit_factor
        y = rect_data.get('y', 0) * unit_factor
        width = rect_data.get('width', 0.1) * unit_factor
        height = rect_data.get('height', 0.1) * unit_factor
        
        if width < 0.000001 or height < 0.000001:  # 忽略过小的矩形
            if self.debug_mode:
                print(f"    忽略过小矩形: 宽度={width}, 高度={height}")
            return [], []
        
        # 计算矩形半宽高
        half_width = width * 0.5
        half_height = height * 0.5
        
        # 创建矩形顶点
        verts = [
            (x - half_width, y - half_height, 0.0),  # 左下
            (x + half_width, y - half_height, 0.0),  # 右下
            (x + half_width, y + half_height, 0.0),  # 右上
            (x - half_width, y + half_height, 0.0)   # 左上
        ]
        
        # 创建两个三角形面
        faces = [[0, 1, 2], [0, 2, 3]]
        
        if self.debug_mode and index < 5:
            print(f"    创建矩形网格: 中心=({x:.6f}, {y:.6f}), 大小={width:.6f}x{height:.6f}")
        
        return verts, faces
    
    def _create_obround_mesh(self, obround_data, index, unit_factor):
        """创建椭圆形网格（实心椭圆）"""
        x = obround_data.get('x', 0) * unit_factor
        y = obround_data.get('y', 0) * unit_factor
        width = obround_data.get('width', 0.1) * unit_factor
        height = obround_data.get('height', 0.1) * unit_factor
        
        if width < 0.000001 or height < 0.000001:  # 忽略过小的椭圆形
            if self.debug_mode:
                print(f"    忽略过小椭圆形: 宽度={width}, 高度={height}")
            return [], []
        
        # 计算半轴
        a = width * 0.5
        b = height * 0.5
        
        # 创建椭圆形网格
        segments = 32
        verts = []
        faces = []
        
        # 中心点
        verts.append((x, y, 0.0))
        
        # 椭圆上的点
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x + a * math.cos(angle)
            py = y + b * math.sin(angle)
            verts.append((px, py, 0.0))
        
        # 创建三角形扇
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([0, i + 1, next_i + 1])
        
        if self.debug_mode and index < 5:
            print(f"    创建椭圆形网格: 中心=({x:.6f}, {y:.6f}), 大小={width:.6f}x{height:.6f}")
        
        return verts, faces
    
    def _create_region_mesh(self, region_data, index, unit_factor):
        """创建区域网格（简单矩形区域）"""
        x = region_data.get('x', 0) * unit_factor
        y = region_data.get('y', 0) * unit_factor
        width = region_data.get('width', 0.1) * unit_factor
        height = region_data.get('height', 0.1) * unit_factor
        
        if width < 0.000001 or height < 0.000001:  # 忽略过小的区域
            if self.debug_mode:
                print(f"    忽略过小区域: 宽度={width}, 高度={height}")
            return [], []
        
        # 计算矩形半宽高
        half_width = width * 0.5
        half_height = height * 0.5
        
        # 创建矩形顶点
        verts = [
            (x - half_width, y - half_height, 0.0),  # 左下
            (x + half_width, y - half_height, 0.0),  # 右下
            (x + half_width, y + half_height, 0.0),  # 右上
            (x - half_width, y + half_height, 0.0)   # 左上
        ]
        
        # 创建两个三角形面
        faces = [[0, 1, 2], [0, 2, 3]]
        
        if self.debug_mode and index < 5:
            print(f"    创建区域网格: 中心=({x:.6f}, {y:.6f}), 大小={width:.6f}x{height:.6f}")
        
        return verts, faces


# ============================================================================
# 设置面板
# ============================================================================
class VIEW3D_PT_gerber_fixed(Panel):
    """Gerber导入设置面板 - 修复版"""
    bl_label = "Gerber导入"
    bl_idname = "VIEW3D_PT_gerber_fixed"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing工具"
    
    def draw(self, context):
        layout = self.layout
        if context is None:
            return
        scene = context.scene
        
        # 标题
        box = layout.box()
        box.label(text="Gerber文件导入", icon='IMPORT')
        
        # 文件选择
        row = box.row(align=True)
        row.prop(scene, "gerber_filepath", text="")
        row.operator("io_fritzing.browse_gerber_files",
                    text="", 
                    icon='FILEBROWSER')
        
        # 文件信息
        filepath = getattr(scene, "gerber_filepath")
        if filepath and os.path.exists(filepath):
            try:
                file_size = os.path.getsize(filepath)
                filename = os.path.basename(filepath)
                
                col = box.column(align=True)
                col.label(text=f"文件大小: {file_size/1024:.1f} KB", icon='INFO')
                col.label(text=f"文件名: {filename}", icon='FILE')
                col.label(text=f"文件类型: Gerber文件", icon='MESH_GRID')
            except:
                pass
        
        # 修复功能
        layout.separator()
        box = layout.box()
        box.label(text="修复功能", icon='TOOL_SETTINGS')
        
        col = box.column(align=True)
        col.label(text="✅ 线段: 连续连接", icon='SHADING_SOLID')
        col.label(text="✅ Region: 正确尺寸", icon='MESH_PLANE')
        col.label(text="✅ 性能: 批量处理", icon='SORTTIME')
        col.label(text="✅ 内存: 自动清理", icon='TRASH')
        
        # 导入选项
        layout.separator()
        box = layout.box()
        box.label(text="导入选项", icon='SETTINGS')
        box.prop(scene, "gerber_debug_mode", text="启用调试模式")
        box.prop(scene, "gerber_optimize_performance", text="启用性能优化")
        
        # 工具状态
        layout.separator()
        box = layout.box()
        box.label(text="工具状态", icon='INFO')
        
        if GERBER_LIB_AVAILABLE:
            box.label(text="✅ python-gerber: 可用", icon='CHECKMARK')
        else:
            box.label(text="❌ python-gerber: 不可用", icon='ERROR')
        
        if EXCELLON_LIB_AVAILABLE:
            box.label(text="✅ python-excellon: 可用", icon='CHECKMARK')
        else:
            box.label(text="❌ python-excellon: 不可用", icon='ERROR')
        
        # 导入按钮
        layout.separator()
        col = layout.column(align=True)
        
        if not GERBER_LIB_AVAILABLE:
            col.label(text="无法导入，缺少Gerber库", icon='ERROR')
            col.label(text="请确保pcb_tools已正确安装", icon='INFO')
            return
        
        filepath = getattr(scene, 'gerber_filepath', None)
        if filepath and os.path.exists(filepath):
            op = col.operator("io_fritzing.import_gerber_file", 
                             text="导入Gerber文件", 
                             icon='IMPORT')
            setattr(op, 'filepath', filepath)
            setattr(op, 'debug_mode', getattr(scene, 'gerber_debug_mode', False))
            setattr(op, 'optimize_performance', getattr(scene, 'gerber_optimize_performance'))
            
            col.separator()
            col.operator("io_fritzing.clear_all_objects", 
                        text="清理所有导入的对象", 
                        icon='TRASH')
        else:
            col.label(text="请先选择Gerber文件", icon='ERROR')

# ============================================================================
# 辅助操作符
# ============================================================================
class IMPORT_OT_browse_gerber_files(Operator):
    """浏览Gerber文件"""
    bl_idname = "io_fritzing.browse_gerber_files"
    bl_label = "浏览"
    
    filepath: StringProperty(name="Gerber文件",
        subtype='FILE_PATH',
        default=""
    ) # type: ignore

    filter_glob: StringProperty(
        default="*.gbr;*.ger;*.gbx;*.gtl;*.gbl;*.gto;*.gts;*.gtp;*.gm1;*.gko",
        options={'HIDDEN'}
    ) # type: ignore
    
    def invoke(self, context, event):
        if context:
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if self.filepath and context:
            setattr(context.scene, 'gerber_filepath', self.filepath)
        return {'FINISHED'}

# ============================================================================
# 注册
# ============================================================================
classes = [
    IMPORT_OT_gerber_fixed,
    IMPORT_OT_browse_gerber_files,
    IMPORT_OT_clear_all_objects,
    VIEW3D_PT_gerber_fixed,
]

def register():
    """注册插件"""
    print("注册Gerber修复导入插件...")
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ 注册类: {cls.__name__}")
        except Exception as e:
            print(f"❌ 注册类 {cls.__name__} 失败: {e}")
    
    # 注册场景属性
    setattr(Scene, 'gerber_filepath', StringProperty(
        name="Gerber File",
        description="Gerber文件路径",
        subtype='FILE_PATH',
        default=""
    ))
    
    setattr(Scene, 'gerber_debug_mode', BoolProperty(
        name="Gerber Debug Mode",
        description="启用调试模式显示详细信息",
        default=False
    ))
    
    setattr(Scene, 'gerber_optimize_performance', BoolProperty(
        name="Optimize Performance",
        description="启用性能优化",
        default=True
    ))
    
    print("✅ Gerber修复导入插件注册完成")

def unregister():
    """注销插件"""
    print("注销Gerber修复导入插件...")
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ 注销类: {cls.__name__}")
        except:
            pass

if __name__ == "__main__":
    register()
