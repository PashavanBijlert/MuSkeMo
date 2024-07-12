def write_inprop(context, filepath, collection_name, delimiter, obj_type, number_format):
    #### obj_type is a string, either "body" or "mesh", or something if you reuse this further
    #### the script will fail if you don't specify it when calling the function.
    #### currently, the script gives inertial properties for bodies or meshes


    import bpy

    
    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    coll = bpy.data.collections[collection_name]
    
    
    header = obj_type + '_name' + delimiter  + 'mass(kg)' + delimiter  + 'CoM_x_in_global' + delimiter  + 'CoM_y' + delimiter   + 'CoM_z' + delimiter  + 'Ixx(kg*m^2)_about_COM_in_global' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Geometry'
    ## if statement for if local frame is specified and obj_type is body:
    ### header = header + delimiter + ... 
    
        
    
    #file.write('body_name' + delimiter  + 'mass(kg)' + delimiter  + 'CoM_x' + delimiter  + 'CoM_y' + delimiter  + 'CoM_z' + delimiter  + 'Ixx(kg*m^2) about COM in global' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Body-frame angle x (rad, XYZ-euler)' + delimiter  + 'angle y' + delimiter  + 'angle z' + delimiter  + 'Ixx(kg*m^2) about COM in body-fixed principal' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Geometry') #headers
    file.write(header) #headers
    
    file.write('\n') 

    for u in coll.objects: #for each body
            
        
        file.write(f"{u.name}{delimiter}")  # body name
        file.write(f"{u['mass']:{number_format}}{delimiter}")  # mass in kg, 4 decimals
        file.write(f"{u['COM'][0]:{number_format}}{delimiter}")  # Com_x location, 4 decimals
        file.write(f"{u['COM'][1]:{number_format}}{delimiter}")  # Com_y
        file.write(f"{u['COM'][2]:{number_format}}{delimiter}")  # Com_z
        file.write(f"{u['inertia_COM'][0]:{number_format}}{delimiter}")  # Ixx wrt body CoM
        file.write(f"{u['inertia_COM'][1]:{number_format}}{delimiter}")  # Iyy wrt body CoM
        file.write(f"{u['inertia_COM'][2]:{number_format}}{delimiter}")  # Izz wrt body CoM
        file.write(f"{u['inertia_COM'][3]:{number_format}}{delimiter}")  # Ixy wrt body CoM
        file.write(f"{u['inertia_COM'][4]:{number_format}}{delimiter}")  # Ixz wrt body CoM
        file.write(f"{u['inertia_COM'][5]:{number_format}}{delimiter}")  # Iyz wrt body CoM

        try:  # check if principal axes body frame is defined
            u['principal_axes_euler_XYZ']
            
        except:
            print('No body frame aligned to principal direction of inertia detected')
        else:
            
            file.write(f"{u['principal_axes_euler_XYZ'][0]:{number_format}}{delimiter}")  # Angle x of body-fixed frame (Euler XYZ, in radians)
            file.write(f"{u['principal_axes_euler_XYZ'][1]:{number_format}}{delimiter}")  # Angle y
            file.write(f"{u['principal_axes_euler_XYZ'][2]:{number_format}}{delimiter}")  # Angle z
            file.write(f"{u['inertia_body_fixed_principal'][0]:{number_format}}{delimiter}")  # Ixx wrt body CoM, expressed in frame aligned to principal directions
            file.write(f"{u['inertia_body_fixed_principal'][1]:{number_format}}{delimiter}")  # Iyy wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][2]:{number_format}}{delimiter}")  # Izz wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][3]:{number_format}}{delimiter}")  # Ixy wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][4]:{number_format}}{delimiter}")  # Ixz wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][5]:{number_format}}{delimiter}")  # Iyz wrt body CoM

        try:
            u['Geometry']
        except KeyError:
            file.write('No attached geometry')
        else:
            file.write(f"{u['Geometry']}")  # or file.write(';'.join(u['Geometry'])) if u['Geometry'] is a list
        file.write('\n')

            
    #file.write('Clever Girl') 

    file.close()
    return {'FINISHED'}