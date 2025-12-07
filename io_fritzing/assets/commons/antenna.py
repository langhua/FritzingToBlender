import bpy
import math
import bmesh
from mathutils import Vector

def clear_scene():
    # 清除默认场景
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)

    # 设置单位为毫米显示
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'

def create_esp12f_antenna(pcb_length_mm, pcb_width_mm, left_margin_mm, top_margin_mm, trace_width_mm, trace_thickness_mm, copper_mat, antenna_collection):
    """创建天线 (12个段)"""
    # 计算坐标
    # 1. 起点(-板宽/2 + 0.5mm, -板高/2)，终点(-板宽/2 + 0.5mm, 板高/2 - 0.3mm)
    start1 = (-pcb_length_mm/2 + left_margin_mm + trace_width_mm/2, -pcb_width_mm/2)
    end1 = (-pcb_length_mm/2 + left_margin_mm + trace_width_mm/2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    
    # 2. 起点(-板宽/2 + 0.5mm, 板高/2 - 0.3mm)，终点((-板宽/2 + 0.5mm)/3, 板高/2 - 0.3mm)
    start2 = (-pcb_length_mm/2 + left_margin_mm + trace_width_mm/2 - trace_width_mm/2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    end2 = ((-pcb_length_mm/2 + left_margin_mm)/3 + trace_width_mm/2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    
    # 3. 起点((-板宽/2 + 0.5mm)/3 * 2, -板高/2)，终点((-板宽/2 + 0.5mm)/3 * 2, 板高/2 - 0.3mm)
    start3 = ((-pcb_length_mm/2 + left_margin_mm)/3 * 2, -pcb_width_mm/2)
    end3 = ((-pcb_length_mm/2 + left_margin_mm)/3 * 2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    
    # 4. 起点((-板宽/2 + 0.5mm)/3, 板高/2 - 0.3mm)，终点((-板宽/2 + 0.5mm)/3, 0)
    start4 = ((-pcb_length_mm/2 + left_margin_mm)/3, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    end4 = ((-pcb_length_mm/2 + left_margin_mm)/3, 0)
    
    # 5. 起点((-板宽/2 + 0.5mm)/3, 0)，终点(0, 0)
    start5 = ((-pcb_length_mm/2 + left_margin_mm)/3 - trace_width_mm/2, 0)
    end5 = (trace_width_mm/2, 0)
    
    # 6. 起点(0, 0)，终点(0, 板高/2 - 0.3mm)
    start6 = (0, 0)
    end6 = (0, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    
    # 7. 起点(0, 板高/2 - 0.3mm)，终点((板宽/2 - 0.5mm)/3, 板高/2 - 0.3mm)
    start7 = (-trace_width_mm/2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    end7 = ((pcb_length_mm/2 - left_margin_mm)/3 + trace_width_mm/2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    
    # 8. 起点((板宽/2 - 0.5mm)/3, 板高/2 - 0.3mm)，终点((板2 - 0.5mm)/3, 0)
    start8 = ((pcb_length_mm/2 - left_margin_mm)/3, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    end8 = ((pcb_length_mm/2 - left_margin_mm)/3, 0)
    
    # 9. 起点((板宽/2 - 0.5mm)/3, 0)，终点((板宽/2 - 0.5mm)/3 * 2, 0)
    start9 = ((pcb_length_mm/2 - left_margin_mm)/3 - trace_width_mm/2, 0)
    end9 = ((pcb_length_mm/2 - left_margin_mm)/3 * 2 + trace_width_mm/2, 0)
    
    # 10. 起点((板宽/2 - 0.5mm)/3 * 2, 0)，终点((板宽/2 - 0.5mm)/3 * 2, 板高/2 - 0.3mm)
    start10 = ((pcb_length_mm/2 - left_margin_mm)/3 * 2, 0)
    end10 = ((pcb_length_mm/2 - left_margin_mm)/3 * 2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    
    # 11. 起点((板宽/2 - 0.5mm)/3 * 2, 板高/2 - 0.3mm)，终点(板宽/2 - 0.5mm, 板高/2 - 0.3mm)
    start11 = ((pcb_length_mm/2 - left_margin_mm)/3 * 2 - trace_width_mm/2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    end11 = (pcb_length_mm/2 - left_margin_mm, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    
    # 12. 起点(板宽/2 - 0.5mm, 板高/2 - 0.3mm)，终点(板宽/2 - 0.5mm, -板高/2)
    start12 = (pcb_length_mm/2 - left_margin_mm - trace_width_mm/2, pcb_width_mm/2 - top_margin_mm - trace_width_mm/2)
    end12 = (pcb_length_mm/2 - left_margin_mm - trace_width_mm/2, -pcb_width_mm/2)
    
    # 创建12个线段
    segments = []
    segment_data = [
        (start1, end1, 1),
        (start2, end2, 2),
        (start3, end3, 3),
        (start4, end4, 4),
        (start5, end5, 5),
        (start6, end6, 6),
        (start7, end7, 7),
        (start8, end8, 8),
        (start9, end9, 9),
        (start10, end10, 10),
        (start11, end11, 11),
        (start12, end12, 12)
    ]
    
    for start, end, num in segment_data:
        segment = create_antenna_segment(start, end, num, trace_width_mm, trace_thickness_mm, copper_mat, antenna_collection)
        segments.append(segment)
        
        # 打印坐标信息
        print(f"段 {num}: 起点({start[0]:.2f}, {start[1]:.2f})mm -> 终点({end[0]:.2f}, {end[1]:.2f})mm")
        print(f"  -> 线段长度: {math.sqrt((end[0] - start[0])**2 + (end[1] - start[1])**2):.2f}mm")
    
    return segments
    
def create_antenna_segment(start_mm, end_mm, segment_number, trace_width, trace_thickness, copper_mat, antenna_collection):
    """创建天线线段"""
    start_x = start_mm[0]
    start_y = start_mm[1]
    end_x = end_mm[0]
    end_y = end_mm[1]
    
    # 计算线段的长度和角度
    dx = end_x - start_x
    dy = end_y - start_y
    length = math.sqrt(dx*dx + dy*dy)
    angle = math.atan2(dy, dx)
    
    # 中心点
    center_x = (start_x + end_x) / 2
    center_y = (start_y + end_y) / 2
    
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    segment = bpy.context.active_object
    segment.name = f"Antenna_Segment_{segment_number}"
    
    # 设置尺寸
    segment.dimensions = (length, trace_width, trace_thickness)
    segment.location = (center_x, center_y, 0)
    segment.rotation_euler.z = angle
    bpy.ops.object.transform_apply(scale=True)
    
    segment.data.materials.append(copper_mat)
    add_to_collection(antenna_collection, segment)
    return segment

def add_to_collection(antenna_collection, obj):
    if obj.name not in antenna_collection.objects:
        antenna_collection.objects.link(obj)
    if obj.name in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.unlink(obj)

def create_material(name, color, metallic=0.0, roughness=0.5):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    for node in nodes:
        nodes.remove(node)
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)
    output = nodes.new(type='ShaderNodeOutputMaterial')
    output.location = (300, 0)
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    bsdf.inputs['Base Color'].default_value = (*color, 1.0)
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    return mat

def create_antenna_pcb_model():
    """创建天线PCB模型的完整函数"""
    
    # 创建新集合
    antenna_collection = bpy.data.collections.new("Antenna_Model")
    bpy.context.scene.collection.children.link(antenna_collection)
    
    # ============================================
    # 1. 创建PCB板 (16×6×0.6mm)
    # 中心在(0,0,0)
    # ============================================
    pcb_length_mm = 16.0
    pcb_width_mm = 6.0
    pcb_thickness_mm = 0.6
    
    # 转换为米
    pcb_length = pcb_length_mm
    pcb_width = pcb_width_mm
    pcb_thickness = pcb_thickness_mm
    
    bpy.ops.mesh.primitive_cube_add(size=1.0)
    pcb = bpy.context.active_object
    pcb.name = "PCB_16x6"
    pcb.location = (0, 0, 0)
    
    # 设置PCB尺寸
    pcb.dimensions = (pcb_length, pcb_width, pcb_thickness)
    bpy.ops.object.transform_apply(scale=True)
    
    add_to_collection(antenna_collection, pcb)
    
    pcb_mat = create_material("PCB_Mat", (0.1, 0.1, 0.1))
    pcb_mat.diffuse_color = (0.1, 0.1, 0.1, 1)
    pcb.data.materials.append(pcb_mat)
    
    # ============================================
    # 2. 创建天线 (12段，宽度0.5mm)
    # 使用中提供的坐标
    # ============================================
    copper_mat = create_material("Copper_Mat", (0.9, 0.6, 0.2), metallic=0.9, roughness=0.3)  # 黄色铜
    copper_mat.diffuse_color = (0.9, 0.6, 0.2, 1)
    left_margin_mm = 0.5
    top_margin_mm = 0.3
    
    # 天线尺寸
    trace_width_mm = 0.5
    trace_thickness_mm = 0.035  # 1oz铜厚 ≈ 0.035mm
    
    trace_width = trace_width_mm
    trace_thickness = trace_thickness_mm
    
    # 天线Z位置 (在PCB板上)
    trace_z = pcb_thickness/2 + trace_thickness/2
    
    # 创建天线
    antenna_segments = create_esp12f_antenna(pcb_length_mm, pcb_width_mm, left_margin_mm, top_margin_mm, trace_width_mm, trace_thickness_mm, copper_mat, antenna_collection)
    for segment in antenna_segments:
        segment.location.z = trace_z
    
    # ============================================
    # 4. 设置视图
    # ============================================
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces[0].shading.type = 'MATERIAL'
    
    # 模型信息
    print("\n" + "=" * 50)
    print("天线PCB模型创建完成！")
    print(f"PCB尺寸: {pcb_length_mm}×{pcb_width_mm}×{pcb_thickness_mm}mm")
    print(f"PCB中心坐标: (0, 0)")
    print(f"PCB实际尺寸: {pcb.dimensions.x:.2f}×{pcb.dimensions.y:.2f}×{pcb.dimensions.z:.2f}mm")
    print(f"天线线宽: {trace_width_mm}mm")
    print(f"天线铜厚: {trace_thickness_mm:.3f}mm (1oz)")
    print(f"天线材质: 铜 (黄色)")
    print(f"PCB材质: 黑色")
    print(f"天线线段数量: {antenna_segments}段")
    print("=" * 50)
    
    return antenna_collection, pcb, antenna_segments

def main():
    clear_scene()
    
    """主函数入口"""
    print("开始创建天线PCB模型...")
    print("=" * 50)
    print("根据描述重新创建天线：")
    print("PCB尺寸: 16×6×0.6mm")
    print("天线: 12段线段，宽度0.5mm")
    print("PCB中心: (0, 0)")
    print("坐标计算:")
    print(f"  PCB宽度: 16mm, 半宽: 8mm")
    print(f"  PCB高度: 6mm, 半高: 3mm")
    print("=" * 50)
    
    try:
        collection, pcb, antenna_segments = create_antenna_pcb_model()
        
        # 验证模型
        print(f"\nPCB尺寸验证: {pcb.dimensions.x:.2f}×{pcb.dimensions.y:.2f}×{pcb.dimensions.z:.2f}mm")
        
        # 验证PCB尺寸
        pcb_length = pcb.dimensions.x
        pcb_width = pcb.dimensions.y
        pcb_thickness = pcb.dimensions.z
        
        expected_length = 16.0
        expected_width = 6.0
        expected_thickness = 0.6
        
        if (abs(pcb_length - expected_length) < 0.1 and 
            abs(pcb_width - expected_width) < 0.1 and 
            abs(pcb_thickness - expected_thickness) < 0.1):
            print(f"✓ PCB尺寸正确: {pcb_length:.2f}×{pcb_width:.2f}×{pcb_thickness:.2f}mm")
        else:
            print(f"⚠ PCB尺寸不符: 期望{expected_length}×{expected_width}×{expected_thickness}mm, 实际{pcb_length:.2f}×{pcb_width:.2f}×{pcb_thickness:.2f}mm")
        
        # 统计对象数量
        pcb_count = len([obj for obj in collection.objects if "PCB" in obj.name])
        antenna_count = len([obj for obj in collection.objects if "Antenna_Segment" in obj.name])
        feed_count = len([obj for obj in collection.objects if "Feed" in obj.name])
        text_count = len([obj for obj in collection.objects if "Text" in obj.name])
        
        print(f"\nPCB对象: {pcb_count}个")
        print(f"天线线段对象: {antenna_count}个")
        print(f"馈点: {feed_count}个")
        print(f"文字: {text_count}个 (M)")
        
        print(f"\n天线线段信息:")
        antenna_segments = [obj for obj in collection.objects if "Antenna_Segment" in obj.name]
        antenna_segments.sort(key=lambda x: int(x.name.split('_')[-1]))
        
        for segment in antenna_segments:
            segment_num = segment.name.split('_')[-1]
            pos_x_mm = segment.location.x
            pos_y_mm = segment.location.y
            pos_z_mm = segment.location.z
            dimensions_mm = segment.dimensions
            print(f"  段{segment_num}: 中心位置({pos_x_mm:.2f}, {pos_y_mm:.2f}, {pos_z_mm:.2f})mm, 尺寸({dimensions_mm.x:.2f}×{dimensions_mm.y:.2f}×{dimensions_mm.z:.2f})mm")
        
        print(f"\n模型创建成功！")
        print(f"在Outliner中查看'Antenna_Model'集合")
        print(f"包含12段天线线段，精确按照描述中的坐标构建")
        print(f"天线宽度: 0.5mm")
        print(f"天线在PCB中心(0,0)对称分布")
        print("=" * 50)
        
    except Exception as e:
        print(f"创建模型时出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()