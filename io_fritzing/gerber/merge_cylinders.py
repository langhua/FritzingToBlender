import bpy
import re
from collections import defaultdict
from bpy.props import BoolProperty, FloatProperty, StringProperty, EnumProperty
from bpy.types import Panel, Operator, PropertyGroup
from bpy.app.translations import pgettext
from io_fritzing.gerber.report import importdata

# Plugin information
bl_info = {
    "name": "Fritzing Drill Tool Manager",
    "version": (2, 1, 0),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > Fritzing Tools > Drill Tools",
    "description": "Merge drill cylinders and generate diameter summary report",
    "category": "Fritzing Tools",
}

# Global variables for storing statistics
pre_merge_stats = None
merge_operation_performed = False

# Custom property group
class DrillToolsProperties(PropertyGroup):
    # Options
    auto_create_labels: BoolProperty(
        name="Auto Create Diameter Labels",
        description="Automatically create diameter labels in 3D view after merge",
        default=True
    ) # type: ignore
    
    # Display options
    show_details: BoolProperty(
        name="Show Details",
        description="Show detailed information for each tool group",
        default=True
    ) # type: ignore
    
    # Merge options
    merge_selected_only: BoolProperty(
        name="Process Selected Only",
        description="Only process selected Drill_Cylinder objects",
        default=False
    ) # type: ignore
    
    rename_single_objects: BoolProperty(
        name="Rename Single Objects",
        description="Rename to standard name even if there's only one cylinder",
        default=True
    ) # type: ignore

# Merge operator
class DRILLTOOLS_OT_MergeCylinders(Operator):
    bl_idname = "drilltools.merge_cylinders"
    bl_label = "Merge Cylinder Tools"
    bl_description = "Merge drill cylinders with the same tool number and generate diameter summary"
    
    def execute(self, context):
        global pre_merge_stats, merge_operation_performed
        
        if context is None:
            return {'CANCELLED'}
        
        props = getattr(context.scene, "drill_tools_props", None)
        if props is None:
            self.report({'ERROR'}, "Drill tool properties group not found")
            return {'CANCELLED'}
        
        # Get settings
        selected_only = props.merge_selected_only
        auto_create_labels = props.auto_create_labels
        rename_single_objects = props.rename_single_objects
        
        # Save pre-merge statistics
        pre_merge_stats = get_current_stats(selected_only)
        
        # Execute merge
        merged_objects, diameter_summary = merge_drill_cylinders_with_simple_diameter(
            selected_only, 
            rename_single_objects
        )
        
        if not merged_objects:
            self.report({'WARNING'}, "No Drill_Cylinder objects found")
            return {'CANCELLED'}
        
        # Set merge operation flag
        merge_operation_performed = True
        
        # Print summary in console
        print_simple_diameter_summary(diameter_summary)
        
        # Select all processed objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in merged_objects:
            if obj and obj.name in bpy.data.objects:
                obj.select_set(True)
        if merged_objects and merged_objects[0].name in bpy.data.objects:
            context.view_layer.objects.active = merged_objects[0]
        
        # Show statistics
        stats = get_diameter_statistics(diameter_summary)
        self.report({'INFO'}, pgettext("Complete! Processed {num_tools} tool types, {num_holes} drill holes").format(num_tools = stats['total_tools'], num_holes = stats['total_holes']))
        
        return {'FINISHED'}

