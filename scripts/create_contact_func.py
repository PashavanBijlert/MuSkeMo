import bpy
from math import nan
import bmesh
from mathutils import Matrix

def create_contact(name, radius, collection_name,
                    pos_in_global = [nan]*3,
                  is_global = True, 
                 parent_body = 'not_assigned', pos_in_parent_frame = [nan]*3):
    

    #check if the collection name exists, and if not create it
    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the scaled contacts

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
    
    #Make sure the "contacts" collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]


    
    ########### create contact
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_icosphere(
        bm,
        subdivisions=3,
        radius=radius,
        matrix=Matrix.Identity(4)
    )

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    obj.location = pos_in_global

    coll.objects.link(obj) #link to correct collection

    #####
    obj.rotation_mode = 'ZYX'    #change rotation sequence

    obj['MuSkeMo_type'] = 'CONTACT'    #to inform the user what type is created
    obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  
    
    obj['parent_body'] = parent_body    #to inform the user what type is created
    obj.id_properties_ui('parent_body').update(description = "The parent body of this contact sphere")

    obj['pos_in_parent_frame'] = pos_in_parent_frame
    obj.id_properties_ui('pos_in_parent_frame').update(description = 'Contact sphere position in the parent body anatomical (local) reference frame (x, y, z, in meters). Optional.')

    bpy.ops.object.select_all(action='DESELECT') 

    if is_global: #if we're constructing in global coordinates
        if pos_in_global != [nan]*3: #if the specified position is not [nan, nan, nan]
            obj.matrix_world.translation = pos_in_global

        #if the body exists, parent the contact to it
        if parent_body in bpy.data.objects: #if the parent body exists
            parent_body_obj = bpy.data.objects[parent_body]

            if 'BODY' in parent_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body
                
                obj.parent = parent_body_obj
                obj.matrix_parent_inverse = parent_body_obj.matrix_world.inverted()      

                # if we parent, we also track ['default_pose']

                obj['default_pose'] = obj.matrix_world #track the default pose to ensure the exported values are in the same pose
               


    matname = 'contact_material'
    color = tuple(bpy.context.scene.muskemo.contact_color)
    transparency = 0.5
        
    ##### Assign a material
    
    if matname not in bpy.data.materials:   #if the material doesn't exist, get it
        from .create_transparent_material_func import create_transparent_material
        create_transparent_material(matname, color, transparency)

    mat = bpy.data.materials[matname]
    obj.data.materials.append(mat)

    

    ### viewport display color

    obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)