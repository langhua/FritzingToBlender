import bpy
from bpy.types import Operator, Mesh
from bpy.props import EnumProperty
import bmesh
from mathutils import Vector
from io_fritzing.assets.utils.material import create_material

ResistorTypes = EnumProperty(
        name="贴片电阻尺寸",
        items=[
            ('0402', "0402", "0402封装 (1.0×0.5mm)"),
            ('0603', "0603", "0603封装 (1.6×0.8mm)"),
            ('0805', "0805", "0805封装 (2.0×1.25mm)"),
            ('1206', "1206", "1206封装 (3.2×1.6mm)"),
            ('1210', "1210", "1210封装 (3.2×2.5mm)"),
            ('1812', "1812", "1812封装 (4.5×3.2mm)"),
            ('2010', "2010", "2010封装 (5.0×2.5mm)"),
            ('2512', "2512", "2512封装 (6.3×3.2mm)")
        ],
        default='0805'
    )

class SMD_RESISTOR_OT_Generate(Operator):
    """生成贴片电阻模型"""
    bl_idname = "resistor.generate_smd"
    bl_label = "生成贴片电阻"
    bl_description = "生成指定尺寸的贴片电阻3D模型"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if context and context.scene:
            smd_size = getattr(context.scene, "smd_resistor_size")
        # 根据选择的尺寸设置参数
        if smd_size == '0402':
            length_mm = 1.0
            width_mm = 0.5
            height_mm = 0.35
            terminal_length_mm = 0.25
        elif smd_size == '0603':
            length_mm = 1.6
            width_mm = 0.8
            height_mm = 0.45
            terminal_length_mm = 0.3
        elif smd_size == '1206':
            length_mm = 3.2
            width_mm = 1.6
            height_mm = 0.55
            terminal_length_mm = 0.5
        elif smd_size == '1210':
            length_mm = 3.2
            width_mm = 2.5
            height_mm = 0.55
            terminal_length_mm = 0.5
        elif smd_size == '1812':
            length_mm = 4.5
            width_mm = 3.2
            height_mm = 0.55
            terminal_length_mm = 0.6
        elif smd_size == '2010':
            length_mm = 5.0
            width_mm = 2.5
            height_mm = 0.55
            terminal_length_mm = 0.6
        elif smd_size == '2512':
            length_mm = 6.3
            width_mm = 3.2
            height_mm = 0.55
            terminal_length_mm = 0.7
        else:  # 0805
            length_mm = 2.0
            width_mm = 1.25
            height_mm = 0.5
            terminal_length_mm = 0.4
        
        self.create_smd_resistor(f"Resistor_{smd_size}", length_mm, width_mm, height_mm, terminal_length_mm)
        
        self.report({'INFO'}, f"{smd_size}贴片电阻生成完成！")
        return {'FINISHED'}
    
    def create_smd_resistor(self, collection_name, length_mm, width_mm, height_mm, terminal_length_mm):
        """创建贴片电阻"""
        # 创建集合
        collection = bpy.data.collections.new(collection_name)
        if bpy.context:
            bpy.context.scene.collection.children.link(collection)
        
        # 计算总长
        total_length = length_mm + 2 * terminal_length_mm
        
        # 创建材质
        metal_mat = create_material("SMD_Metal", (0.92, 0.92, 0.92), metallic=0.9, roughness=0.15)
        ceramic_mat = create_material("SMD_Ceramic", (0.75, 0.75, 0.75), metallic=0.0, roughness=0.8)
        coating_mat = create_material("SMD_Coating", (0.12, 0.12, 0.12), metallic=0.0, roughness=0.95)
        
        # 1. 创建陶瓷基体
        bm_ceramic = bmesh.new()
        ceramic_size = Vector((length_mm, width_mm, height_mm * 0.5))
        bmesh.ops.create_cube(bm_ceramic, size=1.0)
        for v in bm_ceramic.verts:
            v.co = v.co * ceramic_size
            v.co.z -= height_mm * 0.15
        
        mesh_ceramic = bpy.data.meshes.new("Ceramic_Base")
        bm_ceramic.to_mesh(mesh_ceramic)
        obj_ceramic = bpy.data.objects.new("Ceramic_Base", mesh_ceramic)
        collection.objects.link(obj_ceramic)
        if isinstance(obj_ceramic.data, Mesh):
            obj_ceramic.data.materials.append(ceramic_mat)
        
        # 2. 创建金属焊端
        bm_left = bmesh.new()
        left_terminal_size = Vector((terminal_length_mm, width_mm * 1.1, height_mm * 0.8))
        bmesh.ops.create_cube(bm_left, size=1.0)
        for v in bm_left.verts:
            v.co = v.co * left_terminal_size
            v.co.x -= length_mm / 2
            v.co.z += height_mm * 0.1
        
        mesh_left = bpy.data.meshes.new("Left_Terminal")
        bm_left.to_mesh(mesh_left)
        obj_left = bpy.data.objects.new("Left_Terminal", mesh_left)
        collection.objects.link(obj_left)
        if isinstance(obj_left.data, bpy.types.Mesh):
            obj_left.data.materials.append(metal_mat)
        
        bm_right = bmesh.new()
        right_terminal_size = Vector((terminal_length_mm, width_mm * 1.1, height_mm * 0.8))
        bmesh.ops.create_cube(bm_right, size=1.0)
        for v in bm_right.verts:
            v.co = v.co * right_terminal_size
            v.co.x += length_mm / 2
            v.co.z += height_mm * 0.1
        
        mesh_right = bpy.data.meshes.new("Right_Terminal")
        bm_right.to_mesh(mesh_right)
        obj_right = bpy.data.objects.new("Right_Terminal", mesh_right)
        collection.objects.link(obj_right)
        if isinstance(obj_right.data, bpy.types.Mesh):
            obj_right.data.materials.append(metal_mat)
        
        # 3. 创建电阻涂层
        bm_coating = bmesh.new()
        coating_size = Vector((length_mm * 0.9, width_mm * 0.8, height_mm * 0.4))
        bmesh.ops.create_cube(bm_coating, size=1.0)
        for v in bm_coating.verts:
            v.co = v.co * coating_size
            v.co.z += height_mm * 0.25
        
        mesh_coating = bpy.data.meshes.new("Resistor_Coating")
        bm_coating.to_mesh(mesh_coating)
        obj_coating = bpy.data.objects.new("Resistor_Coating", mesh_coating)
        collection.objects.link(obj_coating)
        if isinstance(obj_coating.data, bpy.types.Mesh):
            obj_coating.data.materials.append(coating_mat)
        
        # 清理bmesh
        bm_ceramic.free()
        bm_left.free()
        bm_right.free()
        bm_coating.free()
        
        # 选择所有对象
        bpy.ops.object.select_all(action='DESELECT')
        for obj in collection.objects:
            obj.select_set(True)
        
        if bpy.context:
            bpy.context.view_layer.objects.active = obj_coating