# View summary operator
class DRILLTOOLS_OT_ShowSummary(Operator):
    bl_idname = "drilltools.show_summary"
    bl_label = "View Diameter Summary"
    bl_description = "Display drill tool diameter summary in console"
    
    def execute(self, context):
        global merge_operation_performed
        
        # Get settings
        if context is None:
            return {'CANCELLED'}
        
        props = getattr(context.scene, "drill_tools_props", None)
        if props is None:
            self.report({'ERROR'}, "Drill tool properties group not found")
            return {'CANCELLED'}
        selected_only = props.merge_selected_only
        
        # Get current statistics
        stats = get_current_stats(selected_only)
        
        if not stats['drill_objects']:
            self.report({'WARNING'}, "No Drill_Cylinder objects found")
            return {'CANCELLED'}
        
        # Display summary in console
        print("\n" + "="*50)
        print("Current Drill Tool Statistics")
        print("="*50)
        print(f"Total drill cylinders: {stats['total_holes']}")
        print(f"Tool types: {stats['total_groups']}")
        
        # Display detailed information for each group
        sorted_groups = sorted(stats['cylinder_groups'].items(), key=lambda x: int(x[0]))
        print(f"\n{'Tool No.':<10} {'Count':<8} {'Diameter(m)':<12}")
        print("-" * 40)
        
        for cylinder_number, objects in sorted_groups:
            if objects:
                diameter = objects[0].dimensions.x
                print(f"T{cylinder_number:<9} {len(objects):<8} {diameter:<12.6f}")
        
        # Display merge status
        if merge_operation_performed:
            print("\n⚠ Note: This statistics shows the current state of objects in the scene")
            print("  If a merge operation has been performed, please check the post-merge summary report for detailed diameter information")
        
        self.report({'INFO'}, pgettext("Summary complete: {num_groups} tool types, {num_holes} drill holes").format(num_groups = stats['total_groups'], num_holes = stats['total_holes']))
        return {'FINISHED'}

# Cleanup tool numbers operator
class DRILLTOOLS_OT_CleanupToolNumbers(Operator):
    bl_idname = "drilltools.cleanup_tool_numbers"
    bl_label = "Cleanup Tool Numbers"
    bl_description = "Clean up and renumber tools, ensuring numbering starts from 1 consecutively"
    
    def execute(self, context):
        global merge_operation_performed
        
        all_objects = bpy.data.objects
        cylinder_groups = defaultdict(list)
        
        # Match all possible Drill_Cylinder formats
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
            self.report({'WARNING'}, "No Drill_Cylinder objects found")
            return {'CANCELLED'}
        
        # Renumber
        sorted_numbers = sorted(cylinder_groups.keys())
        renumber_map = {}
        
        for i, old_number in enumerate(sorted_numbers, 1):
            renumber_map[old_number] = i
        
        renamed_count = 0
        for old_number, objects in cylinder_groups.items():
            new_number = renumber_map[old_number]
            
            for obj in objects:
                # Build new name
                if old_number != new_number or not obj.name.startswith(f"Drill_Cylinder_{old_number}"):
                    obj.name = f"Drill_Cylinder_{new_number}"
                    renamed_count += 1
        
        # Reset merge flag
        merge_operation_performed = False
        
        self.report({'INFO'}, pgettext("Renumbering complete: {num_groups} tool types, renamed {renamed_count} objects").format(num_groups = len(cylinder_groups), renamed_count = renamed_count))
        return {'FINISHED'}

