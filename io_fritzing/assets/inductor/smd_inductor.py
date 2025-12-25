import bpy
import bmesh
from mathutils import Vector
from io_fritzing.assets.utils.scene import clear_scene, create_lighting, create_camera
from io_fritzing.assets.utils.origin import set_origin_to_bottom
from io_fritzing.assets.utils.material import create_material

# 定义常见贴片电感封装尺寸（单位：毫米）- 保留所有尺寸
INDUCTOR_SIZES = {
    '0402': {'length': 1.0, 'width': 0.5, 'height': 0.5},
    '0603': {'length': 1.6, 'width': 0.8, 'height': 0.8},
    '0805': {'length': 2.0, 'width': 1.25, 'height': 1.0},
    '1206': {'length': 3.2, 'width': 1.6, 'height': 1.2},
    '1210': {'length': 3.2, 'width': 2.5, 'height': 1.5},
    '1812': {'length': 4.5, 'width': 3.2, 'height': 1.6}
}


def create_smd_inductor_model(size_name='0603'):
    """创建单个叠层高频电感"""
    if size_name not in INDUCTOR_SIZES:
        size_name = '0603'
    
    dimensions = INDUCTOR_SIZES[size_name]
    length = dimensions['length']
    width = dimensions['width']
    height = dimensions['height']
    
    # 焊端参数（尺寸等于电容尺寸）
    terminal_length = length * 0.2
    terminal_width = width
    terminal_height = height
    
    # 叠层本体参数（尺寸为电容尺寸的95%）
    body_length = length - 2 * terminal_length
    body_width = width * 0.95
    body_height = height * 0.95
    
    # 创建集合
    collection_name = f"Inductor_Layer_{size_name}"
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    
    # 创建材质
    layer_mat = create_material(name="Inductor_Layer", base_color=(0.15, 0.25, 0.15), metallic=0.0, roughness=0.2)
    terminal_mat = create_material(name="Terminal_Metal", base_color=(0.9, 0.9, 0.92), metallic=0.95, roughness=0.15)
    
    # 1. 创建叠层本体
    bm_body = bmesh.new()
    body_size = Vector((body_length, body_width, body_height))
    bmesh.ops.create_cube(bm_body, size=1.0)
    for v in bm_body.verts:
        v.co = v.co * body_size
    
    mesh_body = bpy.data.meshes.new("Inductor_Layer_Body")
    bm_body.to_mesh(mesh_body)
    obj_body = bpy.data.objects.new("Inductor_Layer_Body", mesh_body)
    collection.objects.link(obj_body)
    obj_body.data.materials.clear()
    obj_body.data.materials.append(layer_mat)
    
    # 2. 创建左侧金属焊端
    bm_left_terminal = bmesh.new()
    left_terminal_size = Vector((terminal_length, terminal_width, terminal_height))
    bmesh.ops.create_cube(bm_left_terminal, size=1.0)
    for v in bm_left_terminal.verts:
        v.co = v.co * left_terminal_size
        v.co.x -= (body_length + terminal_length) / 2
    
    mesh_left_terminal = bpy.data.meshes.new("Left_Terminal")
    bm_left_terminal.to_mesh(mesh_left_terminal)
    obj_left_terminal = bpy.data.objects.new("Left_Terminal", mesh_left_terminal)
    collection.objects.link(obj_left_terminal)
    obj_left_terminal.data.materials.append(terminal_mat)
    
    # 3. 创建右侧金属焊端
    bm_right_terminal = bmesh.new()
    right_terminal_size = Vector((terminal_length, terminal_width, terminal_height))
    bmesh.ops.create_cube(bm_right_terminal, size=1.0)
    for v in bm_right_terminal.verts:
        v.co = v.co * right_terminal_size
        v.co.x += (body_length + terminal_length) / 2
    
    mesh_right_terminal = bpy.data.meshes.new("Right_Terminal")
    bm_right_terminal.to_mesh(mesh_right_terminal)
    obj_right_terminal = bpy.data.objects.new("Right_Terminal", mesh_right_terminal)
    collection.objects.link(obj_right_terminal)
    obj_right_terminal.data.materials.append(terminal_mat)
    
    # 清理bmesh
    bm_body.free()
    bm_left_terminal.free()
    bm_right_terminal.free()
    
    # 合并所有对象
    bpy.ops.object.select_all(action='DESELECT')
    obj_body.select_set(True)
    obj_left_terminal.select_set(True)
    obj_right_terminal.select_set(True)
    bpy.context.view_layer.objects.active = obj_body
    bpy.ops.object.join()
    obj_body.name = f"SMD_Inductor_{size_name}"

    set_origin_to_bottom(obj_body)

    return obj_body

def main():
    clear_scene()

    # 创建主集合
    collection = bpy.data.collections.new("Inductor_Collection")
    bpy.context.scene.collection.children.link(collection)
    
    print("=" * 60)
    print("创建多种叠层高频电感3D模型")
    print(f"将创建 {len(INDUCTOR_SIZES.keys())} 个叠层高频电感模型")
    
    inducs = []
    y_offset = 0
    increment = 1
    
    for key in INDUCTOR_SIZES.keys():
        inductor = create_smd_inductor_model(key)
        inductor.location.y += y_offset
        y_offset += 2 + increment
        increment += 0.5
        # 添加到集合
        collection.objects.link(inductor)
        inducs.append(inductor)

    print("叠层高频电感3D模型生成完毕！")

    # 创建照明
    print("创建照明...")
    sun, fill_light = create_lighting()
    collection.objects.link(sun)
    collection.objects.link(fill_light)
    
    # 创建相机
    print("创建相机...")
    camera = create_camera()
    collection.objects.link(camera)
    
    # 设置渲染设置
    bpy.context.scene.render.engine = 'CYCLES'
    bpy.context.scene.cycles.samples = 128
    bpy.context.scene.render.resolution_x = 1920
    bpy.context.scene.render.resolution_y = 1080

    # 设置视图显示
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            # 透视视图
            area.spaces[0].region_3d.view_perspective = 'PERSP'
            # 设置视图距离
            area.spaces[0].region_3d.view_distance = 50
            # 设置合适的视角
            area.spaces[0].region_3d.view_rotation = (0.7, 0.4, 0.4, 0.5)
            # 设置显示模式
            area.spaces[0].shading.type = 'RENDERED'
            area.spaces[0].shading.color_type = 'MATERIAL'
            area.spaces[0].shading.show_object_outline = True
    
    return collection


if __name__ == "__main__":
    main()
