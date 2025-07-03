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

import time

from collections import defaultdict #for the uniqueness checker

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
        
        time1 = time.time()        
    

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
                if frames is not None: #if there are frames defined
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
                else: #if there are no frames defined in the joint, assume socket_parent_frame and child are the bodies themselves
                    #and that the positions and orientations are both zero

                    print(joint_name + ' has no frames defined. Automatically creating them. This may cause inconsistencies.')
                    translation = tuple([0.0, 0.0, 0.0])
                    orientation = tuple([0.0, 0.0, 0.0])
                    
                    ## parent
                    parent_body = parent_frame.split('/bodyset/')[-1]

                    if parent_body == '/ground':
                        parent_body = 'ground'

                    parent_frame = parent_body + '_offset', #opensim naming convention
                    frames_data.append({
                    'frame_name': parent_frame,
                    'translation': translation,
                    'orientation': orientation,
                    'socket_parent': parent_body

                    })

                    ## Child
                    child_body  = child_frame.split('/bodyset/')[-1]
                    child_frame = child_body + '_offset'#opensim naming convention
                    frames_data.append({
                    'frame_name': child_frame, 
                    'translation': translation,
                    'orientation': orientation,
                    'socket_parent': child_body

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


            
            ## check if any of the child frames are non-unique            
            #Collect all child_frames and where they occur
            frame_usage = defaultdict(list)

            for joint_name, joint in joint_data.items():
                child_frame = joint['child_frame']
                frame_usage[child_frame].append(joint_name)

            #Find duplicates
            duplicates = {frame: joints for frame, joints in frame_usage.items() if len(joints) > 1}

            # Step 3: Rename and collect original duplicated names, if they exist
            if duplicates:
                renamed_original_frames = set()

                #Loop through duplicate frames
                for duplicate_frame, joints in duplicates.items():
                    renamed_original_frames.add(duplicate_frame)
                    for joint_name in joints:
                        joint = joint_data[joint_name]
                        child_body = joint['child_body']
                        new_frame_name = child_body + "_offset_renamed"

                        # Rename this joint's child_frame
                        joint['child_frame'] = new_frame_name
                        #also rename it in the easy access dict nested within each joint. First is the parent, second is the child. We want the child
                        joint['frames_data'][1]['frame_name'] = new_frame_name

                        # Now rename parent_frame of any joints that use this child_body as their parent_body
                        for other_joint in joint_data.values():
                            if other_joint['parent_body'] == child_body:
                                other_joint['parent_frame'] = new_frame_name
                                #also rename it in the easy access dict nested within each joint. First is the parent, second is the child. We want the parent
                                other_joint['frames_data'][0]['frame_name'] = new_frame_name


                # Convert to list
                renamed_list = list(renamed_original_frames)

                # Issue warning
                warning_message = (
                    f"The following child_frames were used more than once and were renamed during import: "
                    f"{', '.join(renamed_list)}."
                )
                self.report({'WARNING'}, warning_message)
            return joint_data


        

        def get_muscle_data(model):
            muscle_data = {}

            muscle_data['conditional_pathpoint_flag'] = False
            muscle_data['moving_pathpoint_flag'] = False


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
                            path_wrap_data = []
                            if geometry_path is not None:
                                # Handle PathPointSet
                                path_point_set = geometry_path.find('PathPointSet')
                                if path_point_set is not None:
                                    path_points = path_point_set.find('objects')
                                    if path_points is not None:
                                       for point in path_points:  # Iterate over all child elements
                                            point_name = point.get('name')
                                            parent_frame = point.find('socket_parent_frame').text.strip()

                                            if (point.tag == 'PathPoint' or point.tag == 'ConditionalPathPoint'):  # Handle PathPoint and convert ConditionalPathPoint to regular PathPoints
                                                
                                                
                                                location = tuple(map(float, point.find('location').text.split()))

                                                if point.tag == 'ConditionalPathPoint':
                                                    muscle_data['conditional_pathpoint_flag'] = True #if there are conditional pathpoints, we set this to true, so that we can display a warning later

                                                
                                            elif point.tag == 'MovingPathPoint': #if it's a moving path point, we find the position of each point when the associated joint_coordinate is 0
                                                
                                                muscle_data['moving_pathpoint_flag'] = True #if there are moving pathpoints, we set this to true, so that we can display a warning later


                                                #the function gets called below, but is reused for all three points
                                                def get_y_for_x_zero(location_tag):  #a function that extracts the y of each simmspline where the x input (corresponding to the joint coordinate) is zero.
                                                    """Extract y-value corresponding to x=0 from the given location tag (x_location, y_location, z_location)."""
                                                    location_elem = point.find(location_tag)  # e.g., "x_location", "y_location", "z_location"
                                                    if location_elem is not None:

                                                        #these nested if statements assume the simmspline is always within a multiplier function with scale. If this is not correct, add the alternative in the future.
                                                        multiplier_function = location_elem.find(".//MultiplierFunction") 
                                                        if multiplier_function is not None:

                                                            scale_element = multiplier_function.find(".//scale")  # Locate the <scale> element
                                                            scale = float(scale_element.text.strip()) if scale_element is not None else 1.0  # Convert to float, default to 1.0 if not found
                                                            simm_spline = multiplier_function.find(".//SimmSpline")
                                                            if simm_spline is not None:
                                                                # Extract x and y values as lists of floats
                                                                x_values = list(map(float, simm_spline.find('x').text.split()))
                                                                y_values = list(map(float, simm_spline.find('y').text.split()))
                                                                
                                                                if 0 in x_values:  # Check if 0 is in x values
                                                                    zero_index = x_values.index(0)  # Get index of 0
                                                                    return scale*y_values[zero_index]  # Return corresponding y value
                                                                

                                                                else:
                                                                    # Find indices of the two x-values that bridge 0
                                                                    for i in range(len(x_values) - 1):
                                                                        if x_values[i] < 0 < x_values[i + 1]:
                                                                            # Perform linear interpolation
                                                                            x1, x2 = x_values[i], x_values[i + 1]
                                                                            y1, y2 = y_values[i], y_values[i + 1]
                                                                            y_interpolated = y1 + (0 - x1) * (y2 - y1) / (x2 - x1)
                                                                            return scale*float(y_interpolated)
                                                        else:
                                                            return None

                                                    

                                                # Get y-values for spline x=0, for x_location, y_location, z_location of the muscle point.
                                                x_pos_at_zero = get_y_for_x_zero("x_location")
                                                y_pos_at_zero = get_y_for_x_zero("y_location")
                                                z_pos_at_zero = get_y_for_x_zero("z_location")

                                                loc_list = [x_pos_at_zero, y_pos_at_zero, z_pos_at_zero]

                                                if None not in loc_list: #if all the values are not None
                                                    location = tuple(loc_list)
                                                    

                                                else: #if one is None, just make them all None
                                                    location = tuple([None, None, None])    

                                            if None not in location: #only if all the points actually exist

                                                path_points_data.append({
                                                        'point_name': point_name,
                                                        'parent_frame': parent_frame,
                                                        'location': location
                                                    })    
                                            
                                # Handle PathWrapSet
                                path_wrap_set = geometry_path.find('PathWrapSet')
                                if path_wrap_set is not None:
                                    wrap_objects = path_wrap_set.find('objects')
                                    if wrap_objects is not None:
                                        for wrap in wrap_objects.findall('PathWrap'):
                                            wrap_name = wrap.get('name')
                                            wrap_object = wrap.find('wrap_object').text.strip()

                                            path_wrap_data.append({
                                                'wrap_name': wrap_name,
                                                'wrap_object': wrap_object
                                            })

                            # Add the extracted data to the muscle_data dict
                            muscle_data[muscle_name] = {
                                'muscle_type': muscle_type,
                                'tendon_slack_length': tendon_slack_length,
                                'F_max': max_isometric_force,
                                'optimal_fiber_length': optimal_fiber_length,
                                'pennation_angle': pennation_angle,
                                'path_points_data': path_points_data,
                                'path_wrap_data': path_wrap_data  # Add path wrap data here
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
        frame_size = bpy.context.scene.muskemo.frame_axes_size

        # Lists that tracks errors or warnings
        skipped_geoms = [] #empty list that will be populated if the geoms aren't found, only in the local import mode
        transform_axes_warning_list = [] #list to which we will add OpenSim joints for a warning about transform axes that were not aligned with the joint itself. Only in local import mode

        
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

                    or_in_parent_frame_quat = or_in_global_quat #assuming the ground is never rotated

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

                MOI_g_matrix = gRc @ MOI_c_matrix @ cRg #Vallery & Schwab, Advanced Dynamics 2018, eq. 5.53

                inertia_COM_global =   [MOI_g_matrix[0][0],  #Ixx, about COM, in global frame
                                        MOI_g_matrix[1][1],  #Iyy
                                        MOI_g_matrix[2][2],  #Izz
                                        MOI_g_matrix[0][1],  #Ixy
                                        MOI_g_matrix[0][2],  #Ixz
                                        MOI_g_matrix[1][2]]  #Iyz

                geometries = body['geometries']  # This will be a list of dictionaries or empty list


                # If geometries exist, join them with semicolons, otherwise set a default string

                if geometries:
                    
                    geometry_string = '' #should get populated in the for loop. If not, we assign 'no geometry' to this later
                    #geometry_string = ';'.join([geometry['mesh_file'] for geometry in geometries]) + ';' 
                    
                    geometry_pos_in_glob = []
                    geometry_or_in_glob = []
                    geom_scale = []
                    for geometry in geometries: 



                        ##
                        path = geometry['mesh_file']

                        filepath = geometry_parent_dir  + '/' + path
                        if not os.path.exists(filepath): #if the above filepath doesn't exist, add /Geometry/ in front of it, and check again if it exists. This accounts for OpenSim models where the Geometry subdirectory is not explicitly named
                            filepath = geometry_parent_dir + '/Geometry/' + path
                        
                            if not os.path.exists(filepath):
                                
                                skipped_geoms.append(path) #append the current geom to the "skipped_geoms" list for a single warning message at the end
                                continue
                            else:
                                path = '/Geometry/' + path
                        ##
                        geometry_string = geometry_string + path + ';'

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


                    if not geometry_string: #if geometry string wasn't populated in the for loop, explicitly state we don't have geometry
                        geometry_string = 'no geometry'
                        geometry_pos_in_glob = ''
                        geometry_or_in_glob = ''


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

                # Initialize the flag to check for standard axes
                #OpenSim models can have TransformAxes which are not the same as the joint's own axes.
                #Check for this here, and if the axes are not aligned with the joint's axes, we account for that joint separately
                has_standard_axes = True #

                # Loop through each transform axis to check for standard axis vectors
                for transform in joint['spatial_transform']:
                    axis_vector = tuple(transform['axis_vector'])  # Ensure axis_vector is a tuple

                    # Check if the axis_vector is not a standard axis. Standard is the following order: R1 = (1,0,0), R = (0,1,0), R3 = (0,0,1). Same for T1. If the order is different, or the axes are different, the axes are "non standard"
                    # Check this for the three axes separately.
                    # R1 and T1
                    if transform['axis_name'] == ('rotation1' or 'translation1'):
                        if axis_vector != (1,0,0):
                            has_standard_axes = False
                            transform_axes_warning_list.append(joint_name)
                    # R2 and T2
                    if transform['axis_name'] == ('rotation2' or 'translation2'):
                        if axis_vector != (0,1,0):
                            has_standard_axes = False
                            transform_axes_warning_list.append(joint_name)


                    if transform['axis_name'] == ('rotation3' or 'translation3'):
                        if axis_vector != (0,0,1):
                            has_standard_axes = False
                            transform_axes_warning_list.append(joint_name)                                       
                        
                if parent_body_name == 'ground': #if it's a root joint and it is rotated with respect to world, we need to treat this as a non-standard joint so that trajectory importing goes along local transformations
                    if orientation_in_parent_frame != (0,0,0):
                               
                        has_standard_axes = False
                        transform_axes_warning_list.append(joint_name)
                
                if has_standard_axes:
                    
                    # Loop through each transform axis in the joint's spatial_transform data
                    for transform in joint['spatial_transform']: #for transform axis in spatial_transform
                        axis_vector = transform['axis_vector']
                        coordinates = transform['axis_coordinates']

                        
                        if coordinates: #if coordinates aren't none
                        # standard coordinate axes    
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


                if joint['joint_type'] == 'PlanarJoint': #if the joint type is a PlanarJoint, manually set the coordinates
                    coordinate_Rz = joint['coordinates'][0]
                    coordinate_Tx = joint['coordinates'][1]
                    coordinate_Ty = joint['coordinates'][2]



                



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

                #Deal with non-standard axes explicitly            
                if not has_standard_axes:
                    
                    if joint['joint_type'] == 'CustomJoint':
                    
                    
                        joint_obj = bpy.data.objects[joint_name] #get the newly created joint in Blender
                        joint_obj['transform_axes'] = {}
                        joint_obj['transform_axes']['type'] = 'OpenSim CustomJoint' #to track from what type of model the 'transform_axes' are defined 
                        axis_names = ['rotation1', 'rotation2', 'rotation3', 'translation1', 'translation2', 'translation3']

                        for axis_name  in axis_names: #a spatial transform has 6 transform axes. Loop through each explicitly
                            transform = [x for x in joint['spatial_transform'] if x['axis_name']==axis_name][0]
                                        
                            axis_vector = transform['axis_vector']
                            coordinates = transform['axis_coordinates']
                            
                            if coordinates: #if coordinates aren't none
                                # assign the coordinate accordingly

                                
                                #joint_obj.id_properties_ui('transform_axes').update(description="Transform axes defined in the OpenSim custom joint, if they don't align with the joint's own axes. See MuSkeMo manual for details. Optional.")
                                #Python custom properties can't have a tooltip overlay.

                                if axis_name == 'rotation1':
                                    joint_obj['coordinate_Rx'] = coordinates
                                    joint_obj['transform_axes']['transform_axis_Rx'] = axis_vector

                                elif axis_name == 'rotation2':
                                    joint_obj['coordinate_Ry'] = coordinates
                                    joint_obj['transform_axes']['transform_axis_Ry'] = axis_vector


                                elif axis_name == 'rotation3':
                                    joint_obj['coordinate_Rz'] = coordinates
                                    joint_obj['transform_axes']['transform_axis_Rz'] = axis_vector

                                    
                                elif axis_name == 'translation1':
                                    joint_obj['coordinate_Tx'] = coordinates
                                    joint_obj['transform_axes']['transform_axis_Tx'] = axis_vector


                                elif axis_name == 'translation2':
                                    joint_obj['coordinate_Ty'] = coordinates
                                    joint_obj['transform_axes']['transform_axis_Ty'] = axis_vector


                                elif axis_name == 'translation3':
                                    joint_obj['coordinate_Tz'] = coordinates
                                    joint_obj['transform_axes']['transform_axis_Tz'] = axis_vector

                                
                    elif joint['joint_type'] == 'PlanarJoint': #Planar joints are always about Rz, Tx, and Ty, but if it's a root joint and rotated wrt Global, we need to assign Transform axes for the trajectory importer

                        joint_obj = bpy.data.objects[joint_name] #get the newly created joint in Blender
                        joint_obj['transform_axes'] = {}
                        joint_obj['transform_axes']['type'] = 'OpenSim PlanarJoint' #to track from what type of model the 'transform_axes' are defined 
                    
                        joint_obj['transform_axes']['transform_axis_Rz'] = (0,0,1)
                        joint_obj['transform_axes']['transform_axis_Tx'] = (1,0,0)
                        joint_obj['transform_axes']['transform_axis_Ty'] = (0,1,0)


                # Add child joints to the stack to be processed
                for child_joint_name, child_childtree in joint_childtree.items():
                    stack.append((child_joint_name, child_childtree))
                
        #### outside 

        # Throw warning for skipped geometries
        if skipped_geoms:
            warning_message = f"The following geometries were not found in the model directory or 'Geometry' subdirectory and were skipped during import: {', '.join(skipped_geoms)}."
            
            self.report({'WARNING'}, warning_message)
            
        # Throw warning about non-standard transform axes        
        if transform_axes_warning_list: #throw a warning if joints have non-standard transform axes.
            
            warning_message= f"The following joints have transform axes that were not applied in x,y,z order, and/or not about positive principal directions: {', '.join(transform_axes_warning_list)}. See the manual"

            self.report({'WARNING'}, warning_message)

        

        #### Wrapping
        # import the wrapping node template
        enable_wrapping = bpy.context.scene.muskemo.enable_wrapping_on_import #does the user want to enable wrapping?

        renamed_wrap_warning = False #for an if statement that triggers a warning

        if enable_wrapping: #if the user wants wrapping
            
            wrap_nodefilename = 'muscle_wrapper_v6.blend'
            directory = os.path.dirname(os.path.realpath(__file__)) + '\\'  #realpath__file__ gets the path to the current script

            with bpy.data.libraries.load(directory + wrap_nodefilename) as (data_from, data_to):  #see blender documentation, this loads in data from another library/blend file
                data_to.node_groups = data_from.node_groups

            wrap_node_group_name =   'CylinderWrapNodeGroupShell' #this is used later in the script. Can update when new versions of the wrap node are made  
            wrap_node_tree_template = [x for x in data_to.node_groups if wrap_node_group_name in x.name][0] #node tree template

        wrap_objects = {}

        ### create wrapping
        for body_name, body in body_data.items():
                if body['wrap_objects']:  # Check if the body has wrap objects
                    wrap_parent_body = bpy.data.objects.get(body_name)

                    for wrap_obj in body['wrap_objects']:
                        wrap_name = wrap_obj['name']
                        
                        wrap_objects[wrap_name] = wrap_obj  #add to the dict of wrappers
                        
                        #if the wraps have a non-unique name (e.g., same name as a body or a joint) MuSkeMo will have to assign a new name
                        if wrap_name in bpy.data.objects:
                            wrap_name_MuSkeMo =  wrap_name + '_wrap'  #add '_wrap' to the end if the name is non-unique
                            renamed_wrap_warning = True #
                        else:
                            wrap_name_MuSkeMo =  wrap_name #otherwise use the original name
                            

                        wrap_objects[wrap_name]['wrap_name_MuSkeMo'] = wrap_name_MuSkeMo

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


                        else:
                            
                            self.report({'WARNING'}, "Wrapping object '" + wrap_name + "' is of the type '" + wrap_type + "', which is not currently supported. Skipping this wrapping geom.")
                            continue

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
                        create_wrapgeom(name=wrap_name_MuSkeMo,
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

                        ### create a geometry nodegroup for the wrapper using the template
                        if enable_wrapping: 
                            
                            if wrap_type == 'WrapCylinder':
                                

                                wrap_node_tree_new = wrap_node_tree_template.copy()
                                wrap_node_tree_new.name = wrap_node_group_name + '_' + wrap_name_MuSkeMo
                                #set the wrap object
                                wrap_node_tree_new.interface.items_tree['Object'].default_value = bpy.data.objects[wrap_name_MuSkeMo] #the wrap geometry

                                #set the cylinder radius
                                wrap_node_tree_new.interface.items_tree['Wrap Cylinder Radius'].default_value = dimensions['radius']

                                #set the cylinder height
                                wrap_node_tree_new.interface.items_tree['Wrap Cylinder Height'].default_value = dimensions['height']
                                
                                force_wrap = False
                                
                                                        
                                proj_angle = 0 #projection z-angle. An Euler angle for which way to project the wrapping. 0 means in positive x direction.
                                if wrap_obj['quadrant'] == '+x' or wrap_obj['quadrant'] == 'x' :
                                    proj_angle = 0
                                    force_wrap = True

                                elif wrap_obj['quadrant'] == '+y'or wrap_obj['quadrant'] == 'y' :
                                    proj_angle = 90
                                    force_wrap = True
                                
                                elif wrap_obj['quadrant'] == '-x':
                                    proj_angle = 180
                                    force_wrap = True

                                elif wrap_obj['quadrant'] == '-y':
                                    proj_angle = 270
                                    force_wrap = True

                                elif wrap_obj['quadrant'] == 'all':

                                    wrap_node_tree_new.interface.items_tree['Shortest Wrap'].default_value = True


                                else:



                                    self.report({'WARNING'}, "Wrapping object '" + wrap_name + "' has wrapping quadrant '" + wrap_obj['quadrant'] + "', which is not yet supported. You should set the projection orientation angle manually for desired behaviour.")


                                wrap_node_tree_new.interface.items_tree['Projection Angle'].default_value = proj_angle

                                wrap_node_tree_new.interface.items_tree['Force Sided Wrap'].default_value = force_wrap

                                
                            else:

                                self.report({'WARNING'}, "Only cylinder wraps currently work in MuSkeMo. Other wrap objects can be imported for visualization, but they won't support wrapping.")

                          
        if renamed_wrap_warning:
            # Find the names of objects whose name is not equal to 'wrap_obj_name_MuSkeMo'
            changed_name_objects = [
                name for name, obj in wrap_objects.items()
                if name != obj.get('wrap_name_MuSkeMo', '')
            ]

            # Join the names into a single string
            changed_name_objects_str = ", ".join(changed_name_objects)
            self.report({'WARNING'}, "Wrapping objects '" + changed_name_objects_str + "' had identical names to other existing model components (e.g. Joints). '_wrap' has been appended to their names to prevent conflicts.")

            
           
        #### create muscles
            
        for muscle_name, muscle in muscle_data.items():

            if type(muscle) == bool:  #the conditional and moving path point flags are bools, and should be skipped in this loop
                continue


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
                
                point['global_position'] = muscle_point_position #store the global position so that we can potentially compare to wrap object position

                create_muscle(muscle_name = muscle_name, 
                            is_global =True, 
                            body_name = mp_parent_body_name,
                            point_position = muscle_point_position,
                            collection_name=muscle_colname,
                            optimal_fiber_length=optimal_fiber_length,
                            tendon_slack_length=tendon_slack_length,
                            F_max = F_max,
                            pennation_angle = pennation_angle)    

            # Dictionary to store indices and count occurrences
            pre_wrap_indices_count = {} #we use this to track whether a muscle has a multi-object wrap
            
            if (enable_wrapping and muscle['path_wrap_data']): #if wrapping is enabled and the muscle has wrapping

                parametric_wraps = bpy.context.scene.muskemo.parametric_wraps #bool for parametric wraps
                                
                for pathwrap in muscle['path_wrap_data']: #for each wrap in the muscle
                    
                    wrap_objname = pathwrap['wrap_object'] #get the wrap name defined in the muscle's pathwrap info

                    wrap_obj_name_MuSkeMo = wrap_objects[wrap_objname]['wrap_name_MuSkeMo'] #get that wrapper's MuSkeMo name from the earlier defined dictionary

                    if wrap_obj_name_MuSkeMo in bpy.data.objects: #if the wrapping object actually exists
                        
                        wrap_obj = bpy.data.objects[wrap_obj_name_MuSkeMo]

                        if wrap_objects[wrap_objname]['type'] == 'WrapCylinder':

                            muscle_obj = bpy.data.objects[muscle_name]
                            #create a new geometry node for the curve, and set the node tree we just made
                            geonode_name = muscle_name + '_wrap_' + wrap_obj_name_MuSkeMo
                            geonode = muscle_obj.modifiers.new(name = geonode_name, type = 'NODES') #add modifier to curve
                            geonode.node_group = bpy.data.node_groups[wrap_node_group_name + '_' + wrap_obj_name_MuSkeMo]
                            #geonode['Socket_4'] = np.deg2rad(180)  #socket two is the volume input slider

                            ## Add the muscle to the target_muscles property of the wrap object
                            if wrap_obj['target_muscles'] == 'not_assigned': #if the wrap currently has no wrap assigned, assign it
                                wrap_obj['target_muscles'] = muscle_name + ';'

                            else: #else, we add it to the end
                                wrap_obj['target_muscles'] = wrap_obj['target_muscles'] +  muscle_name + ';'   
                            

                            #Ensure the last two modifiers are always the Visualization and then the bevel modifier
                            n_modifiers = len(muscle_obj.modifiers)
                            muscle_obj.modifiers.move(n_modifiers-1, n_modifiers-3) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.
                            
                            ## Here we crudely estimate what the pre-wrap index should be. 
                            # #as a first guess for which two successive points span the wrap, we check which pair of points has the lowest total distance to the wrap object.
                            
                            wrap_obj_pos_glob = bpy.data.objects[wrap_obj_name_MuSkeMo].matrix_world.translation

                            total_dist_to_wrap = []  #this is the summed distance between current point and next point to the wrap object center.
                            for ind, point in enumerate(muscle['path_points_data'][:-1]): #loop through n points-1
                                
                                #if the current point and the next point are attached to the same body, they can't span the wrap, so we set distance to inf
                                if point['parent_frame'] == muscle['path_points_data'][ind+1]['parent_frame']:
                                    total_dist_to_wrap.append(np.inf)
                                else:
                                    dpoint0_wrap = (point['global_position']-wrap_obj_pos_glob).length #distance of current point to wrap
                                    dpoint1_wrap = (muscle['path_points_data'][ind+1]['global_position']-wrap_obj_pos_glob).length #distance of next point to wrap
                                    
                                    #print(dpoint0_wrap)
                                    #rint(dpoint1_wrap)
                                    total_dist_to_wrap.append(dpoint0_wrap+dpoint1_wrap)
                            
                            index_of_pre_wrap_point = total_dist_to_wrap.index(min(total_dist_to_wrap)) +1 #get the index where the two points have minimal distance to the wrap, while also having different frames. Add 1 because the index count starts at 1
                            geonode['Socket_6']  = index_of_pre_wrap_point #socket for setting the index

                            # Track occurrences of index_of_pre_wrap_point
                            pre_wrap_indices_count[index_of_pre_wrap_point] = pre_wrap_indices_count.get(index_of_pre_wrap_point, 0) + 1

                            
                            ## Add a driver
                            if parametric_wraps:
                                #radius
                                driver_str = 'modifiers["' + geonode_name +'"]["Socket_3"]' #wrap geonode cylinder radius socket
                                driver = muscle_obj.driver_add(driver_str)

                                var = driver.driver.variables.new()        #make a new variable
                                var.name = geonode_name + '_' + wrap_obj_name_MuSkeMo + '_rad_var'            #give the variable a name

                                #var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

                                var.targets[0].id = bpy.data.objects[wrap_obj_name_MuSkeMo] #set the id to target object
                                var.targets[0].data_path = 'modifiers["WrapObjMesh"]["Socket_1"]' #get the driving property

                                driver.driver.expression = var.name

                                #height
                                driver_str = 'modifiers["' + geonode_name +'"]["Socket_4"]' #wrap geonode cylinder height socket
                                driver = muscle_obj.driver_add(driver_str)

                                var = driver.driver.variables.new()        #make a new variable
                                var.name = geonode_name + '_' + wrap_obj_name_MuSkeMo + '_height_var'            #give the variable a name

                                #var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

                                var.targets[0].id = bpy.data.objects[wrap_obj_name_MuSkeMo] #set the id to target object
                                var.targets[0].data_path = 'modifiers["WrapObjMesh"]["Socket_2"]' #get the driving property

                                driver.driver.expression = var.name 

            ### Throw a warning about multi object wrapping

            duplicates = [index for index, count in pre_wrap_indices_count.items() if count > 1]

            if duplicates:
                self.report({'WARNING'}, "Muscle with the name '" + muscle_name + "' has multiple wraps sharing the same pre-wrap index. Multiple wraps on one curve segment (without a path-point in between) will not give physically accurate results. See the Manual.")


        ### Throw a warning about wrapped muscle quadrants
        if enable_wrapping:
            #check if any of the wrap objects have quadrants defined. That corresponds to MuSkeMo's Force Sided Wrap
            target_chars = {'x', 'y', 'z'}
            any_match = any(char in obj.get('quadrant', '') for obj in wrap_objects.values() for char in target_chars)
            # Find the names of objects whose "quadrant" contains any of the target characters
            matching_objects = [
                name for name, obj in wrap_objects.items()
                if any(char in obj.get('quadrant', '') for char in target_chars)
            ]

            # Join the names into a single string
            matching_objects_str = ", ".join(matching_objects) 

            if matching_objects:
                self.report({'WARNING'}, "Wrapping objects '" + matching_objects_str + "' have wrapping quadrants defined. In MuSkeMo, this corresponds with the 'Force Sided Wrap' option. You may have to manually adjust 'Flip Wrap', 'Projection angle', and 'Index of pre wrap point'. See the Manual for details")

        
        #### Throw warnings about conditional and/or moving pathpoints

        if muscle_data['conditional_pathpoint_flag']: #if there are conditional pathpoints
            self.report({'WARNING'}, "Imported OpenSim model had ConditionalPathPoints, which have been converted to regular path points. See the Manual for details")

        if muscle_data['moving_pathpoint_flag']: #if there are moving pathpoints
            self.report({'WARNING'}, "Imported OpenSim model had MovingPathPoints, which have been converted to regular path points assuming the coordinate values were 0. See the Manual for details")

                        
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

       
        time2 = time.time()

        print('Elapsed time = ' + str(time2-time1) + ' seconds')

        return {'FINISHED'}
