import bpy

def create_muscle_material(muscle_name):
    #create a new material for a muscle.
    #Inputs: muscle_name (string)
    #muscle materials have the same names as the muscles themselves
    bpy.data.materials.new(name = muscle_name)
    
    mat = bpy.data.materials[muscle_name]
    mat.use_nodes = True
    
    matnode_tree =mat.node_tree
    matnode_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0
    matnode_tree.nodes.new(type = "ShaderNodeHueSaturation")
    
    #if blender type >4

    if bpy.app.version[0] <4: #if blender version is below 4
    
        nodename = 'Hue Saturation Value'

    else: #if blender version is above 4:  
        
        nodename = 'Hue/Saturation/Value'

    
    
    #the name should be different depending on Blender 3.0 or 4.0

    muscle_color = tuple(bpy.context.scene.muskemo.muscle_color)
    matnode_tree.nodes[nodename].inputs['Color'].default_value = muscle_color
    matnode_tree.nodes[nodename].inputs['Saturation'].default_value = 1
    matnode_tree.links.new(matnode_tree.nodes[nodename].outputs['Color'], matnode_tree.nodes["Principled BSDF"].inputs['Base Color'])
    
    ### viewport display color

    mat.diffuse_color = muscle_color

    return mat