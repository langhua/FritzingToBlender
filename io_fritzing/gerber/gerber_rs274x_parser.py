import bpy
import os
import winsound
import math
import time
import glob
import traceback
from bpy.app.translations import pgettext
from bpy.types import Operator, Panel, Scene
from bpy.props import (StringProperty, BoolProperty, FloatProperty)
from bpy_extras.io_utils import ImportHelper
import gc
from pcb_tools.primitives import Line as Rs274x_Line
from pcb_tools import read
from ..assets.utils.material import create_material
from .excellon_parser import DrillParser, DrillGenerator
from .report import importdata, update as update_report

global gerber_fileinfo
gerber_fileinfo = dict()

global gerber_import_info
gerber_import_info = dict()

# ============================================================================
# Performance Optimization Tools
# ============================================================================
class PerformanceOptimizer:
    """Performance optimization utility class"""
    @staticmethod
    def batch_process(primitives, batch_size=50):
        """Batch process primitives to improve performance"""
        for i in range(0, len(primitives), batch_size):
            yield primitives[i:i + batch_size]
    
    @staticmethod
    def clear_unused_data():
        """Clean up unused data"""
        try:
            # Clean up unused meshes
            for mesh in bpy.data.meshes:
                if mesh.users == 0:
                    bpy.data.meshes.remove(mesh)
            
            # Clean up unused materials
            for mat in bpy.data.materials:
                if mat.users == 0:
                    bpy.data.materials.remove(mat)
            
            # Clean up unused curves
            for curve in bpy.data.curves:
                if curve.users == 0:
                    bpy.data.curves.remove(curve)
            
            # Force garbage collection
            gc.collect()
            
            print("🧹 Cleaned up unused data")
            return True
        except Exception as e:
            print(f"Failed to clean up data: {e}")
            return False

