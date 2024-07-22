import bpy
from math import nan


def create_body(name, size, is_global = True, mass=nan,
                inertia_COM= [nan]*6, COM=[nan]*3, 
                inertia_COM_local=[nan]*6, COM_local=[nan]*3, 
                Geometry='no geometry', local_frame='not_assigned'):
    
    '''
    # Creates a MuSkeMo BODY in the blender scene.
    # Inputs:
    # name (string) - Mandatory. Name of the target body.
    # size (float) - Mandatory. Size of the display geometry (in meters)
    # is_global (boolean, optional). Whether to use the global COM location for display. Default is global
    # mass (float, optional) - Mass in kg.
    # inertia_COM (list of 6 floats, optional) - Moment of inertia (in kg m^2) about the COM, in the global frame.
    # COM (list of 3 floats, optional) - Center of mass (in m) in the global frame
    # inertia_COM_local (list of 6 floats, optional) - Moment of inertia (in kg m^2) about the COM, in the local (anatomical) frame.
    # COM_local (list of 3 floats, optional) - Center of mass (in m) in the local frame
    # Geometry (string, optional). List of attached geometry (including the subfolder and the filetype).
    # local frame (string, optional). Name of the local (anatomical) reference frame.
    
    # Default behavior is that none of the properties are known and filled with nan or a string, unless user-specified.
    # is_global is only used during model import, and determines whether global coordinates can be used, or if the model should be imported using local coordinates.
    call looks like this:
    create_body(
    name= ,
    size= ,
    mass= ,
    inertia_COM=,
    COM=,
    inertia_COM_local=,
    COM_local=,
    geometry=,
    local_frame=,
    is_global=  # Explicitly specify True or False for is_global
    )
    
    '''
    
    bpy.ops.object.empty_add(type='ARROWS', radius=size, align='WORLD',location = (0,0,0))
    bpy.context.object.name  = name #set the name
        
    
    obj = bpy.data.objects[name] 
    
    
    obj.rotation_mode = 'ZYX'    #change rotation sequence

    ##### add custom properties to the bodies (see blender documentation for properties)
    #add mass property
    obj['mass'] = mass  # add mass property
    obj.id_properties_ui('mass').update(description='mass of the body in kg')
    
    # Add inertia_COM property
    obj['inertia_COM'] = inertia_COM
    obj.id_properties_ui('inertia_COM').update(description = 'Ixx Iyy Izz Ixy Ixz Iyz (in kg*m^2) about body COM in global frame')
            
    obj['COM'] = COM
    obj.id_properties_ui('COM').update(description='COM position (in global frame)')
    
    
    # Add inertia_COM_local property
    obj['inertia_COM_local'] = inertia_COM_local
    obj.id_properties_ui('inertia_COM_local').update(description='Ixx Iyy Izz Ixy Ixz Iyz (in kg*m^2) about body COM in local frame')

    # Add COM_local property
    obj['COM_local'] = COM_local
    obj.id_properties_ui('COM_local').update(description='COM position (in local frame)')
    
    # Add geometry property
    obj['Geometry'] = Geometry
    obj.id_properties_ui('Geometry').update(description = 'Attached geometry for visualization (eg. bone meshes). Optional')  

    #add local frame property
    obj['local_frame'] = local_frame
    obj.id_properties_ui('local_frame').update(description = "Name of the local reference frame. You can create and assign these in the anatomical local reference frame panel. Optional")  

    ## add MuSkeMo type
    obj['MuSkeMo_type'] = 'BODY'    #to inform the user what type is created
    obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")
    
    ### set the correct display position
    if is_global and COM != [nan]*3:#if is_global is True and COM is defined
        
        obj.matrix_world.translation = COM
      
      
      
    if not is_global and COM_local != [nan]*3:#if is_global is False and COM is defined
        
        print('local body creation not implemented yet')
        ### get frame location and set obj location wrt frame
        
        
    
    
    bpy.ops.object.select_all(action='DESELECT')
    
    
