import bpy
from math import nan

def create_joint(name, radius, is_global = True,
                 parent_body='not_assigned', child_body='not_assigned', 
                 pos_in_global=[nan] * 3, or_in_global_XYZeuler=[nan] * 3, 
                 or_in_global_quat=[nan] * 4,
                 pos_in_parent_frame=[nan] * 3,
                 or_in_parent_frame_XYZeuler=[nan] * 3, or_in_parent_frame_quat=[nan] * 4,
                 pos_in_child_frame=[nan] * 3, 
                 or_in_child_frame_XYZeuler=[nan] * 3, or_in_child_frame_quat=[nan] * 4,
                 coordinate_Tx='', coordinate_Ty='', coordinate_Tz='', 
                 coordinate_Rx='', coordinate_Ry='', coordinate_Rz='',                  
                ):
    """
    Creates a MuSkeMo JOINT in the Blender scene.

    Inputs:
    - name (string) - Mandatory. Name of the joint.
    - radius (float) - Mandatory. Radius of the display geometry (in meters)
    - is_global (boolean) - Optional. Whether the joint should be defined using global coordinates
    - parent_body (string, optional) - Name of the parent body. Default is 'not_assigned'.
    - child_body (string, optional) - Name of the child body. Default is 'not_assigned'.
    - pos_in_global (list of 3 floats, optional) - Joint position in the global frame (in meters).
    - or_in_global_XYZeuler (list of 3 floats, optional) - Joint orientation in the global frame (XYZ Euler angles in radians).
    - or_in_global_quat (list of 4 floats, optional) - Joint orientation in the global frame (quaternion).
    - pos_in_parent_frame (list of 3 floats, optional) - Joint position in the parent body frame (in meters).
    - or_in_parent_frame_XYZeuler (list of 3 floats, optional) - Joint orientation in the parent body frame (XYZ Euler angles in radians).
    - or_in_parent_frame_quat (list of 4 floats, optional) - Joint orientation in the parent body frame (quaternion).
    - pos_in_child_frame (list of 3 floats, optional) - Joint position in the child body frame (in meters).
    - or_in_child_frame_XYZeuler (list of 3 floats, optional) - Joint orientation in the child body frame (XYZ Euler angles in radians).
    - or_in_child_frame_quat (list of 4 floats, optional) - Joint orientation in the child body frame (quaternion).
    - coordinate_Tx (string, optional) - Name of the translational x coordinate.
    - coordinate_Ty (string, optional) - Name of the translational y coordinate.
    - coordinate_Tz (string, optional) - Name of the translational z coordinate.
    - coordinate_Rx (string, optional) - Name of the rotational x coordinate.
    - coordinate_Ry (string, optional) - Name of the rotational y coordinate.
    - coordinate_Rz (string, optional) - Name of the rotational z coordinate.
    

    # Default behavior is that none of the properties are known and filled with nan or a string, unless user-specified.
    # is_global is only used during model import, and determines whether global coordinates can be used, or if the model should be imported using local coordinates.
    
    """
    
    # Create a sphere and set the name
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, enter_editmode=False, align='WORLD', location=(0, 0, 0))
    obj = bpy.context.object
    obj.name = name  # Set the name
    obj = bpy.data.objects[name] 
    obj.rotation_mode = 'ZYX'  # Change rotation sequence
    
    ## set parent & child
    obj['parent_body'] = parent_body
    obj.id_properties_ui('parent_body').update(description='The parent body of this joint')

    obj['child_body'] = child_body
    obj.id_properties_ui('child_body').update(description='The child body of this joint')
    
    
    ## Set global or & pos
   
    obj['pos_in_global'] = pos_in_global
    obj.id_properties_ui('pos_in_global').update(description='Joint position in the global reference frame (x, y, z, in meters). Optional.')

    obj['or_in_global_XYZeuler'] = or_in_global_XYZeuler
    obj.id_properties_ui('or_in_global_XYZeuler').update(description='Joint orientation XYZ-Euler angles in the global reference frame (x, y, z, in rad). Optional.')

    obj['or_in_global_quat'] = or_in_global_quat
    obj.id_properties_ui('or_in_global_quat').update(description='Joint orientation quaternion decomposition in the global reference frame (w, x, y, z). Optional.')
    
       
    ## parent frame data
    
    #obj['parent_frame_name'] = parent_frame_name
    #obj.id_properties_ui('parent_frame_name').update(description='Name of the parent frame.')
    
    obj['pos_in_parent_frame'] = pos_in_parent_frame
    obj.id_properties_ui('pos_in_parent_frame').update(description='Joint position in the parent body anatomical (local) reference frame (x, y, z, in meters). Optional.')

    obj['or_in_parent_frame_XYZeuler'] = or_in_parent_frame_XYZeuler
    obj.id_properties_ui('or_in_parent_frame_XYZeuler').update(description='Joint orientation XYZ-Euler angles in the parent body anatomical (local) reference frame (x, y, z, in rad). Optional.')

    obj['or_in_parent_frame_quat'] = or_in_parent_frame_quat
    obj.id_properties_ui('or_in_parent_frame_quat').update(description='Joint orientation quaternion decomposition in the parent body anatomical (local) reference frame (w, x, y, z). Optional.')

    ## child frame data
    
    #obj['child_frame_name'] = child_frame_name
    #obj.id_properties_ui('child_frame_name').update(description='Name of the child frame.')

    obj['pos_in_child_frame'] = pos_in_child_frame
    obj.id_properties_ui('pos_in_child_frame').update(description='Joint position in the child body anatomical (local) reference frame (x, y, z, in meters). Optional.')

    obj['or_in_child_frame_XYZeuler'] = or_in_child_frame_XYZeuler
    obj.id_properties_ui('or_in_child_frame_XYZeuler').update(description='Joint orientation XYZ-Euler angles in the child body anatomical (local) reference frame (x, y, z, in rad). Optional.')

    obj['or_in_child_frame_quat'] = or_in_child_frame_quat
    obj.id_properties_ui('or_in_child_frame_quat').update(description='Joint orientation quaternion decomposition in the child body anatomical (local) reference frame (w, x, y, z). Optional.')

   
    # Set joint coordinates
    obj['coordinate_Tx'] = coordinate_Tx
    obj.id_properties_ui('coordinate_Tx').update(description='Name of the Translational x coordinate')
    
    obj['coordinate_Ty'] = coordinate_Ty
    obj.id_properties_ui('coordinate_Ty').update(description='Name of the Translational y coordinate')
    
    obj['coordinate_Tz'] = coordinate_Tz
    obj.id_properties_ui('coordinate_Tz').update(description='Name of the Translational z coordinate')
    
    obj['coordinate_Rx'] = coordinate_Rx
    obj.id_properties_ui('coordinate_Rx').update(description='Name of the Rotational x coordinate')
    
    obj['coordinate_Ry'] = coordinate_Ry
    obj.id_properties_ui('coordinate_Ry').update(description='Name of the Rotational y coordinate')
    
    obj['coordinate_Rz'] = coordinate_Rz
    obj.id_properties_ui('coordinate_Rz').update(description='Name of the Rotational z coordinate')
    
    ## set MuSkeMo type
    obj['MuSkeMo_type'] = 'JOINT'
    obj.id_properties_ui('MuSkeMo_type').update(description="The object type. Warning: don't modify this!")
    
    
    if is_global: #if user wants to define using global coordinates
    
        if pos_in_global !=[nan]*3:  #if a global position is supplied
            obj.matrix_world.translation = pos_in_global
        
        if or_in_global_XYZeuler !=[nan]*3:  #if a global orientation is supplied
        
            print('error I have to add this in')
        
        #if same for quat
        
        #if statement for if the parent body exists already, parent it
        #if statement for if the child body exists already, parent it
    
    if not is_global:
        

        #error check for existing frames
        #check if we use quats or euler
        #do the same for both parent and child
        if pos_in_parent_frame != [nan]*3:#if is_global is False and pos in parent is supplied
        
            print('local joint creation not implemented yet')
        ### get frame location and set obj location wrt frame    



    bpy.ops.object.select_all(action='DESELECT')