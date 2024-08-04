import bpy
from math import nan
from mathutils import (Matrix)



def create_frame(name, size, pos_in_global,
                   gRb, parent_body = 'not_assigned',):
    
    '''
    inputs:
    name
    size
    pos_in_global (n x 3 list or vector) of the frame origin position in global
    gRb: 3x3 Matrix or np.array. Rotation matrix from body-fixed to global frame
    parent_body = name of the parent body. Optional
    '''
    
    worldMat = Matrix(gRb).to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

    for i in range(len(pos_in_global)):
        
        worldMat[i][3] = pos_in_global[i]  #set the fourth column as the location


    bpy.ops.object.empty_add(type='ARROWS', radius=size, align='WORLD')
    bpy.context.object.name = name #set the name
    #bpy.context.object.data.name = name #set the name of the object data

    bpy.context.object.rotation_mode = 'ZYX'    #change rotation sequence

    #
    bpy.context.object.matrix_world = worldMat  #set the transformation matrix

    ## it's possible to calculate euler decomposition, but this is prone to gimbal lock.
    # phi_y = np.arcsin(gRl[0,2]) #alternative: phi_y = np.arctan2(gRl[0,2], math.sqrt(1 - (gRl[0,2])**2)) 
    # phi_x = np.arctan2(-gRl[1,2],gRl[2,2])    #angle alpha in wiki
    # phi_z = np.arctan2(-gRl[0,1],gRl[0,0])    #angle gamma in wiki

    #print('Manually computed XYZ Euler angles =')
    #print([phi_x, phi_y, phi_z])
    #bpy.context.object.rotation_euler = [phi_x, phi_y, phi_z]
    #bpy.context.object.location = origin

    bpy.context.object['MuSkeMo_type'] = 'FRAME'  #to inform the user what type is created
    bpy.context.object.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")

    bpy.context.object['parent_body'] = parent_body    #to inform the user what type is created
    bpy.context.object.id_properties_ui('parent_body').update(description = "The parent body of this frame")  

    if parent_body != 'not_assigned':

        #insert code for actually parenting the object
        print('not written yet')

    return
