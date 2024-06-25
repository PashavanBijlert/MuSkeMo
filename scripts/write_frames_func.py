import bpy
from mathutils import Vector
def write_frames(context, filepath, collection_name, delimiter):
    
    from .quaternions import quat_from_matrix
    from .euler_XYZ_body import euler_XYZbody_from_matrix


    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    
    header = ('frame_name' + delimiter  + 'parent_body' + delimiter + 'pos_x_in_global(m)' + delimiter  + 'pos_y' + delimiter  + 'pos_z' + delimiter + 
              'quaternion_w' +  delimiter  + 'quaternion_x'  + delimiter  + 'quaternion_y' +  delimiter  + 'quaternion_z'  + delimiter  + 
               'Euler_XYZ_x(rad)' +  delimiter  + 'Euler_XYZ_y' +  delimiter  + 'Euler_XYZ_z')
    
    
    ## if statement for if local frame is specified:
    ### header = header + delimiter + ... 

    file.write(header) #headers
    
    file.write('\n') 
    

    coll = bpy.data.collections[collection_name]
    

    frames = [i for i in bpy.data.collections[collection_name].objects] #make sure each contact is in the collection named 'frame centers'
    
    for u in range(len(frames)): #for each frame
        
        

        bpy.ops.object.select_all(action='DESELECT')
        

        frame = frames[u]

        wm = frame.matrix_world

        location = wm.translation
        rotation = wm.to_3x3()

        quat = quat_from_matrix(rotation)
        euler_XYZ = euler_XYZbody_from_matrix(rotation)

        
        file.write(frame.name + delimiter) # frame name 

        if frame.parent is None:
            file.write('No_parent' + delimiter) #parent body is ground if there is no parent
        else:
            file.write(frame.parent.name + delimiter) #parent body name
        file.write(f"{location.x:#.4f}{delimiter}")     # x location, 4 decimals
        file.write(f"{location.y:#.4f}{delimiter}")     # y location, 4 decimals
        file.write(f"{location.z:#.4f}{delimiter}")     # z location, 4 decimals
        
        file.write(f"{quat[0]:#.4g}{delimiter}")     # quaternion w, 4 sig dig
        file.write(f"{quat[1]:#.4g}{delimiter}")     # quaternion x, 4 sig dig
        file.write(f"{quat[2]:#.4g}{delimiter}")     # quaternion y, 4 sig dig
        file.write(f"{quat[3]:#.4g}{delimiter}")     # quaternion z, 4 sig dig

        file.write(f"{euler_XYZ[0]:#.4g}{delimiter}")     # euler x, 4 sig dig
        file.write(f"{euler_XYZ[1]:#.4g}{delimiter}")     # euler y, 4 sig dig
        file.write(f"{euler_XYZ[2]:#.4g}{delimiter}")     # euler z, 4 sig dig


        

                   
        
        file.write('\n')                                                        # start a new line
            
   

    file.close()
    return {'FINISHED'}
### frame name, location (glob), orientation glob (body-fixed Euler XYZ), orientation glob (quaternions)