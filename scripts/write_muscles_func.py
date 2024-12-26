import bpy
from mathutils import Vector
from math import nan

### This can use some proper error messages

def write_muscles(context, filepath, collection_name, delimiter, number_format):
    
    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    
    coll = bpy.data.collections[collection_name]   
    
    header = ('MUSCLE_point_name' + delimiter  + 'parent_body_name' + delimiter  + 'pos_x_in_global(m)' + delimiter  + 'pos_y_in_global' + delimiter  + 'pos_z_in_global' + delimiter + #headers
    'parent_frame_name' + delimiter + 'pos_x_in_local(m)' + delimiter + 'pos_y_in_local' + delimiter + 'pos_z_in_local' + delimiter + 
    'optimal_fiber_length(m)' + delimiter + 'tendon_slack_length(m)' + delimiter + 'F_max(N)' + delimiter + 'pennation_angle(deg)' )
    
       
    file.write(header) #headers
    
    file.write('\n') 
    
    curve_names = [x.name for x in coll.objects if 'CURVE' in x.id_data.type] #get the name for each object in bpy.data, if the data type is a 'CURVE'

    muscle_current_position_export = bpy.context.scene.muskemo.muscle_current_position_export

    if muscle_current_position_export: #if current position export is true, we aply the hook modifiers in an evaluated depsgraph copy of each curve to get the position.
        #this allows the user to construct the muscles in a different position than the default model export position
        depsgraph = bpy.context.evaluated_depsgraph_get()


    ### loop through all curves in the scene

    for u in range(len(curve_names)):
        curve = bpy.data.objects[curve_names[u]]
        modifier_list = [x.name for x in curve.modifiers if 'Hook'.casefold() in x.name.casefold()] #list of all the hook modifiers that are added to this curve


        if muscle_current_position_export:
            curve_ev = curve.to_curve(depsgraph, apply_modifiers=True)
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

            if muscle_current_position_export:
                #the depsgraph copy of the evaluated curve doesn't have data, but has a spline directly under it.
                location = curve.matrix_world @ curve_ev.splines[0].points[i].co.xyz  # global location is matrix_world * local_point_location 
            else:
                location = curve.matrix_world @ curve.data.splines[0].points[i].co.xyz  # global location is matrix_world * local_point_location
            position_local = [nan, nan, nan] #this gets overwritten if the point is hooked to a body, and that body has a local frame
            parent_frame_name = 'not_assigned'

            if 'ERROR' in body_name:
                print('ERROR! Point number ' + str(i+1) + ' of ' + curve.name + ' is not hooked to a body')
                
            else:
                parent_body = bpy.data.objects[body_name]
                parent_frame_name = parent_body['local_frame']
                if parent_frame_name != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
                    
                    frame = bpy.data.objects[parent_frame_name]

                    gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
                    bRg = gRb.copy()
                    bRg.transpose()
            
                    frame_or_g = frame.matrix_world.translation                 
                    
                    position_local = bRg @ (location - frame_or_g) #muscle point position in parent frame
                        

            
            file.write(curve_names[u] + point_name + delimiter)  #curve name, point name
            file.write(body_name + delimiter) # body it is attached to
          
            file.write(f"{location.x:{number_format}}{delimiter}")     # x location, 
            file.write(f"{location.y:{number_format}}{delimiter}")     # y location
            file.write(f"{location.z:{number_format}}{delimiter}")     # z location
            file.write(parent_frame_name + delimiter)
            file.write(f"{position_local[0]:{number_format}}{delimiter}")     # x position local 
            file.write(f"{position_local[1]:{number_format}}{delimiter}")     # y 
            file.write(f"{position_local[2]:{number_format}}{delimiter}")     # z 
            file.write(f"{curve['optimal_fiber_length']:{number_format}}{delimiter}")
            file.write(f"{curve['tendon_slack_length']:{number_format}}{delimiter}")
            file.write(f"{curve['F_max']:{number_format}}{delimiter}")
            file.write(f"{curve['pennation_angle']:{number_format}}")


            
                                                                   # start a new line
            file.write('\n')

        if muscle_current_position_export:
            curve.to_curve_clear() #clear the depsgraph evaluated copy

    file.close()
    return {'FINISHED'} 
    