# ============================================================================
# Gerber Parser
# ============================================================================
class GerberParser:
    """Gerber file parser"""
    
    def __init__(self):
        self.primitives = []
        self.file_info = {}
    
    def parse_gerber(self, filepath, debug=False):
        try:
            print(f"🔍 Starting to parse Gerber file: {os.path.basename(filepath)}")
            start_time = time.time()
            
            # Read the Gerber file
            gerber = read(filepath)
            
            # Get units
            units = 'metric' if hasattr(gerber, 'units') and gerber.units == 'metric' else 'inch'
            unit_factor = 0.001 if units == 'metric' else 0.0254

            # Get file information
            self.file_info = self._get_gerber_info(gerber, filepath)
            print(f"📄 Gerber file info: {self.file_info}")
            
            # Extract primitives
            if hasattr(gerber, 'primitives'):
                for i, prim in enumerate(gerber.primitives):
                    prim_data = self._extract_primitive_data(prim, i, units)
                    if prim_data:
                        self.primitives.append(prim_data)

            processing_time = time.time() - start_time
            
            # Analyze primitive types
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
                'message': f"Successfully parsed {len(self.primitives)} primitives"
            }
            
            print(f"\n📊 Gerber parsing statistics:")
            print(f"  - Total primitives: {len(self.primitives)}")
            for prim_type, count in type_stats.items():
                print(f"  - {prim_type}: {count}")
            
            print(f"⏱️  Time taken: {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            error_msg = f"Failed to parse Gerber file: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _get_gerber_info(self, gerber, filepath):
        """Get Gerber file information"""
        info = {
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'units': gerber.units if hasattr(gerber, 'units') else 'metric',
        }
        
        # Get bounding box
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
                print(f"⚠️ Failed to get bounding box: {e}")
        
        return info
    
    def _extract_primitive_data(self, primitive, index, units):
        """Extract primitive data"""
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
                return None
                
        except Exception as e:
            print(f"Failed to extract data for primitive {index}: {e}")
            return None
    
    def _extract_line_data(self, line, index):
        """Extract line data"""
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
            
            # Get line width
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
            print(f"Failed to extract line data: {e}")
            return None
    
    def _extract_region_data(self, region, index):
        """Extract Region data"""
        try:
            # Get vertices
            primitives = region.primitives
            vertices = []
            for primitive in primitives:
                if isinstance(primitive, Rs274x_Line):
                    vertices.append(primitive.start)

            return {
                'type': 'region',
                'vertices': vertices
            }
        except Exception as e:
            print(f"Failed to extract Region data: {e}")
            return None
    
    def _extract_circle_data(self, circle, index):
        """Extract circle data"""
        try:
            # Try multiple possible attribute names
            x = 0
            y = 0
            radius = 0.001
            
            # Try various possible center coordinate attributes
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
            
            # Get radius
            if hasattr(circle, 'radius'):
                radius = circle.radius
            elif hasattr(circle, 'diameter'):
                radius = circle.diameter / 2

            result = {
                'type': 'circle',
                'x': x,
                'y': y,
                'radius': radius
            }

            # Get hole diameter, hole height, hole width
            if hasattr(circle, 'hole_diameter') and circle.hole_diameter > 0.0:
                result['hole_diameter'] = circle.hole_diameter
            if hasattr(circle, 'hole_height') and circle.hole_height > 0.0:
                result['hole_height'] = circle.hole_height
            if hasattr(circle, 'hole_width') and circle.hole_width > 0.0:
                result['hole_width'] = circle.hole_width

            return result
        except Exception as e:
            print(f"Failed to extract circle data: {e}")
            return None
    
    def _extract_rectangle_data(self, rectangle, index):
        """Extract rectangle data"""
        try:
            x = 0
            y = 0
            width = 0.001
            height = 0.001
            
            # Try various possible center coordinate attributes
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
            
            # Get dimensions
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
            print(f"Failed to extract rectangle data: {e}")
            return None
    
    def _extract_obround_data(self, obround, index):
        """Extract obround data"""
        try:
            x = 0
            y = 0
            width = 0.001
            height = 0.001
            
            # Try various possible center coordinate attributes
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
            
            # Get dimensions
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
            print(f"Failed to extract obround data: {e}")
            return None
    
    def _extract_primitives(self, gerber, debug=False):
        """Extract primitives"""
        primitives = []
        
        try:
            if hasattr(gerber, 'primitives') and gerber.primitives:
                print(f"🔍 Extracting primitives from primitives attribute: {len(gerber.primitives)}")
                
                for i, primitive in enumerate(gerber.primitives):
                    primitive_data = self._parse_primitive(primitive, i, debug and i < 5)
                    if primitive_data:
                        primitives.append(primitive_data)
                
                return primitives
            
            return []
            
        except Exception as e:
            print(f"❌ Failed to extract primitives: {e}")
            traceback.print_exc()
            return []
    
    def _parse_primitive(self, primitive, index, debug=False):
        """Parse a single primitive"""
        try:
            class_name = primitive.__class__.__name__
            
            if debug:
                print(f"  🔍 Parsing primitive {index}: {class_name}")
            
            if class_name == 'Line':
                return self._parse_line(primitive, index, debug)
            elif class_name == 'Circle':
                return self._parse_circle(primitive, index, debug)
            elif class_name == 'Rectangle':
                return self._parse_rectangle(primitive, index, debug)
            elif class_name == 'Obround':
                return self._parse_obround(primitive, index, debug)
            elif class_name == 'Region':
                return self._parse_region(primitive, index, debug)
            else:
                return self._parse_unknown(primitive, index, debug)
                
        except Exception as e:
            print(f"❌ Failed to parse primitive {index}: {e}")
            return None
    
    def _parse_line(self, line, index, debug=False):
        """Parse line"""
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
            
            # Get line width
            width = 0.001  # Default width
            
            # Try multiple methods to get width
            if hasattr(line, 'width'):
                width = line.width
            elif hasattr(line, 'aperture'):
                aperture = line.aperture
                if aperture and hasattr(aperture, 'width'):
                    width = aperture.width
                elif aperture and hasattr(aperture, 'diameter'):
                    width = aperture.diameter
            
            if debug:
                print(f"    Line: ({start_x:.3f}, {start_y:.3f}) -> ({end_x:.3f}, {end_y:.3f}), Width: {width:.6f}")
            
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
            print(f"Failed to parse line: {e}")
            return None
    
    def _parse_circle(self, circle, index, debug=False):
        """Parse circle"""
        try:
            position = getattr(circle, 'position', (0, 0))
            if hasattr(position, '__len__') and len(position) >= 2:
                x, y = position[0], position[1]
            else:
                x, y = 0, 0
            
            diameter = getattr(circle, 'diameter', 0.1)
            radius = diameter / 2
            
            if debug:
                print(f"    Circle: Center({x:.3f}, {y:.3f}), Diameter: {diameter:.6f}")
            
            return {
                'id': index,
                'type': 'circle',
                'x': x,
                'y': y,
                'radius': radius,
                'diameter': diameter,
            }
        except Exception as e:
            print(f"Failed to parse circle: {e}")
            return None
    
    def _parse_rectangle(self, rectangle, index, debug=False):
        """Parse rectangle"""
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
                print(f"    Rectangle: Center({x:.3f}, {y:.3f}), Size: {width:.6f}x{height:.6f}")
            
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
            print(f"Failed to parse rectangle: {e}")
            return None
    
    def _parse_obround(self, obround, index, debug=False):
        """Parse obround"""
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
                print(f"    Obround: Center({x:.3f}, {y:.3f}), Size: {width:.6f}x{height:.6f}")
            
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
            print(f"Failed to parse obround: {e}")
            return None
    
    def _parse_region(self, region, index, debug=False):
        """Parse region"""
        try:
            bounding_box = getattr(region, 'bounding_box', ((0, 0), (0, 0)))
            
            if bounding_box and len(bounding_box) >= 2:
                min_x, min_y = bounding_box[0]
                max_x, max_y = bounding_box[1]
                
                width = max_x - min_x
                height = max_y - min_y
                
                # Calculate center point
                center_x = (min_x + max_x) / 2
                center_y = (min_y + max_y) / 2
            else:
                min_x, min_y, max_x, max_y = 0, 0, 0, 0
                width, height = 0, 0
                center_x, center_y = 0, 0
            
            if debug:
                print(f"    Region: Bounding box({min_x:.3f}, {min_y:.3f}) -> ({max_x:.3f}, {max_y:.3f})")
                print(f"          Size: {width:.6f}x{height:.6f}")
            
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
            print(f"Failed to parse region: {e}")
            return None
    
    def _parse_unknown(self, primitive, index, debug=False):
        """Parse unknown primitive"""
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
        """Analyze primitive type statistics"""
        type_stats = {}
        for primitive in self.primitives:
            prim_type = primitive.get('type', 'unknown')
            type_stats[prim_type] = type_stats.get(prim_type, 0) + 1
        return type_stats

# ============================================================================
# Gerber Geometry Generator
# ============================================================================
class GerberGenerator:
    """Gerber geometry generator"""
    
    def __init__(self):
        self.collection = None
        self.created_objects = []
        self.optimizer = PerformanceOptimizer()
    
    def create_gerber_geometry(self, primitives, file_info, debug=False, optimize=True):
        """Create Gerber geometry"""
        if not primitives:
            print("⚠️ No primitive data")
            return {
                'success': True,
                'object_count': 0,
                'collection': None,
                'message': "No primitive data"
            }
        
        try:
            print(f"🛠️ Starting to create geometry for {len(primitives)} primitives")
            
            # Get unit conversion factor
            units = file_info.get('units', 'metric')
            unit_factor = 0.0254 if units == 'inch' else 0.001
            print(f"📏 Unit system: {units}, Conversion factor: {unit_factor}")
            
            # Generate unique collection name
            base_name = f"Gerber_{os.path.basename(file_info['filename']).replace('.', '_')}"
            timestamp = int(time.time())
            final_name = f"{base_name}_{timestamp}"
            
            # Create collection
            self._create_collection_safe(final_name)
            
            # Clean up memory
            if optimize:
                self.optimizer.clear_unused_data()
            
            # Batch process primitives
            created_count = 0
            batch_index = 0
            
            for batch in self.optimizer.batch_process(primitives, batch_size=50):
                print(f"📦 Processing batch {batch_index + 1}, Size: {len(batch)}")
                
                for primitive in batch:
                    if self._create_primitive(primitive, created_count, unit_factor, debug and created_count < 5):
                        created_count += 1
                
                batch_index += 1
                
                # Clean up memory
                if optimize and batch_index % 5 == 0:
                    self.optimizer.clear_unused_data()
            
            result = {
                'success': True,
                'object_count': created_count,
                'collection': final_name,
                'message': f"Created {created_count} objects"
            }
            
            print(f"\n✅ Geometry creation complete: {result['message']}")
            return result
            
        except Exception as e:
            error_msg = f"Failed to create geometry: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _create_collection_safe(self, name):
        """Safely create a collection"""
        try:
            # Create new collection
            self.collection = bpy.data.collections.new(name)
            if bpy.context:
                bpy.context.scene.collection.children.link(self.collection)
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[name]
                print(f"📁 Created collection: {name}")
        except Exception as e:
            print(f"Failed to create collection: {e}")
    
    def _create_primitive(self, primitive, index, unit_factor, debug=False):
        """Create a primitive"""
        primitive_type = primitive.get('type', 'unknown')
        
        try:
            if primitive_type == 'line':
                return self._create_line_connected(primitive, index, unit_factor, debug)
            elif primitive_type == 'circle':
                return self._create_circle(primitive, index, unit_factor, debug)
            elif primitive_type == 'rectangle':
                return self._create_rectangle(primitive, index, unit_factor, debug)
            elif primitive_type == 'obround':
                return self._create_obround(primitive, index, unit_factor, debug)
            elif primitive_type == 'region':
                return self._create_region(primitive, index, unit_factor, True)
            else:
                return self._create_point(primitive, index, unit_factor, debug)
        except Exception as e:
            print(f"Failed to create primitive {index}: {e}")
            return False
    
    def _create_line_connected(self, primitive, index, unit_factor, debug=False):
        """Create a connected line"""
        try:
            start_x = primitive.get('start_x', 0) * unit_factor
            start_y = primitive.get('start_y', 0) * unit_factor
            end_x = primitive.get('end_x', 0) * unit_factor
            end_y = primitive.get('end_y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            
            if debug:
                print(f"  🔧 Creating connected line {index}:")
                print(f"    Start: ({start_x:.6f}, {start_y:.6f})")
                print(f"    End: ({end_x:.6f}, {end_y:.6f})")
                print(f"    Width: {width:.6f}")
            
            # Calculate line direction and length
            dx = end_x - start_x
            dy = end_y - start_y
            length = math.sqrt(dx*dx + dy*dy)
            
            if length == 0:
                return False
            
            # Create a thick line (rectangle)
            # Calculate the four corners of the rectangle
            half_width = width / 2
            
            # Calculate perpendicular direction
            if dx == 0:
                # Vertical line
                perp_x = half_width
                perp_y = 0
            elif dy == 0:
                # Horizontal line
                perp_x = 0
                perp_y = half_width
            else:
                # Diagonal line
                # Calculate perpendicular vector
                perp_length = math.sqrt(dx*dx + dy*dy)
                perp_x = -dy * half_width / perp_length
                perp_y = dx * half_width / perp_length
            
            # Create rectangle vertices
            vertices = [
                (start_x - perp_x, start_y - perp_y, 0),  # Start bottom-left
                (start_x + perp_x, start_y + perp_y, 0),  # Start bottom-right
                (end_x + perp_x, end_y + perp_y, 0),     # End top-right
                (end_x - perp_x, end_y - perp_y, 0),     # End top-left
            ]
            
            # Create face
            faces = [(0, 1, 2, 3)]
            
            # Create mesh
            mesh = bpy.data.meshes.new(f"Gerber_Line_Conn_{index:05d}")
            mesh.from_pydata(vertices, [], faces)
            mesh.update()
            
            # Create object
            line_obj = bpy.data.objects.new(f"Gerber_Line_Conn_{index:05d}", mesh)
            
            try:
                if self.collection:
                    self.collection.objects.link(line_obj)
            except:
                pass

            self.created_objects.append(line_obj)
            return True
            
        except Exception as e:
            print(f"Failed to create connected line: {e}")
            return False
    
    def _create_circle(self, primitive, index, unit_factor, debug=False):
        """Create a circle"""
        if bpy.context is None:
            return False

        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            diameter = primitive.get('diameter', 0.001) * unit_factor
            radius = diameter / 2
            
            if diameter <= 0:
                if debug:
                    print(f"  ⚠️  Circle {index}: Invalid diameter {diameter}")
                return False
            
            if debug:
                print(f"  🔧 Creating circle {index}:")
                print(f"    Center: ({x:.6f}, {y:.6f})")
                print(f"    Diameter: {diameter:.6f}")
            
            # Create circle
            bpy.ops.mesh.primitive_circle_add(
                vertices=32,
                radius=radius,
                fill_type='NGON',
                location=(x, y, 0)
            )
            circle = bpy.context.active_object
            if circle:
                circle.name = f"Gerber_Circle_{index:05d}"
            
            # Link to collection
            if circle and self.collection:
                self.collection.objects.link(circle)
            
            # Remove from scene collection
            if circle and circle.name in bpy.context.scene.collection.objects:
                bpy.context.scene.collection.objects.unlink(circle)
            
            self.created_objects.append(circle)
            return True
            
        except Exception as e:
            print(f"Failed to create circle: {e}")
            return False
    
    def _create_rectangle(self, primitive, index, unit_factor, debug=False):
        """Create a rectangle"""
        if bpy.context is None:
            return False

        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            height = primitive.get('height', 0.001) * unit_factor
            rotation = primitive.get('rotation', 0)
            
            if width <= 0 or height <= 0:
                if debug:
                    print(f"  ⚠️  Rectangle {index}: Invalid dimensions {width}x{height}")
                return False
            
            if debug:
                print(f"  🔧 Creating rectangle {index}:")
                print(f"    Center: ({x:.6f}, {y:.6f})")
                print(f"    Size: {width:.6f}x{height:.6f}")
            
            # Create plane
            bpy.ops.mesh.primitive_plane_add(
                size=1.0,
                location=(x, y, 0)
            )
            plane = bpy.context.active_object
            if plane:
                plane.name = f"Gerber_Rect_{index:05d}"
            
                # Rotate
                if rotation != 0:
                    plane.rotation_euler.z = math.radians(rotation)
                
                # Scale
                plane.scale = (width, height, 1)
            
            self.created_objects.append(plane)
            return True
            
        except Exception as e:
            print(f"Failed to create rectangle: {e}")
            return False
    
    def _create_obround(self, primitive, index, unit_factor, debug=False):
        """Create an obround"""
        if bpy.context is None:
            return False

        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0.001) * unit_factor
            height = primitive.get('height', 0.001) * unit_factor
            rotation = primitive.get('rotation', 0)
            
            if width <= 0 or height <= 0:
                if debug:
                    print(f"  ⚠️  Obround {index}: Invalid dimensions {width}x{height}")
                return False
            
            if debug:
                print(f"  🔧 Creating obround {index}:")
                print(f"    Center: ({x:.6f}, {y:.6f})")
                print(f"    Size: {width:.6f}x{height:.6f}")
            
            # Create circle
            radius = min(width, height) / 2
            bpy.ops.mesh.primitive_circle_add(
                vertices=32,
                radius=radius,
                fill_type='NGON',
                location=(x, y, 0)
            )
            circle = bpy.context.active_object
            if circle:
                circle.name = f"Gerber_Obround_{index:05d}"
                # Rotate
                if rotation != 0:
                    circle.rotation_euler.z = math.radians(rotation)
                # Scale to obround
                if width != height:
                    circle.scale = (width/height, 1, 1)
            
            self.created_objects.append(circle)
            return True
            
        except Exception as e:
            print(f"Failed to create obround: {e}")
            return False
    
    def _create_region(self, primitive, index, unit_factor, debug=False):
        """Create a region"""
        if bpy.context is None:
            return False

        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            width = primitive.get('width', 0) * unit_factor
            height = primitive.get('height', 0) * unit_factor
            is_valid = primitive.get('is_valid', False)
            
            if not is_valid or width <= 0 or height <= 0:
                if debug:
                    print(f"  ⚠️  Region {index}: Invalid dimensions {width}x{height}")
                return False
            
            if debug:
                print(f"  🔧 Creating region {index}:")
                print(f"    Center: ({x:.6f}, {y:.6f})")
                print(f"    Size: {width:.6f}x{height:.6f}")
            
            # Create smaller region (1/10 of original size to avoid being too large)
            scale_factor = 0.1
            scaled_width = width * scale_factor
            scaled_height = height * scale_factor
            
            # Create plane to represent region
            bpy.ops.mesh.primitive_plane_add(
                size=1.0,
                location=(x, y, 0)
            )
            plane = bpy.context.active_object
            if plane:
                plane.name = f"Gerber_Region_{index:05d}"
                # Scale
                plane.scale = (scaled_width, scaled_height, 1)
            
            self.created_objects.append(plane)
            return True
            
        except Exception as e:
            print(f"Failed to create region: {e}")
            return False
    
    def _create_point(self, primitive, index, unit_factor, debug=False):
        """Create a point"""
        try:
            x = primitive.get('x', 0) * unit_factor
            y = primitive.get('y', 0) * unit_factor
            
            # Create cube
            bpy.ops.mesh.primitive_cube_add(
                size=0.0005,
                location=(x, y, 0)
            )
            if bpy.context is None:
                return False
            cube = bpy.context.active_object
            setattr(cube, 'name', f"Gerber_Point_{index:05d}")
            
            self.created_objects.append(cube)
            return True
            
        except Exception as e:
            print(f"Failed to create point: {e}")
            return False

# ============================================================================
# Clear Operator
# ============================================================================
class IMPORT_OT_clear_all_objects(Operator):
    """Clear all imported objects"""
    bl_idname = "io_fritzing.clear_all_objects"
    bl_label = "Clear All Imported Objects"
    bl_description = "Clear all imported objects to improve performance"
    
    def execute(self, context):
        try:
            # Clean up unused data
            optimizer = PerformanceOptimizer()
            optimizer.clear_unused_data()
            
            # Count objects before cleanup
            meshes_before = len(bpy.data.meshes)
            materials_before = len(bpy.data.materials)
            
            # Clean up collections
            collections_to_remove = []
            for collection in bpy.data.collections:
                if collection.name.startswith(("Gerber_", "Drill_", "PCB_")):
                    collections_to_remove.append(collection)
            
            for collection in collections_to_remove:
                # Delete all objects in the collection
                for obj in collection.objects:
                    bpy.data.objects.remove(obj, do_unlink=True)
                # Delete the collection
                bpy.data.collections.remove(collection)
            
            # Clean up standalone Gerber objects
            objects_to_remove = []
            for obj in bpy.data.objects:
                if obj.name.startswith(("Gerber_", "Drill_")):
                    objects_to_remove.append(obj)
            
            for obj in objects_to_remove:
                bpy.data.objects.remove(obj, do_unlink=True)
            
            # Force garbage collection
            gc.collect()
            
            # Count objects after cleanup
            meshes_after = len(bpy.data.meshes)
            materials_after = len(bpy.data.materials)
            
            message = pgettext("Cleanup complete: Deleted {collections_to_remove} collections, {objects_to_remove} objects").format(collections_to_remove = len(collections_to_remove), objects_to_remove = len(objects_to_remove))
            message += pgettext(" Meshes reduced: {meshes_before} -> {meshes_after}").format(meshes_before = meshes_before, meshes_after = meshes_after)
            message += pgettext(" Materials reduced: {materials_before} -> {materials_after}").format(materials_before = materials_before, materials_after = materials_after)
            
            self.report({'INFO'}, message)
            return {'FINISHED'}
            
        except Exception as e:
            error_msg = pgettext("Cleanup failed: {error}").format(error = str(e))
            self.report({'ERROR'}, error_msg)
            return {'CANCELLED'}

# ============================================================================
# Main Import Operator
# ============================================================================
class IMPORT_OT_gerber(Operator):
    """Import Gerber Folder"""
    bl_idname = "io_fritzing.import_gerber_file"
    bl_label = "Import Gerber Folder"
    bl_description = "Import Gerber Folder"
    bl_options = {'REGISTER', 'UNDO'}
    bl_order = 1
    
    debug_mode: BoolProperty(
        name="Debug mode",
        description="Output debug information in console",
        default=False
    ) # type: ignore
    
    optimize_performance: BoolProperty(
        name="Optimize performance",
        description="Enable performance optimization (batch processing and memory cleanup)",
        default=True
    ) # type: ignore
    
    def invoke(self, context, event):
        """Invoke dialog"""
        global gerber_fileinfo
        if not gerber_fileinfo or len(gerber_fileinfo) == 0:
            if context:
                context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return self.execute(context)
    
    def execute(self, context):
        """Execute import"""
        global gerber_fileinfo

        main_collection = None
        import_success = 0
        for layer_name, file_info in gerber_fileinfo.items():
            filepath = file_info['filepath']
            if not filepath or not os.path.exists(filepath):
                continue
            if bpy.context is None:
                continue

            if main_collection is None:
                # Create main collection
                cut = filepath.rindex(os.path.sep[0])
                directory = filepath[0:cut]
                collection_name = os.path.basename(directory).replace('.', '_')
                if collection_name.endswith('_'):
                    collection_name = collection_name[:-1]
                collection_name = f"Gerber_{collection_name[:20]}"
                
                main_collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(main_collection)
                bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]

            try:
                if layer_name == 'drill':
                    parser = DrillParser()
                    result = parser.parse_drill_file(filepath, debug=self.debug_mode)
                    
                    if not result.get('success', False):
                        self.report({'ERROR'}, pgettext("Parse failed: ") + result.get('error', pgettext('Unknown error')))
                        return {'CANCELLED'}
                    
                    # Create geometry
                    generator = DrillGenerator()
                    primitives = result.get('primitives', [])
                    file_info = result.get('file_info', {})
                    height = importdata.board_thickness + 0.0002
                    
                    create_result = generator.create_drill_geometry(layer_name,
                        main_collection,
                        primitives, 
                        file_info,
                        height=height,
                        debug=self.debug_mode
                    )
                    
                    if not create_result.get('success', False):
                        self.report({'ERROR'}, pgettext("Geometry creation failed: {create_result_error}").format(create_result_error = create_result.get('error', pgettext('Unknown error'))))
                        return {'CANCELLED'}
                    
                    message = pgettext("Import complete: {object_count)} drills").format(object_count = create_result.get('object_count', 0))
                    self.report({'INFO'}, message)
                    import_success += 1

                else:
                    # Parse Gerber RS-274X file
                    parser = GerberParser()
                    result = parser.parse_gerber(filepath, debug=self.debug_mode)
                    
                    if not result.get('success', False):
                        self.report({'ERROR'}, pgettext("Parse failed: ") + result.get('error', pgettext('Unknown error')))
                        return {'CANCELLED'}
                    
                    result_stats = _create_gerber_mesh_filled(layer_name,
                        result.get('primitives', []), 
                        main_collection,
                        result.get('unit_factor', 0.001)
                    )
                    
                    # Report result
                    message = pgettext("Import complete: {total_prims} primitives, {total_verts} vertices, {total_faces} faces").format(total_prims=result_stats['total_prims'], total_verts=result_stats['total_verts'], total_faces=result_stats['total_faces'])
                    self.report({'INFO'}, message)
                    print(f"Import result: {message}")
                    print(f"Collection name: {collection_name}")
                    if result_stats.get('success', False):
                        import_success += 1
                
            except Exception as e:
                error_msg = pgettext("Import process error: {error}").format(error = str(e))
                self.report({'ERROR'}, error_msg)

        if import_success == len(gerber_fileinfo.items()) and context:
            setattr(context.scene, 'gerber_import_issuccess', True)

        if os.name == 'nt':
            frequency = 1500
            # Set Duration To 1000 ms == 1 second
            duration = 1000
            winsound.Beep(frequency, duration)

        return {'FINISHED'}


