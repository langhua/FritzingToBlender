import bpy
# 材质创建函数
def create_material(name, base_color, metallic=0.0, roughness=0.8):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    
    mat = bpy.data.materials.new(name=name)
    mat.diffuse_color = (*base_color, 1.0)
    mat.use_nodes = True
    
    # 清除默认节点
    if mat.node_tree:
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # 创建PBR材质节点
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        bsdf.inputs['Base Color'].__setattr__('default_value', (*base_color, 1.0))
        bsdf.inputs['Metallic'].__setattr__('default_value', metallic)
        bsdf.inputs['Roughness'].__setattr__('default_value', roughness)
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])
    
    return mat
