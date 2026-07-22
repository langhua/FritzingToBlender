import bpy
from .report import importdata
from bpy.types import Operator
import time

# ── KNOWN LIMITATIONS ──
# 1. Boolean drill success rate is low on complex PCB meshes.
#    Only large holes (≥1.5mm by default, adjustable via Cylinder Filter)
#    are drilled; small vias and pads are filtered out.
# 2. The BooleanModifier (batch boolean) algorithm is the most reliable;
#    AutoBoolean and Booltron require third-party addons.
# 3. Board mesh must be clean: merged layers, no non-manifold geometry.


class GerberDrillHoles(Operator):
    bl_idname = "fritzing.gerber_drill_holes"
    bl_label = "Fritzing Gerber post import: drill holes"
    
    def execute(self, context):
        try:
            if bpy.context is not None:
                joined_layer = bpy.context.view_layer.objects['JoinedLayer']
                drill_layer = None
                try:
                    drill_layer = importdata.svgLayers['drill']
                except:
                    pass
                algorithm = 'BooleanModifier'
                if context and hasattr(context.scene, 'gerber_drill_algorithm_setting'):
                    algorithm = str(getattr(context.scene, 'gerber_drill_algorithm_setting'))
                if drill_layer and joined_layer:
                    self.drillHoles(context, joined_layer, drill_layer=drill_layer, algorithm=algorithm)
        except Exception as e:
            print('--DrillHoles exception: ' + str(e))
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'gerber_import_error')("INVOKE_DEFAULT")

        importdata.step_name = 'FINISHED'
        return {"FINISHED"}


    def drillHoles(self, context, layer, drill_layer, algorithm):
        if context is None:
            return
        
        self.refresh_3d(context)
        time_start = time.time()

        cylinder_filter_setting = float(getattr(context.scene, 'gerber_cylinder_filter_setting', 0.0))
        
        if not layer or not drill_layer:
            return
        
        if algorithm == 'AutoBoolean':
            self._drill_auto_boolean(context, layer, drill_layer, cylinder_filter_setting)
        elif algorithm == 'NonDestructiveDifference':
            self._drill_nondestructive(context, layer, drill_layer, cylinder_filter_setting)
        elif algorithm == 'BooleanModifier':
            self._drill_batched_boolean(context, layer, drill_layer, cylinder_filter_setting)
        
        print(f'📊 Drill holes done in {time.time() - time_start:.2f}s')
    
    # ── Improved BooleanModifier: batch all cylinders into one cutter ──
    def _drill_batched_boolean(self, context, layer, drill_layer, cyl_filter):
        """Join all drill cylinders into one cutter, apply a SINGLE boolean."""
        # 1. Collect drill cylinders that pass the filter
        cutter_objects = []
        for obj in drill_layer.objects:
            if obj.type == 'MESH' and self._pass_filter(obj, cyl_filter):
                cutter_objects.append(obj)
        
        if not cutter_objects:
            print("No drill cylinders to process")
            return
        
        print(f"🔧 Batching {len(cutter_objects)} drill cylinders into one cutter...")
        
        # 2. Ensure board is in OBJECT mode
        if layer.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
        
        # 3. Copy cylinders → join into one cutter
        if len(cutter_objects) == 1:
            # Single cylinder: just duplicate it
            cutter_objects[0].select_set(True)
            context.view_layer.objects.active = cutter_objects[0]
            bpy.ops.object.duplicate()
            cutter = context.view_layer.objects.active
            cutter.name = "DrillCutter"
        else:
            # Multiple cylinders: duplicate first, then duplicate+join others
            bpy.ops.object.select_all(action='DESELECT')
            for obj in cutter_objects:
                obj.select_set(True)
            context.view_layer.objects.active = cutter_objects[0]
            bpy.ops.object.duplicate()
            # Now the duplicated copies are selected
            bpy.ops.object.join()
            cutter = context.view_layer.objects.active
            cutter.name = "DrillCutter"
        
        print(f"  Cutter created: {cutter.name}, vertices: {len(cutter.data.vertices)}")
        self.refresh_3d(context)
        
        # 4. Clean up cutter mesh
        context.view_layer.objects.active = cutter
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.000001)
        bpy.ops.mesh.normals_make_consistent(inside=False)
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 5. Apply Boolean modifier — use FAST solver (fast & reliable for cylinders)
        context.view_layer.objects.active = layer
        modifier = layer.modifiers.new(name="Drill_Boolean", type="BOOLEAN")
        modifier.operation = 'DIFFERENCE'
        modifier.object = cutter
        modifier.solver = 'FAST'
        modifier.use_self = False
        
        print(f"  Applying boolean modifier (Fast solver)...")
        try:
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        except RuntimeError:
            # Fast solver failed, try Exact as fallback
            print("  Fast solver failed, trying Exact solver...")
            modifier = layer.modifiers.new(name="Drill_Boolean", type="BOOLEAN")
            modifier.operation = 'DIFFERENCE'
            modifier.object = cutter
            modifier.solver = 'EXACT'
            modifier.use_self = False
            bpy.ops.object.modifier_apply(modifier=modifier.name)
        
        self.refresh_3d(context)
        
        # 6. Clean up result
        context.view_layer.objects.active = layer
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=0.000001)
        bpy.ops.mesh.delete_loose()
        bpy.ops.object.mode_set(mode='OBJECT')
        
        # 7. Remove cutter
        bpy.data.objects.remove(cutter, do_unlink=True)
        
        print(f"✅ Batch boolean complete: {len(cutter_objects)} holes")
    
    # ── BMesh Direct Cut: no Boolean modifier, directly delete faces ──
    # ── AutoBoolean (unchanged) ──
    def _drill_auto_boolean(self, context, layer, drill_layer, cyl_filter):
        bpy.ops.object.select_all(action='DESELECT')
        layer.select_set(True)
        for obj in drill_layer.objects:
            if obj.type == 'MESH' and self._pass_filter(obj, cyl_filter):
                print(f'Drilling hole: {obj.name}')
                obj.select_set(True)
                context.view_layer.objects.active = layer
                getattr(bpy.ops.object, 'boolean_auto_difference')("INVOKE_DEFAULT")
                self.refresh_3d(context)
    
    # ── NonDestructiveDifference ──
    def _drill_nondestructive(self, context, layer, drill_layer, cyl_filter):
        bpy.ops.object.select_all(action='DESELECT')
        layer.select_set(True)
        setattr(getattr(context.window_manager, 'booltron'), 'non_destructive.solver', 'EXACT')
        for obj in drill_layer.objects:
            if obj.type == 'MESH' and self._pass_filter(obj, cyl_filter):
                print(f'Drilling hole: {obj.name}')
                obj.select_set(True)
                layer.select_set(True)
                context.view_layer.objects.active = layer
                getattr(bpy.ops.object, 'booltron_nondestructive_difference')()
                self.refresh_3d(context)
    
    def _pass_filter(self, obj, cylinder_filter_setting):
        """Check if a drill cylinder passes the diameter filter."""
        if cylinder_filter_setting <= 0:
            return True
        if len(importdata.diameter_summary) == 0:
            return obj.dimensions.x >= cylinder_filter_setting
        info = importdata.diameter_summary.get(obj.name, {})
        return info.get('diameter', 0) >= cylinder_filter_setting
    
    def fix_object_encoding(self, obj):
        """Fix object encoding issues"""
        safe_name = obj.name.encode('ascii', 'ignore').decode('ascii')
        if safe_name and safe_name != obj.name:
            print(f"Renaming object: {obj.name} -> {safe_name}")
            obj.name = safe_name
        if obj.data:
            safe_data_name = obj.data.name.encode('ascii', 'ignore').decode('ascii')
            if safe_data_name != obj.data.name:
                obj.data.name = safe_data_name
        return obj
    
    def refresh_3d(self, context):
        areas = context.window.screen.areas
        for area in areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()


def pass_filtered(obj, cylinder_filter_setting):
    """Legacy filter function for backward compatibility."""
    if len(importdata.diameter_summary) == 0:
        if obj.dimensions.x >= cylinder_filter_setting:
            return True
    elif importdata.diameter_summary[obj.name]['diameter'] >= cylinder_filter_setting:
        return True
    return False
