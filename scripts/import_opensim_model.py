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
            
            body_data = []
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

                body_data.append({
                    'name': name,
                    'mass': mass,
                    'mass_center': mass_center,
                    'inertia': inertia,
                    'geometries': geometries
                })

            return body_data


        

        def get_joint_data(model):
            joint_set = model.find('JointSet')
            joints = joint_set.find('objects')

            joint_data = []
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
                        axis_coordinates = axis.find('coordinates').text.strip() if axis.find('coordinates') is not None else None
                        axis_vector = tuple(map(float, axis.find('axis').text.split()))
                        transform_function = axis.find('LinearFunction')
                        
                        coefficients = None
                        if transform_function is not None:
                            coeff_values = tuple(map(float, transform_function.find('coefficients').text.split()))
                            if coeff_values != (1.0, 0.0):  # Only include if coefficients are not "1 0"
                                coefficients = coeff_values

                        spatial_transform.append({
                            'axis_name': axis_name,
                            'axis_coordinates': axis_coordinates,
                            'axis_vector': axis_vector,
                            'coefficients': coefficients
                        })

                joint_data.append({
                    'joint_name': joint_name,
                    'joint_type': joint_type,
                    'parent_frame': parent_frame,
                    'child_frame': child_frame,
                    'parent_body': parent_body,
                    'child_body': child_body,
                    'frames_data': frames_data,
                    'coordinates': coordinates,
                    'spatial_transform': spatial_transform
                })

            return joint_data


       
        # Extract body data from the model
        body_data = get_body_data(model)

        #### create bodies
        from .create_body_func import create_body

        body_colname = bpy.context.scene.muskemo.body_collection #name for the collection that will contain the hulls
        size = bpy.context.scene.muskemo.axes_size #axis length, in meters
        geometry_parent_dir = os.path.dirname(self.filepath)
        import_geometry = bpy.context.scene.muskemo.import_visual_geometry #user switch for import geometry, true or false

        if import_geometry: #if the user wants imported geometry, we check if the folder exists

            # Loop through the data to find the first valid geometry path
            for body in body_data:
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
                    geometry_dir = first_geometry_path.split('/')[0]
                    
                    folder_path = geometry_parent_dir + '/' + geometry_dir
                    if not os.path.exists(folder_path) or not os.path.isdir(folder_path): #if the path doesn't exist or isn't a folder
                        import_geometry = False
                        self.report({'WARNING'}, "The geometry folder '" + geometry_dir + "' specified in the model file does not appear to be in the same directory. Skipping geometry import.")

                    # Break the loop as we've found the first valid geometry path
                    break


        for body in body_data:
            name = body['name']
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
            create_body(name=name, is_global = True, size = size,
                        mass=mass, COM=COM,  inertia_COM=inertia_COM, Geometry=geometry_string, 
                        collection_name=body_colname,  
                        import_geometry = import_geometry, #the bool property
                            geometry_parent_dir = geometry_parent_dir)
            

        # Extract joint data from the model
        joint_data = get_joint_data(model)

        #### create joints
        from .create_joint_func import create_joint

        joint_colname = bpy.context.scene.muskemo.joint_collection #name for the collection that will contain the joints
        rad = bpy.context.scene.muskemo.jointsphere_size #joint_radius

        for joint in joint_data:

            name = joint['joint_name']
            parent_body = joint['parent_body']
            child_body = joint['child_body']

            frames_dict = {frame['frame_name']: frame for frame in joint['frames_data']} #dictionary for easier access

            parent_frame_name = joint['parent_frame']
            child_frame_name = joint['child_frame']

            translation_in_parent_frame = frames_dict[parent_frame_name]['translation']
            orientation_in_parent_frame = frames_dict[parent_frame_name]['orientation']

            translation_in_child_frame = frames_dict[child_frame_name]['translation']
            orientation_in_child_frame = frames_dict[child_frame_name]['orientation']

            # if is_global

            pos_in_global = translation_in_parent_frame
            or_in_global_XYZeuler = orientation_in_parent_frame

            create_joint(name = name, radius = rad, 
                         is_global = True,
                         parent_body=parent_body, 
                         child_body=child_body,
                         pos_in_global = pos_in_global, 
                        or_in_global_XYZeuler = or_in_global_XYZeuler,
            )
                        #or_in_global_quat= or_in_global_quat,
                        #pos_in_parent_frame = pos_in_parent_frame, 
                        #or_in_parent_frame_XYZeuler = or_in_parent_frame_XYZeuler,
                        #or_in_parent_frame_quat= or_in_parent_frame_quat,
                        #pos_in_child_frame = pos_in_child_frame, 
                        #or_in_child_frame_XYZeuler = or_in_child_frame_XYZeuler,
                        #or_in_child_frame_quat= or_in_child_frame_quat,
                        #coordinate_Tx = coordinate_Tx,
                        #coordinate_Ty = coordinate_Ty,
                        #coordinate_Tz = coordinate_Tz,
                        #coordinate_Rx = coordinate_Rx,
                        #coordinate_Ry = coordinate_Ry,
                        #coordinate_Rz = coordinate_Rz,'''
                         





       

        return {'FINISHED'}
