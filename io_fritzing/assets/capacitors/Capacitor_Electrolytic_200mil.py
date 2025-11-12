import bpy
import bmesh
from mathutils import Vector
import math

def safe_clean_scene():
    """安全地清理场景，避免上下文错误"""
    # 确保在对象模式下
    if bpy.context.active_object is not None:
        if bpy.context.active_object.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
    
    # 选择并删除所有对象
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
    
    if bpy.context.selected_objects:
        bpy.ops.object.delete(use_global=False)
        
    # 设置场景单位
    scene = bpy.context.scene
    scene.unit_settings.system = 'METRIC'
    scene.unit_settings.length_unit = 'MILLIMETERS'
    scene.unit_settings.scale_length = 0.001


def create_electrolytic_capacitor(rad_type="RAD-0.2", capacitance="10uF", voltage="16V"):
    """
    创建直插电解电容3D模型，将负极标志与电容主体质心对齐
    """
    
    # 安全清理场景
    safe_clean_scene()
    
    # 电解电容尺寸参数
    dimensions = {
        "100mil": {
            "pin_spacing": 2.54,
            "body_diameter": 4.5,
            "body_height": 11.0,
            "pin_length": 12.0,
            "pin_diameter": 0.6,
            "base_height": 1.0
        },
        "200mil": {
            "pin_spacing": 5.08,
            "body_diameter": 6.0,
            "body_height": 16.0,
            "pin_length": 15.0,
            "pin_diameter": 0.7,
            "base_height": 1.2
        },
        "300mil": {
            "pin_spacing": 7.62,
            "body_diameter": 8.0,
            "body_height": 20.0,
            "pin_length": 18.0,
            "pin_diameter": 0.8,
            "base_height": 1.5
        }
    }
    
    if rad_type not in dimensions:
        rad_type = "200mil"
    
    dim = dimensions[rad_type]
    
    # 创建电容主体（铝壳）
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=dim["body_diameter"] / 2,
        depth=dim["body_height"],
        location=(0, 0, dim["body_height"] / 2 + dim["base_height"])
    )
    body = bpy.context.active_object
    body.name = f"Electrolytic_Capacitor_Body_{rad_type}"
    
    # 创建底部基座
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=dim["body_diameter"] / 2 + 0.3,
        depth=dim["base_height"],
        location=(0, 0, dim["base_height"] / 2)
    )
    base = bpy.context.active_object
    base.name = f"Capacitor_Base_{rad_type}"
    
    # 创建引脚
    pin_spacing = dim["pin_spacing"] / 2
    
    # 负极引脚
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=dim["pin_diameter"] / 2,
        depth=dim["pin_length"],
        location=(-pin_spacing, 0, -dim["pin_length"] / 2)
    )
    pin_negative = bpy.context.active_object
    pin_negative.name = f"Pin_Negative_{rad_type}"
    
    # 正极引脚
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=16,
        radius=dim["pin_diameter"] / 2,
        depth=dim["pin_length"] * 1.2,
        location=(pin_spacing, 0, -dim["pin_length"] * 0.6)
    )
    pin_positive = bpy.context.active_object
    pin_positive.name = f"Pin_Positive_{rad_type}"
    
    # 创建正确贴合的负极带，与电容主体质心对齐
    stripe = create_aligned_negative_stripe(body, dim)
    
    # 分配材质
    assign_materials(body, base, pin_negative, pin_positive, stripe, dim, rad_type)
    
    # 组织到集合
    all_objects = [body, base, pin_negative, pin_positive]
    if stripe:
        all_objects.append(stripe)
    organize_collection(all_objects, rad_type)
    
    print(f"成功创建 {rad_type} 封装电解电容模型，电容值: {capacitance}，电压: {voltage}")
    return body

