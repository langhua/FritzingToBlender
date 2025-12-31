"""
Gerber完整导入插件 - 支持Gerber和Drill文件
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
# 设置pcb_tools路径
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
# PCB文件类型检测
# ============================================================================
class PCBAnalyzer:
    """PCB文件类型分析器"""
    
    @staticmethod
    def detect_file_type(filepath):
        """检测文件类型"""
        filename = os.path.basename(filepath).lower()
        
        # Gerber文件扩展名
        gerber_extensions = [
            '.gbr', '.ger', '.gbx', 
            '.gtl', '.gbl', '.gto', '.gts', '.gtp', '.gm1', '.gko',
            '.gtl1', '.gtl2', '.gbl1', '.gbl2',
            '.gto1', '.gto2', '.gts1', '.gts2',
            '.gtp1', '.gtp2', '.gm1', '.gm2', '.gko1', '.gko2'
        ]
        
        # Drill/Excellon文件扩展名
        drill_extensions = [
            '.drl', '.txt', '.drill', '.xln', '.xlnx',
            '.drd', '.drl1', '.drl2', '.txt1', '.txt2'
        ]
        
        # 检查扩展名
        _, ext = os.path.splitext(filename)
        
        if ext in gerber_extensions:
            return 'gerber'
        elif ext in drill_extensions:
            return 'drill'
        elif '_drill' in filename or '_drl' in filename:
            return 'drill'
        elif 'drill' in filename and ext in ['.txt', '.']:
            return 'drill'
        else:
            # 尝试读取文件内容判断
            try:
                with open(filepath, 'r') as f:
                    first_line = f.readline(100)
                    
                    # Excellon文件通常以";"开头或包含"%"
                    if first_line.startswith(';') or '%' in first_line:
                        return 'drill'
                    # Gerber文件通常以"%"开头
                    elif first_line.startswith('%'):
                        return 'gerber'
            except:
                pass
        
        return 'unknown'
    
    @staticmethod
    def get_layer_name(filename):
        """获取图层名称"""
        filename_lower = filename.lower()
        
        layer_map = {
            # Gerber层
            '.gtl': '顶层铜层',
            '.gbl': '底层铜层',
            '.gto': '顶层丝印',
            '.gts': '顶层阻焊',
            '.gtp': '顶层焊膏',
            '.gm1': '板框层',
            '.gko': '板框层',
            
            # 钻孔层
            '.drl': '钻孔层',
            '.txt': '钻孔层',
            '.drill': '钻孔层',
            
            # 其他
            'top': '顶层',
            'bottom': '底层',
            'front': '前层',
            'back': '后层',
            'inner': '内层',
            'silkscreen': '丝印层',
            'soldermask': '阻焊层',
            'paste': '焊膏层',
            'outline': '板框层',
            'drill': '钻孔层',
        }
        
        # 检查扩展名
        _, ext = os.path.splitext(filename_lower)
        if ext in layer_map:
            return layer_map[ext]
        
        # 检查文件名中的关键字
        for key, value in layer_map.items():
            if key in filename_lower and key not in ['.gtl', '.gbl', '.gto', '.gts', '.gtp', '.gm1', '.gko', '.drl', '.txt']:
                return value
        
        return '未知层'

# ============================================================================
# 通用PCB解析器
# ============================================================================
class UniversalPCBParser:
    """通用PCB文件解析器 - 支持Gerber和Drill"""
    
    def __init__(self):
        self.primitives = []
        self.file_info = {}
        self.file_type = 'unknown'
    
    def parse_file(self, filepath, debug=False):
        """解析PCB文件"""
        if not ALL_LIB_AVAILABLE:
            return {
                'success': False, 
                'error': '缺少必要的库',
                'install_hint': '请确保pcb_tools已正确安装'
            }
        
        try:
            print(f"🔍 开始解析文件: {os.path.basename(filepath)}")
            start_time = time.time()
            
            # 检测文件类型
            self.file_type = PCBAnalyzer.detect_file_type(filepath)
            print(f"📁 检测到的文件类型: {self.file_type}")
            
            # 根据文件类型调用相应的解析器
            if self.file_type == 'gerber' and GERBER_LIB_AVAILABLE:
                result = self._parse_gerber_file(filepath, debug)
            elif self.file_type == 'drill' and EXCELLON_LIB_AVAILABLE:
                result = self._parse_drill_file(filepath, debug)
            else:
                return {
                    'success': False,
                    'error': f'不支持的文件类型: {self.file_type}',
                    'hint': '请确保安装了相应的库'
                }
            
            processing_time = time.time() - start_time
            
            if result.get('success', False):
                result['processing_time'] = processing_time
                print(f"⏱️  耗时: {processing_time:.2f} 秒")
            else:
                result['processing_time'] = processing_time
            
            return result
            
        except Exception as e:
            error_msg = f"解析文件失败: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _parse_gerber_file(self, filepath, debug=False):
        """解析Gerber文件"""
        try:
            # 读取Gerber文件
            gerber = read(filepath)
            
            # 获取文件信息
            self.file_info = self._get_gerber_info(gerber, filepath)
            print(f"📄 Gerber文件信息: {self.file_info}")
            
            # 提取图元
            self.primitives = self._extract_gerber_primitives(gerber, debug)
            
            # 统计图元类型
            type_stats = self._analyze_primitive_types()
            
            result = {
                'success': True,
                'file_type': 'gerber',
                'file_info': self.file_info,
                'primitives': self.primitives,
                'primitive_count': len(self.primitives),
                'type_stats': type_stats,
                'message': f"成功解析 {len(self.primitives)} 个图元"
            }
            
            print(f"\n📊 Gerber解析统计:")
            print(f"  - 总图元数: {len(self.primitives)}")
            for prim_type, count in type_stats.items():
                print(f"  - {prim_type}: {count} 个")
            
            return result
            
        except Exception as e:
            error_msg = f"解析Gerber文件失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _parse_drill_file(self, filepath, debug=False):
        """解析Drill文件"""
        try:
            # 读取Excellon文件
            drill = read_excellon(filepath)
            
            # 获取文件信息
            self.file_info = self._get_drill_info(drill, filepath)
            print(f"📄 Drill文件信息: {self.file_info}")
            
            # 提取钻孔
            self.primitives = self._extract_drill_primitives(drill, debug)
            
            # 统计钻孔类型
            type_stats = self._analyze_primitive_types()
            
            result = {
                'success': True,
                'file_type': 'drill',
                'file_info': self.file_info,
                'primitives': self.primitives,
                'primitive_count': len(self.primitives),
                'type_stats': type_stats,
                'message': f"成功解析 {len(self.primitives)} 个钻孔"
            }
            
            print(f"\n📊 Drill解析统计:")
            print(f"  - 总钻孔数: {len(self.primitives)}")
            for prim_type, count in type_stats.items():
                print(f"  - {prim_type}: {count} 个")
            
            return result
            
        except Exception as e:
            error_msg = f"解析Drill文件失败: {str(e)}"
            print(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def _get_gerber_info(self, gerber, filepath):
        """获取Gerber文件信息"""
        info = {
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'units': gerber.units if hasattr(gerber, 'units') else 'metric',
            'layer_name': PCBAnalyzer.get_layer_name(os.path.basename(filepath)),
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
    
    def _get_drill_info(self, drill, filepath):
        """获取Drill文件信息"""
        info = {
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'units': drill.units if hasattr(drill, 'units') else 'metric',
            'layer_name': '钻孔层',
        }
        
        # 获取工具表
        if hasattr(drill, 'tools'):
            info['tools'] = {k: v for k, v in drill.tools.items()}
            info['tool_count'] = len(drill.tools)
        
        # 获取钻孔统计
        if hasattr(drill, 'drills'):
            info['drill_count'] = len(drill.drills) if drill.drills else 0
        
        # 获取边界框
        if hasattr(drill, 'bounds') and drill.bounds:
            try:
                bounds = drill.bounds
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
    
    def _extract_gerber_primitives(self, gerber, debug=False):
        """提取Gerber图元"""
        primitives = []
        
        try:
            if hasattr(gerber, 'primitives') and gerber.primitives:
                print(f"🔍 从primitives属性提取图元: {len(gerber.primitives)} 个")
                
                for i, primitive in enumerate(gerber.primitives):
                    primitive_data = self._parse_gerber_primitive(primitive, i)
                    if primitive_data:
                        primitives.append(primitive_data)
                
                return primitives
            
            return []
            
        except Exception as e:
            print(f"❌ 提取图元失败: {e}")
            return []
    
    def _parse_gerber_primitive(self, primitive, index):
        """解析Gerber图元"""
        try:
            class_name = primitive.__class__.__name__
            
            if class_name == 'Line':
                return self._parse_gerber_line(primitive, index)
            elif class_name == 'Circle':
                return self._parse_gerber_circle(primitive, index)
            elif class_name == 'Rectangle':
                return self._parse_gerber_rectangle(primitive, index)
            elif class_name == 'Obround':
                return self._parse_gerber_obround(primitive, index)
            elif class_name == 'Region':
                return self._parse_gerber_region(primitive, index)
            else:
                return self._parse_gerber_unknown(primitive, index)
        except Exception as e:
            print(f"❌ 解析图元 {index} 失败: {e}")
            return None
    
    def _parse_gerber_line(self, line, index):
        """解析Gerber线段"""
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
            }
        except Exception as e:
            print(f"解析线段失败: {e}")
            return None
    
    def _parse_gerber_circle(self, circle, index):
        """解析Gerber圆形"""
        try:
            position = getattr(circle, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            diameter = getattr(circle, 'diameter', 1.0)
            radius = diameter / 2
            
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
    
    def _parse_gerber_rectangle(self, rectangle, index):
        """解析Gerber矩形"""
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
            print(f"解析矩形失败: {e}")
            return None
    
    def _parse_gerber_obround(self, obround, index):
        """解析Gerber椭圆形"""
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
            print(f"解析椭圆形失败: {e}")
            return None
    
    def _parse_gerber_region(self, region, index):
        """解析Gerber区域"""
        try:
            bounding_box = getattr(region, 'bounding_box', ((0, 0), (0, 0)))
            min_x, min_y = bounding_box[0]
            max_x, max_y = bounding_box[1]
            
            return {
                'id': index,
                'type': 'region',
                'x': (min_x + max_x) / 2,
                'y': (min_y + max_y) / 2,
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y,
                'width': max_x - min_x,
                'height': max_y - min_y,
            }
        except Exception as e:
            print(f"解析区域失败: {e}")
            return None
    
    def _parse_gerber_unknown(self, primitive, index):
        """解析Gerber未知图元"""
        try:
            return {
                'id': index,
                'type': 'unknown',
                'x': 0,
                'y': 0,
            }
        except Exception as e:
            return None
    
    def _extract_drill_primitives(self, drill, debug=False):
        """提取钻孔"""
        primitives = []
        
        try:
            # 提取所有钻孔
            if hasattr(drill, 'drills') and drill.drills:
                print(f"🔍 从drills属性提取钻孔: {len(drill.drills)} 个")
                
                for i, hole in enumerate(drill.drills):
                    hole_data = self._parse_drill_hole(hole, i, drill)
                    if hole_data:
                        primitives.append(hole_data)
                
                return primitives
            
            return []
            
        except Exception as e:
            print(f"❌ 提取钻孔失败: {e}")
            return []
    
    def _parse_drill_hole(self, hole, index, drill):
        """解析单个钻孔"""
        try:
            # 获取位置
            if hasattr(hole, 'position'):
                position = hole.position
                if hasattr(position, '__len__') and len(position) >= 2:
                    x, y = position[0], position[1]
                else:
                    x, y = 0, 0
            else:
                x, y = 0, 0
            
            # 获取工具ID和直径
            tool_id = getattr(hole, 'tool', 'unknown')
            diameter = 0.1  # 默认直径
            
            if hasattr(drill, 'tools') and tool_id in drill.tools:
                tool = drill.tools[tool_id]
                if hasattr(tool, 'diameter'):
                    diameter = tool.diameter
                elif hasattr(tool, 'size'):
                    diameter = tool.size
            
            return {
                'id': index,
                'type': 'drill',
                'x': x,
                'y': y,
                'diameter': diameter,
                'radius': diameter / 2,
                'tool_id': tool_id,
            }
        except Exception as e:
            print(f"❌ 解析钻孔 {index} 失败: {e}")
            return None
    
    def _analyze_primitive_types(self):
        """分析图元类型统计"""
        type_stats = {}
        for primitive in self.primitives:
            prim_type = primitive.get('type', 'unknown')
            type_stats[prim_type] = type_stats.get(prim_type, 0) + 1
        return type_stats

# ============================================================================
# 通用PCB几何生成器
# ============================================================================
class UniversalPCBGenerator:
    """通用PCB几何生成器 - 支持Gerber和Drill"""
    
    def __init__(self):
        self.collection = None
        self.created_objects = []
    
    def create_pcb_geometry(self, primitives, file_info, file_type, debug=False):
        """创建PCB几何体"""
        if not primitives:
            print("⚠️ 没有图元数据，创建边界框")
            return self._create_bounding_box_only(file_info, "PCB_Empty")
        
        try:
            print(f"🛠️ 开始创建几何体，共 {len(primitives)} 个图元")
            print(f"📁 文件类型: {file_type}")
            
            # 获取单位转换因子
            units = file_info.get('units', 'metric')
            unit_factor = 0.0254 if units == 'inch' else 0.001
            print(f"📏 单位系统: {units}, 转换因子: {unit_factor}")
            
            # 生成唯一集合名称
            base_name = f"PCB_{os.path.basename(file_info['filename']).replace('.', '_')}"
            timestamp = int(time.time())
            final_name = f"{base_name}_{timestamp}"
            
            # 创建集合
            self._create_collection_safe(final_name)
            
            # 根据文件类型创建几何体
            created_count = 0
            
            if file_type == 'gerber':
                created_count = self._create_gerber_geometry(primitives, unit_factor, debug)
            elif file_type == 'drill':
                created_count = self._create_drill_geometry(primitives, unit_factor, debug)
            
            result = {
                'success': True,
                'object_count': created_count,
                'collection': final_name,
                'file_type': file_type,
                'message': f"创建了 {created_count} 个{file_type}对象"
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
            print(f"📁 创建集合: {name}")
            
        except Exception as e:
            print(f"创建集合失败: {e}")
    
    def _create_gerber_geometry(self, primitives, unit_factor, debug=False):
        """创建Gerber几何体"""
        created_count = 0
        
        for i, primitive in enumerate(primitives):
            if self._create_gerber_primitive(primitive, i, unit_factor, debug and i < 5):
                created_count += 1
            
            # 显示进度
            if i % 20 == 0 and i > 0:
                print(f"📊 Gerber进度: {i}/{len(primitives)}")
        
        return created_count
    
    def _create_gerber_primitive(self, primitive, index, unit_factor, debug=False):
        """创建Gerber图元"""
        primitive_type = primitive.get('type', 'unknown')
        
        try:
            if primitive_type == 'line':
                return self._create_line(primitive, index, unit_factor)
            elif primitive_type == 'circle':
                return self._create_circle(primitive, index, unit_factor)
            elif primitive_type == 'rectangle':
                return self._create_rectangle(primitive, index, unit_factor)
            elif primitive_type == 'obround':
                return self._create_obround(primitive, index, unit_factor)
            elif primitive_type == 'region':
                return self._create_region(primitive, index, unit_factor)
            else:
                return self._create_point(primitive, index, unit_factor)
        except Exception as e:
            print(f"创建图元 {index} 失败: {e}")
            return False
    
    def _create_drill_geometry(self, primitives, unit_factor, debug=False):
        """创建钻孔几何体"""
        created_count = 0
        
        for i, hole in enumerate(primitives):
            if self._create_drill_hole(hole, i, unit_factor, debug and i < 5):
                created_count += 1
            
            # 显示进度
            if i % 20 == 0 and i > 0:
                print(f"📊 Drill进度: {i}/{len(primitives)}")
        
        return created_count
    
    def _create_drill_hole(self, hole, index, unit_factor, debug=False):
        """创建钻孔"""
        try:
            x = hole.get('x', 0) * unit_factor
            y = hole.get('y', 0) * unit_factor
            diameter = hole.get('diameter', 0.001) * unit_factor
            radius = diameter / 2
            tool_id = hole.get('tool_id', 'unknown')
            
            if debug:
                print(f"  🔧 创建钻孔 {index}:")
                print(f"    位置: ({x:.6f}, {y:.6f})")
                print(f"    直径: {diameter:.6f}")
                print(f"    工具ID: {tool_id}")
            
            # 创建圆柱体表示钻孔
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=radius,
                depth=0.002,  # 较小的厚度
                location=(x, y, 0)
            )
            cylinder = bpy.context.active_object
            cylinder.name = f"Drill_{tool_id}_{index:05d}"
            
            # 旋转圆柱体使其在XY平面
            cylinder.rotation_euler.x = math.radians(90)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Drill_Hole_Mat")
            mat.diffuse_color = (0.1, 0.1, 0.1, 1.0)  # 深灰色
            
            if cylinder.data.materials:
                cylinder.data.materials[0] = mat
            else:
                cylinder.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(cylinder)
            
            # 从场景集合中移除
            if cylinder.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(cylinder)
            
            self.created_objects.append(cylinder)
            return True
            
        except Exception as e:
            print(f"创建钻孔失败: {e}")
            return False
    
    def _create_line(self, primitive, index, unit_factor):
        """创建线段"""
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
    
    def _create_circle(self, primitive, index, unit_factor):
        """创建圆形"""
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
    
    def _create_rectangle(self, primitive, index, unit_factor):
        """创建矩形"""
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
    
    def _create_obround(self, primitive, index, unit_factor):
        """创建椭圆形"""
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
    
    def _create_region(self, primitive, index, unit_factor):
        """创建区域"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            height = primitive.get('height', 0.001) * unit_factor
            
            # 创建平面表示区域
            bpy.ops.mesh.primitive_plane_add(
                size=1.0,
                location=(x, y, 0)
            )
            plane = bpy.context.active_object
            plane.name = f"Gerber_Region_{index:05d}"
            
            # 缩放
            plane.scale = (width, height, 1)
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Region_Mat")
            mat.diffuse_color = (0.2, 0.8, 0.8, 0.7)  # 青色，半透明
            
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
            print(f"创建区域失败: {e}")
            return False
    
    def _create_point(self, primitive, index, unit_factor):
        """创建点"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            
            # 创建立方体
            bpy.ops.mesh.primitive_cube_add(
                size=0.0005,
                location=(x, y, 0)
            )
            cube = bpy.context.active_object
            cube.name = f"Gerber_Point_{index:05d}"
            
            # 创建材质
            mat = bpy.data.materials.new(name="Gerber_Point_Mat")
            mat.diffuse_color = (0.8, 0.8, 0.2, 1.0)  # 黄色
            
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
            mat = bpy.data.materials.new(name="PCB_Bounds_Mat")
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
class IMPORT_OT_pcb_universal(Operator):
    """通用PCB导入"""
    bl_idname = "io_fritzing.import_pcb_universal"
    bl_label = "导入PCB文件（通用版）"
    bl_description = "支持Gerber和Drill文件的通用导入"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="PCB文件",
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
            self.report({'ERROR'}, "请选择有效的PCB文件")
            return {'CANCELLED'}
        
        if not ALL_LIB_AVAILABLE:
            self.report({'ERROR'}, "缺少必要的库")
            return {'CANCELLED'}
        
        try:
            # 解析PCB文件
            parser = UniversalPCBParser()
            result = parser.parse_file(self.filepath, debug=self.debug_mode)
            
            if not result.get('success', False):
                self.report({'ERROR'}, f"解析失败: {result.get('error', '未知错误')}")
                return {'CANCELLED'}
            
            # 创建几何体
            generator = UniversalPCBGenerator()
            primitives = result.get('primitives', [])
            file_info = result.get('file_info', {})
            file_type = result.get('file_type', 'unknown')
            
            create_result = generator.create_pcb_geometry(
                primitives, 
                file_info,
                file_type,
                debug=self.debug_mode
            )
            
            if not create_result.get('success', False):
                self.report({'ERROR'}, f"创建几何体失败: {create_result.get('error', '未知错误')}")
                return {'CANCELLED'}
            
            # 显示统计信息
            type_stats = result.get('type_stats', {})
            stats_text = ", ".join([f"{k}:{v}" for k, v in type_stats.items()])
            
            layer_name = file_info.get('layer_name', '未知层')
            message = f"导入完成 ({layer_name}): {create_result.get('object_count', 0)} 个对象 [{stats_text}]"
            
            self.report({'INFO'}, message)
            return {'FINISHED'}
            
        except Exception as e:
            error_msg = f"导入过程错误: {str(e)}"
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}

# ============================================================================
# 批量导入操作符
# ============================================================================
class IMPORT_OT_pcb_batch(Operator):
    """批量导入PCB文件"""
    bl_idname = "io_fritzing.import_pcb_batch"
    bl_label = "批量导入PCB文件"
    bl_description = "批量导入多个PCB文件"
    
    directory: StringProperty(subtype='FILE_PATH')
    files: bpy.props.CollectionProperty(type=bpy.types.OperatorFileListElement)
    filter_glob: StringProperty(
        default="*.gbr;*.ger;*.gbx;*.gtl;*.gbl;*.gto;*.gts;*.gtp;*.gm1;*.gko;"
                "*.drl;*.txt;*.drill;*.xln;*.xlnx;*.drd",
        options={'HIDDEN'}
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if not self.files:
            self.report({'ERROR'}, "没有选择文件")
            return {'CANCELLED'}
        
        if not ALL_LIB_AVAILABLE:
            self.report({'ERROR'}, "缺少必要的库")
            return {'CANCELLED'}
        
        imported_count = 0
        failed_files = []
        import_summary = []
        
        for file in self.files:
            filepath = os.path.join(self.directory, file.name)
            
            try:
                # 解析PCB文件
                parser = UniversalPCBParser()
                result = parser.parse_file(filepath, debug=False)
                
                if not result.get('success', False):
                    failed_files.append(f"{file.name}: {result.get('error', '未知错误')}")
                    continue
                
                # 创建几何体
                generator = UniversalPCBGenerator()
                primitives = result.get('primitives', [])
                file_info = result.get('file_info', {})
                file_type = result.get('file_type', 'unknown')
                
                create_result = generator.create_pcb_geometry(
                    primitives, 
                    file_info,
                    file_type,
                    debug=False
                )
                
                if create_result.get('success', False):
                    imported_count += 1
                    
                    # 记录导入摘要
                    layer_name = file_info.get('layer_name', '未知层')
                    object_count = create_result.get('object_count', 0)
                    import_summary.append(f"{file.name} ({layer_name}): {object_count} 个对象")
                    
                else:
                    failed_files.append(f"{file.name}: {create_result.get('error', '未知错误')}")
                    
            except Exception as e:
                failed_files.append(f"{file.name}: {str(e)}")
        
        # 显示结果
        if imported_count > 0:
            message = f"批量导入完成: 成功 {imported_count}/{len(self.files)} 个文件"
            if import_summary:
                message += "\n导入摘要:\n" + "\n".join([f"  - {summary}" for summary in import_summary])
            if failed_files:
                message += f"\n失败的文件: {', '.join(failed_files[:5])}"  # 只显示前5个失败的文件
            self.report({'INFO'}, message)
        else:
            self.report({'ERROR'}, f"所有文件导入失败")
        
        return {'FINISHED'}

# ============================================================================
# 设置面板
# ============================================================================
class VIEW3D_PT_pcb_universal(Panel):
    """PCB导入设置面板 - 通用版"""
    bl_label = "PCB导入（通用版）"
    bl_idname = "VIEW3D_PT_pcb_universal"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing工具"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 标题
        box = layout.box()
        box.label(text="PCB文件导入（通用版）", icon='IMPORT')
        
        # 文件选择
        row = box.row(align=True)
        row.prop(scene, "pcb_file_universal", text="")
        row.operator("io_fritzing.browse_pcb_universal", 
                    text="", 
                    icon='FILEBROWSER')
        
        # 文件信息
        if scene.pcb_file_universal and os.path.exists(scene.pcb_file_universal):
            try:
                file_size = os.path.getsize(scene.pcb_file_universal)
                filename = os.path.basename(scene.pcb_file_universal)
                
                col = box.column(align=True)
                col.label(text=f"文件大小: {file_size/1024:.1f} KB", icon='INFO')
                col.label(text=f"文件名: {filename}", icon='FILE')
                
                # 检测文件类型
                file_type = PCBAnalyzer.detect_file_type(scene.pcb_file_universal)
                layer_name = PCBAnalyzer.get_layer_name(filename)
                
                col.label(text=f"文件类型: {file_type}", icon='FILE_HIDDEN')
                col.label(text=f"图层: {layer_name}", icon='MESH_GRID')
            except:
                pass
        
        # 导入选项
        layout.separator()
        box = layout.box()
        box.label(text="导入选项", icon='SETTINGS')
        box.prop(scene, "pcb_debug_mode_universal", text="启用调试模式")
        
        # 工具状态
        layout.separator()
        box = layout.box()
        box.label(text="工具状态", icon='INFO')
        
        if GERBER_LIB_AVAILABLE:
            box.label(text="✅ python-gerber: 可用", icon='CHECKMARK')
        else:
            box.label(text="⚠️ python-gerber: 不可用", icon='ERROR')
        
        if EXCELLON_LIB_AVAILABLE:
            box.label(text="✅ python-excellon: 可用", icon='CHECKMARK')
        else:
            box.label(text="⚠️ python-excellon: 不可用", icon='ERROR')
        
        if not ALL_LIB_AVAILABLE:
            box.label(text="⚠️ 部分功能可能受限", icon='ERROR')
        
        # 支持的格式
        layout.separator()
        box = layout.box()
        box.label(text="支持的文件格式", icon='FILE')
        
        col = box.column(align=True)
        col.label(text="Gerber文件:")
        col.label(text="  .gbr, .ger, .gbx")
        col.label(text="  .gtl (顶层), .gbl (底层)")
        col.label(text="  .gto (丝印), .gts (阻焊)")
        col.label(text="  .gtp (焊膏), .gm1 (板框)")
        
        col.separator()
        col.label(text="Drill文件:")
        col.label(text="  .drl, .txt, .drill")
        col.label(text="  .xln, .xlnx, .drd")
        
        # 导入按钮
        layout.separator()
        col = layout.column(align=True)
        
        if not ALL_LIB_AVAILABLE:
            col.label(text="无法导入，缺少必要的库", icon='ERROR')
            col.label(text="请确保pcb_tools已正确安装", icon='INFO')
            return
        
        if scene.pcb_file_universal and os.path.exists(scene.pcb_file_universal):
            op = col.operator("io_fritzing.import_pcb_universal", 
                             text="导入PCB文件（通用版）", 
                             icon='IMPORT')
            op.filepath = scene.pcb_file_universal
            op.debug_mode = scene.pcb_debug_mode_universal
            
            col.separator()
            col.operator("io_fritzing.import_pcb_batch", 
                        text="批量导入多个PCB文件", 
                        icon='FILEBROWSER')
        else:
            col.label(text="请先选择PCB文件", icon='ERROR')

# ============================================================================
# 辅助操作符
# ============================================================================
class IMPORT_OT_browse_pcb_universal(Operator):
    """浏览PCB文件"""
    bl_idname = "io_fritzing.browse_pcb_universal"
    bl_label = "浏览"
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(
        default="*.gbr;*.ger;*.gbx;*.gtl;*.gbl;*.gto;*.gts;*.gtp;*.gm1;*.gko;"
                "*.drl;*.txt;*.drill;*.xln;*.xlnx;*.drd",
        options={'HIDDEN'}
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if self.filepath:
            context.scene.pcb_file_universal = self.filepath
        return {'FINISHED'}

# ============================================================================
# 清理操作符
# ============================================================================
class IMPORT_OT_clear_all_pcb(Operator):
    """清理所有PCB导入"""
    bl_idname = "io_fritzing.clear_all_pcb"
    bl_label = "清理所有PCB导入"
    
    def execute(self, context):
        # 查找并删除所有PCB相关的集合
        collections_to_remove = []
        
        for collection in bpy.data.collections:
            if (collection.name.startswith("PCB_") or 
                collection.name.startswith("Gerber_") or 
                collection.name.startswith("Drill_")):
                collections_to_remove.append(collection)
        
        for collection in collections_to_remove:
            # 删除集合中的所有对象
            for obj in collection.objects:
                bpy.data.objects.remove(obj, do_unlink=True)
            # 删除集合
            bpy.data.collections.remove(collection)
        
        message = f"清理了 {len(collections_to_remove)} 个PCB集合"
        self.report({'INFO'}, message)
        return {'FINISHED'}

# ============================================================================
# 注册
# ============================================================================
classes = [
    IMPORT_OT_pcb_universal,
    IMPORT_OT_pcb_batch,
    IMPORT_OT_browse_pcb_universal,
    IMPORT_OT_clear_all_pcb,
    VIEW3D_PT_pcb_universal,
]

def register():
    """注册插件"""
    print("注册PCB通用导入插件...")
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ 注册类: {cls.__name__}")
        except Exception as e:
            print(f"❌ 注册类 {cls.__name__} 失败: {e}")
    
    # 注册场景属性
    Scene.pcb_file_universal = StringProperty(
        name="PCB File",
        description="PCB文件路径",
        subtype='FILE_PATH',
        default=""
    )
    
    Scene.pcb_debug_mode_universal = BoolProperty(
        name="PCB Debug Mode",
        description="启用调试模式显示详细信息",
        default=False
    )
    
    print("✅ PCB通用导入插件注册完成")

def unregister():
    """注销插件"""
    print("注销PCB通用导入插件...")
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ 注销类: {cls.__name__}")
        except:
            pass

if __name__ == "__main__":
    register()