import bpy
import bmesh
from mathutils import Vector

# 清理默认场景
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False, confirm=False)

# 定义常见贴片电容封装尺寸（单位：毫米）- 保留所有尺寸
CAPACITOR_SIZES = {
    '0402': {'length': 1.0, 'width': 0.5, 'height': 0.5},
    '0603': {'length': 1.6, 'width': 0.8, 'height': 0.8},
    '0805': {'length': 2.0, 'width': 1.25, 'height': 1.0},
    '1206': {'length': 3.2, 'width': 1.6, 'height': 1.2},
    '1210': {'length': 3.2, 'width': 2.5, 'height': 1.5},
    '1812': {'length': 4.5, 'width': 3.2, 'height': 1.6}
}

def create_capacitor_material(name, base_color, metallic=0.0, roughness=0.8):
    """创建电容材质"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    rgba_color = (*base_color, 1.0)
    mat.diffuse_color = rgba_color
    
    nodes = mat.node_tree.nodes
    nodes.clear()
    
    bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
    bsdf.inputs['Base Color'].default_value = rgba_color
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Roughness'].default_value = roughness
    
    output = nodes.new(type='ShaderNodeOutputMaterial')
    mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat

def create_capacitor(size_name='1206'):
    """创建单个陶瓷贴片电容"""
    if size_name not in CAPACITOR_SIZES:
        size_name = '1206'
    
    dimensions = CAPACITOR_SIZES[size_name]
    length = dimensions['length']
    width = dimensions['width']
    height = dimensions['height']
    
    # 焊端参数（尺寸等于电容尺寸）
    terminal_length = length * 0.3
    terminal_width = width
    terminal_height = height
    
    # 陶瓷本体参数（尺寸为电容尺寸的95%）
    body_length = length - 2 * terminal_length
    body_width = width * 0.95
    body_height = height * 0.95
    
    # 创建集合
    collection_name = f"Ceramic_Capacitor_{size_name}"
    collection = bpy.data.collections.new(collection_name)
    bpy.context.scene.collection.children.link(collection)
    
    # 创建材质（陶瓷本体颜色加深）
    ceramic_mat = create_capacitor_material("Ceramic_Body_Dark", (0.7, 0.7, 0.75), metallic=0.0, roughness=0.9)
    terminal_mat = create_capacitor_material("Terminal_Metal", (0.9, 0.9, 0.92), metallic=0.95, roughness=0.15)
    
    # 1. 创建陶瓷本体
    bm_body = bmesh.new()
    body_size = Vector((body_length, body_width, body_height))
    bmesh.ops.create_cube(bm_body, size=1.0)
    for v in bm_body.verts:
        v.co = v.co * body_size
    
    mesh_body = bpy.data.meshes.new("Ceramic_Body")
    bm_body.to_mesh(mesh_body)
    obj_body = bpy.data.objects.new("Ceramic_Body", mesh_body)
    collection.objects.link(obj_body)
    obj_body.data.materials.append(ceramic_mat)
    
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
    
    # 选择所有对象
    bpy.ops.object.select_all(action='DESELECT')
    for obj in collection.objects:
        obj.select_set(True)
    
    bpy.context.view_layer.objects.active = obj_body
    
    return collection, dimensions

def create_multiple_capacitors():
    """创建多个不同封装的陶瓷电容并水平排列（保留此函数供需要时使用）"""
    capacitor_sizes = ['0805', '1210', '1812']
    main_collection = bpy.data.collections.new("Multiple_Ceramic_Capacitors")
    bpy.context.scene.collection.children.link(main_collection)
    
    spacing = 15.0
    current_x = 0.0
    
    for size_name in capacitor_sizes:
        sub_collection = bpy.data.collections.new(f"Capacitor_{size_name}")
        main_collection.children.link(sub_collection)
        
        dimensions = CAPACITOR_SIZES[size_name]
        length = dimensions['length']
        width = dimensions['width']
        height = dimensions['height']
        
        terminal_length = length * 0.3
        terminal_width = width
        terminal_height = height
        body_length = length - 2 * terminal_length
        body_width = width * 0.95
        body_height = height * 0.95
        
        ceramic_mat = create_capacitor_material(f"Ceramic_{size_name}", (0.7, 0.7, 0.75), metallic=0.0, roughness=0.9)
        terminal_mat = create_capacitor_material(f"Terminal_{size_name}", (0.9, 0.9, 0.92), metallic=0.95, roughness=0.15)
        
        # 创建陶瓷本体
        bm_body = bmesh.new()
        body_size = Vector((body_length, body_width, body_height))
        bmesh.ops.create_cube(bm_body, size=1.0)
        for v in bm_body.verts:
            v.co = v.co * body_size
            v.co.x += current_x
        
        mesh_body = bpy.data.meshes.new(f"Ceramic_Body_{size_name}")
        bm_body.to_mesh(mesh_body)
        obj_body = bpy.data.objects.new(f"Ceramic_Body_{size_name}", mesh_body)
        sub_collection.objects.link(obj_body)
        obj_body.data.materials.append(ceramic_mat)
        
        # 创建左侧焊端
        bm_left_terminal = bmesh.new()
        left_terminal_size = Vector((terminal_length, terminal_width, terminal_height))
        bmesh.ops.create_cube(bm_left_terminal, size=1.0)
        for v in bm_left_terminal.verts:
            v.co = v.co * left_terminal_size
            v.co.x -= (body_length + terminal_length) / 2
            v.co.x += current_x
        
        mesh_left_terminal = bpy.data.meshes.new(f"Left_Terminal_{size_name}")
        bm_left_terminal.to_mesh(mesh_left_terminal)
        obj_left_terminal = bpy.data.objects.new(f"Left_Terminal_{size_name}", mesh_left_terminal)
        sub_collection.objects.link(obj_left_terminal)
        obj_left_terminal.data.materials.append(terminal_mat)
        
        # 创建右侧焊端
        bm_right_terminal = bmesh.new()
        right_terminal_size = Vector((terminal_length, terminal_width, terminal_height))
        bmesh.ops.create_cube(bm_right_terminal, size=1.0)
        for v in bm_right_terminal.verts:
            v.co = v.co * right_terminal_size
            v.co.x += (body_length + terminal_length) / 2
            v.co.x += current_x
        
        mesh_right_terminal = bpy.data.meshes.new(f"Right_Terminal_{size_name}")
        bm_right_terminal.to_mesh(mesh_right_terminal)
        obj_right_terminal = bpy.data.objects.new(f"Right_Terminal_{size_name}", mesh_right_terminal)
        sub_collection.objects.link(obj_right_terminal)
        obj_right_terminal.data.materials.append(terminal_mat)
        
        bm_body.free()
        bm_left_terminal.free()
        bm_right_terminal.free()
        
        current_x += length + spacing
    
    bpy.ops.object.select_all(action='DESELECT')
    for obj in main_collection.all_objects:
        obj.select_set(True)
    
    return main_collection

# 默认创建1206封装的陶瓷电容（根据用户需求修改）
collection, dimensions = create_capacitor('1206')

print("陶瓷贴片电容3D模型生成完毕！")
print("默认显示：1206封装")
print(f"尺寸：{dimensions['length']}mm × {dimensions['width']}mm × {dimensions['height']}mm")
print("可用封装尺寸：")
for size_name, dim in CAPACITOR_SIZES.items():
    print(f"- {size_name}: {dim['length']}mm × {dim['width']}mm × {dim['height']}mm")
print("如需创建其他封装，可调用 create_capacitor('尺寸名称') 函数")
print("如需创建多个电容，可调用 create_multiple_capacitors() 函数")
