import bpy
from math import nan

def create_contact(name, radius, pos_in_global = [nan]*3,
                  is_global = True, 
                 parent_body = 'not_assigned', pos_in_parent_frame = [nan]*3):
    


    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, enter_editmode=False, align='WORLD', location = (0,0,0)) #create a sphere
    bpy.context.object.name = name #set the name
    bpy.context.object.data.name = name #set the name of the object data
    obj = bpy.data.objects[name]
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

        
    #if statement for if the parent body exists already, parent it
    #error check for existing frames        #do the same for both parent and child