# ============================================================================
# Gerber 2D Primitive Parsing
# ============================================================================
def _create_gerber_mesh_filled(layer_name, primitives, collection, unit_factor, debug_mode=False):
    """Create Gerber mesh - 2D filled mode core function"""
    stats = {
        'total_prims': len(primitives),
        'total_verts': 0,
        'total_faces': 0,
        'meshes_created': 0,
        'success': False
    }
    if bpy.context is None:
        print("Warning: Must be run in Blender")
        return stats
    
    print(f"Starting to create Gerber mesh: {len(primitives)} primitives")
    print(f"Unit conversion factor: {unit_factor}")
    
    # Merge all primitives into one mesh
    all_verts = []
    all_faces = []
    
    # Process each primitive
    for i, prim in enumerate(primitives):
        if i < 5 or debug_mode:  # Show debug info for the first few
            print(f"  Processing primitive {i+1}/{len(primitives)}: {prim.get('type', 'unknown')}")
        
        # Create mesh data for each primitive
        verts, faces = _create_mesh_from_primitive(prim, i, unit_factor, debug_mode)
        
        if verts and faces:
            # Adjust face indices because we're merging into the same mesh
            vert_offset = len(all_verts)
            for face in faces:
                all_faces.append([v_idx + vert_offset for v_idx in face])
            
            all_verts.extend(verts)
            
            stats['total_verts'] += len(verts)
            stats['total_faces'] += len(faces)
    
    if not all_verts:
        print("Warning: No mesh data created")
        return stats
    
    # Create merged mesh
    mesh_data = bpy.data.meshes.new(layer_name)
    mesh_data.from_pydata(all_verts, [], all_faces)
    mesh_data.update()
    
    # Create mesh object
    mesh_obj = bpy.data.objects.new(layer_name, mesh_data)
    
    # Ensure object is a 2D plane (Z coordinate is 0)
    mesh_obj.location.z = 0
    
    # Add to collection
    collection.objects.link(mesh_obj)
    
    # Set as active object
    bpy.context.view_layer.objects.active = mesh_obj
    mesh_obj.select_set(True)
    stats['mesh_obj'] = mesh_obj
    
    # Update scene
    bpy.context.view_layer.update()
    
    stats['meshes_created'] = 1
    
    print(f"Mesh creation complete: {len(all_verts)} vertices, {len(all_faces)} faces")
    print(f"Mesh dimensions: {mesh_obj.dimensions}")

    stats['success'] = True
    
    return stats

