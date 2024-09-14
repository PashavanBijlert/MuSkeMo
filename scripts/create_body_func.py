import bpy
from math import nan
import os


def create_body(name, size, self,
                is_global = True, mass=nan,
                inertia_COM= [nan]*6, COM=[nan]*3, 
                inertia_COM_local=[nan]*6, COM_local=[nan]*3, 
                Geometry='no geometry', local_frame='not_assigned', 
                collection_name = 'Bodies', import_geometry = False,
                geometry_collection_name = '',
                geometry_parent_dir = ''):
    
    '''
    # Creates a MuSkeMo BODY in the blender scene.
    # Inputs:
    # name (string) - Mandatory. Name of the target body.
    # size (float) - Mandatory. Size of the display geometry (in meters)
    # self - Mandatory. The 'self' parameter of the Operator from which this function is called.
    # is_global (boolean, optional). Whether to use the global COM location for display. Default is global
    # mass (float, optional) - Mass in kg.
    # inertia_COM (list of 6 floats, optional) - Moment of inertia (in kg m^2) about the COM, in the global frame.
    # COM (list of 3 floats, optional) - Center of mass (in m) in the global frame
    # inertia_COM_local (list of 6 floats, optional) - Moment of inertia (in kg m^2) about the COM, in the local (anatomical) frame.
    # COM_local (list of 3 floats, optional) - Center of mass (in m) in the local frame
    # Geometry (string, optional). List of attached geometry (including the subfolder and the filetype).
    # local frame (string, optional). Name of the local (anatomical) reference frame.
    # collection_name (string, optional). Name of the collection where the bodies will be placed. Default = 'Bodies'
    # import_geometry (boolean, optional). Do you want visual geometries to be imported and parented to the bodies?
    # geometry_collection_name (string, optional). Name of the collection where the geometries will be placed. Gets overwritten with the MuSkeMo property "geometry collection" if empty, or overwritten by the subdirectory defined in the body
    # geometry_parent_dir (string, mandatory if importing geometry). Path to parent directory which contains the 'Geometry' directory


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
    collection_name =,
    import_geometry = ,
    geometry_collection_name = ,
    geometry_parent_dir,
    )
    
    '''
    
      
    #check if the collection name exists, and if not create it
    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the scaled  hulls

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
    
    #Make sure the "bodies" collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]



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

    

    #### geometry import
    
    if not import_geometry: #if import_geometry is false, end the script here
        return
    
    if Geometry == 'no geometry': #if the body has no geometry
        return
       
    geo_paths = Geometry.split(';') #This splits the string according to ;, and should result in the separate geometry paths
    # Extract the folder name from the first path
    geometry_collection_name = os.path.dirname(geo_paths[0])

    if geometry_collection_name: #if the collection name is nonempty (i.e., if the body has a designated geometry folder)
        bpy.context.scene.muskemo.geometry_collection = geometry_collection_name #update this MuSkeMo property

    else: #get whatever is the default or user-modified value in MuSkeMo

        geometry_collection_name = bpy.context.scene.muskemo.geometry_collection 


    #check if the collection name exists, and if not create it
    if geometry_collection_name not in bpy.data.collections:
        bpy.data.collections.new(geometry_collection_name)
        

    coll = bpy.data.collections[geometry_collection_name] #Collection which will recieve the scaled  hulls

    if geometry_collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
    
    #Make sure the geom collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[geometry_collection_name]
    
    

    geo_paths = [path for path in geo_paths if path] #remove empty strings after splitting

    for path in geo_paths:

        filepath = geometry_parent_dir + '/' + path

        if not os.path.exists(filepath): #if the above filepath doesn't exist, add Geometry/ in front of it. This accounts for OpenSim models where the Geometry subdirectory is not explicitly named
            filepath = geometry_parent_dir + '/Geometry/' + path
        
        if not os.path.exists(filepath):
            self.report({'WARNING'}, "Geometry '" + path + "' not found in model directory or 'Geometry' subdirectory. Geometry skipped")

            continue
        
        if filepath.endswith('.obj'): #if the file exists, and it is an obj file

            if bpy.app.version[0] <4: #if blender version is below 4
                bpy.ops.import_scene.obj(filepath= filepath, axis_forward = 'Y', axis_up = 'Z', use_image_search = False)
                    
            else: #if blender version is above 4:    
                bpy.ops.wm.obj_import(filepath= filepath, forward_axis = 'Y', up_axis = 'Z' ,
                                    use_split_objects = False,)


        
            # Include the extension in the newly created object's name, to prevent potential naming conflicts
            file_name_with_extension = os.path.basename(path)  # e.g. 'Humerus.001.obj'
            #mesh_name, extension = os.path.splitext(file_name_with_extension)  # e.g. 'Humerus.001', '.obj'    
            bpy.context.selected_objects[0].name =  file_name_with_extension            
            bpy.ops.object.select_all(action='DESELECT')
            
            geom_obj = bpy.data.objects[file_name_with_extension]

        elif filepath.endswith('.vtp'):
            
            self.report({'WARNING'}, "VTP import not supported yet")
            continue

        elif filepath.endswith('.stl'):
            
            self.report({'WARNING'}, "STL import not supported yet")
            continue

        else: #if it's not an obj, vtp, or stl

            self.report({'WARNING'}, "Only obj, stl, or vtp formats are supported for geometry import. Geometry '" + path + "' skipped")
            continue  

        geom_obj.parent = obj #parent a mesh to a body, but this moves it
        geom_obj.matrix_parent_inverse = obj.matrix_world.inverted() #move it back
        geom_obj.data.materials.clear()
        #geom_obj.data.materials.append(mat)

        ## Assign a MuSkeMo_type

        geom_obj['MuSkeMo_type'] = 'GEOMETRY'    #to inform the user what type is created
        geom_obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  

        geom_obj['Attached to'] = obj.name
        geom_obj.id_properties_ui('Attached to').update(description = "The body that this geometry is attached to")
            

    
    
