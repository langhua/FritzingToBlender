"""
修复钻孔方向的Drill导入插件
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
# 增强的Drill文件解析器
# ============================================================================
class EnhancedDrillParser:
    """增强的Drill文件解析器"""
    
    def __init__(self):
        self.primitives = []
        self.file_info = {}
    
    def parse_drill_file(self, filepath, debug=False):
        """解析Drill文件"""
        if not EXCELLON_LIB_AVAILABLE:
            return {
                'success': False, 
                'error': '缺少python-excellon库',
                'install_hint': '请确保pcb_tools已正确安装'
            }
        
        try:
            print(f"🔍 开始解析Drill文件: {os.path.basename(filepath)}")
            start_time = time.time()
            
            # 读取Excellon文件
            drill = read_excellon(filepath)
            
            # 获取文件信息
            self.file_info = self._get_drill_info(drill, filepath)
            print(f"📄 Drill文件信息: {self.file_info}")
            
            # 提取钻孔
            self.primitives = self._extract_all_holes_enhanced(drill, debug)
            
            processing_time = time.time() - start_time
            
            # 统计图元类型
            type_stats = self._analyze_primitive_types()
            
            result = {
                'success': True,
                'file_type': 'drill',
                'file_info': self.file_info,
                'primitives': self.primitives,
                'primitive_count': len(self.primitives),
                'type_stats': type_stats,
                'processing_time': processing_time,
                'message': f"成功解析 {len(self.primitives)} 个钻孔"
            }
            
            print(f"\n📊 Drill解析统计:")
            print(f"  - 总钻孔数: {len(self.primitives)}")
            for prim_type, count in type_stats.items():
                print(f"  - {prim_type}: {count} 个")
            
            # 显示工具统计
            if 'tools' in self.file_info:
                print(f"\n🛠️ 工具统计:")
                for tool_id, tool in self.file_info['tools'].items():
                    if hasattr(tool, 'diameter'):
                        print(f"  - 工具 {tool_id}: 直径 {tool.diameter:.6f} inch")
            
            print(f"⏱️  耗时: {processing_time:.2f} 秒")
            return result
            
        except Exception as e:
            error_msg = f"解析Drill文件失败: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _get_drill_info(self, drill, filepath):
        """获取Drill文件信息"""
        info = {
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'units': drill.units if hasattr(drill, 'units') else 'inch',
            'layer_name': '钻孔层',
        }
        
        # 获取工具表
        if hasattr(drill, 'tools'):
            info['tools'] = {k: v for k, v in drill.tools.items()}
            info['tool_count'] = len(drill.tools)
        
        # 尝试多种方法获取边界框
        bounds = None
        
        # 方法1: 从bounds属性获取
        if hasattr(drill, 'bounds'):
            bounds = drill.bounds
        
        # 方法2: 从statements计算
        if not bounds and hasattr(drill, 'statements'):
            bounds = self._calculate_bounds_from_statements(drill)
        
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
        
        return info
    
    def _calculate_bounds_from_statements(self, drill):
        """从statements计算边界框"""
        try:
            positions = []
            
            if hasattr(drill, 'statements'):
                for stmt in drill.statements:
                    if hasattr(stmt, 'x') and hasattr(stmt, 'y'):
                        x, y = stmt.x, stmt.y
                        if x is not None and y is not None:
                            positions.append((x, y))
            
            if positions:
                x_coords = [p[0] for p in positions]
                y_coords = [p[1] for p in positions]
                return ((min(x_coords), min(y_coords)), (max(x_coords), max(y_coords)))
            
            return None
        except Exception as e:
            print(f"计算边界框失败: {e}")
            return None
    
    def _extract_all_holes_enhanced(self, drill, debug=False):
        """提取所有钻孔 - 增强版"""
        holes = []
        
        try:
            # 首先，让我们看看drill对象有哪些属性
            if debug:
                print(f"\n🔍 检查drill对象属性:")
                for attr in dir(drill):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(drill, attr)
                            if not callable(value):
                                print(f"  {attr}: {type(value).__name__} = {value}")
                        except:
                            pass
            
            # 方法1: 从holes属性提取
            if hasattr(drill, 'holes') and drill.holes:
                print(f"🔍 从holes属性提取钻孔: {len(drill.holes)} 个")
                
                for i, hole in enumerate(drill.holes):
                    hole_data = self._parse_hole_enhanced(hole, i, drill, debug and i < 5)
                    if hole_data:
                        holes.append(hole_data)
                
                if holes:
                    return holes
            
            # 方法2: 从statements提取
            if hasattr(drill, 'statements'):
                holes_from_statements = self._extract_holes_from_statements_enhanced(drill, debug)
                if holes_from_statements:
                    holes.extend(holes_from_statements)
                    return holes
            
            # 方法3: 从drills属性提取
            if hasattr(drill, 'drills') and drill.drills:
                print(f"🔍 从drills属性提取钻孔: {len(drill.drills)} 个")
                
                for i, hole in enumerate(drill.drills):
                    hole_data = self._parse_hole_enhanced(hole, i, drill, debug and i < 5)
                    if hole_data:
                        holes.append(hole_data)
                
                if holes:
                    return holes
            
            print("⚠️ 未找到钻孔数据")
            return []
            
        except Exception as e:
            print(f"❌ 提取钻孔失败: {e}")
            traceback.print_exc()
            return []
    
    def _extract_holes_from_statements_enhanced(self, drill, debug=False):
        """从statements提取钻孔 - 增强版"""
        holes = []
        
        try:
            if not hasattr(drill, 'statements'):
                return []
            
            print(f"🔍 从statements提取钻孔: {len(drill.statements)} 个语句")
            
            # 跟踪当前使用的工具
            current_tool = None
            
            # 记录每种工具的使用数量
            tool_usage = {}
            
            for i, stmt in enumerate(drill.statements):
                # 检查是否是工具选择语句
                if hasattr(stmt, 'tool'):
                    current_tool = stmt.tool
                    if debug and i < 10:
                        print(f"  🔧 语句 {i}: 选择工具 {current_tool}")
                
                # 检查是否是钻孔语句
                if hasattr(stmt, 'x') and hasattr(stmt, 'y'):
                    x, y = stmt.x, stmt.y
                    
                    if x is None or y is None:
                        if debug:
                            print(f"  ⚠️  语句 {i}: 忽略无效坐标 (x={x}, y={y})")
                        continue
                    
                    # 确定工具ID
                    tool_id = 'unknown'
                    if hasattr(stmt, 'tool') and stmt.tool is not None:
                        tool_id = stmt.tool
                    elif current_tool is not None:
                        tool_id = current_tool
                    
                    # 统计工具使用
                    tool_usage[tool_id] = tool_usage.get(tool_id, 0) + 1
                    
                    # 获取直径
                    diameter = 0.1  # 默认直径
                    
                    if hasattr(drill, 'tools') and tool_id in drill.tools:
                        tool = drill.tools[tool_id]
                        if hasattr(tool, 'diameter'):
                            diameter = tool.diameter
                        elif hasattr(tool, 'size'):
                            diameter = tool.size
                    
                    hole_data = {
                        'id': len(holes),
                        'type': 'drill',
                        'x': x,
                        'y': y,
                        'diameter': diameter,
                        'radius': diameter / 2,
                        'tool_id': tool_id,
                    }
                    holes.append(hole_data)
                    
                    if debug and len(holes) <= 5:
                        print(f"  🔍 从语句提取钻孔 {len(holes)}: 位置=({x:.6f}, {y:.6f}), 工具={tool_id}")
            
            print(f"✅ 从statements提取了 {len(holes)} 个钻孔")
            
            # 显示工具使用统计
            if tool_usage:
                print(f"\n📊 语句中工具使用统计:")
                for tool_id, count in tool_usage.items():
                    print(f"  - 工具 {tool_id}: {count} 个钻孔")
            
            return holes
            
        except Exception as e:
            print(f"❌ 从statements提取钻孔失败: {e}")
            traceback.print_exc()
            return []
    
    def _parse_hole_enhanced(self, hole, index, drill, debug=False):
        """增强解析钻孔"""
        try:
            # 获取位置
            x, y = 0, 0
            
            if hasattr(hole, 'position'):
                pos = hole.position
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(hole, 'x') and hasattr(hole, 'y'):
                x, y = hole.x, hole.y
            
            if x is None or y is None:
                if debug:
                    print(f"  ⚠️  钻孔 {index}: 忽略无效坐标 (x={x}, y={y})")
                return None
            
            # 获取工具
            tool_id = 'unknown'
            if hasattr(hole, 'tool'):
                tool_id = hole.tool
            
            # 获取直径
            diameter = 0.1  # 默认直径
            
            if hasattr(drill, 'tools'):
                # 尝试多种可能的工具ID格式
                tool_keys_to_try = []
                
                # 原始工具ID
                if tool_id in drill.tools:
                    tool_keys_to_try.append(tool_id)
                
                # 转换为字符串
                str_tool_id = str(tool_id)
                if str_tool_id in drill.tools:
                    tool_keys_to_try.append(str_tool_id)
                
                # 转换为整数
                try:
                    int_tool_id = int(tool_id)
                    if int_tool_id in drill.tools:
                        tool_keys_to_try.append(int_tool_id)
                except:
                    pass
                
                # 尝试所有可能的键
                for key in tool_keys_to_try:
                    tool = drill.tools[key]
                    if hasattr(tool, 'diameter'):
                        diameter = tool.diameter
                        break
                    elif hasattr(tool, 'size'):
                        diameter = tool.size
                        break
            
            if debug:
                print(f"  🔍 钻孔 {index}: 位置=({x:.6f}, {y:.6f}), 工具={tool_id}, 直径={diameter:.6f}")
            
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
# 修复钻孔方向的Drill几何生成器
# ============================================================================
class FixedOrientationDrillGenerator:
    """修复钻孔方向的Drill几何生成器"""
    
    def __init__(self):
        self.collection = None
        self.created_objects = []
    
    def create_drill_geometry(self, primitives, file_info, debug=False):
        """创建钻孔几何体"""
        if not primitives:
            print("⚠️ 没有钻孔数据，创建边界框")
            return self._create_bounding_box_only(file_info, "Drill_Empty")
        
        try:
            print(f"🛠️ 开始创建钻孔几何体，共 {len(primitives)} 个钻孔")
            
            # 获取单位转换因子
            units = file_info.get('units', 'inch')
            unit_factor = 0.0254 if units == 'inch' else 0.001
            print(f"📏 单位系统: {units}, 转换因子: {unit_factor}")
            
            # 生成唯一集合名称
            base_name = f"Drill_{os.path.basename(file_info['filename']).replace('.', '_')}"
            timestamp = int(time.time())
            final_name = f"{base_name}_{timestamp}"
            
            # 创建集合
            self._create_collection_safe(final_name)
            
            # 创建钻孔
            created_count = 0
            tool_stats = {}
            failed_indices = []
            
            for i, hole in enumerate(primitives):
                try:
                    if self._create_drill_hole_z_axis(hole, i, unit_factor, debug and i < 5):
                        created_count += 1
                        
                        # 统计工具使用
                        tool_id = hole.get('tool_id', 'unknown')
                        tool_stats[tool_id] = tool_stats.get(tool_id, 0) + 1
                    else:
                        failed_indices.append(i)
                except Exception as e:
                    print(f"❌ 创建钻孔 {i} 时失败: {e}")
                    failed_indices.append(i)
                
                # 显示进度
                if i % 20 == 0 and i > 0:
                    print(f"📊 钻孔进度: {i}/{len(primitives)}")
            
            # 显示失败统计
            if failed_indices:
                print(f"\n❌ 失败的钻孔索引: {failed_indices[:10]}... (共{len(failed_indices)}个)")
            
            # 显示工具统计
            if tool_stats:
                print(f"\n🛠️ 工具使用统计:")
                for tool_id, count in sorted(tool_stats.items()):
                    print(f"  - 工具 {tool_id}: {count} 个钻孔")
            
            result = {
                'success': True,
                'object_count': created_count,
                'failed_count': len(failed_indices),
                'collection': final_name,
                'message': f"创建了 {created_count} 个钻孔，{len(failed_indices)} 个失败"
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
    
    def _create_drill_hole_z_axis(self, hole, index, unit_factor, debug=False):
        """创建沿Z轴方向的钻孔"""
        try:
            x = hole.get('x', 0)
            y = hole.get('y', 0)
            diameter = hole.get('diameter', 0.1)  # 默认0.1 inch
            tool_id = hole.get('tool_id', 'unknown')
            
            # 检查坐标和直径是否有效
            if x is None or y is None:
                if debug:
                    print(f"  ⚠️  钻孔 {index}: 无效坐标 (x={x}, y={y})")
                return False
            
            if diameter is None:
                if debug:
                    print(f"  ⚠️  钻孔 {index}: 无效直径，使用默认值")
                diameter = 0.1
            
            # 转换单位
            x_m = x * unit_factor
            y_m = y * unit_factor
            diameter_m = diameter * unit_factor
            
            if diameter_m <= 0:
                if debug:
                    print(f"  ⚠️  钻孔 {index}: 无效直径 {diameter_m}，使用最小值")
                diameter_m = 0.000254  # 0.01mm
            
            radius_m = diameter_m / 2
            
            if debug:
                print(f"  🔧 创建钻孔 {index}:")
                print(f"    原始位置: ({x:.6f}, {y:.6f}) inch")
                print(f"    转换位置: ({x_m:.6f}, {y_m:.6f}, 0.001) m")
                print(f"    原始直径: {diameter:.6f} inch")
                print(f"    转换直径: {diameter_m:.6f} m")
                print(f"    工具ID: {tool_id}")
            
            # 方法1: 创建圆柱体表示钻孔 - 沿Z轴方向
            # 注意：圆柱体默认是沿着Z轴方向的
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=radius_m,
                depth=0.002,  # 厚度
                location=(x_m, y_m, 0)  # 在Z=0平面上
            )
            cylinder = bpy.context.active_object
            cylinder.name = f"Drill_{tool_id}_{index:05d}"
            
            # 方法2: 创建圆锥体表示钻孔（用于可视化区分）
            # 这种方法创建沿Z轴方向的圆锥体
            bpy.ops.mesh.primitive_cone_add(
                vertices=8,
                radius1=radius_m * 1.2,  # 顶部半径稍大
                radius2=radius_m,        # 底部半径
                depth=0.001,            # 高度
                location=(x_m, y_m, 0.001)  # 稍微抬起
            )
            cone = bpy.context.active_object
            cone.name = f"Drill_Cone_{tool_id}_{index:05d}"
            
            # 根据工具ID设置不同的颜色
            color = self._get_tool_color(tool_id)
            
            # 为圆柱体创建材质
            mat_cylinder = bpy.data.materials.new(name=f"Drill_Cylinder_{tool_id}_Mat")
            mat_cylinder.diffuse_color = color
            
            if cylinder.data.materials:
                cylinder.data.materials[0] = mat_cylinder
            else:
                cylinder.data.materials.append(mat_cylinder)
            
            # 为圆锥体创建材质（稍浅的颜色）
            color_cone = (color[0]*0.8, color[1]*0.8, color[2]*0.8, 1.0)
            mat_cone = bpy.data.materials.new(name=f"Drill_Cone_{tool_id}_Mat")
            mat_cone.diffuse_color = color_cone
            
            if cone.data.materials:
                cone.data.materials[0] = mat_cone
            else:
                cone.data.materials.append(mat_cone)
            
            # 链接到集合
            self.collection.objects.link(cylinder)
            self.collection.objects.link(cone)
            
            # 从场景集合中移除
            if cylinder.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(cylinder)
            if cone.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(cone)
            
            self.created_objects.append(cylinder)
            self.created_objects.append(cone)
            return True
            
        except Exception as e:
            print(f"❌ 创建钻孔 {index} 失败: {e}")
            traceback.print_exc()
            return False
    
    def _create_drill_hole_simple_z_axis(self, hole, index, unit_factor, debug=False):
        """简化的沿Z轴方向钻孔创建"""
        try:
            x = hole.get('x', 0)
            y = hole.get('y', 0)
            diameter = hole.get('diameter', 0.1)
            tool_id = hole.get('tool_id', 'unknown')
            
            if x is None or y is None:
                return False
            
            if diameter is None:
                diameter = 0.1
            
            # 转换单位
            x_m = x * unit_factor
            y_m = y * unit_factor
            diameter_m = diameter * unit_factor
            
            if diameter_m <= 0:
                diameter_m = 0.000254
            
            radius_m = diameter_m / 2
            
            # 创建圆柱体 - 默认沿Z轴
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=16,
                radius=radius_m,
                depth=0.002,
                location=(x_m, y_m, 0.001)  # 在Z轴方向
            )
            cylinder = bpy.context.active_object
            cylinder.name = f"Drill_{tool_id}_{index:05d}"
            
            # 创建材质
            color = self._get_tool_color(tool_id)
            mat = bpy.data.materials.new(name=f"Drill_{tool_id}_Mat")
            mat.diffuse_color = color
            
            if cylinder.data.materials:
                cylinder.data.materials[0] = mat
            else:
                cylinder.data.materials.append(mat)
            
            # 链接到集合
            self.collection.objects.link(cylinder)
            
            if cylinder.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(cylinder)
            
            self.created_objects.append(cylinder)
            return True
            
        except Exception as e:
            print(f"创建钻孔 {index} 失败: {e}")
            return False
    
    def _get_tool_color(self, tool_id):
        """根据工具ID获取颜色"""
        color_map = {
            '1': (0.8, 0.2, 0.2, 1.0),    # 红色
            '2': (0.2, 0.8, 0.2, 1.0),    # 绿色
            '3': (0.2, 0.2, 0.8, 1.0),    # 蓝色
            '100': (0.8, 0.8, 0.2, 1.0),  # 黄色
            '101': (0.8, 0.2, 0.8, 1.0),  # 紫色
            '102': (0.2, 0.8, 0.8, 1.0),  # 青色
            '103': (0.8, 0.5, 0.2, 1.0),  # 橙色
            '104': (0.5, 0.2, 0.8, 1.0),  # 深紫
            '105': (0.2, 0.5, 0.8, 1.0),  # 天蓝
            '106': (0.8, 0.2, 0.5, 1.0),  # 粉红
            '107': (0.5, 0.8, 0.2, 1.0),  # 黄绿
        }
        
        str_tool_id = str(tool_id)
        if str_tool_id in color_map:
            return color_map[str_tool_id]
        
        try:
            int_tool_id = int(tool_id)
            if str(int_tool_id) in color_map:
                return color_map[str(int_tool_id)]
        except:
            pass
        
        return (0.5, 0.5, 0.5, 1.0)  # 默认灰色
    
    def _create_bounding_box_only(self, file_info, collection_name):
        """只创建边界框"""
        try:
            if collection_name in bpy.data.collections:
                collection = bpy.data.collections[collection_name]
            else:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            
            bpy.ops.mesh.primitive_cube_add(size=0.05)
            cube = bpy.context.active_object
            cube.name = f"{collection_name}_Bounds"
            cube.location = (0, 0, 0)
            
            mat = bpy.data.materials.new(name="Drill_Bounds_Mat")
            mat.diffuse_color = (0.5, 0.5, 0.5, 0.3)
            
            if cube.data.materials:
                cube.data.materials[0] = mat
            else:
                cube.data.materials.append(mat)
            
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
class IMPORT_OT_drill_z_axis(Operator):
    """沿Z轴方向的Drill导入"""
    bl_idname = "io_fritzing.import_drill_z_axis"
    bl_label = "导入Drill文件（Z轴方向）"
    bl_description = "沿Z轴方向创建钻孔的导入"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="Drill文件",
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
            self.report({'ERROR'}, "请选择有效的Drill文件")
            return {'CANCELLED'}
        
        if not EXCELLON_LIB_AVAILABLE:
            self.report({'ERROR'}, "python-excellon库不可用")
            return {'CANCELLED'}
        
        try:
            # 使用之前的解析器
            parser = EnhancedDrillParser()  # 使用之前定义好的解析器
            result = parser.parse_drill_file(self.filepath, debug=self.debug_mode)
            
            if not result.get('success', False):
                self.report({'ERROR'}, f"解析失败: {result.get('error', '未知错误')}")
                return {'CANCELLED'}
            
            # 创建几何体
            generator = FixedOrientationDrillGenerator()
            primitives = result.get('primitives', [])
            file_info = result.get('file_info', {})
            
            create_result = generator.create_drill_geometry(
                primitives, 
                file_info,
                debug=self.debug_mode
            )
            
            if not create_result.get('success', False):
                self.report({'ERROR'}, f"创建几何体失败: {create_result.get('error', '未知错误')}")
                return {'CANCELLED'}
            
            message = f"导入完成: {create_result.get('object_count', 0)} 个钻孔"
            self.report({'INFO'}, message)
            return {'FINISHED'}
            
        except Exception as e:
            error_msg = f"导入过程错误: {str(e)}"
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}

# ============================================================================
# 设置面板
# ============================================================================
class VIEW3D_PT_drill_z_axis(Panel):
    """Drill导入设置面板 - Z轴方向"""
    bl_label = "Drill导入（Z轴方向）"
    bl_idname = "VIEW3D_PT_drill_z_axis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing工具"
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        
        # 标题
        box = layout.box()
        box.label(text="Drill文件导入（Z轴方向）", icon='IMPORT')
        
        # 文件选择
        row = box.row(align=True)
        row.prop(scene, "drill_file_z_axis", text="")
        row.operator("io_fritzing.browse_drill_z_axis", 
                    text="", 
                    icon='FILEBROWSER')
        
        # 文件信息
        if scene.drill_file_z_axis and os.path.exists(scene.drill_file_z_axis):
            try:
                file_size = os.path.getsize(scene.drill_file_z_axis)
                filename = os.path.basename(scene.drill_file_z_axis)
                
                col = box.column(align=True)
                col.label(text=f"文件大小: {file_size/1024:.1f} KB", icon='INFO')
                col.label(text=f"文件名: {filename}", icon='FILE')
                col.label(text=f"文件类型: 钻孔文件", icon='MESH_GRID')
                col.label(text=f"方向: 沿Z轴（垂直方向）", icon='ORIENTATION_GIMBAL')
            except:
                pass
        
        # 导入选项
        layout.separator()
        box = layout.box()
        box.label(text="导入选项", icon='SETTINGS')
        box.prop(scene, "drill_debug_mode_z_axis", text="启用调试模式")
        
        # 方向说明
        layout.separator()
        box = layout.box()
        box.label(text="钻孔方向说明", icon='ORIENTATION_GIMBAL')
        col = box.column(align=True)
        col.label(text="✅ 圆柱体沿Z轴方向")
        col.label(text="✅ 圆锥体沿Z轴方向")
        col.label(text="✅ 所有钻孔垂直于XY平面")
        
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
        
        # 支持的格式
        layout.separator()
        box = layout.box()
        box.label(text="支持的Drill格式", icon='FILE')
        
        col = box.column(align=True)
        col.label(text="Excellon钻孔文件:")
        col.label(text="  .drl, .txt, .drill")
        col.label(text="  .xln, .xlnx, .drd")
        
        # 导入按钮
        layout.separator()
        col = layout.column(align=True)
        
        if not EXCELLON_LIB_AVAILABLE:
            col.label(text="无法导入，缺少Excellon库", icon='ERROR')
            col.label(text="请确保pcb_tools已正确安装", icon='INFO')
            return
        
        if scene.drill_file_z_axis and os.path.exists(scene.drill_file_z_axis):
            op = col.operator("io_fritzing.import_drill_z_axis", 
                             text="导入Drill文件（Z轴方向）", 
                             icon='IMPORT')
            op.filepath = scene.drill_file_z_axis
            op.debug_mode = scene.drill_debug_mode_z_axis
        else:
            col.label(text="请先选择Drill文件", icon='ERROR')

# ============================================================================
# 辅助操作符
# ============================================================================
class IMPORT_OT_browse_drill_z_axis(Operator):
    """浏览Drill文件"""
    bl_idname = "io_fritzing.browse_drill_z_axis"
    bl_label = "浏览"
    
    filepath: StringProperty(subtype='FILE_PATH')
    filter_glob: StringProperty(
        default="*.drl;*.txt;*.drill;*.xln;*.xlnx;*.drd",
        options={'HIDDEN'}
    )
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if self.filepath:
            context.scene.drill_file_z_axis = self.filepath
        return {'FINISHED'}

# ============================================================================
# 注册
# ============================================================================
classes = [
    IMPORT_OT_drill_z_axis,
    IMPORT_OT_browse_drill_z_axis,
    VIEW3D_PT_drill_z_axis,
]

def register():
    """注册插件"""
    print("注册Drill Z轴方向导入插件...")
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ 注册类: {cls.__name__}")
        except Exception as e:
            print(f"❌ 注册类 {cls.__name__} 失败: {e}")
    
    # 注册场景属性
    Scene.drill_file_z_axis = StringProperty(
        name="Drill File",
        description="Drill文件路径",
        subtype='FILE_PATH',
        default=""
    )
    
    Scene.drill_debug_mode_z_axis = BoolProperty(
        name="Drill Debug Mode",
        description="启用调试模式显示详细信息",
        default=False
    )
    
    print("✅ Drill Z轴方向导入插件注册完成")

def unregister():
    """注销插件"""
    print("注销Drill Z轴方向导入插件...")
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ 注销类: {cls.__name__}")
        except:
            pass

if __name__ == "__main__":
    register()