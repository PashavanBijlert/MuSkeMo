import bpy
from mathutils import (Vector,
                       Matrix)


from bpy.types import (Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)

import xml.etree.ElementTree as ET


from math import nan


import numpy as np
import os

import time


class ImportGaitsymModel(Operator):
    bl_description = "Import a Gaitsym 2019 model"
    bl_idname = "import.import_gaitsym_model"
    bl_label = "Import Gaitsym model"


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

        self.filter_glob = "*.gaitsym;*.xml" 
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    
    def execute(self, context):
        """Reads XML data from the specified filepath"""
        filepath = self.filepath
        tree = ET.parse(filepath)
        root = tree.getroot()    
        time1 = time.time()        
    
        def get_body_data(root):
            """Extracts data from each <BODY> element in the XML root."""
            bodies = []
            for body_elem in root.findall('BODY'):
                body_data = {}
                for attr_name, attr_value in body_elem.items():
                    # Try converting to float if possible
                    try:
                        # Split the attribute value by spaces
                        values = list(map(float, attr_value.split()))
                        # If it's a single value, store it as a float, otherwise as a tuple
                        body_data[attr_name] = values[0] if len(values) == 1 else tuple(values)
                    except ValueError:
                        # If conversion to float fails, store it as a string (e.g., "DragControl")
                        body_data[attr_name] = attr_value
                bodies.append(body_data)
            return bodies

        

        def get_joint_data(root):
            """Extracts data from each <JOINT> element in the XML root."""
            joints = []
            for joint_elem in root.findall('JOINT'):
                joint_data = {}
                for attr_name, attr_value in joint_elem.items():
                    # Try converting to float if possible
                    try:
                        # Split the attribute value by spaces
                        values = list(map(float, attr_value.split()))
                        # If it's a single value, store it as a float, otherwise as a tuple
                        joint_data[attr_name] = values[0] if len(values) == 1 else tuple(values)
                    except ValueError:
                        # If conversion to float fails, store it as a string (e.g., "Type")
                        joint_data[attr_name] = attr_value
                joints.append(joint_data)
            return joints

        
        def get_marker_data(root):
            """Extracts marker data from XML and returns a dictionary keyed by marker ID."""
            marker_data = {}

            for marker in root.findall('MARKER'):
                marker_id = marker.get('ID')
                marker_data[marker_id] = {attr: marker.get(attr) for attr in marker.keys()}

            return marker_data

 
        def get_strap_data(root):
            """Extracts strap data from XML and returns a dictionary keyed by strap ID."""
            strap_data = {}

            for strap_elem in root.findall('STRAP'):
                strap_id = strap_elem.get('ID')
                if strap_id:
                    # Initialize a dictionary for this strap's attributes
                    attributes = {}
                    for attr_name, attr_value in strap_elem.items():
                        try:
                            # Split the attribute value by spaces
                            values = list(map(float, attr_value.split()))
                            # If it's a single value, store it as a float, otherwise as a tuple
                            attributes[attr_name] = values[0] if len(values) == 1 else tuple(values)
                        except ValueError:
                            # If conversion to float fails, store it as a string (e.g., "Type")
                            attributes[attr_name] = attr_value
                    # Store the attributes dictionary under the strap ID in the main dictionary
                    strap_data[strap_id] = attributes

            return strap_data

        def get_muscle_data(root):
            """Extracts data from each <MUSCLE> element in the XML root."""
            muscles = []
            for muscle_elem in root.findall('MUSCLE'):
                muscle_data = {}
                for attr_name, attr_value in muscle_elem.items():
                    # Try converting to float if possible
                    try:
                        # Split the attribute value by spaces
                        values = list(map(float, attr_value.split()))
                        # If it's a single value, store it as a float, otherwise as a tuple
                        muscle_data[attr_name] = values[0] if len(values) == 1 else tuple(values)
                    except ValueError:
                        # If conversion to float fails, store it as a string (e.g., "Type")
                        muscle_data[attr_name] = attr_value
                muscles.append(muscle_data)
            return muscles

        # Check for model import rotation 
        
        import_gRi = Matrix(((1.0, 0.0, 0.0),  #import gRi and iRg are identity matrices by default, so no rotation. From import frame to global
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0)))
        
        import_iRg = import_gRi

        gaitsym_import_euler = bpy.context.scene.muskemo.rotate_gaitsym_on_import
        gaitsym_import_euler = (gaitsym_import_euler[0],gaitsym_import_euler[1],gaitsym_import_euler[2])

        from .quaternions import (matrix_from_quaternion, quat_from_matrix)
        from .euler_XYZ_body import matrix_from_euler_XYZbody
        if gaitsym_import_euler != (0,0,0): #if not zero rotation, we set up an import rotation matrix
            
            [import_gRi, import_iRg] = matrix_from_euler_XYZbody(np.deg2rad(gaitsym_import_euler))



        # Extract body data from the model
        body_data = get_body_data(root)
        
        #### create bodies
        from .create_body_func import create_body

        body_colname = bpy.context.scene.muskemo.body_collection #name for the collection that will contain the hulls
        size = bpy.context.scene.muskemo.axes_size #axis length, in meters
        geometry_parent_dir = os.path.dirname(self.filepath)
        import_geometry = bpy.context.scene.muskemo.import_visual_geometry #user switch for import geometry, true or false
        gaitsym_geo_folder = bpy.context.scene.muskemo.gaitsym_geometry_folder

        if import_geometry: #if the user wants imported geometry, we check if the folder exists

            if gaitsym_geo_folder:  #if the user filled in the subfolder name

                                
                folder_path = geometry_parent_dir + '/' + gaitsym_geo_folder
                if not os.path.exists(folder_path) or not os.path.isdir(folder_path): #if the path doesn't exist or isn't a folder
                    import_geometry = False
                    self.report({'WARNING'}, "The Gaitsym geometry folder '" + gaitsym_geo_folder + "' specified in the model file does not appear to be in the model directory. Skipping geometry import.")

                
            else:
                self.report({'WARNING'}, "Gaitsym models don't specify where the geometry meshes are located. If you want to import visual geometry, you must ensure they're in a subdirectory of the model, and you must type in the directory name under 'Gaitsym geometry folder'. Skipping geometry import.")
                import_geometry = False


        for body in body_data:
            name = body['ID']
            mass = body['Mass']
            COM = import_gRi @ Vector(body['ConstructionPosition'])  # tuple to vector, premultiply by rot matrix
            COM = list(COM) #body func expects a list

            inertia_COM_import = body['MOI']  # Tuple, inertia about COM as a 6 element long vector 

            MOI_i = Matrix(((inertia_COM_import[0], inertia_COM_import[3], inertia_COM_import[4]), #MOI tensor about COM in b (which is import frame)
                        (inertia_COM_import[3],inertia_COM_import[1],inertia_COM_import[5]),
                        (inertia_COM_import[4],inertia_COM_import[5],inertia_COM_import[2])))
        
            MOI_g = import_gRi @ MOI_i @ import_iRg #rotated

            inertia_COM_global = [MOI_g[0][0],  #Ixx, about COM, in global frame
                     MOI_g[1][1],  #Iyy
                     MOI_g[2][2],  #Izz
                     MOI_g[0][1],  #Ixy
                     MOI_g[0][2],  #Ixz
                     MOI_g[1][2]]  #Iyz
            
            inertia_COM_global = list(inertia_COM_global) #create_body_func expects a list


            geometries = [body[x] for x in body if 'GraphicFile' in x]  # list of geometry names
                
            # If geometries exist, join them with semicolons, otherwise set a default string
            if geometries:
                geometry_string = ';'.join([gaitsym_geo_folder + '/' + geometry for geometry in geometries]) + ';' 
                geometry_or_in_glob = [import_gRi for geometry in geometries]#pass the rotation matrix for create_body_func

            else:
                geometry_string = 'no geometry'


            # Call create_body with the prepared geometry string
            create_body(name=name, self = self,
                         is_global = True, size = size,
                        mass=mass, COM=COM,  inertia_COM=inertia_COM_global, Geometry=geometry_string, 
                        collection_name=body_colname,  
                        import_geometry = import_geometry, #the bool property
                            geometry_parent_dir = geometry_parent_dir,
                            geometry_or_in_glob = geometry_or_in_glob)
            

        # Extract joint data from the model
        joint_data = get_joint_data(root)
        

        # Extract marker data
        marker_data = get_marker_data(root)


        #### create joints
        from .create_joint_func import create_joint

        joint_colname = bpy.context.scene.muskemo.joint_collection #name for the collection that will contain the joints
        rad = bpy.context.scene.muskemo.jointsphere_size #joint_radius

        for joint in joint_data:

            name = joint['ID']
            
            body1_markerID = joint['Body1MarkerID']
            body1_marker = marker_data[body1_markerID]

            body2_markerID = joint['Body2MarkerID']
            body2_marker = marker_data[body2_markerID]

            parent_body = body1_marker['BodyID']
            child_body = body2_marker['BodyID']

            pos_in_import = [float(x) for x in body1_marker['WorldPosition'].split()]
            pos_in_global = import_gRi@(Vector(pos_in_import)) #import rotation
            pos_in_global = list(pos_in_global) #joint func expects a list

            or_in_import_quat = [float(x) for x in body1_marker['WorldQuaternion'].split()]

            [joint_iRb, joint_bRi] = matrix_from_quaternion(or_in_import_quat)
            or_in_global = import_gRi @ joint_iRb
            or_in_global_quat = list(quat_from_matrix(or_in_global)) #joint func expects a list

            ## coordinates

            coordinate_Tx = ''
            coordinate_Ty = ''
            coordinate_Tz = ''
            coordinate_Rx = ''
            coordinate_Ry = ''
            coordinate_Rz = ''


            #ADD AUTOMATIC COORDINATES BASED ON JOINT TYPE?
            #THERE MAY BE A JOINT AXIS PROBLEM?
            '''# Loop through each transform axis in the joint's spatial_transform data
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
            '''
            # if is_global

            
            



            create_joint(name = name, radius = rad, 
                         collection_name=joint_colname,
                         is_global = True,
                         parent_body=parent_body, 
                         child_body=child_body,
                         pos_in_global = pos_in_global, 
                        or_in_global_quat = or_in_global_quat,
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
                        
        # Extract muscle data from the model
        strap_data = get_strap_data(root)
        muscle_data = get_muscle_data(root)
        #### create muscles
        from .create_muscle_func import create_muscle

        muscle_colname = bpy.context.scene.muskemo.muscle_collection #name for the collection that will contain the joints
        #rad = bpy.context.scene.muskemo.jointsphere_size #joint_radius                         

        for muscle in muscle_data:

            muscle_name = muscle['ID']

        
            
        
            if "DampedSpring" in muscle['Type']: #if it's a spring (i.e., a ligament)
                self.report({'WARNING'}, "Ligaments are currently not supported by MuSkeMo yet. DampedSpring '" + muscle_name + "' will be imported as a muscle.")
                F_max = 0
                optimal_fiber_length = 0

            else: #if it's a muscle

                F_max = muscle['PCA']*muscle['ForcePerUnitArea']
                optimal_fiber_length = muscle['FibreLength']


            strapID = muscle['StrapID']

            strap = strap_data[strapID]
            strapType = strap['Type']

            points_ID_list = []
            
            if strapType == 'TwoPoint':

                points_ID_list.append(strap['OriginMarkerID'])
                points_ID_list.append(strap['InsertionMarkerID'])

            elif strapType == 'NPoint':

                points_ID_list.append(strap['OriginMarkerID'])

                [points_ID_list.append(x) for x in strap['ViaPointMarkerIDList'].split()]
                points_ID_list.append(strap['InsertionMarkerID'])

            for point in points_ID_list:

                #parent_frame = point['parent_frame']
                marker = marker_data[point]

                parent_body_name = marker['BodyID']
                point_position = Vector([float(x) for x in marker['WorldPosition'].split()])
                point_position_glob = list(import_gRi @ point_position)
                
                

                create_muscle(muscle_name = muscle_name, 
                            is_global =True, 
                            body_name = parent_body_name,
                            point_position = point_position_glob,
                            collection_name=muscle_colname,
                            optimal_fiber_length=optimal_fiber_length,
                            #tendon_slack_length=tendon_slack_length,
                            F_max = F_max,
                            #pennation_angle = pennation_angle
                            )
         

        time2 = time.time()

        print('Elapsed time = ' + str(time2-time1) + ' seconds')

        return {'FINISHED'}