def _create_mesh_from_primitive(prim, index, unit_factor, debug_mode=False):
    """Create spline from primitive"""
    try:
        prim_type = prim.get('type', '')
        if prim_type == 'line':
            return _create_line_mesh(prim, index, unit_factor, debug_mode)
        elif prim_type == 'circle':
            return _create_circle_mesh(prim, index, unit_factor, debug_mode)
        elif prim_type == 'rectangle':
            return _create_rectangle_mesh(prim, index, unit_factor, debug_mode)
        elif prim_type == 'obround':
            return _create_obround_mesh(prim, index, unit_factor, debug_mode)
        elif prim_type == 'region':
            return _create_region_mesh(prim, index, unit_factor, debug_mode)
        else:
            print(f"Unknown primitive type {prim_type}: {prim}")
            return [], []
    except Exception as e:
        print(f"Failed to create spline {index}: {e}")
        return [], []
    
def _create_line_mesh(line_data, index, unit_factor, debug_mode=False):
    """Create line mesh (rectangle with width)"""
    # Apply offset and unit conversion
    x1 = line_data.get('x1', 0) * unit_factor
    y1 = line_data.get('y1', 0) * unit_factor
    x2 = line_data.get('x2', 0) * unit_factor
    y2 = line_data.get('y2', 0) * unit_factor
    width = line_data.get('width', 0.1) * unit_factor
    
    # Calculate line direction and perpendicular direction
    dx = x2 - x1
    dy = y2 - y1
    length = math.sqrt(dx*dx + dy*dy)
    
    if length < 0.000001 or width < 0.000001:  # Ignore too short lines
        if debug_mode:
            print(f"    Ignoring too short line: length={length}, width={width}")
        return [], []
    
    # Calculate unit vector
    ux = dx / length
    uy = dy / length
    
    # Calculate perpendicular vector
    vx = -uy * (width * 0.5)
    vy = ux * (width * 0.5)
    
    # Calculate the four corners of the rectangle
    verts = [
        (x1 - vx, y1 - vy, 0.0),  # Bottom-left
        (x1 + vx, y1 + vy, 0.0),  # Bottom-right
        (x2 + vx, y2 + vy, 0.0),  # Top-right
        (x2 - vx, y2 - vy, 0.0)   # Top-left
    ]
    
    # Create two triangular faces
    faces = [[0, 1, 2], [0, 2, 3]]

    # Create two circles at the endpoints with diameter equal to line width
    circle_verts, circle_faces = _create_line_terminal_circle_mesh(x1, y1, x2, y2, width/2)
    vert_offset = len(verts)
    for face in circle_faces:
        faces.append([v_idx + vert_offset for v_idx in face])
    verts.extend(circle_verts)

    if debug_mode and index < 5:
        print(f"    Creating line mesh: start=({x1:.6f}, {y1:.6f}), end=({x2:.6f}, {y2:.6f}), width={width:.6f}")
    
    return verts, faces

