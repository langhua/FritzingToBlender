import bpy
# 材质创建函数
def create_material(name, base_color, metallic=0.0, roughness=0.8, weight=None, ior=None, emission_color=None, emission_strength=0.0, alpha=1.0) -> bpy.types.Material:
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    
    mat = bpy.data.materials.new(name=name)
    if base_color is not None and len(base_color) == 3:
        mat.diffuse_color = (*base_color, 1.0)
    elif base_color is not None and len(base_color) == 4:
        mat.diffuse_color = base_color
    mat.use_nodes = True
    
    # 清除默认节点
    if mat.node_tree:
        nodes = mat.node_tree.nodes
        nodes.clear()
        
        # 创建PBR材质节点
        bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
        if base_color is not None and len(base_color) == 3:
            bsdf.inputs['Base Color'].__setattr__('default_value', (*base_color, 1.0))
        elif base_color is not None and len(base_color) == 4:
            bsdf.inputs['Base Color'].__setattr__('default_value', base_color)
        bsdf.inputs['Metallic'].__setattr__('default_value', metallic)
        bsdf.inputs['Roughness'].__setattr__('default_value', roughness)

        if alpha:
            bsdf.inputs['Alpha'].default_value = alpha
        if weight is not None:
            bsdf.inputs['Transmission Weight'].__setattr__('default_value', weight)
        if ior is not None:
            bsdf.inputs['IOR'].__setattr__('default_value', ior)
        
        output = nodes.new(type='ShaderNodeOutputMaterial')
        if weight is not None or ior is not None:
            output.location = (400, 0)
        mat.node_tree.links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

        if emission_color:
            bsdf.inputs['Emission Color'].default_value = (*emission_color, 1.0)
            bsdf.inputs['Emission Strength'].default_value = emission_strength
        
        if alpha < 1.0:
            mat.blend_method = 'BLEND'
            mat.shadow_method = 'CLIP'
            mat.show_transparent_back = True

    return mat
