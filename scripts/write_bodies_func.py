def write_bodies(context, filepath, collection_name, delimiter):
    
    import bpy


    file = open(filepath, 'w', encoding='utf-8') #create or open a file called muscle_landmarks,  "w" means it's writeable
    coll = bpy.data.collections[collection_name]
    
    
    
        
    
    #file.write('body_name' + delimiter  + 'mass(kg)' + delimiter  + 'CoM_x' + delimiter  + 'CoM_y' + delimiter  + 'CoM_z' + delimiter  + 'Ixx(kg*m^2) about COM in global' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Body-frame angle x (rad, XYZ-euler)' + delimiter  + 'angle y' + delimiter  + 'angle z' + delimiter  + 'Ixx(kg*m^2) about COM in body-fixed principal' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Geometry') #headers
    file.write('body_name' + delimiter  + 'mass(kg)' + delimiter  + 'CoM_x' + delimiter  + 'CoM_y' + delimiter  
    + 'CoM_z' + delimiter  + 'Ixx(kg*m^2) about COM in global' + delimiter  + 'Iyy' + delimiter  + 'Izz' + delimiter  
    + 'Ixy' + delimiter  + 'Ixz' + delimiter  + 'Iyz' + delimiter  + 'Geometry') #headers
    
    file.write('\n') 

    for u in coll.objects: #for each body
            
        
        file.write(f"{u.name}{delimiter}")  # body name
        file.write(f"{u['mass']:#.4g}{delimiter}")  # mass in kg, 4 decimals
        file.write(f"{u['COM'][0]:#.4f}{delimiter}")  # Com_x location, 4 decimals
        file.write(f"{u['COM'][1]:#.4f}{delimiter}")  # Com_y
        file.write(f"{u['COM'][2]:#.4f}{delimiter}")  # Com_z
        file.write(f"{u['inertia_COM'][0]:#.4g}{delimiter}")  # Ixx wrt body CoM
        file.write(f"{u['inertia_COM'][1]:#.4g}{delimiter}")  # Iyy wrt body CoM
        file.write(f"{u['inertia_COM'][2]:#.4g}{delimiter}")  # Izz wrt body CoM
        file.write(f"{u['inertia_COM'][3]:#.4g}{delimiter}")  # Ixy wrt body CoM
        file.write(f"{u['inertia_COM'][4]:#.4g}{delimiter}")  # Ixz wrt body CoM
        file.write(f"{u['inertia_COM'][5]:#.4g}{delimiter}")  # Iyz wrt body CoM

        try:  # check if principal axes body frame is defined
            u['principal_axes_euler_XYZ']
            
        except:
            print('No body frame aligned to principal direction of inertia detected')
        else:
            
            file.write(f"{u['principal_axes_euler_XYZ'][0]:#.4g}{delimiter}")  # Angle x of body-fixed frame (Euler XYZ, in radians)
            file.write(f"{u['principal_axes_euler_XYZ'][1]:#.4g}{delimiter}")  # Angle y
            file.write(f"{u['principal_axes_euler_XYZ'][2]:#.4g}{delimiter}")  # Angle z
            file.write(f"{u['inertia_body_fixed_principal'][0]:#.4g}{delimiter}")  # Ixx wrt body CoM, expressed in frame aligned to principal directions
            file.write(f"{u['inertia_body_fixed_principal'][1]:#.4g}{delimiter}")  # Iyy wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][2]:#.4g}{delimiter}")  # Izz wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][3]:#.4g}{delimiter}")  # Ixy wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][4]:#.4g}{delimiter}")  # Ixz wrt body CoM
            file.write(f"{u['inertia_body_fixed_principal'][5]:#.4g}{delimiter}")  # Iyz wrt body CoM

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