def _create_line_terminal_circle_mesh(x1, y1, x2, y2, radius):
    segments = 32
    
    # 1. Create a circle with center at (x1, y1) and radius
    verts = []
    faces = []

    # Center point
    verts.append((x1, y1, 0.0))
    
    # Points on the circumference
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        px = x1 + radius * math.cos(angle)
        py = y1 + radius * math.sin(angle)
        verts.append((px, py, 0.0))
    
    # Create triangle fan
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([0, i + 1, next_i + 1])

    # 2. Create a circle with center at (x2, y2) and radius
    # Center point
    verts.append((x2, y2, 0.0))
    
    # Points on the circumference
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        px = x2 + radius * math.cos(angle)
        py = y2 + radius * math.sin(angle)
        verts.append((px, py, 0.0))
    
    # Create triangle fan
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([segments + 1, i + 2 + segments, next_i + 2 + segments])
    
    return verts, faces

def _create_circle_mesh(circle_data, index, unit_factor, debug_mode=False):
    """Create circle mesh (solid circle or ring)"""
    x = circle_data.get('x', 0) * unit_factor
    y = circle_data.get('y', 0) * unit_factor
    radius = circle_data.get('radius', 0.05) * unit_factor

    # Create mesh
    segments = 32
    verts = []
    faces = []
    print(f'Circle({index}): {circle_data}')
    if circle_data.get('hole_diameter', 0.0) == 0.0:
        # Solid circle
        if radius < 0.000001:  # Ignore too small circles
            if debug_mode:
                print(f"    Ignoring too small circle: radius={radius}")
            return [], []
        
        # Center point
        verts.append((x, y, 0.0))
        
        # Points on the circumference
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            verts.append((px, py, 0.0))
        
        # Create triangle fan
        for i in range(segments):
            next_i = (i + 1) % segments
            faces.append([0, i + 1, next_i + 1])
        
        if debug_mode and index < 5:
            print(f"    Creating circle mesh: center=({x:.6f}, {y:.6f}), radius={radius:.6f}")
    else:
        # Ring
        hole_radius = circle_data['hole_diameter'] * unit_factor/2

        # Points on the outer circumference
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            verts.append((px, py, 0.0))
        
        # Points on the inner circumference
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            px = x + hole_radius * math.cos(angle)
            py = y + hole_radius * math.sin(angle)
            verts.append((px, py, 0.0))

        # Create faces (connecting inner and outer circles)
        for i in range(segments):
            next_i = (i + 1) % segments
            
            # Outer circle current point and next point
            outer_current = i
            outer_next = next_i
            
            # Inner circle current point and next point (note index offset)
            inner_current = i + segments
            inner_next = next_i + segments
            
            # Create two triangles to form a quadrilateral
            # Triangle 1: outer current -> outer next -> inner next
            faces.append([outer_current, outer_next, inner_next])
            
            # Triangle 2: outer current -> inner next -> inner current
            faces.append([outer_current, inner_next, inner_current])
        
    return verts, faces

