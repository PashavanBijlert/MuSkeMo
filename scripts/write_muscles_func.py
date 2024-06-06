import bpy
from mathutils import Vector

### This can use some proper error messages

def write_muscles(context, filepath, collection_name, delimiter):
    
    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    
    coll = bpy.data.collections[collection_name]   
    
    file.write('muscle_point_name' + delimiter  + 'pos_x_in_global(m)' + delimiter  + 'pos_y' + delimiter  + 'pos_z') #headers
    
    file.write('\n') 
    
    curve_names = [x.name for x in coll.objects if 'CURVE' in x.id_data.type] #get the name for each object in bpy.data, if the data type is a 'CURVE'



    ### loop through all curves in the scene

    for u in range(len(curve_names)):
        curve = bpy.data.objects[curve_names[u]]
        modifier_list = [x.name for x in curve.modifiers if 'Hook'.casefold() in x.name.casefold()] #list of all the hook modifiers that are added to this curve

    ### loop through points

        for i in range(0, len(curve.data.splines[0].points)): #for each point
            if i == 0:                                        #if it's the first point name it or
                point_name = '_or'
            elif i == len(curve.data.splines[0].points)-1:    #if it's the last point name it ins
                point_name = '_ins'
            else:                                             #if it's any other point name it via
                point_name = '_via' + str(i)

    ### find which body each point is attached through, you have to loop through all the modifiers for this
           
            body_name = 'ERROR, point not hooked to a body'   #this gets overwritten unless you forget to hook each point to a body
            for h in range(len(modifier_list)):               #for each hook modifier that is added to this curve
                modifier = curve.modifiers[modifier_list[h]]  #modifier is the h'th modifier in the list
                for j in range(len(modifier.vertex_indices)): #vertex index = connected curve point, so for each connected curve point j, which starts counting at 0
                    if i == modifier.vertex_indices[j]:       
                        body_name = modifier.object.name      #if curve point i equals a connected curve point j in modifier h, get the corresponding body name
                        
            if 'ERROR' in body_name:
                print('ERROR! Point number ' + str(i+1) + ' of ' + curve.name + ' is not hooked to a body')
                
            location = curve.matrix_world @ curve.data.splines[0].points[i].co.xyz  # global location is matrix_world * local_point_location
            file.write(curve_names[u] + point_name + delimiter)  #curve name, point name
            file.write(body_name + delimiter) # body it is attached to
          
            file.write(f"{location.x:#.4f}{delimiter}")     # x location, 4 decimals
            file.write(f"{location.y:#.4f}{delimiter}")     # y location, 4 decimals
            file.write(f"{location.z:#.4f}")     # z location, 4 decimals                                                        # start a new line
            file.write('\n')
    

    file.close()
    return {'FINISHED'} 
    