def create_aligned_negative_stripe(body, dim):
    """创建与电容主体质心对齐的负极带"""
    body_radius = dim["body_diameter"] / 2
    body_height = dim["body_height"]
    base_height = dim["base_height"]
    
    # 计算电容主体的质心位置
    body_center_z = base_height + body_height / 2
    
    # 创建一个薄的圆柱体作为负极带
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=32,
        radius=body_radius + 0.1,
        depth=body_height,
        location=(0, 0, body_center_z)  # 初始位置与电容主体质心对齐
    )
    stripe = bpy.context.active_object
    stripe.name = "Negative_Stripe"
    
    # 进入编辑模式，删除不需要的部分
    bpy.context.view_layer.objects.active = stripe
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    
    # 使用bmesh进行精确操作
    bm = bmesh.from_edit_mesh(stripe.data)
    
    # 删除顶部和底部面
    bpy.ops.mesh.select_all(action='DESELECT')
    for face in bm.faces:
        if abs(face.normal.z) > 0.9:  # 选择顶部和底部面
            face.select = True
    
    bpy.ops.mesh.delete(type='FACE')
    
    # 删除大部分侧面，只保留一小部分作为负极带
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.select_all(action='DESELECT')
    
    # 选择Y轴正方向的面（大约45度范围）
    for face in bm.faces:
        center = face.calc_center_median()
        # 计算角度，只保留Y轴正方向的面
        if center.y > 0 and abs(center.x) < body_radius * 0.3:
            face.select = True
    
    # 反选并删除
    bpy.ops.mesh.select_all(action='INVERT')
    bpy.ops.mesh.delete(type='FACE')
    
    # 退出编辑模式
    bpy.ops.object.mode_set(mode='OBJECT')
    
    # 添加实体化修改器，使负极带有厚度
    solidify = stripe.modifiers.new(name="Solidify", type='SOLIDIFY')
    solidify.thickness = 0.1
    solidify.offset = 0.0
    bpy.ops.object.modifier_apply(modifier=solidify.name)
    
    # 围绕Z轴逆时针旋转90度
    stripe.rotation_euler.z = math.radians(90)
    
    # 调整位置，使其贴合电容主体表面
    # 由于已经与质心对齐，只需要向外移动半径距离
#    stripe.location.y -= body_radius - 0.05
    stripe.location.x += 0.1
    stripe.location.z -= body_height / 2 + base_height
    
    # 将负极带设为主体的子对象
    stripe.parent = body
    
    return stripe

def assign_materials(body, base, pin_negative, pin_positive, stripe, dim, rad_type):
    """分配材质"""
    
    def create_material(name, color, metallic=0.0, roughness=0.4):
        mat = bpy.data.materials.new(name=name)
        mat.diffuse_color = color
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = metallic
        bsdf.inputs['Roughness'].default_value = roughness
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        
        links = mat.node_tree.links
        links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
        
        return mat
    
    # 修正颜色
    # 电容主体使用深灰色 (0.3, 0.3, 0.3)
    body_material = create_material("Aluminum_Body", (0.3, 0.3, 0.3, 1.0), metallic=0.1, roughness=0.6)
    # 基座材质使用黑色
    base_material = create_material("Plastic_Base", (0.1, 0.1, 0.1, 1.0), metallic=0.0, roughness=0.8)
    # 引脚材质使用金属色
    pin_material = create_material("Pin_Material", (0.8, 0.8, 0.8, 1.0), metallic=0.8, roughness=0.2)
    # 负极带材质使用浅灰色 (0.8, 0.8, 0.8)
    stripe_material = create_material("Negative_Stripe", (0.8, 0.8, 0.8, 1.0), metallic=0.1, roughness=0.8)
    
    # 为所有对象分配材质
    for obj, mat in [(body, body_material), (base, base_material), 
                     (pin_negative, pin_material), (pin_positive, pin_material)]:
        if len(obj.data.materials) == 0:
            obj.data.materials.append(mat)
        else:
            obj.data.materials[0] = mat
    
    if stripe:
        if len(stripe.data.materials) == 0:
            stripe.data.materials.append(stripe_material)
        else:
            stripe.data.materials[0] = stripe_material

def organize_collection(objects, rad_type):
    """组织到集合"""
    collection_name = f"Electrolytic_Capacitor_{rad_type}"
    
    # 创建新集合
    if collection_name in bpy.data.collections:
        collection = bpy.data.collections[collection_name]
    else:
        collection = bpy.data.collections.new(collection_name)
        bpy.context.scene.collection.children.link(collection)
    
    # 确保所有对象都在场景集合中
    for obj in objects:
        if obj.name not in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.link(obj)
    
    # 将对象移动到新集合
    for obj in objects:
        # 如果对象在其他集合中，先移除
        for coll in obj.users_collection:
            coll.objects.unlink(obj)
        # 添加到新集合
        collection.objects.link(obj)
    
    # 设置活动对象
    if objects:
        bpy.context.view_layer.objects.active = objects[0]

# 使用示例
if __name__ == "__main__":
    # 创建单个电解电容
    create_electrolytic_capacitor("200mil", "100uF", "25V")
    
    # 更新视图
    bpy.context.view_layer.update()