def _create_rectangle_mesh(rect_data, index, unit_factor, debug_mode=False):
    """Create rectangle mesh (solid rectangle)"""
    x = rect_data.get('x', 0) * unit_factor
    y = rect_data.get('y', 0) * unit_factor
    width = rect_data.get('width', 0.1) * unit_factor
    height = rect_data.get('height', 0.1) * unit_factor
    
    if width < 0.000001 or height < 0.000001:  # Ignore too small rectangles
        if debug_mode:
            print(f"    Ignoring too small rectangle: width={width}, height={height}")
        return [], []
    
    # Calculate half width and height
    half_width = width * 0.5
    half_height = height * 0.5
    
    # Create rectangle vertices
    verts = [
        (x - half_width, y - half_height, 0.0),  # Bottom-left
        (x + half_width, y - half_height, 0.0),  # Bottom-right
        (x + half_width, y + half_height, 0.0),  # Top-right
        (x - half_width, y + half_height, 0.0)   # Top-left
    ]
    
    # Create two triangular faces
    faces = [[0, 1, 2], [0, 2, 3]]
    
    if debug_mode and index < 5:
        print(f"    Creating rectangle mesh: center=({x:.6f}, {y:.6f}), size={width:.6f}x{height:.6f}")
    
    return verts, faces

def _create_obround_mesh(obround_data, index, unit_factor, debug_mode=False):
    """Create obround mesh (solid obround)"""
    x = obround_data.get('x', 0) * unit_factor
    y = obround_data.get('y', 0) * unit_factor
    width = obround_data.get('width', 0.1) * unit_factor
    height = obround_data.get('height', 0.1) * unit_factor
    
    if width < 0.000001 or height < 0.000001:  # Ignore too small obrounds
        if debug_mode:
            print(f"    Ignoring too small obround: width={width}, height={height}")
        return [], []
    
    # Calculate semi-axes
    a = width * 0.5
    b = height * 0.5
    
    # Create obround mesh
    segments = 32
    verts = []
    faces = []
    
    # Center point
    verts.append((x, y, 0.0))
    
    # Points on the obround
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        px = x + a * math.cos(angle)
        py = y + b * math.sin(angle)
        verts.append((px, py, 0.0))
    
    # Create triangle fan
    for i in range(segments):
        next_i = (i + 1) % segments
        faces.append([0, i + 1, next_i + 1])
    
    if debug_mode and index < 5:
        print(f"    Creating obround mesh: center=({x:.6f}, {y:.6f}), size={width:.6f}x{height:.6f}")
    
    return verts, faces

