import bpy
from math import nan

def create_wrapgeom(name, geomtype, collection_name,
                    parent_body='not_assigned', 
                    pos_in_global=[nan] * 3,
                    or_in_global_XYZeuler=[nan] * 3, 
                    or_in_global_quat=[nan] * 4,
                    pos_in_parent_frame=[nan] * 3,
                    or_in_parent_frame_XYZeuler=[nan] * 3, 
                    or_in_parent_frame_quat=[nan] * 4,
                    dimensions = {},
                    ):
    
    from .quaternions import matrix_from_quaternion
    from .euler_XYZ_body import matrix_from_euler_XYZbody

    #check if the collection name exists, and if not create it
    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the scaled contacts

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
    
    #Make sure the "contacts" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]


    if geomtype == 'Cylinder':
        # Create a cylinder using bpy.ops
        bpy.ops.mesh.primitive_cylinder_add(
            radius=dimensions['radius'], 
            depth=dimensions['height'], 
            
        )


        bpy.context.object.name = name #set the name
        bpy.context.object.data.name = name #set the name of the object data
        obj = bpy.data.objects[name]

        obj['wrap_type'] = 'WRAP'    #to inform the user what type is created
        obj.id_properties_ui('wrap_type').update(description = "The object type. Warning: don't modify this!")


        obj['cylinder_radius'] = dimensions['radius']    #to inform the user what type is created
        obj.id_properties_ui('cylinder_radius').update(description = "Cylinder radius in m")

        obj['cylinder_height'] = dimensions['height']    #to inform the user what type is created
        obj.id_properties_ui('cylinder_height').update(description = "Cylinder height in m")


    bpy.context.object.name = name #set the name
    bpy.context.object.data.name = name #set the name of the object data
    obj = bpy.data.objects[name]
    obj.rotation_mode = 'ZYX'    #change rotation sequence

    obj['MuSkeMo_type'] = 'WRAP'    #to inform the user what type is created
    obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")

    
    obj['parent_body'] = parent_body    #to inform the user what type is created
    obj.id_properties_ui('parent_body').update(description = "The parent body of this wrap geometry")

    obj['pos_in_parent_frame'] = pos_in_parent_frame
    obj.id_properties_ui('pos_in_parent_frame').update(description = 'Wrap geometry position in the parent body anatomical (local) reference frame (x, y, z, in meters). Optional.')

    obj['or_in_parent_frame_XYZeuler'] = or_in_parent_frame_XYZeuler
    obj.id_properties_ui('or_in_parent_frame_XYZeuler').update(description='Wrap geometry orientation XYZ-Euler angles in the parent body anatomical (local) reference frame (x, y, z, in rad). Optional.')

    obj['or_in_parent_frame_quat'] = or_in_parent_frame_quat
    obj.id_properties_ui('or_in_parent_frame_quat').update(description='Wrap geometry orientation quaternion decomposition in the parent body anatomical (local) reference frame (w, x, y, z). Optional.')


    bpy.ops.object.select_all(action='DESELECT') 


    if or_in_global_quat !=[nan]*4:  #if a global orientation is supplied as a quaternion
        [gRb, bRg] = matrix_from_quaternion(or_in_global_quat)
        obj.matrix_world = gRb.to_4x4()

    
    if or_in_global_quat == [nan]*4 and or_in_global_XYZeuler != [nan]*3:

        [gRb, bRg] = matrix_from_euler_XYZbody(or_in_global_XYZeuler)
        obj.matrix_world = gRb.to_4x4()
    
    if pos_in_global != [nan]*3: #if the specified position is not [nan, nan, nan]
        obj.matrix_world.translation = pos_in_global

    #if the body exists, parent the contact to it
    if parent_body in bpy.data.objects: #if the parent body exists
        parent_body_obj = bpy.data.objects[parent_body]

        if 'BODY' in parent_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body
            
            obj.parent = parent_body_obj
            obj.matrix_parent_inverse = parent_body_obj.matrix_world.inverted()     
    
    #####
    #     
    matname = 'wrap_geom_material'
    color = tuple(bpy.context.scene.muskemo.wrap_geom_color)
    transparency = 0.5

    ##### Assign a material
    
    if matname not in bpy.data.materials:   #if the material doesn't exist, get it
        from .create_transparent_material_func import create_transparent_material
        create_transparent_material(matname, color, transparency)

    mat = bpy.data.materials[matname]
    obj.data.materials.append(mat)

    ### viewport display color

    obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)    
        
        
        
        
