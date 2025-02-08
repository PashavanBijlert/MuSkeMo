import bpy
import numpy as np
from mathutils import Vector
def write_wrapping(context, filepath, collection_name, delimiter, number_format):
    from .euler_XYZ_body import euler_XYZbody_from_matrix
    from .quaternions import quat_from_matrix

    file = open(filepath, 'w', encoding='utf-8') #create or open a file,  "w" means it's writeable
    
    header = ('WRAP_name' + delimiter  + 'WRAP_type' + delimiter  + 
              'dimension1' + delimiter  + 'dimension2' + delimiter  + 'dimension3' + delimiter  + #Unused dims are nan.
              'parent_body' + delimiter  + 
            'pos_x_in_global(m)' + delimiter  + 'pos_y_in_global' + delimiter  + 'pos_z_in_global' + delimiter   +
            'or_x_in_global(XYZeuler_rad)' + delimiter + 'or_y_in_global(XYZeuler)' + delimiter + 'or_z_in_global(XYZeuler)' + delimiter + 
            'or_w_in_global(quat)' + delimiter + 'or_x_in_global(quat)' + delimiter + 'or_y_in_global(quat)' + delimiter + 'or_z_in_global(quat)' + delimiter + 
            'parent_frame_name' + delimiter + 'pos_x_in_parent_frame(m)' + delimiter  + 'pos_y_in_parent_frame' + delimiter  + 'pos_z_in_parent_frame' + delimiter   +
            'or_x_in_parent_frame(XYZeuler)' + delimiter + 'or_y_in_parent_frame(XYZeuler)' + delimiter + 'or_z_in_parent_frame(XYZeuler)' + delimiter + 
            'or_w_in_parent_frame(quat)' + delimiter + 'or_x_in_parent_frame(quat)' + delimiter + 'or_y_in_parent_frame(quat)' + delimiter + 'or_z_in_parent_frame(quat)' + delimiter +
            'target_muscles' + delimiter + 'pre_wrap_muscle_points' 
            )

    file.write(header) #headers
    
    file.write('\n') 
    

    coll = bpy.data.collections[collection_name]
    

    wrapobjects = [i for i in bpy.data.collections[collection_name].objects] #get all the objects in a collection
    
    for u in range(len(wrapobjects)): #for each wrapobj
        
        

        bpy.ops.object.select_all(action='DESELECT')
        

        wrapobj = wrapobjects[u]
        location = wrapobj.matrix_world.translation

        gRb = wrapobj.matrix_world.to_3x3() #orientation matrix from local to global
        
        or_glob_eulerXYZ = euler_XYZbody_from_matrix(gRb)
        or_glob_quat = quat_from_matrix(gRb)
        
        
        
        ### wrapobj name, type, dimensions

        file.write(wrapobj.name + delimiter) # wrapobj name 
        
        wrap_type = wrapobj['wrap_type']
        file.write( wrap_type + delimiter) # wrapobj type

        if wrap_type.lower() == 'cylinder':

            
            file.write(f"{wrapobj.modifiers['WrapObjMesh']['Socket_1']:{number_format}}{delimiter}")     # dimension 1 is radius
            file.write(f"{wrapobj.modifiers['WrapObjMesh']['Socket_2']:{number_format}}{delimiter}")     # dimension 2 is height
            file.write(f"{np.nan:{number_format}}{delimiter}")     # dimension 3 is nan

        ### once implemented these should get the info from the modifier sockets
        elif wrap_type.lower() == 'sphere':
            file.write(f"{wrapobj['radius']:{number_format}}{delimiter}")     # dimension 1 is radius
            file.write(f"{np.nan:{number_format}}{delimiter}")     # dimension 2 is height
            file.write(f"{np.nan:{number_format}}{delimiter}")     # dimension 3 is nan

        elif wrap_type.lower() == 'ellipsoid':
            file.write(f"{wrapobj['radius1']:{number_format}}{delimiter}")     # dimension 1 is radius1
            file.write(f"{wrapobj['radius2']:{number_format}}{delimiter}")     # dimension 2 is radius2
            file.write(f"{wrapobj['radius3']:{number_format}}{delimiter}")     # dimension 3 is radius3

        elif wrap_type.lower() == 'torus':
            file.write(f"{wrapobj['minor_radius']:{number_format}}{delimiter}")     # dimension 1 is minor radius
            file.write(f"{wrapobj['major_radius']:{number_format}}{delimiter}")     # dimension 2 is major radius
            file.write(f"{np.nan:{number_format}}{delimiter}")     # dimension 3 is nan       

        
        #### parent body
        file.write(wrapobj['parent_body'] + delimiter) # parent body name 
        

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
        if wrapobj['parent_body'] == 'not_assigned':
            file.write('not_assigned' + delimiter) #if there is no parent body, there is no parent frame assigned
        
        
    
        else:
            parent = bpy.data.objects[wrapobj['parent_body']]
            file.write(parent['local_frame'] + delimiter) #parent frame name
        
        file.write(f"{wrapobj['pos_in_parent_frame'][0]:{number_format}}{delimiter}")     # x location
        file.write(f"{wrapobj['pos_in_parent_frame'][1]:{number_format}}{delimiter}")     # y location
        file.write(f"{wrapobj['pos_in_parent_frame'][2]:{number_format}}{delimiter}")     # z location


        file.write(f"{wrapobj['or_in_parent_frame_XYZeuler'][0]:{number_format}}{delimiter}") # orientation eulerXYZ x
        file.write(f"{wrapobj['or_in_parent_frame_XYZeuler'][1]:{number_format}}{delimiter}") # orientation eulerXYZ y
        file.write(f"{wrapobj['or_in_parent_frame_XYZeuler'][2]:{number_format}}{delimiter}") # orientation eulerXYZ z

        file.write(f"{wrapobj['or_in_parent_frame_quat'][0]:{number_format}}{delimiter}") #orientation quat w
        file.write(f"{wrapobj['or_in_parent_frame_quat'][1]:{number_format}}{delimiter}") #orientation quat x
        file.write(f"{wrapobj['or_in_parent_frame_quat'][2]:{number_format}}{delimiter}") #orientation quat y
        file.write(f"{wrapobj['or_in_parent_frame_quat'][3]:{number_format}}{delimiter}") #orientation quat z


        #### target muscles
        file.write(wrapobj['target_muscles']+ delimiter) # wrapobj name
        
        target_muscle_objects = [bpy.data.objects[x] for x in wrapobj['target_muscles'].split(';') if (x and x!='not_assigned')]
        
        pre_wrap_points = []
        for tm in target_muscle_objects:
            #for each of the target muscles, get the correct modifier in the muscle's modif stack and get the socket for the pre wrap point
            pre_wrap_points.append(tm.modifiers[tm.name + '_wrap_' + wrapobj.name]['Socket_6']) #the pre wrap point
            
        pre_wrap_points_string = ';'.join([str(x) for x in pre_wrap_points]) + ';' #this gets written to the file

        file.write(pre_wrap_points_string) # write pre-wrap curve indices (as strings, delimited by ;)


        file.write('\n')                                                        # start a new line
            
   

    file.close()
    return {'FINISHED'}