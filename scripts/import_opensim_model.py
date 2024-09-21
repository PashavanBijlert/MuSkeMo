import bpy
from mathutils import (Vector, Matrix)
from bpy.types import (Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)

import xml.etree.ElementTree as ET
from math import nan
import numpy as np
import os
import pprint


class ImportOpenSimModel(Operator):
    bl_description = "Import an OpenSim 4.0+ model"
    bl_idname = "import.import_opensim_model"
    bl_label = "Import OpenSim model"


    # This section is based on importhelper
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    #this filters other filetypes from the window during export. The actual value is set in invoke, by setting the filetype
    filter_glob: bpy.props.StringProperty(default = "",options={'HIDDEN'}, maxlen=255)

    #run the file select window manager, with a filter for .osim extension files
    def invoke(self, context, _event):

        self.filter_glob = "*.osim"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    
    def execute(self, context):
        """Reads XML data from the specified filepath"""
        filepath = self.filepath
        tree = ET.parse(filepath)
        root = tree.getroot()    
        model = root.find('Model')
        
        from .quaternions import (matrix_from_quaternion, quat_from_matrix)
        from .euler_XYZ_body import (matrix_from_euler_XYZbody, euler_XYZbody_from_matrix)
    
        def get_body_data(model):
            body_set = model.find('BodySet')
            bodies = body_set.find('objects')

            body_data = {}
            for body in bodies.findall('Body'):
                name = body.get('name')
                mass = float(body.find('mass').text)

                # Check if mass_center exists
                mass_center_element = body.find('mass_center')
                if mass_center_element is not None:
                    mass_center = tuple(map(float, mass_center_element.text.split()))
                else:
                    mass_center = (0, 0, 0)

                # Check if inertia exists
                inertia_element = body.find('inertia')
                if inertia_element is not None:
                    inertia = tuple(map(float, inertia_element.text.split()))
                else:
                    inertia = None  # Or another default value if inertia is absent

                geometries = []

                # First, try to find PhysicalOffsetFrames, if they exist
                components = body.find('components')
                if components is not None:
                    offset_frames = components.findall('PhysicalOffsetFrame')
                    for offset_frame in offset_frames:
                        attached_geometry = offset_frame.find('attached_geometry')
                        if attached_geometry is not None:
                            for mesh in attached_geometry.findall('Mesh'):
                                mesh_file = mesh.find('mesh_file').text.strip()
                                translation = offset_frame.find('translation').text
                                orientation = offset_frame.find('orientation').text

                                # Check for scale_factors
                                scale_elem = mesh.find('scale_factors')
                                if scale_elem is not None:
                                    scale_factors = list(map(float, scale_elem.text.strip().split()))
                                else:
                                    scale_factors = [1.0, 1.0, 1.0]

                                geometries.append({
                                    'mesh_file': mesh_file,
                                    'translation': translation,
                                    'orientation': orientation,
                                    'scale_factors': scale_factors,
                                })

                # If no PhysicalOffsetFrame exists, check directly within the Body
                if not geometries:
                    attached_geometry = body.find('attached_geometry')
                    if attached_geometry is not None:
                        for mesh in attached_geometry.findall('Mesh'):
                            mesh_file = mesh.find('mesh_file').text.strip()
                            
                            # Check for scale_factors
                            scale_elem = mesh.find('scale_factors')
                            if scale_elem is not None:
                                scale_factors = list(map(float, scale_elem.text.strip().split()))
                            else:
                                scale_factors = [1.0, 1.0, 1.0]

                            geometries.append({
                                'mesh_file': mesh_file,
                                'scale_factors': scale_factors
                            })

                # Wrap Object Set (handle any wrap object type)
                wrap_objects = []
                wrap_object_set = body.find('WrapObjectSet')
                if wrap_object_set is not None:
                    for wrap_object in wrap_object_set.find('objects').findall('*'):  # Get all wrap object types
                        wrap_data = {
                            'type': wrap_object.tag,  # Save the type of the wrap object (e.g., WrapCylinder, WrapSphere, etc.)
                            'name': wrap_object.get('name')
                        }

                        # Collect all child elements of the wrap object dynamically
                        for child in wrap_object:
                            # Handle scalar and vector types
                            value = child.text.strip() if child.text else None
                            if value is not None:
                                if value.lower() in ['true', 'false']:  # Handle boolean values
                                    wrap_data[child.tag] = value.lower() == 'true'
                                else:
                                    try:
                                        # Try to convert to float (for numbers)
                                        wrap_data[child.tag] = float(value)
                                    except ValueError:
                                        # If it cannot be converted, store it as a string or tuple
                                        if ' ' in value:
                                            wrap_data[child.tag] = tuple(map(float, value.split()))  # Handle vectors
                                        else:
                                            wrap_data[child.tag] = value  # Store as string if it's not a number

                            # Special case for Appearance
                            if child.tag == 'Appearance':
                                appearance = {}
                                for appearance_child in child:
                                    if appearance_child.tag == 'color':
                                        appearance['color'] = tuple(map(float, appearance_child.text.split()))
                                    elif appearance_child.tag == 'opacity':
                                        appearance['opacity'] = float(appearance_child.text)
                                    elif appearance_child.tag == 'SurfaceProperties':
                                        appearance['representation'] = appearance_child.find('representation').text
                                wrap_data['appearance'] = appearance

                        wrap_objects.append(wrap_data)

                # Add body data to dictionary
                body_data[name] = {
                    'mass': mass,
                    'mass_center': mass_center,
                    'inertia': inertia,
                    'geometries': geometries,
                    'wrap_objects': wrap_objects  # Modular wrap object data
                }

            return body_data



        def get_joint_data(model):
            joint_set = model.find('JointSet')
            joints = joint_set.find('objects')

            joint_data = {}
            for joint in joints:
                joint_name = joint.get('name')
                joint_type = joint.tag

                # Extract parent and child frames
                parent_frame = joint.find('socket_parent_frame').text.strip()
                child_frame = joint.find('socket_child_frame').text.strip()

                # Initialize parent_body and child_body to None
                parent_body = None
                child_body = None

                # Extract frames within the joint
                frames_data = []
                frames = joint.find('frames')
                if frames is not None:
                    for frame in frames.findall('PhysicalOffsetFrame'):
                        frame_name = frame.get('name')
                        translation = tuple(map(float, frame.find('translation').text.split()))
                        orientation = tuple(map(float, frame.find('orientation').text.split()))
                        socket_parent = frame.find('socket_parent').text.strip()

                        # Match parent_frame with frame_name to get parent_body
                        if frame_name == parent_frame:
                            parent_body = socket_parent.split('/bodyset/')[-1]
                            if parent_body == '/ground':
                                parent_body = 'ground'

                        # Match child_frame with frame_name to get child_body
                        if frame_name == child_frame:
                            child_body = socket_parent.split('/bodyset/')[-1]

                        frames_data.append({
                            'frame_name': frame_name,
                            'translation': translation,
                            'orientation': orientation,
                            'socket_parent': socket_parent
                        })

                # Extract coordinates if any
                coordinates = []
                coords_element = joint.find('coordinates')
                if coords_element is not None:
                    for coord in coords_element.findall('Coordinate'):
                        coordinates.append(coord.get('name'))

                # Extract spatial transform data if present
                spatial_transform = []
                spatial_transform_element = joint.find('SpatialTransform')
                if spatial_transform_element is not None:
                    for axis in spatial_transform_element.findall('TransformAxis'):
                        axis_name = axis.get('name')
                        axis_coordinates_element = axis.find('coordinates')
                        axis_coordinates = axis_coordinates_element.text.strip() if axis_coordinates_element is not None and axis_coordinates_element.text is not None else None
                        axis_vector = tuple(map(float, axis.find('axis').text.split()))

                        # Check if the transform axis has a LinearFunction and extract its coefficients
                        transform_function = axis.find('LinearFunction')
                        coefficients = None
                        if transform_function is not None:
                            coeff_values = tuple(map(float, transform_function.find('coefficients').text.split()))
                            coefficients = coeff_values
                            if coeff_values != (1.0, 0.0):
                                print(f"Warning: Joint '{joint_name}' has a transform function that MuSkeMo may not support. Treating as regular joint.")

                        spatial_transform.append({
                            'axis_name': axis_name,
                            'axis_coordinates': axis_coordinates,
                            'axis_vector': axis_vector,
                            'coefficients': coefficients
                        })

                # Store the extracted joint data in the dictionary
                joint_data[joint_name] = {
                    'joint_type': joint_type,
                    'parent_frame': parent_frame,
                    'child_frame': child_frame,
                    'parent_body': parent_body,
                    'child_body': child_body,
                    'frames_data': frames_data,
                    'coordinates': coordinates,
                    'spatial_transform': spatial_transform
                }

            return joint_data


        def get_muscle_data(model):
            muscle_data = {}

            # Locate the ForceSet in the model
            forceset = model.find('ForceSet')
            if forceset is not None:
                # Locate all muscle objects (assuming they end with 'Muscle')
                muscles = forceset.find('objects')
                if muscles is not None:
                    for muscle in muscles:
                        if muscle.tag.endswith('Muscle'):
                            muscle_name = muscle.get('name')
                            muscle_type = muscle.tag

                            # Initialize variables with default values
                            tendon_slack_length = 0.0
                            max_isometric_force = 0.0
                            optimal_fiber_length = 0.0
                            pennation_angle = 0.0

                            # Extract specific muscle properties if they exist
                            if muscle.find('tendon_slack_length') is not None:
                                tendon_slack_length = float(muscle.find('tendon_slack_length').text)
                            if muscle.find('max_isometric_force') is not None:
                                max_isometric_force = float(muscle.find('max_isometric_force').text)
                            if muscle.find('optimal_fiber_length') is not None:
                                optimal_fiber_length = float(muscle.find('optimal_fiber_length').text)
                            if muscle.find('pennation_angle_at_optimal') is not None:
                                pennation_angle = np.rad2deg(float(muscle.find('pennation_angle_at_optimal').text))

                            # Extract GeometryPath information
                            geometry_path = muscle.find('GeometryPath')
                            path_points_data = []
                            if geometry_path is not None:
                                path_point_set = geometry_path.find('PathPointSet')
                                if path_point_set is not None:
                                    path_points = path_point_set.find('objects')
                                    if path_points is not None:
                                        for point in path_points.findall('PathPoint'):
                                            point_name = point.get('name')
                                            parent_frame = point.find('socket_parent_frame').text.strip()
                                            location = tuple(map(float, point.find('location').text.split()))

                                            path_points_data.append({
                                                'point_name': point_name,
                                                'parent_frame': parent_frame,
                                                'location': location
                                            })

                            # Add the extracted data to the muscle_data dict
                            muscle_data[muscle_name] = {
                                'muscle_type': muscle_type,
                                'tendon_slack_length': tendon_slack_length,
                                'F_max': max_isometric_force,
                                'optimal_fiber_length': optimal_fiber_length,
                                'pennation_angle': pennation_angle,
                                'path_points_data': path_points_data
                            }

            return muscle_data
       
        def get_contact_data(model):
            contact_data = {}

            # Locate the ContactGeometrySet in the model
            contact_geometry_set = model.find('ContactGeometrySet')
            if contact_geometry_set is not None:
                # Locate all contact geometry objects
                contact_objects = contact_geometry_set.find('objects')
                if contact_objects is not None:
                    for contact_geometry in contact_objects:
                        geometry_name = contact_geometry.get('name')
                        geometry_type = contact_geometry.tag

                        # Initialize variables with default values
                        socket_frame = None
                        location = (0.0, 0.0, 0.0)
                        orientation = (0.0, 0.0, 0.0)
                        radius = None  # Not all geometries will have a radius

                        # Extract frame, location, and orientation
                        if contact_geometry.find('socket_frame') is not None:
                            socket_frame = contact_geometry.find('socket_frame').text.strip()

                        if contact_geometry.find('location') is not None:
                            location = tuple(map(float, contact_geometry.find('location').text.split()))

                        if contact_geometry.find('orientation') is not None:
                            orientation = tuple(map(float, contact_geometry.find('orientation').text.split()))

                        # Extract radius if it's a sphere
                        if geometry_type == 'ContactSphere' and contact_geometry.find('radius') is not None:
                            radius = float(contact_geometry.find('radius').text)

                        # Add the extracted data to the contact_data dict
                        contact_data[geometry_name] = {
                            'geometry_type': geometry_type,
                            'socket_frame': socket_frame,
                            'location': location,
                            'orientation': orientation,
                            'radius': radius  # Will be None for geometries without a radius
                        }

            return contact_data



        # Extract body data from the model, and check if geometry folder exists
        body_data = get_body_data(model)
        
        body_colname = bpy.context.scene.muskemo.body_collection #name for the collection that will contain the hulls
        body_axes_size = bpy.context.scene.muskemo.axes_size #axis length, in meters
        geometry_parent_dir = os.path.dirname(self.filepath)
        import_geometry = bpy.context.scene.muskemo.import_visual_geometry #user switch for import geometry, true or false

        wrap_colname = bpy.context.scene.muskemo.wrap_geom_collection

        if import_geometry: #if the user wants imported geometry, we check if the folder exists

            # Loop through the data to find the first valid geometry path
            for body in body_data.values():
                geometries = body['geometries']  # list of dictionaries
                
                # If geometries exist, join them with semicolons, otherwise set a default string
                if geometries:
                    geometry_string = ';'.join([geometry['mesh_file'] for geometry in geometries]) + ';' 

                else:
                    geometry_string = 'no geometry'

                if 'no geometry' not in geometry_string.lower(): #set lowercase when checking
                    # Split the geometry string by ';' and take the first path
                    first_geometry_path = geometry_string.split(';')[0]
                    
                    # Extract the folder name from the first path
                    geometry_dir = os.path.dirname(first_geometry_path)
                    
                    folder_path = geometry_parent_dir + '/' + geometry_dir
                    
                    if geometry_dir: #if there is a geometry folder specified
                        
                        if not os.path.exists(folder_path) or not os.path.isdir(folder_path): #if the path doesn't exist or isn't a folder
                            import_geometry = False
                            self.report({'WARNING'}, "The geometry folder '" + geometry_dir + "' specified in the model file does not appear to be in the same directory. Skipping geometry import.")

                    else: #no geometry folder specified
                        self.report({'WARNING'}, "The model does not specify a geometry (sub)directory. If the geometries are not in the model directory or in a subdirectory named 'Geometry', they will be skipped during import.")

                    
                    # Break the loop as we've found the first valid geometry path
                    break
                   

        # Extract joint data from the model
        joint_data = get_joint_data(model)

        joint_colname = bpy.context.scene.muskemo.joint_collection #name for the collection that will contain the joints
        joint_rad = bpy.context.scene.muskemo.jointsphere_size #joint_radius

        # Extract muscle data from the model
        muscle_data = get_muscle_data(model)
        muscle_colname = bpy.context.scene.muskemo.muscle_collection #name for the collection that will contain the muscles
        
        # Extract the contact data from the model
        contact_data = get_contact_data(model)
        contact_colname =  bpy.context.scene.muskemo.contact_collection #name for the collection that will contain the contacts



        #### import the component creation functions

        from .create_body_func import create_body
        from .create_joint_func import create_joint
        from .create_muscle_func import create_muscle
        from .create_frame_func import create_frame
        from .create_contact_func import create_contact
        from .create_wrapgeom_func import create_wrapgeom


        # Frame related user inputs
        frame_colname = bpy.context.scene.muskemo.frame_collection
        frame_size = bpy.context.scene.muskemo.ARF_axes_size
        
        if bpy.context.scene.muskemo.model_import_style == 'glob':  #if importing a model using global definitions
            
            #### create bodies
            for body_name, body in body_data.items():
                
                mass = body['mass']
                COM = list(body['mass_center'])  # Convert tuple to list
                inertia_COM = list(body['inertia'])  # Convert tuple to list
                geometries = body['geometries']  # This will be a list of dictionaries or empty list


                # If geometries exist, join them with semicolons, otherwise set a default string
                if geometries:
                    geometry_string = ';'.join([geometry['mesh_file'] for geometry in geometries]) + ';' 

                else:
                    geometry_string = 'no geometry'

                # Call create_body with the prepared geometry string
                create_body(name=body_name, self=self,
                             is_global = True, size = body_axes_size,
                            mass=mass, COM=COM,  inertia_COM=inertia_COM, Geometry=geometry_string, 
                            collection_name=body_colname,  
                            import_geometry = import_geometry, #the bool property
                                geometry_parent_dir = geometry_parent_dir)
                

            #### create joints
            

            for joint_name, joint in joint_data.items():

                
                parent_body = joint['parent_body']
                child_body = joint['child_body']

                frames_dict = {frame['frame_name']: frame for frame in joint['frames_data']} #dictionary for easier access

                parent_frame_name = joint['parent_frame']
                child_frame_name = joint['child_frame']

                translation_in_parent_frame = frames_dict[parent_frame_name]['translation']
                orientation_in_parent_frame = frames_dict[parent_frame_name]['orientation']

                translation_in_child_frame = frames_dict[child_frame_name]['translation']
                orientation_in_child_frame = frames_dict[child_frame_name]['orientation']

                ## coordinates

                coordinate_Tx = ''
                coordinate_Ty = ''
                coordinate_Tz = ''
                coordinate_Rx = ''
                coordinate_Ry = ''
                coordinate_Rz = ''

                # Loop through each transform axis in the joint's spatial_transform data
                for transform in joint['spatial_transform']:
                    axis_vector = transform['axis_vector']
                    coordinates = transform['axis_coordinates']

                    
                    if coordinates: #if coordinates aren't none
                    # Check which axis the transform corresponds to and assign the coordinate accordingly
                        if axis_vector == (1, 0, 0):  # X-axis
                            if 'rotation' in transform['axis_name']:
                                coordinate_Rx = coordinates
                            elif 'translation' in transform['axis_name']:
                                coordinate_Tx = coordinates
                        elif axis_vector == (0, 1, 0):  # Y-axis
                            if 'rotation' in transform['axis_name']:
                                coordinate_Ry = coordinates
                            elif 'translation' in transform['axis_name']:
                                coordinate_Ty = coordinates
                        elif axis_vector == (0, 0, 1):  # Z-axis
                            if 'rotation' in transform['axis_name']:
                                coordinate_Rz = coordinates
                            elif 'translation' in transform['axis_name']:
                                coordinate_Tz = coordinates
                
                #because we're importing a model constructed with global definitions
                pos_in_global = translation_in_parent_frame
                or_in_global_XYZeuler = orientation_in_parent_frame

                create_joint(name = joint_name, radius = joint_rad, 
                            collection_name=joint_colname,
                            is_global = True,
                            parent_body=parent_body, 
                            child_body=child_body,
                            pos_in_global = pos_in_global, 
                            or_in_global_XYZeuler = or_in_global_XYZeuler,
                            or_in_global_quat = quat_from_matrix(matrix_from_euler_XYZbody(or_in_global_XYZeuler)[0]),
                            coordinate_Tx = coordinate_Tx,
                            coordinate_Ty = coordinate_Ty,
                            coordinate_Tz = coordinate_Tz,
                            coordinate_Rx = coordinate_Rx,
                            coordinate_Ry = coordinate_Ry,
                            coordinate_Rz = coordinate_Rz,
                )
                            #or_in_global_quat= or_in_global_quat,
                            #pos_in_parent_frame = pos_in_parent_frame, 
                            #or_in_parent_frame_XYZeuler = or_in_parent_frame_XYZeuler,
                            #or_in_parent_frame_quat= or_in_parent_frame_quat,
                            #pos_in_child_frame = pos_in_child_frame, 
                            #or_in_child_frame_XYZeuler = or_in_child_frame_XYZeuler,
                            #or_in_child_frame_quat= or_in_child_frame_quat,
                            
        
         
        else: #if using local definitions
            
            
            def build_joint_tree(joint_data, parent_body):
                # Find all joints where the parent_body is the current body
                child_joints = {}
                
                for joint_name, joint in joint_data.items():
                    if joint['parent_body'] == parent_body:
                        # Recursively build the tree for this joint's child body
                        child_body = joint['child_body']
                        child_joints[joint_name] = build_joint_tree(joint_data, child_body)
                
                return child_joints

            # Get the entire joint topology as a tree structure
            joint_tree = build_joint_tree(joint_data, 'ground') #this assumes ground is always the parent body of the model

            # Pretty print the resulting tree structure
            pprint.pprint(joint_tree)

            #iterate through the joint_tree and create the joints, frames, and child bodies
            # Initialize the stack with the root joints
            stack = list(joint_tree.items())
            frames = {} #initialize a frames dict
            while stack:
                # Get the current joint and its child tree
                joint_name, joint_childtree = stack.pop()

                # unpack some of the joint data
                joint = joint_data[joint_name]
                
                parent_body_name = joint['parent_body']
                child_body_name = joint['child_body']

                frames_dict = {frame['frame_name']: frame for frame in joint['frames_data']} #dictionary for easier access

                parent_frame_name = joint['parent_frame']
                child_frame_name = joint['child_frame']

                translation_in_parent_frame = frames_dict[parent_frame_name]['translation']
                orientation_in_parent_frame = frames_dict[parent_frame_name]['orientation']

                translation_in_child_frame = frames_dict[child_frame_name]['translation']
                orientation_in_child_frame = frames_dict[child_frame_name]['orientation']

                if parent_body_name == 'ground':

                    pos_in_global = translation_in_parent_frame 
                    or_in_global_XYZeuler = orientation_in_parent_frame
                    or_in_global_quat = quat_from_matrix(matrix_from_euler_XYZbody(or_in_global_XYZeuler)[0])

                else:
                    
                    parent_frame = frames[parent_frame_name]  #this calls the dictionary that is created earlier. Since we start at root, this is populated by the time we get here

                    gRp = parent_frame['gRf'] #parent frame orientation in global
                    pRj, jRp = matrix_from_euler_XYZbody(orientation_in_parent_frame) #p is parent frame, j is joint
                    or_in_parent_frame_quat = quat_from_matrix(pRj)
                    
                    gRj =  gRp @ pRj  #parent frame in global times orientation in parent. Results in joint orientation in global frame
                    
                    or_in_global_XYZeuler = euler_XYZbody_from_matrix(gRj) #MAYBE CONVERT IT ALL TO QUATS?

                    #   position in global = gRp @ loc_p + par_frame_loc_g   (joint translation in parent frame must be rotated to global, and then added to the parent frame global position)                    
                    pos_in_global = gRp @ Vector(translation_in_parent_frame) + parent_frame['frame_pos_in_global']
                    
                    or_in_global_quat= quat_from_matrix(gRj)

                #### reconstruct the child frame
                gRj, jRg = matrix_from_euler_XYZbody(or_in_global_XYZeuler) # g is global frame, j is joint
                cRj, jRc = matrix_from_euler_XYZbody(orientation_in_child_frame) #c is child frame, j is joint

                or_in_child_frame_quat= quat_from_matrix(cRj)

                gRc = gRj @ jRc  #child frame orientation in global
                

                frame_pos_in_global = Vector(pos_in_global) - gRc @ Vector(translation_in_child_frame)

                #add to the frames dictionary
                frames[child_frame_name] = {'frame_pos_in_global': frame_pos_in_global,
                                            'gRf': gRc, # frame orientation in global
                                            }
                

                #### construct child body
                
                body = body_data[child_body_name]

                mass = body['mass']
                COM_local = list(body['mass_center'])  # Convert tuple to list, COM in child body frame
                inertia_COM_local = list(body['inertia'])  # Convert tuple to list, COM in child body frame (c frame)

                COM_global = gRc @ Vector(COM_local) + frame_pos_in_global #gRc is child body frame orientation in global
                
                MOI_c_matrix = Matrix(((inertia_COM_local[0], inertia_COM_local[3], inertia_COM_local[4]), #MOI tensor about COM in global
                        (inertia_COM_local[3],inertia_COM_local[1],inertia_COM_local[5]),
                        (inertia_COM_local[4],inertia_COM_local[5],inertia_COM_local[2])))
                
                cRg = gRc.copy() #copy the gRc matrix
                cRg.transpose() #transpose it so that it becomes cRg

                MOI_g_matrix = gRc @ MOI_c_matrix @ cRg

                inertia_COM_global =   [MOI_g_matrix[0][0],  #Ixx, about COM, in global frame
                                        MOI_g_matrix[1][1],  #Iyy
                                        MOI_g_matrix[2][2],  #Izz
                                        MOI_g_matrix[0][1],  #Ixy
                                        MOI_g_matrix[0][2],  #Ixz
                                        MOI_g_matrix[1][2]]  #Iyz

                geometries = body['geometries']  # This will be a list of dictionaries or empty list


                # If geometries exist, join them with semicolons, otherwise set a default string
                if geometries:
                    geometry_string = ';'.join([geometry['mesh_file'] for geometry in geometries]) + ';' 
                    
                    geometry_pos_in_glob = []
                    geometry_or_in_glob = []
                    geom_scale = []
                    for geometry in geometries: 
                        #if body has geometries attached
                        if 'translation' in geometry: #if translation is in a geometry, it was attached to an offsetframe wrt the body local frame (see the get_body_data function). We need to account for this during geometry import
                                                      
                            #c = child body frame, o = offset frame wrt child frame
                            [cRo, oRc] = matrix_from_euler_XYZbody([float(x) for x in geometry['orientation'].split()]) 
                            
                            gRo = gRc@cRo #rotation matrix from offset frame to global
                            geometry_or_in_glob.append(gRo)
                            
                            #child frame here means child body of the joint. It is actually the parent of the offest frame!
                            offset_pos_in_child_frame = Vector([float(x) for x in geometry['translation'].split()])
                            geometry_pos_in_glob.append(frame_pos_in_global + gRc @ offset_pos_in_child_frame)
                            

                        else:#geometry is directly attached to body frame     
                            geometry_pos_in_glob.append(frame_pos_in_global)
                            geometry_or_in_glob.append(gRc)

                        geom_scale.append(Vector(geometry['scale_factors']))



                else:
                    geometry_string = 'no geometry'
                    geometry_pos_in_glob = ''
                    geometry_or_in_glob = ''

                # Call create_body with the prepared geometry string
                create_body(name=child_body_name, self = self,
                            is_global = True, size = body_axes_size,
                            mass=mass, 
                            COM = COM_global, inertia_COM = inertia_COM_global,
                            COM_local=COM_local,  inertia_COM_local=inertia_COM_local,
                            local_frame = child_frame_name, 
                            Geometry=geometry_string, 
                            collection_name=body_colname,  
                            import_geometry = import_geometry, #the bool property
                            geometry_parent_dir = geometry_parent_dir,
                            geometry_pos_in_glob = geometry_pos_in_glob,
                            geometry_or_in_glob = geometry_or_in_glob,
                            geometry_scale = geom_scale,
                            )


                #### construct child frame

                create_frame(name = child_frame_name, size = frame_size , 
                             pos_in_global=frame_pos_in_global,
                        gRb = gRc, 
                        parent_body = child_body_name,
                        collection_name = frame_colname) 



                #### construct joint

                ## create coordinates

                coordinate_Tx = ''
                coordinate_Ty = ''
                coordinate_Tz = ''
                coordinate_Rx = ''
                coordinate_Ry = ''
                coordinate_Rz = ''

                # Loop through each transform axis in the joint's spatial_transform data
                for transform in joint['spatial_transform']:
                    axis_vector = transform['axis_vector']
                    coordinates = transform['axis_coordinates']

                    
                    if coordinates: #if coordinates aren't none
                    # Check which axis the transform corresponds to and assign the coordinate accordingly
                        if axis_vector == (1, 0, 0):  # X-axis
                            if 'rotation' in transform['axis_name']:
                                coordinate_Rx = coordinates
                            elif 'translation' in transform['axis_name']:
                                coordinate_Tx = coordinates
                        elif axis_vector == (0, 1, 0):  # Y-axis
                            if 'rotation' in transform['axis_name']:
                                coordinate_Ry = coordinates
                            elif 'translation' in transform['axis_name']:
                                coordinate_Ty = coordinates
                        elif axis_vector == (0, 0, 1):  # Z-axis
                            if 'rotation' in transform['axis_name']:
                                coordinate_Rz = coordinates
                            elif 'translation' in transform['axis_name']:
                                coordinate_Tz = coordinates
                
                if joint['joint_type'] == 'PinJoint': #if the joint type is a pinjoint, manually set the coordinate
                    coordinate_Rz = joint['coordinates'][0]



                if parent_body_name == 'ground': #set position and orientation in parent to nan, since these are equal to global.
                    #I'm assuming ground never has a rotation or orientation.
                    pos_in_parent_frame = [nan]*3 
                    or_in_parent_frame_XYZeuler = [nan]*3
                    or_in_parent_frame_quat= [nan]*4




                create_joint(name = joint_name, radius = joint_rad, 
                            collection_name=joint_colname,
                            is_global = True,
                            parent_body=parent_body_name, 
                            child_body=child_body_name,
                            pos_in_global = pos_in_global, 
                            or_in_global_XYZeuler = or_in_global_XYZeuler,
                            or_in_global_quat= or_in_global_quat,
                            pos_in_parent_frame = translation_in_parent_frame, 
                            or_in_parent_frame_XYZeuler = orientation_in_parent_frame,
                            or_in_parent_frame_quat= or_in_parent_frame_quat,
                            pos_in_child_frame = translation_in_child_frame, 
                            or_in_child_frame_XYZeuler = orientation_in_child_frame,
                            or_in_child_frame_quat= or_in_child_frame_quat,
                            coordinate_Tx = coordinate_Tx,
                            coordinate_Ty = coordinate_Ty,
                            coordinate_Tz = coordinate_Tz,
                            coordinate_Rx = coordinate_Rx,
                            coordinate_Ry = coordinate_Ry,
                            coordinate_Rz = coordinate_Rz,
                )
                            
                            

                # Add child joints to the stack to be processed
                for child_joint_name, child_childtree in joint_childtree.items():
                    stack.append((child_joint_name, child_childtree))
                
        #### outside 
       
            
        #### create muscles
            
        for muscle_name, muscle in muscle_data.items():

            
            F_max = muscle['F_max']
            optimal_fiber_length = muscle['optimal_fiber_length']
            tendon_slack_length = muscle['tendon_slack_length']
            pennation_angle = muscle['pennation_angle']

            for point in muscle['path_points_data']:

                socket_parent_frame_name = point['parent_frame']
                mp_parent_body_name = socket_parent_frame_name.split('/bodyset/')[-1]  #this assumes the muscle points are always expressed in the parent body frame, not an offset frame
                               
                muscle_point_position = point['location']
                
                if bpy.context.scene.muskemo.model_import_style == 'loc':  #if importing a model using local definitions, muscle points are provided wrt parent frame
                    
                    mp_parent_body = bpy.data.objects[mp_parent_body_name] ## this assumes muscle point parent frames are always expressed in a body, thus in the /bodyset/
                    mp_parent_frame = frames[mp_parent_body['local_frame']] #fill the body parent frame name in the frames dict to get some of the preprocessed frame data

                    gRp = mp_parent_frame['gRf']  #global orientation of parent frame
                    parent_frame_pos_in_glob = mp_parent_frame['frame_pos_in_global']

                    muscle_point_position = parent_frame_pos_in_glob + gRp @ Vector(muscle_point_position)

                create_muscle(muscle_name = muscle_name, 
                            is_global =True, 
                            body_name = mp_parent_body_name,
                            point_position = muscle_point_position,
                            collection_name=muscle_colname,
                            optimal_fiber_length=optimal_fiber_length,
                            tendon_slack_length=tendon_slack_length,
                            F_max = F_max,
                            pennation_angle = pennation_angle)    
           

        ### create contacts    
        for contact_name, contact in contact_data.items():

            if contact['geometry_type'] == 'ContactSphere':# if it's a Sphere

                contact_radius = contact['radius']
                
                c_socket_parent_frame_name = contact['socket_frame']
                contact_parent_body_name = c_socket_parent_frame_name.split('/bodyset/')[-1]  #this assumes the contacts are always expressed in the parent body frame, not an offset frame
                contact_position = contact['location']
                contact_pos_in_global = [nan]*3
                contact_pos_in_parent_frame = [nan]*3

                if bpy.context.scene.muskemo.model_import_style == 'glob':  #if importing a model using global definitions, the location corresponds to global location
                    
                    contact_pos_in_global = contact_position

                elif bpy.context.scene.muskemo.model_import_style == 'loc':  #

                    contact_pos_in_parent_frame = contact_position
                    contact_parent_body = bpy.data.objects[contact_parent_body_name] ## this assumes contact parent frames are always expressed in a body, thus in the /bodyset/
                    contact_parent_frame = frames[contact_parent_body['local_frame']] #fill the body parent frame name in the frames dict to get some of the preprocessed frame data

                    gRp = contact_parent_frame['gRf']  #global orientation of parent frame
                    parent_frame_pos_in_glob = contact_parent_frame['frame_pos_in_global']

                    contact_pos_in_global = parent_frame_pos_in_glob + gRp @ Vector(contact_position)
                
                create_contact(name = contact_name,
                               radius = contact_radius,
                               collection_name = contact_colname,
                               pos_in_global = contact_pos_in_global,
                               parent_body = contact_parent_body_name,
                               pos_in_parent_frame=contact_pos_in_parent_frame,
                               is_global = True,
                               )

        ### create wrapping
        for body_name, body in body_data.items():
                if body['wrap_objects']:  # Check if the body has wrap objects
                    wrap_parent_body = bpy.data.objects.get(body_name)

                    for wrap_obj in body['wrap_objects']:
                        wrap_name = wrap_obj['name']
                        wrap_type = wrap_obj['type']
                        wrap_position = wrap_obj.get('translation', [float('nan')] * 3)  # Translation in parent frame
                        wrap_orientation = wrap_obj.get('xyz_body_rotation', [0] * 3)  # Orientation in parent frame
                        dimensions = {}  # Collect dimensions based on the type of wrap geometry

                        if wrap_type == 'WrapCylinder':
                            dimensions['radius'] = wrap_obj.get('radius', float('nan'))
                            dimensions['height'] = wrap_obj.get('length', float('nan'))
                            geomtype = 'Cylinder'

                        elif wrap_type == 'WrapSphere':
                            dimensions['radius'] = wrap_obj.get('radius', float('nan'))
                            geomtype = 'Sphere'

                        # Fill in global position/orientation if importing globally
                        wrap_pos_in_global = [float('nan')] * 3
                        wrap_or_in_global_XYZeuler = [float('nan')] * 3
                        wrap_or_in_global_quat = [float('nan')] * 4

                        wrap_pos_in_parent_frame = [float('nan')] * 3
                        wrap_or_in_parent_frame_XYZeuler = [float('nan')] * 3
                        wrap_or_in_parent_frame_quat = [float('nan')] * 4

                        if bpy.context.scene.muskemo.model_import_style == 'glob':  # Global import
                            wrap_pos_in_global = wrap_position
                            wrap_or_in_global_XYZeuler = wrap_orientation  # Assuming you want the euler angles in global coordinates

                        elif bpy.context.scene.muskemo.model_import_style == 'loc':  # Local import
                            wrap_parent_frame = frames[wrap_parent_body['local_frame']]
                            gRp = wrap_parent_frame['gRf']  # Global orientation of parent frame
                            parent_frame_pos_in_glob = wrap_parent_frame['frame_pos_in_global']

                            wrap_pos_in_global = parent_frame_pos_in_glob + gRp @ Vector(wrap_position)
                            wrap_pos_in_parent_frame = wrap_position
                            
                            [wrap_pRb, wrap_bRp ] = matrix_from_euler_XYZbody(wrap_orientation)
                            wrap_or_in_global_quat = quat_from_matrix(gRp @ wrap_pRb)
                            wrap_or_in_parent_frame_XYZeuler = wrap_orientation
                            wrap_or_in_parent_frame_quat = quat_from_matrix(wrap_pRb)

                        # Create the wrap geometry using create_wrapgeom
                        create_wrapgeom(name=wrap_name,
                                        geomtype=geomtype,
                                        collection_name=wrap_colname,
                                        parent_body=body_name,
                                        pos_in_global=wrap_pos_in_global,
                                        or_in_global_XYZeuler=wrap_or_in_global_XYZeuler,
                                        or_in_global_quat=wrap_or_in_global_quat,
                                        pos_in_parent_frame=wrap_pos_in_parent_frame,
                                        or_in_parent_frame_XYZeuler=wrap_or_in_parent_frame_XYZeuler,
                                        or_in_parent_frame_quat = wrap_or_in_parent_frame_quat,
                                        dimensions=dimensions
                                    )



       

        return {'FINISHED'}
