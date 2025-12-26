import bpy
from io_fritzing.svg.report import importdata
from bpy.types import Operator
from mathutils import Vector

class MergeLayers(Operator):
    bl_idname = "fritzing.merge_layers"
    bl_label = "Fritzing post import: merge layers"
    
    def execute(self, context):
        try:
            svgLayers = importdata.svgLayers
            joinedLayer = None
            if svgLayers:
                bpy.ops.object.select_all(action="DESELECT")
                for layerClass, layer in svgLayers.items():
                    if layerClass != 'drill':
                        layer.select_set(True)
                for layerClass, layer in svgLayers.items():
                    if layerClass != 'drill' and bpy.context:
                        bpy.context.view_layer.objects.active = layer
                        break
                bpy.ops.object.join()
                if bpy.context:
                    joinedLayer = bpy.context.view_layer.objects.active
                    if joinedLayer:
                        joinedLayer.name = 'JoinedLayer'
                        # 获取物体边界框
                        bbox = [joinedLayer.matrix_world @ Vector(corner) for corner in joinedLayer.bound_box]
                        # x轴最小值
                        x_min = min(v.x for v in bbox)
                        y_min = min(v.y for v in bbox)
                        # 移动到原点
                        joinedLayer.location.x -= x_min
                        joinedLayer.location.y -= y_min
                        joinedLayer.lock_scale = (True, True, True)
        except Exception as e:
            print('--MergeLayers exception: ' + str(e))
            importdata.error_msg = str(e)
            getattr(getattr(bpy.ops, 'fritzing'), 'import_error')("INVOKE_DEFAULT")

        # importdata.step_name = 'FINISHED'
        importdata.step_name = 'POST_DRILL_HOLES'
        return {"FINISHED"}