def _create_region_mesh(region_data, index, unit_factor, debug_mode=False):
    points_2d = region_data.get('vertices')
    if len(points_2d) < 3:
        print(f"Error: At least 3 points are required")
        return [], []
    
    # Convert to 3D vertices
    verts = [(x * unit_factor, y * unit_factor, 0.0) for x, y in points_2d]
    
    # Create faces - using convex polygon triangulation
    faces = []
    for j in range(1, len(verts) - 1):
        faces.append([0, j, j + 1])
    if debug_mode and index < 5:
        print(f"    Creating region mesh: {len(verts)} vertices, {len(faces)} faces, vertices={verts}")
    
    return verts, faces


# ============================================================================
# Settings Panel
# ============================================================================
class VIEW3D_PT_gerber(Panel):
    """Gerber Import Settings Panel"""
    bl_label = "Gerber Import"
    bl_idname = "VIEW3D_PT_gerber"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing Tools"
    bl_order = 1

    stats = {}
    processing_times = {}

    def draw_header(self, context):
        if context and getattr(context.scene, 'gerber_import_issuccess', False):
            self.layout.label(text="", icon='CHECKMARK')
    
    def draw(self, context):
        global gerber_fileinfo
        layout = self.layout
        if context is None:
            return
        scene = context.scene
        
        # Title
        box = layout.box()
        box.label(text="Gerber Folder Import", icon='IMPORT')
        
        # File selection
        row = box.row(align=True)
        row.prop(scene, "gerber_filepath", text="")
        row.operator("io_fritzing.browse_gerber_files",
                    text="", 
                    icon='FILEBROWSER')
        
        # File information
        filepath = getattr(scene, "gerber_filepath")
        can_process = False
        if filepath and os.path.exists(filepath) and len(gerber_fileinfo) > 0:
            try:
                col = box.column(align=True)
                col.label(text=pgettext("{count} files found:").format(count=len(gerber_fileinfo)), icon='INFO')
                for layer_name, file_info in gerber_fileinfo.items():
                    postfix = os.path.splitext(file_info['filepath'])[1]
                    total = file_info['total_prims']
                    if total >= 0:
                        can_process = True
                        row = box.row()
                        col1 = row.column()
                        col1.scale_x = 0.6
                        col1.label(text=pgettext(layer_name) + "(" + postfix + "):", icon='CHECKMARK')
                        col2 = row.column()
                        col2.scale_x = 0.5
                        col2.label(text=str(total) + pgettext(" primitives"))
                    else:
                        row = box.row()
                        col = row.column()
                        col.label(text="(" + postfix + "): " + pgettext("Parse failed"), icon='X')
                if can_process:
                    row = box.row()
                    col = row.column()
                    col.label(text=pgettext("Parse time: ") + f"{getattr(context.scene, 'fetch_gerber_prims_time_consumed'): .2f}s", icon='PREVIEW_RANGE')
            except Exception as e:
                print(f'Unexpected error: {e}')
                pass

        # Import button
        layout.separator()
        col = layout.column(align=True)
        
        if can_process:
            op = col.operator("io_fritzing.import_gerber_file", 
                             text="Import Gerber Files", 
                             icon='IMPORT')
            setattr(op, 'debug_mode', getattr(scene, 'gerber_debug_mode', False))
            setattr(op, 'optimize_performance', getattr(scene, 'gerber_optimize_performance'))
            
            col.separator()
            col.operator("io_fritzing.clear_all_objects", 
                        text="Clear All Imported Objects", 
                        icon='TRASH')
        else:
            col.label(text="Please select Gerber folder first", icon='ERROR')

    def get_gerber_stats(self, filepath):
        start_time = time.time()
        try:
            gerber = read(filepath)
            # Extract primitives
            lines = 0
            circles = 0
            regions = 0
            rects = 0
            obrounds = 0
            if gerber.primitives and len(gerber.primitives) > 0:
                total = len(gerber.primitives)
                for i, prim in enumerate(gerber.primitives):
                    prim_type = prim.__class__.__name__.lower()
                    if prim_type == 'line':
                        lines += 1
                    elif prim_type == 'circle':
                        circles += 1
                    elif prim_type == 'region':
                        regions += 1
                    elif prim_type == 'rectangle':
                        rects += 1
                    elif prim_type == 'obround':
                        obrounds += 1
                    else:
                        return None

                stats = {'total': total}
                if lines > 0:
                    stats.__setitem__('lines', lines)
                if circles > 0:
                    stats.__setitem__('circles', circles)
                if regions > 0:
                    stats.__setitem__('regions', regions)
                if rects > 0:
                    stats.__setitem__('rects', rects)
                if obrounds > 0:
                    stats.__setitem__('obrounds', obrounds)
                processing_time = time.time() - start_time
                self.processing_times.__setitem__(filepath, processing_time)
                self.stats.__setitem__(filepath, stats)
        except:
            pass


# ============================================================================
# Auxiliary Operators
# ============================================================================
class IMPORT_OT_browse_gerber_files(Operator, ImportHelper):
    """Browse Gerber Files"""
    bl_idname = "io_fritzing.browse_gerber_files"
    bl_label = "Import Gerber Folder"
    
    use_filter_folder = True

    filter_glob: StringProperty(
        default="*.gm1;*.gbl;*.gtl;*drill.txt;*.gbo;*.gto;",
        options={'HIDDEN'}
    ) # type: ignore
    
    def invoke(self, context, event):
        if context:
            context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if context is None:
            return
        time_start = time.time()
        global gerber_fileinfo
        # Set wait cursor
        context.window.cursor_modal_set('WAIT')
        directory = self.properties['filepath']
        cut = directory.rindex(os.path.sep[0])
        directory = directory[0:cut]
        gerber_fileinfo = dict()
        tmp_filenames = glob.glob(os.path.join(directory, '*.*'))
        # get filenames dictionary contains outline, bottom, top, bottomsilk, topsilk, drill
        for filename in tmp_filenames:
            layer_name = None
            if filename.endswith('.gm1'):
                layer_name = 'outline'
            elif filename.endswith('.gbl'):
                layer_name = 'bottom'
            elif filename.endswith('.gtl'):
                layer_name = 'top'
            elif filename.endswith('_drill.txt'):
                layer_name = 'drill'
            elif filename.endswith('.gbo'):
                layer_name = 'bottomsilk'
            elif filename.endswith('.gto'):
                layer_name = 'topsilk'
            if layer_name:
                self.count_gerber_prims(layer_name, filename)
        if os.path.exists(directory):
            setattr(context.scene, 'gerber_filepath', directory)
        setattr(context.scene, 'fetch_gerber_prims_time_consumed', time.time() - time_start)

        # Restore cursor
        context.window.cursor_modal_set('DEFAULT')
        return {'FINISHED'}

    def count_gerber_prims(self, layer_name, filename):
        global gerber_fileinfo
        total = 0
        try:
            gerber = read(filename)
            total = len(gerber.primitives)
        except:
            total = -1   # Failed to parse gerber
            pass
        gerber_fileinfo[layer_name] = {'filepath': filename, 'total_prims': total}


