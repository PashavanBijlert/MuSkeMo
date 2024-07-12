import bpy
from mathutils import Vector
def write_loc_and_pbody(context, filepath, collection_name, delimiter, obj_type, number_format):  #write location and parent body. This is reused for both contacts and landmarks.
    
    #### obj_type is a string, either "contact" or "landmark", or something else if you reuse this further
    #### the script will fail if you don't specify it when calling the function

    


    file = open(filepath, 'w', encoding='utf-8') #create or open a file,  "w" means it's writeable
    
    header = obj_type + '_name' + delimiter  + 'pos_x_in_global(m)' + delimiter  + 'pos_y' + delimiter  + 'pos_z' + delimiter  + 'parent_body'  #headers


    ## if statement for if local frame is specified:
    ### header = header + delimiter + ... 
     
    file.write(header) 
    
    file.write('\n') 
    
    
    

    coll = bpy.data.collections[collection_name]
    

    objects = [i for i in bpy.data.collections[collection_name].objects] #get each obj from the designated collection #ADD IF STATEMENT FOR MUSKEMO TYPE?
    
    for u in range(len(objects)): #for each contact
        
        bpy.ops.object.select_all(action='DESELECT')
        

        obj = objects[u]
        location = obj.matrix_world.translation
        
        
        file.write(obj.name + delimiter) # contact name 
        file.write(f"{location.x:{number_format}}{delimiter}")     # x location, 4 decimals
        file.write(f"{location.y:{number_format}}{delimiter}")     # y location, 4 decimals
                                      
        file.write(f"{location.z:{number_format}}{delimiter}")     # z location, 4 decimals
        
        if obj.parent is None:
            file.write('No_parent_assigned') #if there is no parent, say so
            
        else:
            file.write(obj.parent.name) #parent body name
        
        ## when extending this, add delimiter to both options          
        
        file.write('\n')                                                        # start a new line
            
   

    file.close()
    return {'FINISHED'}