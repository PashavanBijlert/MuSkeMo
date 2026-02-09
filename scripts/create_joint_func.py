import bpy
import bmesh
from mathutils import Matrix
from math import nan
#from .euler_XYZ_body import euler_XYZbody_from_matrix
from .quaternions import matrix_from_quaternion
from .euler_XYZ_body import matrix_from_euler_XYZbody

def create_joint(name, radius, is_global = True, collection_name = 'Joint centers',
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
    - collection_name (string, optional) - Name of the collection (blender folder) where the joints will be placed      
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

    #check if the collection name exists, and if not create it
    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        #If the collection didn't even exist yet, we're probably starting from scratch. Turn off the object children filter to help the user.
        bpy.ops.muskemo.set_child_visibility_outliner()

        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the joints

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
    
    #Make sure the "joints" collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
    
    # Create a sphere and set the name
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()

    bmesh.ops.create_icosphere(
        bm,
        subdivisions=3,
        radius=radius,
        matrix=Matrix.Identity(4)
    )

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    

    coll.objects.link(obj) #link to correct collection

    #####
    
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
    
        
        
        if or_in_global_quat !=[nan]*4:  #if a global orientation is supplied as a quaternion
            [gRb, bRg] = matrix_from_quaternion(or_in_global_quat)
            obj.matrix_world = gRb.to_4x4()

        
        if or_in_global_quat == [nan]*4 and or_in_global_XYZeuler != [nan]*3:

            [gRb, bRg] = matrix_from_euler_XYZbody(or_in_global_XYZeuler)
            obj.matrix_world = gRb.to_4x4()





        if pos_in_global !=[nan]*3:  #if a global position is supplied
            obj.matrix_world.translation = pos_in_global    



        
        if parent_body in bpy.data.objects: #if the parent body exists
            parent_body_obj = bpy.data.objects[parent_body]

            if 'BODY' in parent_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body
                
                obj.parent = parent_body_obj
                obj.matrix_parent_inverse = parent_body_obj.matrix_world.inverted()                      

                obj['default_pose'] = list(obj.matrix_world) #### keep track of the default pose of the object
                

        
        if child_body in bpy.data.objects: #if the child body exists
            child_body_obj = bpy.data.objects[child_body]

            if 'BODY' in child_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body
                
                child_body_obj.parent = obj
                child_body_obj.matrix_parent_inverse = obj.matrix_world.inverted()

                if 'default_pose' not in obj: #if it wasn't created during parent object setting, set it here
                    obj['default_pose'] = list(obj.matrix_world) #### keep track of the default pose of the object
                
                
        #if local frame is assigned, then you can assign the local orientation and position
        #otherwise give warning that it's ignored
    
    if not is_global:
        

        #error check for existing frames
        #check if we use quats or euler
        #do the same for both parent and child
        if pos_in_parent_frame != [nan]*3:#if is_global is False and pos in parent is supplied
        
            print('local joint creation not implemented yet')
        ### get frame location and set obj location wrt frame    
    

    matname = 'joint_material'
    color = tuple(bpy.context.scene.muskemo.joint_color)
    transparency = 0.5

    ##### Assign a material
    
    if matname not in bpy.data.materials:   #if the material doesn't exist, get it
        from .create_transparent_material_func import create_transparent_material
        create_transparent_material(matname, color, transparency)

    mat = bpy.data.materials[matname]
    obj.data.materials.append(mat)

    ### viewport display color

    obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)

    
    bpy.ops.object.select_all(action='DESELECT')