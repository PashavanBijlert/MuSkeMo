import bpy
from mathutils import Vector
def write_joints(context, filepath, collection_name, delimiter, number_format):
    from .euler_XYZ_body import euler_XYZbody_from_matrix
    from .quaternions import quat_from_matrix

    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    
    header = ('joint_name' + delimiter  + 'parent_body' + delimiter  + 'child_body' + delimiter + 
            'pos_x_in_global(m)' + delimiter  + 'pos_y_in_global' + delimiter  + 'pos_z_in_global' + delimiter   +
            'or_x_in_global(XYZeuler_rad)' + delimiter + 'or_y_in_global(XYZeuler)' + delimiter + 'or_z_in_global(XYZeuler)' + delimiter + 
            'or_w_in_global(quat)' + delimiter + 'or_x_in_global(quat)' + delimiter + 'or_y_in_global(quat)' + delimiter + 'or_z_in_global(quat)' + delimiter + 
            'parent_frame_name' + delimiter + 'pos_x_in_parent_frame(m)' + delimiter  + 'pos_y_in_parent_frame' + delimiter  + 'pos_z_in_parent_frame' + delimiter   +
            'or_x_in_parent_frame(XYZeuler)' + delimiter + 'or_y_in_parent_frame(XYZeuler)' + delimiter + 'or_z_in_parent_frame(XYZeuler)' + delimiter + 
            'or_w_in_parent_frame(quat)' + delimiter + 'or_x_in_parent_frame(quat)' + delimiter + 'or_y_in_parent_frame(quat)' + delimiter + 'or_z_in_parent_frame(quat)' + delimiter + 
            'child_frame_name' + delimiter + 'pos_x_in_child_frame(m)' + delimiter  + 'pos_y_in_child_frame' + delimiter  + 'pos_z_in_child_frame' + delimiter   +
            'or_x_in_child_frame(XYZeuler)' + delimiter + 'or_y_in_child_frame(XYZeuler)' + delimiter + 'or_z_in_child_fram(XYZeuler)' + delimiter + 
            'or_w_in_child_frame(quat)' + delimiter + 'or_x_in_child_frame(quat)' + delimiter + 'or_y_in_child_frame(quat)' + delimiter + 'or_z_in_child_frame(quat)' + delimiter + 
            'coordinate_Tx' + delimiter + 'coordinate_Ty' + delimiter +  'coordinate_Tz' + delimiter + 'coordinate_Rx' + delimiter + 'coordinate_Ry' + delimiter +  'coordinate_Rz'  
              )

    file.write(header) #headers
    
    file.write('\n') 
    

    coll = bpy.data.collections[collection_name]
    

    joints = [i for i in bpy.data.collections[collection_name].objects] #make sure each contact is in the collection named 'joint centers'
    
    for u in range(len(joints)): #for each joint
        
        

        bpy.ops.object.select_all(action='DESELECT')
        

        joint = joints[u]
        location = joint.matrix_world.translation

        gRb = joint.matrix_world.to_3x3() #orientation matrix from local to global
        
        or_glob_eulerXYZ = euler_XYZbody_from_matrix(gRb)
        or_glob_quat = quat_from_matrix(gRb)
        
        
        #if location == Vector((0,0,0)):  #ground pelvis has transformations applied.
        #    joint.select_set(True)
        #    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
            
        #    location = Vector(joint.matrix_world.translation)
        #    bpy.ops.object.transform_apply()
        #    bpy.ops.object.select_all(action='DESELECT')

        ### joint name, parent body and child body
        file.write(joint.name + delimiter) # joint name 
        file.write(joint['parent_body'] + delimiter) # joint name 
        file.write(joint['child_body'] + delimiter) # joint name 

        ### pos and or global

        file.write(f"{location.x:{number_format}}{delimiter}")     # x location
        file.write(f"{location.y:{number_format}}{delimiter}")     # y location
        file.write(f"{location.z:{number_format}}{delimiter}")     # z location


        file.write(f"{or_glob_eulerXYZ[0]:{number_format}}{delimiter}") #glob orientation eulerXYZ x
        file.write(f"{or_glob_eulerXYZ[1]:{number_format}}{delimiter}") #glob orientation eulerXYZ y
        file.write(f"{or_glob_eulerXYZ[2]:{number_format}}{delimiter}") #glob orientation eulerXYZ z

        file.write(f"{or_glob_quat[0]:{number_format}}{delimiter}") #glob orientation quat w
        file.write(f"{or_glob_quat[1]:{number_format}}{delimiter}") #glob orientation quat x
        file.write(f"{or_glob_quat[2]:{number_format}}{delimiter}") #glob orientation quat y
        file.write(f"{or_glob_quat[3]:{number_format}}{delimiter}") #glob orientation quat z
        

        ### parent frame and pos and or in parent frame
        if joint['parent_body'] == 'not_assigned':
            file.write('not_assigned' + delimiter) #if there is no parent body, there is no parent frame assigned
        else:
            parent = bpy.data.objects[joint['parent_body']]
            file.write(parent['local_frame'] + delimiter) #parent frame name
        
        file.write(f"{joint['pos_in_parent_frame'][0]:{number_format}}{delimiter}")     # x location
        file.write(f"{joint['pos_in_parent_frame'][1]:{number_format}}{delimiter}")     # y location
        file.write(f"{joint['pos_in_parent_frame'][2]:{number_format}}{delimiter}")     # z location


        file.write(f"{joint['or_in_parent_frame_XYZeuler'][0]:{number_format}}{delimiter}") # orientation eulerXYZ x
        file.write(f"{joint['or_in_parent_frame_XYZeuler'][1]:{number_format}}{delimiter}") # orientation eulerXYZ y
        file.write(f"{joint['or_in_parent_frame_XYZeuler'][2]:{number_format}}{delimiter}") # orientation eulerXYZ z

        file.write(f"{joint['or_in_parent_frame_quat'][0]:{number_format}}{delimiter}") #orientation quat w
        file.write(f"{joint['or_in_parent_frame_quat'][1]:{number_format}}{delimiter}") #orientation quat x
        file.write(f"{joint['or_in_parent_frame_quat'][2]:{number_format}}{delimiter}") #orientation quat y
        file.write(f"{joint['or_in_parent_frame_quat'][3]:{number_format}}{delimiter}") #orientation quat z


        ### child frame and pos and or in child frame
        if joint['child_body'] == 'not_assigned':
            file.write('not_assigned' + delimiter) #if there is no child body, there is no child frame assigned
        else:
            child = bpy.data.objects[joint['child_body']]
            file.write(child['local_frame'] + delimiter) #child frame name

        file.write(f"{joint['pos_in_child_frame'][0]:{number_format}}{delimiter}")     # x location
        file.write(f"{joint['pos_in_child_frame'][1]:{number_format}}{delimiter}")     # y location
        file.write(f"{joint['pos_in_child_frame'][2]:{number_format}}{delimiter}")     # z location


        file.write(f"{joint['or_in_child_frame_XYZeuler'][0]:{number_format}}{delimiter}") # orientation eulerXYZ x
        file.write(f"{joint['or_in_child_frame_XYZeuler'][1]:{number_format}}{delimiter}") # orientation eulerXYZ y
        file.write(f"{joint['or_in_child_frame_XYZeuler'][2]:{number_format}}{delimiter}") # orientation eulerXYZ z

        file.write(f"{joint['or_in_child_frame_quat'][0]:{number_format}}{delimiter}") #orientation quat w
        file.write(f"{joint['or_in_child_frame_quat'][1]:{number_format}}{delimiter}") #orientation quat x
        file.write(f"{joint['or_in_child_frame_quat'][2]:{number_format}}{delimiter}") #orientation quat y
        file.write(f"{joint['or_in_child_frame_quat'][3]:{number_format}}{delimiter}") #orientation quat z

        ### coordinates
        file.write(f"{joint['coordinate_Tx']}{delimiter}") # coordinate Tx
        file.write(f"{joint['coordinate_Ty']}{delimiter}") # coordinate Ty  
        file.write(f"{joint['coordinate_Tz']}{delimiter}") # coordinate Tz  
        file.write(f"{joint['coordinate_Rx']}{delimiter}") # coordinate Rx  
        file.write(f"{joint['coordinate_Ry']}{delimiter}") # coordinate Ry  
        file.write(f"{joint['coordinate_Rz']}{delimiter}") # coordinate Rz      
        
        file.write('\n')                                                        # start a new line
            
   

    file.close()
    return {'FINISHED'}