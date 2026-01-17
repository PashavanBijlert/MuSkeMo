import bpy
from math import nan

def create_landmark(landmark_name, landmark_radius, collection_name,
                    pos_in_global = [nan]*3,
                  is_global = True, 
                 parent_body = 'not_assigned', pos_in_parent_frame = [nan]*3):


    muskemo = bpy.context.scene.muskemo


    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the landmarks

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
    #Make sure the landmarks collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]    

    ## Create landmark
    bpy.ops.mesh.primitive_uv_sphere_add(radius=landmark_radius, enter_editmode=False, align='WORLD', location = pos_in_global) #create a sphere
    bpy.context.object.name = landmark_name #set the name
    bpy.context.object.data.name = landmark_name #set the name of the object data

    landmark_name = bpy.context.object.name ### because duplicate names get automatically numbered in Blender
    bpy.context.object['MuSkeMo_type'] = 'LANDMARK'    #to inform the user what type is created
    bpy.context.object.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  

    bpy.ops.object.select_all(action='DESELECT')


    obj = bpy.data.objects[landmark_name]

    parent_body_obj = bpy.data.objects[parent_body]
    obj.parent = parent_body_obj

    #this undoes the transformation after parenting
    obj.matrix_parent_inverse = parent_body_obj.matrix_world.inverted()

    
    ##### Assign a material
    matname = 'marker_material'
    color = tuple(muskemo.marker_color)
    transparency = 0.5
        
            
    if matname not in bpy.data.materials:   #if the material doesn't exist, get it
        from .create_transparent_material_func import create_transparent_material
        create_transparent_material(matname, color, transparency)

    mat = bpy.data.materials[matname]
    obj.data.materials.append(mat)

    ### viewport display color

    obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
            
        