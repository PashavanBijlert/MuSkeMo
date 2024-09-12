import bpy
from mathutils import Vector


from bpy.types import (Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)

import xml.etree.ElementTree as ET


from math import nan


import numpy as np
import os



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
                    mass_center = (0, 0, 0)  #

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
                                geometries.append({
                                    'mesh_file': mesh_file,
                                    'translation': translation,
                                    'orientation': orientation
                                })

                # If no PhysicalOffsetFrame exists, check directly within the Body
                if not geometries:  # Only do this if no geometries found via PhysicalOffsetFrame
                    attached_geometry = body.find('attached_geometry')
                    if attached_geometry is not None:
                        for mesh in attached_geometry.findall('Mesh'):
                            mesh_file = mesh.find('mesh_file').text.strip()
                            geometries.append({
                                'mesh_file': mesh_file
                                # No translation or orientation since it's directly attached to the body
                            })

                body_data[name] ={ #body_data dictionary
                    'mass': mass,
                    'mass_center': mass_center,
                    'inertia': inertia,
                    'geometries': geometries
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
                        axis_name = axis.get('name') #e.g. rotation 3
                        axis_coordinates_element = axis.find('coordinates')
                        axis_coordinates = axis_coordinates_element.text.strip() if axis_coordinates_element is not None and axis_coordinates_element.text is not None else None
                        axis_vector = tuple(map(float, axis.find('axis').text.split())) #eg (0, 0, 1) if z-axis
                        transform_function = axis.find('LinearFunction') #if it's a linear function
                        
                        coefficients = None
                        if transform_function is not None:
                            coeff_values = tuple(map(float, transform_function.find('coefficients').text.split()))
                            coefficients = coeff_values
                            if coeff_values != (1.0, 0.0):  # Only include if coefficients are not "1 0"
                                self.report({'WARNING'}, "Joint with the name '" + joint_name + "' specified in the model file has a transform function that is not supported by MuSkeMo. It will be treated like a regular joint.")


                        spatial_transform.append({
                            'axis_name': axis_name,
                            'axis_coordinates': axis_coordinates,
                            'axis_vector': axis_vector,
                            'coefficients': coefficients
                        })
                
                joint_data[joint_name] = { #joint_data dictionary
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
       
        # Extract body data from the model, and check if geometry folder exists
        body_data = get_body_data(model)
        
        body_colname = bpy.context.scene.muskemo.body_collection #name for the collection that will contain the hulls
        body_axes_size = bpy.context.scene.muskemo.axes_size #axis length, in meters
        geometry_parent_dir = os.path.dirname(self.filepath)
        import_geometry = bpy.context.scene.muskemo.import_visual_geometry #user switch for import geometry, true or false

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
                    if not os.path.exists(folder_path) or not os.path.isdir(folder_path): #if the path doesn't exist or isn't a folder
                        import_geometry = False
                        self.report({'WARNING'}, "The geometry folder '" + geometry_dir + "' specified in the model file does not appear to be in the same directory. Skipping geometry import.")

                    # Break the loop as we've found the first valid geometry path
                    break


        # Extract joint data from the model
        joint_data = get_joint_data(model)

        joint_colname = bpy.context.scene.muskemo.joint_collection #name for the collection that will contain the joints
        joint_rad = bpy.context.scene.muskemo.jointsphere_size #joint_radius

        # Extract muscle data from the model
        muscle_data = get_muscle_data(model)
        muscle_colname = bpy.context.scene.muskemo.muscle_collection #name for the collection that will contain the joints
        
        #### create bodies
        from .create_body_func import create_body


        for body_name, body in body_data.items():
            name = body_name
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
            create_body(name=name, is_global = True, size = body_axes_size,
                        mass=mass, COM=COM,  inertia_COM=inertia_COM, Geometry=geometry_string, 
                        collection_name=body_colname,  
                        import_geometry = import_geometry, #the bool property
                            geometry_parent_dir = geometry_parent_dir)
            

        #### create joints
        from .create_joint_func import create_joint

        for joint_name, joint in joint_data.items():

            name = joint_name
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
            
            # if is_global

            

            pos_in_global = translation_in_parent_frame
            or_in_global_XYZeuler = orientation_in_parent_frame

            create_joint(name = name, radius = joint_rad, 
                         collection_name=joint_colname,
                         is_global = True,
                         parent_body=parent_body, 
                         child_body=child_body,
                         pos_in_global = pos_in_global, 
                        or_in_global_XYZeuler = or_in_global_XYZeuler,
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
                        
       

        #### create muscles
        from .create_muscle_func import create_muscle

        for muscle_name, muscle in muscle_data.items():

            
            F_max = muscle['F_max']
            optimal_fiber_length = muscle['optimal_fiber_length']
            tendon_slack_length = muscle['tendon_slack_length']
            pennation_angle = muscle['pennation_angle']

            for point in muscle['path_points_data']:

                parent_frame = point['parent_frame']
                parent_body_name = parent_frame.split('/bodyset/')[-1]  #this assumes the muscle points are always expressed in the parent body frame, not an offset frame
                point_position = point['location']
                

                create_muscle(muscle_name = muscle_name, 
                              is_global =True, 
                              body_name = parent_body_name,
                              point_position = point_position,
                              collection_name=muscle_colname,
                              optimal_fiber_length=optimal_fiber_length,
                              tendon_slack_length=tendon_slack_length,
                              F_max = F_max,
                              pennation_angle = pennation_angle)
         

       

        return {'FINISHED'}