# Panel
class DRILLTOOLS_PT_MainPanel(Panel):
    bl_label = "Cylinder Merge Tools"
    bl_idname = "DRILLTOOLS_PT_MainPanel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Fritzing Tools"
    bl_context = "objectmode"
    bl_order = 3
    bl_options = {'DEFAULT_CLOSED'}
    
    def draw(self, context):
        global pre_merge_stats, merge_operation_performed
        
        layout = self.layout
        if context is None:
            return {'CANCELLED'}
        
        props = getattr(context.scene, "drill_tools_props", None)
        
        # Main operation buttons
        box = layout.box()
        row = box.row()
        row.scale_y = 1.5
        row.operator("drilltools.merge_cylinders", text=pgettext("Merge Cylinder Tools"), icon='AUTOMERGE_OFF')
        
        # Options
        box = layout.box()
        box.label(text="Options", icon='PREFERENCES')
        
        box.prop(props, "merge_selected_only")
        box.prop(props, "rename_single_objects")
        box.prop(props, "show_details")
        
        # Tool buttons
        box = layout.box()
        box.label(text="Tools", icon='TOOL_SETTINGS')
        
        col = box.column(align=True)
        col.operator("drilltools.show_summary", icon='VIEWZOOM')
        col.operator("drilltools.cleanup_tool_numbers", icon='SORTALPHA')
        
        # Status information
        if props and props.show_details:
            box = layout.box()
            box.label(text="Status", icon='INFO')
            
            # Display different status information based on whether merge operation has been performed
            if merge_operation_performed and pre_merge_stats:
                # Display pre-merge statistics
                stats = pre_merge_stats
                if merge_operation_performed:
                    box.label(text="*Merge operation performed*", icon='INFO')
                    box.label(text="The following are pre-merge statistics:")
            else:
                # Get current real-time statistics
                stats = get_current_stats(props.merge_selected_only)
            
            if stats['drill_objects']:
                box.label(text=pgettext("Total {stats_total_holes} drill cylinders").format(stats_total_holes=stats['total_holes']), icon='MESH_CYLINDER')
                box.label(text=pgettext("Total {stats_total_groups} tool numbers").format(stats_total_groups=stats['total_groups']), icon='LINENUMBERS_ON')
                
                # Display tool list
                sorted_groups = sorted(stats['cylinder_groups'].items(), key=lambda x: int(x[0]))
                for i, (num, objects) in enumerate(sorted_groups[:6]):  # Display up to 6
                    if objects and objects[0]:
                        diameter = objects[0].dimensions.x
                        box.label(text=f"  T{num}: {len(objects)} " + pgettext("holes") + f", {diameter:.4f}m")
                
                if len(stats['cylinder_groups']) > 6:
                    box.label(text=pgettext("  ... and {num_more} more tool types").format(num_more = len(stats['cylinder_groups']) - 6))
                
                # If merged, add explanation
                if merge_operation_performed:
                    box.separator()
                    box.label(text="After merge, each tool group has been merged into a single object", icon='INFO')
                    current_stats = get_current_stats(props.merge_selected_only)
                    if current_stats['total_objects'] != stats['total_groups']:
                        box.label(text=f"Currently there are {current_stats['total_objects']} Drill_Cylinder objects", icon='OUTLINER_OB_MESH')
            else:
                box.label(text="No Drill_Cylinder found", icon='ERROR')

