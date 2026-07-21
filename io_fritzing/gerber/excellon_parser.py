import bpy
import os
import time
import traceback
import winsound
from bpy.app.translations import pgettext
from bpy.types import Operator, Panel, Scene
from bpy.props import StringProperty, BoolProperty, FloatProperty
from ..assets.utils.material import create_material
from pcb_tools.excellon import read as read_excellon

# ============================================================================
# Drill File Parser
# ============================================================================
class DrillParser:
    """Drill file parser"""
    
    def __init__(self):
        self.primitives = []
        self.file_info = {}
    
    def parse_drill_file(self, filepath, debug=False):
        """Parse drill file"""
        try:
            print(f"🔍 Starting to parse drill file: {os.path.basename(filepath)}")
            start_time = time.time()
            
            # Read Excellon file
            drill = read_excellon(filepath)
            
            # Get file information
            self.file_info = self._get_drill_info(drill, filepath)
            print(f"📄 Drill file info: {self.file_info}")
            
            # Extract drills
            self.primitives = self._extract_all_holes(drill, debug)
            
            processing_time = time.time() - start_time
            
            # Analyze primitive types
            type_stats = self._analyze_primitive_types()
            
            result = {
                'success': True,
                'file_type': 'drill',
                'file_info': self.file_info,
                'primitives': self.primitives,
                'primitive_count': len(self.primitives),
                'type_stats': type_stats,
                'processing_time': processing_time,
                'message': f"Successfully parsed {len(self.primitives)} drills"
            }
            
            print(f"\n📊 Drill parsing statistics:")
            print(f"  - Total drills: {len(self.primitives)}")
            for prim_type, count in type_stats.items():
                print(f"  - {prim_type}: {count}")
            
            # Display tool statistics
            if 'tools' in self.file_info:
                print(f"\n🛠️ Tool statistics:")
                for tool_id, tool in self.file_info['tools'].items():
                    if hasattr(tool, 'diameter'):
                        print(f"  - Tool {tool_id}: Diameter {tool.diameter:.6f} inch")
            
            print(f"⏱️  Time taken: {processing_time:.2f} seconds")
            return result
            
        except Exception as e:
            error_msg = pgettext("Failed to parse drill file: ") + str(e)
            print(f"❌ {error_msg}")
            traceback.print_exc()
            return {'success': False, 'error': error_msg}
    
    def _get_drill_info(self, drill, filepath):
        """Get drill file information"""
        info = {
            'filename': os.path.basename(filepath),
            'file_size': os.path.getsize(filepath),
            'units': drill.units if hasattr(drill, 'units') else 'inch',
            'layer_name': 'Drill Layer',
        }
        
        # Get tool table
        if hasattr(drill, 'tools'):
            info['tools'] = {k: v for k, v in drill.tools.items()}
            info['tool_count'] = len(drill.tools)
        
        # Try multiple methods to get bounding box
        bounds = None
        
        # Method 1: Get from bounds attribute
        if hasattr(drill, 'bounds'):
            bounds = drill.bounds
        
        # Method 2: Calculate from statements
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
        
        if hasattr(drill, 'primitives'):
            info['total_prims'] = len(drill.primitives)

        return info
    
    def _calculate_bounds_from_statements(self, drill):
        """Calculate bounding box from statements"""
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
            print(f"Failed to calculate bounding box: {e}")
            return None
    
    def _extract_all_holes(self, drill, debug=False):
        """Extract all drills"""
        holes = []
        
        try:
            # First, let's see what attributes the drill object has
            if debug:
                print(f"\n🔍 Checking drill object attributes:")
                for attr in dir(drill):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(drill, attr)
                            if not callable(value):
                                print(f"  {attr}: {type(value).__name__} = {value}")
                        except:
                            pass
            
            # Method 1: Extract from holes attribute
            if hasattr(drill, 'holes') and drill.holes:
                print(f"🔍 Extracting drills from holes attribute: {len(drill.holes)}")
                
                for i, hole in enumerate(drill.holes):
                    hole_data = self._parse_hole(hole, i, drill, debug and i < 5)
                    if hole_data:
                        holes.append(hole_data)
                
                if holes:
                    return holes
            
            # Method 2: Extract from statements
            if hasattr(drill, 'statements'):
                holes_from_statements = self._extract_holes_from_statements(drill, debug)
                if holes_from_statements:
                    holes.extend(holes_from_statements)
                    return holes
            
            # Method 3: Extract from drills attribute
            if hasattr(drill, 'drills') and drill.drills:
                print(f"🔍 Extracting drills from drills attribute: {len(drill.drills)}")
                
                for i, hole in enumerate(drill.drills):
                    hole_data = self._parse_hole(hole, i, drill, debug and i < 5)
                    if hole_data:
                        holes.append(hole_data)
                
                if holes:
                    return holes
            
            print("⚠️ No drill data found")
            return []
            
        except Exception as e:
            print(f"❌ Failed to extract drills: {e}")
            traceback.print_exc()
            return []
    
    def _extract_holes_from_statements(self, drill, debug=False):
        """Extract drills from statements"""
        holes = []
        
        try:
            if not hasattr(drill, 'statements'):
                return []
            
            print(f"🔍 Extracting drills from statements: {len(drill.statements)} statements")
            
            # Track the currently used tool
            current_tool = None
            
            # Record the usage count of each tool
            tool_usage = {}
            
            for i, stmt in enumerate(drill.statements):
                # Check if it's a tool selection statement
                if hasattr(stmt, 'tool'):
                    current_tool = stmt.tool
                    if debug and i < 10:
                        print(f"  🔧 Statement {i}: Select tool {current_tool}")
                
                # Check if it's a drill statement
                if hasattr(stmt, 'x') and hasattr(stmt, 'y'):
                    x, y = stmt.x, stmt.y
                    
                    if x is None or y is None:
                        if debug:
                            print(f"  ⚠️  Statement {i}: Ignoring invalid coordinates (x={x}, y={y})")
                        continue
                    
                    # Determine tool ID
                    tool_id = 'unknown'
                    if hasattr(stmt, 'tool') and stmt.tool is not None:
                        tool_id = stmt.tool
                    elif current_tool is not None:
                        tool_id = current_tool
                    
                    # Count tool usage
                    tool_usage[tool_id] = tool_usage.get(tool_id, 0) + 1
                    
                    # Get diameter
                    diameter = 0.1  # Default diameter
                    
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
                        print(f"  🔍 Extracted drill {len(holes)} from statement: Position=({x:.6f}, {y:.6f}), Tool={tool_id}")
            
            print(f"✅ Extracted {len(holes)} drills from statements")
            
            # Display tool usage statistics
            if tool_usage:
                print(f"\n📊 Tool usage statistics in statements:")
                for tool_id, count in tool_usage.items():
                    print(f"  - Tool {tool_id}: {count} drills")
            
            return holes
            
        except Exception as e:
            print(f"❌ Failed to extract drills from statements: {e}")
            traceback.print_exc()
            return []
    
    def _parse_hole(self, hole, index, drill, debug=False):
        """Enhanced drill parsing"""
        try:
            # Get position
            x, y = 0, 0
            
            if hasattr(hole, 'position'):
                pos = hole.position
                if hasattr(pos, '__len__') and len(pos) >= 2:
                    x, y = pos[0], pos[1]
            elif hasattr(hole, 'x') and hasattr(hole, 'y'):
                x, y = hole.x, hole.y
            
            if x is None or y is None:
                if debug:
                    print(f"  ⚠️  Drill {index}: Ignoring invalid coordinates (x={x}, y={y})")
                return None
            
            # Get tool
            tool_id = 'unknown'
            if hasattr(hole, 'tool'):
                tool_id = hole.tool
            
            # Get diameter
            diameter = 0.1  # Default diameter
            
            if hasattr(drill, 'tools'):
                # Try multiple possible tool ID formats
                tool_keys_to_try = []
                
                # Original tool ID
                if tool_id in drill.tools:
                    tool_keys_to_try.append(tool_id)
                
                # Convert to string
                str_tool_id = str(tool_id)
                if str_tool_id in drill.tools:
                    tool_keys_to_try.append(str_tool_id)
                
                # Convert to integer
                try:
                    int_tool_id = int(tool_id)
                    if int_tool_id in drill.tools:
                        tool_keys_to_try.append(int_tool_id)
                except:
                    pass
                
                # Try all possible keys
                for key in tool_keys_to_try:
                    tool = drill.tools[key]
                    if hasattr(tool, 'diameter'):
                        diameter = tool.diameter
                        break
                    elif hasattr(tool, 'size'):
                        diameter = tool.size
                        break
            
            if debug:
                print(f"  🔍 Drill {index}: Position=({x:.6f}, {y:.6f}), Tool={tool_id}, Diameter={diameter:.6f}")
            
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
            print(f"❌ Failed to parse drill {index}: {e}")
            return None
    
    def _analyze_primitive_types(self):
        """Analyze primitive type statistics"""
        type_stats = {}
        for primitive in self.primitives:
            prim_type = primitive.get('type', 'unknown')
            type_stats[prim_type] = type_stats.get(prim_type, 0) + 1
        return type_stats

