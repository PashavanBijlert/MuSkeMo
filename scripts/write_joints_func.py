import bpy
from mathutils import Vector
def write_joints(context, filepath, collection_name, delimiter):
    
    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    
    header = 'joint_name' + delimiter  + 'pos_x_in_global(m)' + delimiter  + 'pos_y' + delimiter  + 'pos_z' + delimiter   + 'parent_body' + delimiter  + 'child_body'
    ## if statement for if local frame is specified:
    ### header = header + delimiter + ... 

    file.write(header) #headers
    
    file.write('\n') 
    

    coll = bpy.data.collections[collection_name]
    

    joints = [i for i in bpy.data.collections[collection_name].objects] #make sure each contact is in the collection named 'joint centers'
    
    for u in range(len(joints)): #for each joint
        
        

        bpy.ops.object.select_all(action='DESELECT')
        

        joint = joints[u]
        location = joint.matrix_world.translation
        
        if location == Vector((0,0,0)):  #ground pelvis has transformations applied.
            joint.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_MASS')
            
            location = Vector(joint.matrix_world.translation)
            bpy.ops.object.transform_apply()
            bpy.ops.object.select_all(action='DESELECT')


        file.write(joint.name + delimiter) # joint name 
        file.write(f"{location.x:#.4f}{delimiter}")     # x location, 4 decimals
        file.write(f"{location.y:#.4f}{delimiter}")     # y location, 4 decimals
                                       # y location
        
        
        file.write(f"{location.z:#.4f}{delimiter}")     # z location, 4 decimals
        
        if joint.parent is None:
            file.write('ground' + delimiter) #parent body is ground if there is no parent
            print(joint.name + ' joint has no parent, parent body set to Ground')
        else:
            file.write(joint.parent.name + delimiter) #parent body name
        
        file.write(joint.children[0].name) #child body name
            
        
        file.write('\n')                                                        # start a new line
            
   

    file.close()
    return {'FINISHED'}