# ============================================================================
# Operators used by the menu import process
# ============================================================================
class ImportSingleGerber(Operator):
    bl_idname = "fritzing.import_single_gerber"
    bl_label = "Import a single Fritzing Gerber file"

    def execute(self, context):
        """Execute import"""
        layer_name = None
        try:
            layer_name = next(iter(importdata.filenames))
        except StopIteration as e:
            if len(importdata.filenames) == 0:
                importdata.step_name = 'POST_GERBER_EXTRUDE'
                return {'FINISHED'}
            else:
                self.report({'ERROR'}, pgettext("No more Gerber files to process"))
                return {'CANCELLED'}

        filepath = importdata.filenames[layer_name]
        if not filepath or not os.path.exists(filepath):
            self.report({'ERROR'}, pgettext("Gerber file {filepath} does not exist").format(filepath = filepath))
            return {'CANCELLED'}
        if bpy.context is None:
            return {'CANCELLED'}

        importdata.current_file = filepath
        if context and hasattr(context.scene, 'gerber_progress_indicator_text'):
            setattr(context.scene, 'gerber_progress_indicator_text', pgettext('Importing ') + filepath[filepath.rindex(os.path.sep[0]) + 1 :])

        # Create main collection
        cut = filepath.rindex(os.path.sep[0])
        directory = filepath[0:cut]
        collection_name = os.path.basename(directory).replace('.', '_')
        if collection_name.endswith('_'):
            collection_name = collection_name[:-1]
        collection_name = f"Gerber_{collection_name[:20]}"
        main_collection = bpy.data.collections.get(collection_name)
        if main_collection is None:
            main_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(main_collection)
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]

        try:
            if layer_name == 'drill':
                parser = DrillParser()  # Use the previously defined parser
                result = parser.parse_drill_file(filepath, debug=False)
                
                if not result.get('success', False):
                    self.report({'ERROR'}, pgettext("Parse failed: ") + result.get('error', pgettext('Unknown error')))
                    return {'CANCELLED'}
                
                # Create geometry
                generator = DrillGenerator()
                primitives = result.get('primitives', [])
                file_info = result.get('file_info', {})
                height = importdata.board_thickness + 0.0004
                
                create_result = generator.create_drill_geometry(layer_name,
                    main_collection,
                    primitives, 
                    file_info,
                    height=height,
                    debug=False
                )
                
                if not create_result.get('success', False):
                    self.report({'ERROR'}, pgettext("Geometry creation failed: {create_result_error}").format(create_result_error = create_result.get('error', pgettext('Unknown error'))))
                    getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")
                
                message = pgettext("Import complete: {object_count)} drills").format(object_count = create_result.get('object_count', 0))
                self.report({'INFO'}, message)

                layer = create_result['layer']
                importdata.svgLayers[layer_name] = layer
                importdata.filenames.pop(layer_name)
                importdata.current = importdata.current + 1
            else:
                # Parse Gerber RS-274X file
                parser = GerberParser()
                result = parser.parse_gerber(filepath, debug=False)
                
                if not result.get('success', False):
                    self.report({'ERROR'}, pgettext("Parse failed: ") + result.get('error', pgettext('Unknown error')))
                    getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")
                
                result_stats = _create_gerber_mesh_filled(layer_name,
                    result.get('primitives', []), 
                    main_collection,
                    result.get('unit_factor', 0.001),
                )
                
                # Report result
                message = pgettext("Import complete: {total_prims} primitives, {total_verts} vertices, {total_faces} faces").format(total_prims=result_stats['total_prims'], total_verts=result_stats['total_verts'], total_faces=result_stats['total_faces'])
                self.report({'INFO'}, message)
                print(f"Import result: {message}")
                print(f"Collection name: {collection_name}")

                if result_stats.get('success', False):
                    obj = result_stats['mesh_obj']
                    importdata.svgLayers[layer_name] = obj
                    importdata.filenames.pop(layer_name)
                    importdata.current = importdata.current + 1
                else: 
                    self.report({'ERROR'}, pgettext("Geometry creation failed: {create_result_error}").format(create_result_error = create_result.get('error', pgettext('Unknown error'))))
                    getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")
        except Exception as e:
            error_msg = pgettext("Import process error: {error}").format(error = str(e))
            self.report({'ERROR'}, error_msg)
            print(f"Error importing {layer_name}, try again...")
            getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")

        return {'FINISHED'}


# ============================================================================
# Registration
# ============================================================================
classes = [
    IMPORT_OT_gerber,
    IMPORT_OT_browse_gerber_files,
    IMPORT_OT_clear_all_objects,
    VIEW3D_PT_gerber,
    ImportSingleGerber,
]

def register():
    """Register plugin"""
    print("Registering Gerber import plugin...")
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Registered class: {cls.__name__}")
        except Exception as e:
            print(f"❌ Failed to register class {cls.__name__}: {e}")
    
    # Register scene properties
    setattr(Scene, 'gerber_filepath', StringProperty(
        name="Gerber File",
        description="Path to Gerber file",
        default=""
    ))
    
    setattr(Scene, 'gerber_debug_mode', BoolProperty(
        name="Gerber Debug Mode",
        description="Enable debug mode to show detailed information",
        default=False
    ))
    
    setattr(Scene, 'gerber_optimize_performance', BoolProperty(
        name="Optimize Performance",
        description="Enable performance optimization",
        default=True
    ))

    setattr(Scene, 'fetch_gerber_prims_time_consumed', FloatProperty(
        name="Time to Fetch Gerber Primitives",
        description="Time taken to fetch primitives from a batch of Gerber files",
    ))
    
    setattr(Scene, 'gerber_import_time_consumed', FloatProperty(
        name="Gerber Files Import Time Consumed",
        description="Time taken to import a batch of Gerber files",
    ))
    
    setattr(Scene, 'gerber_import_issuccess', BoolProperty(
        name="Gerber Import Success",
        description="Whether Gerber import was successful",
        default=False
    ))
    
    print("✅ Gerber import plugin registration complete")

def unregister():
    """Unregister plugin"""
    print("Unregistering Gerber import plugin...")
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ Unregistered class: {cls.__name__}")
        except:
            pass

    delattr(Scene, 'gerber_filepath')
    delattr(Scene, 'gerber_debug_mode')
    delattr(Scene, 'gerber_optimize_performance')
    delattr(Scene, 'fetch_gerber_prims_time_consumed')

if __name__ == "__main__":
    register()