# ============================================================================
# Drill Geometry Generator with Fixed Drill Direction
# ============================================================================
class DrillGenerator:
    """Drill geometry generator with fixed drill direction"""
    
    def __init__(self):
        self.collection = None
        self.created_objects = []
    
    def create_drill_geometry(self, layer_name, collection, primitives, file_info, height=0.0018, debug=False):
        """Create drill geometry"""
        if not primitives:
            print("⚠️ No drill data, creating bounding box")
            return self._create_bounding_box_only(file_info, "Drill_Empty")
        
        try:
            print(f"🛠️ Starting to create drill geometry for {len(primitives)} drills")
            
            # Get unit conversion factor
            units = file_info.get('units', 'inch')
            unit_factor = 0.0254 if units == 'inch' else 0.001
            print(f"📏 Unit system: {units}, Conversion factor: {unit_factor}")
            
            # Generate unique collection name
            base_name = f"Drill_{os.path.basename(file_info['filename']).replace('.', '_')}"
            timestamp = int(time.time())
            if layer_name:
                final_name = layer_name
            else:
                final_name = f"{base_name}_{timestamp}"
            
            # Create collection
            self._create_collection_safe(final_name)
            if self.collection:
                if collection:
                    collection.children.link(self.collection)
                    if bpy.context:
                        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection.name].children[self.collection.name]
                elif bpy.context:
                    bpy.context.scene.collection.children.link(self.collection)
                    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[final_name]

            # Create drills
            created_count = 0
            tool_stats = {}
            failed_indices = []
            
            for i, hole in enumerate(primitives):
                try:
                    if self._create_drill_hole_z_axis(hole, i, unit_factor, height, debug and i < 5):
                        created_count += 1
                        
                        # Count tool usage
                        tool_id = hole.get('tool_id', 'unknown')
                        tool_stats[tool_id] = tool_stats.get(tool_id, 0) + 1
                    else:
                        failed_indices.append(i)
                except Exception as e:
                    print(f"❌ Failed to create drill {i}: {e}")
                    failed_indices.append(i)
                
                # Show progress
                if i % 20 == 0 and i > 0:
                    print(f"📊 Drill progress: {i}/{len(primitives)}")
            
            # Show failure statistics
            if failed_indices:
                print(f"\n❌ Failed drill indices: {failed_indices[:10]}... (Total: {len(failed_indices)})")
            
            # Show tool statistics
            if tool_stats:
                print(f"\n🛠️ Tool usage statistics:")
                for tool_id, count in sorted(tool_stats.items()):
                    print(f"  - Tool {tool_id}: {count} drills")
            
            result = {
                'success': True,
                'object_count': created_count,
                'failed_count': len(failed_indices),
                'collection': final_name,
                'message': f"Created {created_count} drills, {len(failed_indices)} failed",
                'layer': self.collection,
            }
            
            print(f"\n✅ Geometry creation complete: {result['message']}")
            
        except Exception as e:
            error_msg = f"Failed to create geometry: {str(e)}"
            print(f"❌ {error_msg}")
            traceback.print_exc()
            result = {'success': False, 'error': error_msg}
        
        if collection and bpy.context:
            bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]

        # zoom in by drill layer seems more suitable than other layer
        for obj in getattr(self.collection, 'all_objects'):
            obj.select_set(True)
        if bpy.context:
            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    with bpy.context.temp_override(area=area, region=area.regions[-1]):
                        bpy.ops.view3d.view_selected()
            bpy.ops.object.select_all(action='DESELECT')

        return result
    
    def _create_collection_safe(self, name):
        """Safely create a collection"""
        try:
            # Create new collection
            self.collection = bpy.data.collections.new(name)
            print(f"📁 Created collection: {name}")
        except Exception as e:
            print(f"Failed to create collection: {e}")
    
    def _create_drill_hole_z_axis(self, hole, index, unit_factor, height=0.0018, debug=False):
        """Create a drill hole along the Z-axis"""
        if bpy.context is None:
            return False
        try:
            x = hole.get('x', 0)
            y = hole.get('y', 0)
            diameter = hole.get('diameter', 0.1)      # Default 0.1 inch
            tool_id = hole.get('tool_id', 'unknown')
            
            # Check if coordinates and diameter are valid
            if x is None or y is None:
                if debug:
                    print(f"  ⚠️  Drill {index}: Invalid coordinates (x={x}, y={y})")
                return False
            
            if diameter is None:
                if debug:
                    print(f"  ⚠️  Drill {index}: Invalid diameter, using default value")
                diameter = 0.1
            
            # Convert units
            x_m = x * unit_factor
            y_m = y * unit_factor
            diameter_m = diameter * unit_factor
            
            if diameter_m <= 0:
                if debug:
                    print(f"  ⚠️  Drill {index}: Invalid diameter {diameter_m}, using minimum value")
                diameter_m = 0.000254  # 0.01mm
            
            radius_m = diameter_m / 2
            
            if debug:
                print(f"  🔧 Creating drill {index}:")
                print(f"    Original position: ({x:.6f}, {y:.6f}) inch")
                print(f"    Converted position: ({x_m:.6f}, {y_m:.6f}, 0.001) m")
                print(f"    Original diameter: {diameter:.6f} inch")
                print(f"    Converted diameter: {diameter_m:.6f} m")
                print(f"    Height: {height:.6f} m")
                print(f"    Tool ID: {tool_id}")
            
            # Create cylinder to represent drill - along Z-axis
            bpy.ops.mesh.primitive_cylinder_add(
                vertices=24,
                radius=radius_m,
                depth=height,
                location=(x_m, y_m, 0)
            )
            cylinder = bpy.context.active_object
            if cylinder is not None:
                setattr(cylinder, 'name', f"Drill_Cylinder_{tool_id}")
                cylinder.scale = (1, 1, 1)
            
            # Set different colors based on tool ID
            color = self._get_tool_color(tool_id)
            
            # Create material for the cylinder
            mat_cylinder = create_material(name=f"Drill_Cylinder_{tool_id}_Mat", base_color=color, alpha=1.0, roughness=0.4)
            if cylinder:
                if getattr(cylinder.data, 'materials'):
                    getattr(cylinder.data, 'materials')[0] = mat_cylinder
                else:
                    getattr(cylinder.data, 'materials').append(mat_cylinder)
            
            self.created_objects.append(cylinder)
            return True
            
        except Exception as e:
            print(f"❌ Failed to create drill {index}: {e}")
            traceback.print_exc()
            return False
    
    def _get_tool_color(self, tool_id):
        """Get color based on tool ID"""
        color_map = {
            '1': (0.8, 0.2, 0.2, 1.0),    # Red
            '2': (0.2, 0.8, 0.2, 1.0),    # Green
            '3': (0.2, 0.2, 0.8, 1.0),    # Blue
            '100': (0.8, 0.8, 0.2, 1.0),  # Yellow
            '101': (0.8, 0.2, 0.8, 1.0),  # Purple
            '102': (0.2, 0.8, 0.8, 1.0),  # Cyan
            '103': (0.8, 0.5, 0.2, 1.0),  # Orange
            '104': (0.5, 0.2, 0.8, 1.0),  # Deep Purple
            '105': (0.2, 0.5, 0.8, 1.0),  # Sky Blue
            '106': (0.8, 0.2, 0.5, 1.0),  # Pink
            '107': (0.5, 0.8, 0.2, 1.0),  # Yellow-Green
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
        
        return (0.5, 0.5, 0.5, 1.0)  # Default gray
    
    def _create_bounding_box_only(self, file_info, collection_name):
        """Create only bounding box"""
        if bpy.context is None:
            return {'success': False, 'error': 'Must be run in Blender'}
        try:
            if collection_name in bpy.data.collections:
                collection = bpy.data.collections[collection_name]
            else:
                collection = bpy.data.collections.new(collection_name)
                bpy.context.scene.collection.children.link(collection)
            
            bpy.ops.mesh.primitive_cube_add(size=0.05)
            cube = bpy.context.active_object
            setattr(cube, 'name', f"{collection_name}_Bounds")
            setattr(cube, 'location', (0, 0, 0))
            
            mat = create_material(name="Drill_Bounds_Mat", base_color=(0.5, 0.5, 0.5, 0.3))
            
            if cube:
                if getattr(cube.data, 'materials'):
                    getattr(cube.data, 'materials')[0] = mat
                else:
                    getattr(cube.data, 'materials').append(mat)
            
                collection.objects.link(cube)
            
            self.created_objects.append(cube)
            
            return {
                'success': True,
                'object_count': 1,
                'collection': collection_name,
                'message': f"Created bounding box"
            }
            
        except Exception as e:
            print(f"Failed to create bounding box: {e}")
            return {'success': False, 'error': str(e)}

# ============================================================================
# Main Import Operator
# ============================================================================
class IMPORT_OT_drill_z_axis(Operator):
    """Import Drill along Z-axis"""
    bl_idname = "io_fritzing.import_drill_z_axis"
    bl_label = "Import Drill File (Z-axis)"
    bl_description = "Import that creates drills along the Z-axis"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(
        name="Drill File",
        subtype='FILE_PATH',
        default=""
    ) # type: ignore
    
    debug_mode: BoolProperty(
        name="Debug Mode",
        description="Show detailed debug information",
        default=False
    ) # type: ignore
    
    def invoke(self, context, event):
        """Invoke dialog"""
        if context is None:
            return {'CANCELLED'}
        if not self.filepath or not os.path.exists(self.filepath):
            context.window_manager.fileselect_add(self)
            return {'RUNNING_MODAL'}
        return self.execute(context)
    
    def execute(self, context):
        if context is None:
            return {'CANCELLED'}

        """Launch modal drill import operator"""
        if not self.filepath or not os.path.exists(self.filepath):
            self.report({'ERROR'}, pgettext("Please select a valid Drill file"))
            return {'CANCELLED'}
        
        # Store parameters for the modal operator
        global _drill_import_filepath, _drill_import_debug
        _drill_import_filepath = self.filepath
        _drill_import_debug = self.debug_mode
        
        # Reset progress (with safety check for unregistered property)
        if hasattr(context.scene, 'drill_importing_progress'):
            setattr(context.scene, 'drill_importing_progress', 0.0)
        if hasattr(context.scene, 'drill_importing_current_step'):
            setattr(context.scene, 'drill_importing_current_step', '')
        
        # Launch modal import operator
        bpy.ops.io_fritzing.drill_import_modal('INVOKE_DEFAULT')
        return {'FINISHED'}

# ============================================================================
# Modal Drill Import Operator (async import with progress)
# ============================================================================

# Module-level state for drill import modal
_drill_import_filepath = ''
_drill_import_debug = False


class IMPORT_OT_drill_import_modal(Operator):
    """Import drill file with progress (modal)"""
    bl_idname = "io_fritzing.drill_import_modal"
    bl_label = "Import Drill File (Modal)"
    bl_options = {'REGISTER'}
    
    _timer = None
    _phase = 0  # 0=parsing, 1=geometry, 2=done
    _wm = None  # for system progress bar
    
    def _redraw_panel(self, context):
        if context.screen:
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
    
    def _set_progress(self, context, step, progress):
        if self._wm:
            self._wm.progress_update(int(progress))
        try:
            setattr(context.scene, 'drill_importing_current_step', step)
        except Exception:
            pass
        try:
            setattr(context.scene, 'drill_importing_progress', progress)
        except Exception:
            pass
        if step:
            self.report({'INFO'}, step)
        self._redraw_panel(context)
    
    def modal(self, context, event):
        global _drill_import_filepath, _drill_import_debug
        
        if event.type == 'TIMER':
            if self._phase == 0:
                # Phase 0: Parse the drill file
                self._set_progress(context,
                    pgettext("Parsing drill file..."), 10.0)
                
                parser = DrillParser()
                result = parser.parse_drill_file(_drill_import_filepath, debug=_drill_import_debug)
                
                if not result.get('success', False):
                    self.report({'ERROR'}, pgettext("Parse failed: ") +
                               result.get('error', pgettext('Unknown error')))
                    if self._timer:
                        context.window_manager.event_timer_remove(self._timer)
                    if self._wm:
                        self._wm.progress_end()
                    return {'CANCELLED'}
                
                # Store result for next phase
                self._parse_result = result
                self._phase = 1
                return {'RUNNING_MODAL'}
            
            elif self._phase == 1:
                # Phase 1: Create drill geometry
                self._set_progress(context,
                    pgettext("Creating drill geometry..."), 50.0)
                
                result = self._parse_result
                generator = DrillGenerator()
                primitives = result.get('primitives', [])
                file_info = result.get('file_info', {})
                
                create_result = generator.create_drill_geometry(
                    None, None,
                    primitives, file_info,
                    height=0.0018,
                    debug=_drill_import_debug)
                
                if not create_result.get('success', False):
                    self.report({'ERROR'},
                               pgettext("Geometry creation failed: {err}").format(
                                   err=create_result.get('error', '')))
                    if self._timer:
                        context.window_manager.event_timer_remove(self._timer)
                    if self._wm:
                        self._wm.progress_end()
                    return {'CANCELLED'}
                
                self._object_count = create_result.get('object_count', 0)
                self._phase = 2
                return {'RUNNING_MODAL'}
            
            elif self._phase == 2:
                # Phase 2: Done
                self._set_progress(context,
                    pgettext("Import complete"), 100.0)
                
                self.report({'INFO'},
                           pgettext("Imported {n} drills").format(
                               n=self._object_count))
                
                if self._timer:
                    context.window_manager.event_timer_remove(self._timer)
                if self._wm:
                    self._wm.progress_end()
                
                if os.name == 'nt':
                    winsound.Beep(1500, 1000)
                
                return {'FINISHED'}
        
        return {'PASS_THROUGH'}
    
    def invoke(self, context, event):
        self._phase = 0
        
        if not hasattr(Scene, 'drill_importing_current_step'):
            setattr(Scene, 'drill_importing_current_step', StringProperty(
                name="Current Drill Import Step",
                description="The current step of the drill import",
                default=""))
        if not hasattr(Scene, 'drill_importing_progress'):
            setattr(Scene, 'drill_importing_progress', FloatProperty(
                name="Drill Import Progress",
                description="Progress of drill file import (0 to 100)",
                default=0.0, min=0.0, max=100.0, subtype='PERCENTAGE'))
        
        wm = context.window_manager
        self._wm = wm
        wm.progress_begin(0, 100)
        self._timer = wm.event_timer_add(0.3, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}
    
    def cancel(self, context):
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
        if self._wm:
            self._wm.progress_end()


# ============================================================================
# Settings Panel
# ============================================================================
class VIEW3D_PT_drill_z_axis(Panel):
    """Drill Import Settings Panel - Z-axis"""
    bl_label = "Drill Import (Z-axis)"
    bl_idname = "VIEW3D_PT_drill_z_axis"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing Tools"
    bl_order = 2

    filepath = ''
    
    def draw(self, context):
        if context is None:
            return
        
        layout = self.layout
        scene = context.scene
        
        # === Progress display (top, always visible during import) ===
        if hasattr(scene, 'drill_importing_current_step'):
            drill_step = getattr(scene, 'drill_importing_current_step', '')
            is_importing = (drill_step and drill_step != pgettext("Import complete"))
            if drill_step and hasattr(scene, 'drill_importing_progress'):
                progress_box = layout.box()
                progress_box.label(text=drill_step, icon='IMPORT')
                row = progress_box.row(align=True)
                row.prop(scene, 'drill_importing_progress', text=pgettext("Progress"), slider=True)
        else:
            drill_step = ''
            is_importing = False
        
        # If importing, only show progress
        if is_importing:
            return
        
        # Title
        box = layout.box()
        box.label(text="Import Drill File (Z-axis)", icon='IMPORT')
        
        # File selection
        row = box.row(align=True)
        row.prop(scene, "drill_file_z_axis", text="")
        row.operator("io_fritzing.browse_drill_z_axis", 
                    text="", 
                    icon='FILEBROWSER')
        
        # File information
        filepath = getattr(scene, 'drill_file_z_axis')
        if filepath and os.path.exists(filepath) and not is_importing:
            if self.filepath != filepath:
                self.filepath = filepath
                try:
                    file_size = os.path.getsize(filepath)
                    filename = os.path.basename(filepath)
                    
                    col = box.column(align=True)
                    col.label(text=pgettext("File size: ") + f"{file_size/1024:.1f} KB", icon='INFO')
                    col.label(text=pgettext("File name: ") + filename, icon='FILE')
                    col.label(text=pgettext("File type: Drill file"), icon='MESH_GRID')
                    col.label(text=pgettext("Direction: Along Z-axis (vertical)"), icon='ORIENTATION_GIMBAL')

                    # Get file information
                    parser = DrillParser()
                    drill = read_excellon(filepath)
                    file_info = parser._get_drill_info(drill, filepath)
                    if file_info and file_info['total_prims']:
                        col.label(text=pgettext("Primitives: ") + str(file_info['total_prims']), icon='FILE_VOLUME')
                except:
                    pass
        
        # Import options
        layout.separator()
        box = layout.box()
        box.label(text="Import Options", icon='SETTINGS')
        box.prop(scene, "drill_debug_mode_z_axis", text="Enable Debug Mode")
        
        # Supported formats
        layout.separator()
        box = layout.box()
        box.label(text="Supported Drill File Formats", icon='FILE')
        
        col = box.column(align=True)
        col.label(text="Excellon drill files:")
        col.label(text="  .drl, .txt, .drill")
        col.label(text="  .xln, .xlnx, .drd")
        
        # Import button
        layout.separator()
        col = layout.column(align=True)
        
        if is_importing:
            col.label(text=pgettext("⏳ Importing drill file..."), icon='SORTTIME')
        elif filepath and os.path.exists(filepath):
            op = col.operator("io_fritzing.import_drill_z_axis", 
                             text="Import Drill File (Z-axis)", 
                             icon='IMPORT')
            setattr(op, 'filepath', filepath)
            setattr(op, 'debug_mode', getattr(scene, 'drill_debug_mode_z_axis'))
        else:
            col.label(text="Please select a Drill file first", icon='ERROR')

# ============================================================================
# Auxiliary Operators
# ============================================================================
class IMPORT_OT_browse_drill_z_axis(Operator):
    """Browse Drill File"""
    bl_idname = "io_fritzing.browse_drill_z_axis"
    bl_label = "Import Drill File"
    
    filepath: StringProperty(
        name="Drill File",
        subtype='FILE_PATH',
        default=""
    ) # type: ignore

    filter_glob: StringProperty(
        default="*.drl;*.txt;*.drill;*.xln;*.xlnx;*.drd",
        options={'HIDDEN'}
    ) # type: ignore
    
    def invoke(self, context, event):
        if context is None:
            return {'CANCELLED'}
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def execute(self, context):
        if context is None:
            return {'CANCELLED'}
        if self.filepath:
            setattr(context.scene, 'drill_file_z_axis', self.filepath)
        return {'FINISHED'}


# ============================================================================
# Method to improve drill success rate
# ============================================================================
def create_clean_cylinder_no_internal_edges(radius, depth, location=(0, 0, 0), vertices=32):

    
    return None

# ============================================================================
# Registration
# ============================================================================
classes = [
    IMPORT_OT_drill_z_axis,
    IMPORT_OT_drill_import_modal,
    IMPORT_OT_browse_drill_z_axis,
    VIEW3D_PT_drill_z_axis,
]

def register():
    """Register plugin"""
    print("Registering Drill Z-axis import plugin...")
    
    for cls in classes:
        try:
            bpy.utils.register_class(cls)
            print(f"✅ Registered class: {cls.__name__}")
        except Exception as e:
            print(f"❌ Failed to register class {cls.__name__}: {e}")
    
    # Register scene properties
    setattr(Scene, 'drill_file_z_axis', StringProperty(
        name="Drill File",
        description="Path to Drill file",
        default=""
    ))
    
    setattr(Scene, 'drill_debug_mode_z_axis', BoolProperty(
        name="Drill Debug Mode",
        description="Enable debug mode to show detailed information",
        default=False
    ))
    
    setattr(Scene, 'drill_importing_current_step', StringProperty(
        name="Current Drill Import Step",
        description="The current step of the drill import",
        default=""
    ))
    
    setattr(Scene, 'drill_importing_progress', FloatProperty(
        name="Drill Import Progress",
        description="Progress of drill file import (0 to 100)",
        default=0.0,
        min=0.0,
        max=100.0,
        subtype='PERCENTAGE'
    ))
    
    print("✅ Drill Z-axis import plugin registration complete")

def unregister():
    """Unregister plugin"""
    print("Unregistering Drill Z-axis import plugin...")
    
    for cls in reversed(classes):
        try:
            bpy.utils.unregister_class(cls)
            print(f"✅ Unregistered class: {cls.__name__}")
        except:
            pass
    
    delattr(Scene, 'drill_file_z_axis')
    delattr(Scene, 'drill_debug_mode_z_axis')
    delattr(Scene, 'drill_importing_current_step')
    delattr(Scene, 'drill_importing_progress')

if __name__ == "__main__":
    register()
