import bpy
from mathutils import (Vector, Matrix)
import numpy as np
def write_pos_and_pbody(context, filepath, collection_name, delimiter, obj_type, number_format, self):  #write location and parent body. This is reused for both contacts and landmarks.
    
    #### obj_type is a string, either "contact" or "landmark", or something else if you reuse this further
    #### the script will fail if you don't specify it when calling the function

    coll = bpy.data.collections[collection_name]
    

    for obj in coll.objects:
        if 'default_pose' in obj: #remove this if statement once landmarks also have a default pose
            worldmat = np.array(obj.matrix_world)
            default_pose = np.array(obj['default_pose'])

            if not np.allclose(worldmat, default_pose, atol = 1e-6): #compare matrices with abstol of 1e-6, to account for single precision in Blender
       
                self.report({'ERROR'}, "Contact '" + obj.name + "' was parented in a different pose than the current pose. Reset the model to the default  (using the button), or reparent the contact. Operation cancelled")
                return {'FINISHED'}


    file = open(filepath, 'w', encoding='utf-8') #create or open a file,  "w" means it's writeable
    
    header = ( obj_type + '_name' + delimiter  + 'pos_x_in_global(m)' + delimiter  + 'pos_y_in_global' + delimiter  + 'pos_z_in_global' )
    
    if obj_type == 'CONTACT':
        header = header + ( delimiter  + 'parent_body' +  delimiter + 'parent_frame_name' + delimiter + 
                           'pos_x_in_local(m)' + delimiter + 'pos_y_in_local' + delimiter + 'pos_z_in_local')#headers


    
    file.write(header) 
    
    file.write('\n') 
    

    objects = [i for i in bpy.data.collections[collection_name].objects] #get each obj from the designated collection #ADD IF STATEMENT FOR MUSKEMO TYPE?
    
    for u in range(len(objects)): #for each contact
        
        bpy.ops.object.select_all(action='DESELECT')
        

        obj = objects[u]
        location = obj.matrix_world.translation
        
        
        file.write(obj.name + delimiter) # contact name 
        file.write(f"{location.x:{number_format}}{delimiter}")     # x location, 
        file.write(f"{location.y:{number_format}}{delimiter}")     # y location, 
        file.write(f"{location.z:{number_format}}")     # z location, 
        
        if obj_type == 'CONTACT':
            file.write(f"{delimiter}{obj.parent.name}{delimiter}") #parent body name
            file.write(obj.parent['local_frame'] + delimiter) #parent body local frame
            file.write(f"{obj['pos_in_parent_frame'][0]:{number_format}}{delimiter}") #x location local
            file.write(f"{obj['pos_in_parent_frame'][1]:{number_format}}{delimiter}") #y location local
            file.write(f"{obj['pos_in_parent_frame'][2]:{number_format}}") #z location local
            #contact radius?
        
            


        
        ## when extending this, add delimiter to both options          
        
        file.write('\n')                                                        # start a new line
            
   

    file.close()
    return {'FINISHED'}