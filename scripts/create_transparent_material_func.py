import bpy

def create_transparent_material(matname, color, transparency):
    #create a new material with a regular principled bsdf shader, that gets the color,
    # and a transparent shader. These are mixed with a mix_shader node.
    #Inputs: matname (string)
    #color: 4 element tuple, rgb+alpha, 0-1 
    #transparency = 0 -1


    bpy.data.materials.new(name = matname)
    mat = bpy.data.materials[matname]
    mat.use_nodes = True
    matnode_tree =mat.node_tree
    #matnode_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0
    
    # Get the existing Principled BSDF node
    bsdf_node = matnode_tree.nodes.get('Principled BSDF')
    if not bsdf_node:
        raise ValueError("Principled BSDF node not found in the material.")

    # Set the Base Color
    bsdf_node.inputs['Base Color'].default_value = color

    # Find Material Output node
    output_node = matnode_tree.nodes.get('Material Output')
    if not output_node:
        raise ValueError("Material Output node not found in the material.")
    output_node.location = (output_node.location.x +300, output_node.location.y)
    # Add the Mix Shader and Transparent BSDF nodes
    mix_shader_node = matnode_tree.nodes.new('ShaderNodeMixShader')
    mix_shader_node.location = (bsdf_node.location.x + 300, bsdf_node.location.y)

    transparent_node = matnode_tree.nodes.new('ShaderNodeBsdfTransparent')
    transparent_node.location = (bsdf_node.location.x, bsdf_node.location.y - 400)

    # Break the link between the Principled BSDF and the Material Output
    for link in matnode_tree.links:
        if link.from_node == bsdf_node and link.to_node == output_node:
            matnode_tree.links.remove(link)
            break

    # Create new links
    matnode_tree.links.new(bsdf_node.outputs['BSDF'], mix_shader_node.inputs[1])  # Connect Principled BSDF to Mix Shader's first input
    matnode_tree.links.new(transparent_node.outputs['BSDF'], mix_shader_node.inputs[2])  # Connect Transparent BSDF to Mix Shader's second input
    matnode_tree.links.new(mix_shader_node.outputs['Shader'], output_node.inputs['Surface'])  # Connect Mix Shader to Material Output

    # Set transparency factor
    mix_shader_node.inputs['Fac'].default_value = transparency

    return