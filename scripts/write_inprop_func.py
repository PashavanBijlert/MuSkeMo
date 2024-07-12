def write_inprop(context, filepath, collection_name, delimiter, obj_type, number_format):
    #### obj_type is a string, either "body" or "mesh", or something if you reuse this further
    #### the script will fail if you don't specify it when calling the function.
    #### currently, the script gives inertial properties for bodies or meshes


    import bpy

    
    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    coll = bpy.data.collections[collection_name]
    
    
    header = (obj_type + '_name' + delimiter  + 'mass(kg)' + delimiter  + 
              'CoM_x_in_global' + delimiter  + 'CoM_y_in_global' + delimiter   + 'CoM_z_in_global' + delimiter  + 
              'Ixx(kg*m^2)_about_COM_in_global' + delimiter  + 'Iyy_in_global' + delimiter  + 'Izz_in_global' + delimiter  + 'Ixy_in_global' + delimiter  + 'Ixz_in_global' + delimiter  + 'Iyz_in_global' )
          
    if obj_type == 'BODY':

        header = header + ( delimiter + 'Geometry' + delimiter + 'local_frame_name' + delimiter + 'COM_x_in_local' + delimiter + 'COM_y_in_local' + delimiter + 'COM_z_in_local' + delimiter + 
             'Ixx(kg*m^2)_COM_in_local' + delimiter + 'Iyy_in_local' + delimiter + 'Izz_in_local' + delimiter + 'Ixy_in_local' + delimiter + 'Ixz_in_local' + delimiter + 'Iyz_in_local'             
              )
    
    if obj_type == 'mesh':

        header = header + delimiter + 'density(kg*m^-3)' 

    
        
    #file.write('body_name' + delimiter  + 'mass(kg)' + delimiter  + 'CoM_x' + delimiter  + 'CoM_y' + delimiter  + 'CoM_z' + delimiter  + 'Ixx(kg*m^2) about COM in global' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Body-frame angle x (rad, XYZ-euler)' + delimiter  + 'angle y' + delimiter  + 'angle z' + delimiter  + 'Ixx(kg*m^2) about COM in body-fixed principal' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Geometry') #headers
    file.write(header) #headers
    
    file.write('\n') 

    for u in coll.objects: #for each body
            
        
        file.write(f"{u.name}{delimiter}")  # body name
        file.write(f"{u['mass']:{number_format}}{delimiter}")  # mass in kg,
        file.write(f"{u['COM'][0]:{number_format}}{delimiter}")  # Com_x location, global
        file.write(f"{u['COM'][1]:{number_format}}{delimiter}")  # Com_y
        file.write(f"{u['COM'][2]:{number_format}}{delimiter}")  # Com_z
        file.write(f"{u['inertia_COM'][0]:{number_format}}{delimiter}")  # Ixx wrt body CoM
        file.write(f"{u['inertia_COM'][1]:{number_format}}{delimiter}")  # Iyy wrt body CoM
        file.write(f"{u['inertia_COM'][2]:{number_format}}{delimiter}")  # Izz wrt body CoM
        file.write(f"{u['inertia_COM'][3]:{number_format}}{delimiter}")  # Ixy wrt body CoM
        file.write(f"{u['inertia_COM'][4]:{number_format}}{delimiter}")  # Ixz wrt body CoM
        file.write(f"{u['inertia_COM'][5]:{number_format}}{delimiter}")  # Iyz wrt body CoM
        

        if obj_type == 'BODY':

            file.write(f"{u['Geometry']}{delimiter}")  # geometry list
            file.write(f"{u['local_frame']}{delimiter}")  # local frame name
            file.write(f"{u['COM_local'][0]:{number_format}}{delimiter}")  # Com_x location, local
            file.write(f"{u['COM_local'][1]:{number_format}}{delimiter}")  # Com_y
            file.write(f"{u['COM_local'][2]:{number_format}}{delimiter}")  # Com_z
            file.write(f"{u['inertia_COM_local'][0]:{number_format}}{delimiter}")  # Ixx wrt body CoM, local
            file.write(f"{u['inertia_COM_local'][1]:{number_format}}{delimiter}")  # Iyy wrt body CoM
            file.write(f"{u['inertia_COM_local'][2]:{number_format}}{delimiter}")  # Izz wrt body CoM
            file.write(f"{u['inertia_COM_local'][3]:{number_format}}{delimiter}")  # Ixy wrt body CoM
            file.write(f"{u['inertia_COM_local'][4]:{number_format}}{delimiter}")  # Ixz wrt body CoM
            file.write(f"{u['inertia_COM_local'][5]:{number_format}}")  # Iyz wrt body CoM
        
        if obj_type == 'mesh':
            file.write(f"{u['density']:{number_format}}")
            
        file.write('\n')

            
    #file.write('Clever Girl') 

    file.close()
    return {'FINISHED'}