# Tool functions
def get_current_stats(selected_only=False):
    """Get Drill_Cylinder statistics in the current scene"""
    if bpy.context is None:
        return {}
    # Get objects
    if selected_only:
        all_objects = bpy.context.selected_objects
    else:
        all_objects = bpy.data.objects
    
    # Store Drill_Cylinders grouped by number
    cylinder_groups = defaultdict(list)
    
    # Use multiple patterns for matching
    patterns = [
        re.compile(r'^Drill_Cylinder_(\d+)(?:_Mat)?(?:\.\d{3})?$'),
        re.compile(r'^Drill_Cylinder_(\d+)_\d+$'),  # Match Drill_Cylinder_1_001
        re.compile(r'^Drill_Cylinder_(\d+)\.\d+$'),  # Match Drill_Cylinder_1.001
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
    
    # Calculate statistics
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
    """Simplified version: Merge Drill_Cylinders and extract diameter information"""
    
    print("Starting to merge Drill_Cylinders and extract diameter information...")
    
    if bpy.context is None:
        return [], {}

    # Get objects
    if selected_only:
        all_objects = bpy.context.selected_objects
    else:
        all_objects = bpy.data.objects
    
    # Store Drill_Cylinders grouped by number
    cylinder_groups = defaultdict(list)
    
    # Use multiple patterns for matching
    patterns = [
        re.compile(r'^Drill_Cylinder_(\d+)(?:_Mat)?(?:\.\d{3})?$'),
        re.compile(r'^Drill_Cylinder_(\d+)_\d+$'),  # Match Drill_Cylinder_1_001
        re.compile(r'^Drill_Cylinder_(\d+)\.\d+$'),  # Match Drill_Cylinder_1.001
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
        print("No Drill_Cylinder objects found")
        return [], {}
    
    print(f"Found {len(cylinder_groups)} groups of Drill_Cylinders")
    
    # Merge each group and record diameter information
    merged_objects = []
    diameter_summary = {}
    
    for cylinder_number, objects in cylinder_groups.items():
        if not objects:
            continue
            
        # Simplified diameter calculation: take the X dimension of the first object as the diameter
        first_obj = objects[0]
        diameter = first_obj.dimensions.x
        
        # Handle single or multiple objects
        if len(objects) > 1:
            print(f"Merging group {cylinder_number} ({len(objects)} objects, diameter: {diameter:.6f}m):")
            merged_obj = merge_cylinder_group_safe(objects, cylinder_number)
            if merged_obj:
                merged_objects.append(merged_obj)
                current_obj = merged_obj
            else:
                # If merge fails, use the first object
                current_obj = first_obj
                if rename_single_objects:
                    current_obj.name = f"Drill_Cylinder_{cylinder_number}"
        else:
            # Only one object
            print(f"Group {cylinder_number} has only 1 object (diameter: {diameter:.6f}m)")
            current_obj = first_obj
            if rename_single_objects:
                if not current_obj.name.startswith(f"Drill_Cylinder_{cylinder_number}"):
                    current_obj.name = f"Drill_Cylinder_{cylinder_number}"
            merged_objects.append(current_obj)
        
        # Record diameter information
        diameter_summary[f"Drill_Cylinder_{cylinder_number}"] = {
            'object': current_obj,
            'diameter': diameter,
            'object_count': len(objects),  # Note: This is the number of holes before merge
            'tool_number': cylinder_number
        }
    
    print(f"Processing complete! Processed {len(merged_objects)} cylinders in total")
    return merged_objects, diameter_summary

def merge_cylinder_group_safe(objects, cylinder_number):
    """Safely merge cylinders in the same group, avoiding references to deleted objects"""
    if len(objects) < 2:
        return objects[0] if objects else None
    
    if bpy.context is None:
        return None

    # Save current selection and active state (save names, not object references)
    original_selected_names = [obj.name for obj in bpy.context.selected_objects]
    original_active_name = bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else None
    
    try:
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Select all objects to be merged
        for obj in objects:
            obj.select_set(True)
        
        # Set the first object as the active object
        bpy.context.view_layer.objects.active = objects[0]
        
        # Execute merge
        bpy.ops.object.join()
        
        # Get the merged object
        merged_obj = bpy.context.active_object
        if merged_obj is None:
            return None
        
        # Rename to Drill_Cylinder_number
        new_name = f"Drill_Cylinder_{cylinder_number}"
        merged_obj.name = new_name
        
        print(f"  ✓ Merged to: {new_name}")
        
        return merged_obj
        
    except Exception as e:
        print(f"  ✗ Error merging group {cylinder_number}: {e}")
        return None
        
    finally:
        # Restore original selection state (find objects by name)
        bpy.ops.object.select_all(action='DESELECT')
        
        # Restore selection state
        for obj_name in original_selected_names:
            if obj_name in bpy.data.objects:
                bpy.data.objects[obj_name].select_set(True)
        
        # Restore active object
        if original_active_name and original_active_name in bpy.data.objects:
            bpy.context.view_layer.objects.active = bpy.data.objects[original_active_name]

def print_simple_diameter_summary(diameter_summary):
    """Print simplified diameter summary table"""
    if not diameter_summary:
        print("No diameter data to summarize")
        return
    
    print("\n" + "="*50)
    print("Drill Tool Diameter Summary Table")
    print("="*50)
    
    # Sort by tool number
    sorted_summary = sorted(diameter_summary.items(), key=lambda x: x[1]['tool_number'])
    
    # Print table header
    print(f"{'Tool No.':<15} {'Diameter(m)':<15} {'Hole Count':<8} {'Status':<10}")
    print("-" * 60)
    
    total_holes = 0
    total_objects = 0
    
    # Print each row of data
    for tool_name, data in sorted_summary:
        diameter = data['diameter']
        count = data['object_count']
        status = "Merged" if data['object_count'] > 1 else "Single"
        tool_number = data['tool_number']
        
        print(f"{tool_number:<15} {diameter:<15.6f} {count:<8} {status:<10}")
        total_holes += count
        total_objects += 1
    
    # Statistics
    print("-" * 60)
    unique_diameters = len(set(round(data['diameter'], 6) for data in diameter_summary.values()))
    
    print(f"Tool types: {len(diameter_summary)}")
    print(f"Total holes before merge: {total_holes}")
    print(f"Objects after merge: {len(diameter_summary)}")
    print(f"Unique diameters: {unique_diameters}")
    

def get_diameter_statistics(diameter_summary):
    """Get diameter statistics"""
    if not diameter_summary:
        return {}
    
    diameters = [data['diameter'] for data in diameter_summary.values()]
    counts = [data['object_count'] for data in diameter_summary.values()]
    
    stats = {
        'total_tools': len(diameter_summary),
        'total_holes': sum(counts),
        'total_objects': len(diameter_summary),  # Number of objects after merge
        'avg_diameter': sum(diameters) / len(diameters) if diameters else 0,
        'min_diameter': min(diameters) if diameters else 0,
        'max_diameter': max(diameters) if diameters else 0,
        'diameter_range': (max(diameters) - min(diameters)) if diameters else 0,
        'unique_diameters': len(set(round(d, 6) for d in diameters)) if diameters else 0
    }
    
    return stats


class GerberMergeCylinders(Operator):
    bl_idname = "fritzing.gerber_merge_cylinders"
    bl_label = "Fritzing Gerber post import: merge cylinders"
    
    def execute(self, context):
        global pre_merge_stats, merge_operation_performed
        
        if context is None:
            return {'CANCELLED'}
        
        # Execute merge
        merged_objects, diameter_summary = merge_drill_cylinders_with_simple_diameter(
            False, 
            True
        )
        
        if not merged_objects:
            importdata.error_msg = "No Drill_Cylinder objects found"
            print('--MergeLayers exception: ' + importdata.error_msg)
            getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")
            return {'CANCELLED'}
        
        importdata.diameter_summary = diameter_summary
        
        # Print summary in console
        print_simple_diameter_summary(diameter_summary)
        
        # Select all processed objects
        bpy.ops.object.select_all(action='DESELECT')
        for obj in merged_objects:
            if obj and obj.name in bpy.data.objects:
                obj.select_set(True)
        if merged_objects and merged_objects[0].name in bpy.data.objects:
            context.view_layer.objects.active = merged_objects[0]
        
        importdata.step_name = 'POST_GERBER_DRILL_HOLES'
        # importdata.step_name = 'FINISHED'
        return {'FINISHED'}


# Register/unregister functions
classes = [
    DrillToolsProperties,
    DRILLTOOLS_OT_MergeCylinders,
    DRILLTOOLS_OT_ShowSummary,
    DRILLTOOLS_OT_CleanupToolNumbers,
    DRILLTOOLS_PT_MainPanel,
    GerberMergeCylinders,
]

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Register custom properties
    setattr(bpy.types.Scene, "drill_tools_props", bpy.props.PointerProperty(type=DrillToolsProperties))
    
    print("Fritzing Drill Tool Manager registered (version 2.1.0)")

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    
    # Delete custom properties
    delattr(bpy.types.Scene, "drill_tools_props")
    
    print("Fritzing Drill Tool Manager unregistered")

# If run as a standalone script
if __name__ == "__main__":
    # Temporarily register for testing
    try:
        unregister()
    except:
        pass
    register()
