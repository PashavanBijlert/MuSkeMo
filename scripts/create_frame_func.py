import bpy
from math import nan
from mathutils import (Matrix)



def create_frame(name, size,
                 pos_in_global,
                   gRb, 
                    collection_name = 'Frames',
                    parent_body = 'not_assigned',):
    
    '''
    inputs:
    name
    size
    pos_in_global (n x 3 list or vector) of the frame origin position in global
    gRb: 3x3 Matrix or np.array. Rotation matrix from body-fixed to global frame
    collection_name (string, optional. Name of the collection where the frames will be stored)
    parent_body = name of the parent body. Optional, to be filled in when importing models
    '''
    #check if the collection name exists, and if not create it
    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the frames

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
    
    #Make sure the collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]


    worldMat = Matrix(gRb).to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

    for i in range(len(pos_in_global)):
        
        worldMat[i][3] = pos_in_global[i]  #set the fourth column as the location


    bpy.ops.object.empty_add(type='ARROWS', radius=size, align='WORLD')
    bpy.context.object.name = name #set the name
    #bpy.context.object.data.name = name #set the name of the object data
    obj = bpy.data.objects[name]
    obj.rotation_mode = 'ZYX'    #change rotation sequence

    #
    obj.matrix_world = worldMat  #set the transformation matrix

    ## it's possible to calculate euler decomposition, but this is prone to gimbal lock.
    # phi_y = np.arcsin(gRl[0,2]) #alternative: phi_y = np.arctan2(gRl[0,2], math.sqrt(1 - (gRl[0,2])**2)) 
    # phi_x = np.arctan2(-gRl[1,2],gRl[2,2])    #angle alpha in wiki
    # phi_z = np.arctan2(-gRl[0,1],gRl[0,0])    #angle gamma in wiki

    #print('Manually computed XYZ Euler angles =')
    #print([phi_x, phi_y, phi_z])
    #bpy.context.object.rotation_euler = [phi_x, phi_y, phi_z]
    #bpy.context.object.location = origin

    obj['MuSkeMo_type'] = 'FRAME'  #to inform the user what type is created
    obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")

    obj['parent_body'] = parent_body    #to inform the user what type is created
    obj.id_properties_ui('parent_body').update(description = "The parent body of this frame")  

    if parent_body != 'not_assigned' and parent_body in bpy.data.objects: #if a parent body is assigned and it exists in the scene, parent it

        parent_body = bpy.data.objects[parent_body]
        obj.parent = parent_body
            
        #this undoes the transformation after parenting
        obj.matrix_parent_inverse = parent_body.matrix_world.inverted()

        
    return
