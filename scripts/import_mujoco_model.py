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

class ImportMuJoCoModel(Operator):
    bl_description = "Import a MuJoCo model"
    bl_idname = "import.import_mujoco_model"
    bl_label = "Import MuJoCo model"


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

        self.filter_glob = "*.xml"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    
    def execute(self, context):
        """Reads XML data from the specified filepath"""
        filepath = self.filepath
        tree = ET.parse(filepath)
        root = tree.getroot()    
                
        time1 = time.time()        
        
        from .quaternions import matrix_from_quaternion, quat_from_matrix
        from .euler_XYZ_body import matrix_from_euler_XYZbody, euler_XYZbody_from_matrix
             

        def parse_numerical(value):
            """ Converts space-separated numerical strings into lists of floats if possible. """
            if value is None:
                return None
            values = value.split()
            try:
                return [float(x) for x in values]  # Convert to float list if numeric
            except ValueError:
                return value  # Keep as string if conversion fails

        def get_body_data(element):
            """ Extracts data from a body element, keeping only necessary nesting. """
            element_data = {key: parse_numerical(value) for key, value in element.attrib.items()}
            
            children = {}
            
            for child in element:
                if child.tag == "body":
                    # Recursively process child bodies
                    child_name = child.attrib.get("name", "unnamed_body")
                    children[child_name] = get_body_data(child)
                else:
                    # Store non-body elements as attributes
                    child_data = {key: parse_numerical(value) for key, value in child.attrib.items()}
                    
                    if child.tag in element_data:
                        # Avoid redundant lists if only one element exists
                        if isinstance(element_data[child.tag], list):
                            element_data[child.tag].append(child_data)
                        else:
                            element_data[child.tag] = [element_data[child.tag], child_data]
                    else:
                        element_data[child.tag] = child_data

            if children:
                element_data["children"] = children  # Store only if there are children

            return element_data



        def get_muscle_data(root):
            """ Extracts tendon and actuator data from the XML root, converting numerical attributes. """
            
            muscle_data = {"tendons": [], "actuators": []}

            # Extract tendon data
            tendon_section = root.find("tendon")
            if tendon_section is not None:
                for tendon in tendon_section.findall("spatial"):
                    tendon_info = {key: parse_numerical(value) for key, value in tendon.attrib.items()}
                    tendon_info["sites"] = [site.attrib for site in tendon.findall("site")]
                    tendon_info["geoms"] = [geom.attrib for geom in tendon.findall("geom")]
                    muscle_data["tendons"].append(tendon_info)

            # Extract actuator data
            actuator_section = root.find("actuator")
            if actuator_section is not None:
                for actuator in actuator_section.findall("general"):
                    actuator_info = {key: parse_numerical(value) for key, value in actuator.attrib.items()}
                    muscle_data["actuators"].append(actuator_info)

            return muscle_data

        def get_asset_data(root):
            asset_data = []
            asset_element = root.find("asset")

            if asset_element is not None:
                for element in asset_element:
                    # Extract relevant attributes (e.g., for texture and mesh)
                    if element.tag in ["texture", "mesh"]:
                        asset_data.append({
                            "type": element.tag,
                            "name": element.get("name"),
                            "file": element.get("file"),
                            "other_attributes": {k: v for k, v in element.attrib.items() if k not in ["name", "file"]}
                        })

            return asset_data



        # Find the worldbody (where all bodies are defined)
        worldbody = root.find("worldbody")

        # Extract body hierarchy
        body_hierarchy = [get_body_data(body) for body in worldbody.findall("body")]
            
        # Extract muscle data
        muscle_data = get_muscle_data(root)
             
        # Extract asset data
        asset_data = get_asset_data(root)
            
        ########## MuSkeMo settings, user switches, MuSkeMo scripts, etc.
        muskemo = bpy.context.scene.muskemo
        ### Bodies
        body_colname = muskemo.body_collection #name for the collection that will contain the hulls
        body_axes_size = muskemo.axes_size #axis length, in meters
        #geometry_parent_dir = os.path.dirname(self.filepath)
        import_geometry = muskemo.import_visual_geometry #user switch for import geometry, true or false

        ### Wrap
        wrap_colname = muskemo.wrap_geom_collection
        
        ### Joints
        joint_colname = muskemo.joint_collection #name for the collection that will contain the joints
        joint_rad = muskemo.jointsphere_size #joint_radius

        ### Muscles
        muscle_colname = muskemo.muscle_collection #name for the collection that will contain the muscles
        
        ### Contacts
        contact_colname =  muskemo.contact_collection #name for the collection that will contain the contacts

        ### Frames
        frame_colname = muskemo.frame_collection
        frame_size = muskemo.frame_axes_size

        # Check for model import rotation 
        ### If I use this, it would be better to not compute all the local frame data, but just construct the model in global coordinates, rotate it, create the bodies and frames without assigning them respectively, and then calling the frame assignment operator.
        
        
        import_gRi = Matrix(((1.0, 0.0, 0.0),  #import gRi and iRg are identity matrices by default, so no rotation. From import frame to global
                            (0.0, 1.0, 0.0),
                            (0.0, 0.0, 1.0)))
        
        import_iRg = import_gRi

        mujoco_import_euler = bpy.context.scene.muskemo.rotate_on_import
        mujoco_import_euler = (mujoco_import_euler[0],mujoco_import_euler[1],mujoco_import_euler[2])

       
        if mujoco_import_euler != (0,0,0): #if not zero rotation, we set up an import rotation matrix
            
            [import_gRi, import_iRg] = matrix_from_euler_XYZbody(np.deg2rad(mujoco_import_euler))



        #### import the component creation functions

        from .create_body_func import create_body
        from .create_joint_func import create_joint
        from .create_muscle_func import create_muscle
        from .create_frame_func import create_frame
        from .create_contact_func import create_contact
        from .create_wrapgeom_func import create_wrapgeom


        
        # Stack-based traversal
        stack = [(body_data, 0) for body_data in body_hierarchy]  # Start with top-level bodies

        body_dict = {} #bodies in a dict for easy access
        frame_dict = {} #frames in a dict, as their data are extracted from the MuJoCo bodies
        joint_dict = {} # joint in a dict, as their data are extracted from the MuJoCo bodies
        site_dict = {} #muscles sites in a dict, as their data are extracted from the MuJoCo bodies

        while stack:
            body_info, depth = stack.pop()  # Get the next body in the stack

            # Get the name (if it exists)
            body_name = body_info.get("name")
            print("  " * depth + f"Processing body: {body_name}")

            if depth == 0: #if depth is 0, we create dict entries here. For all children they're created below.
                body_dict[body_name] = {} 
                body_dict[body_name]['parent_frame_pos_in_global'] = [0,0,0] #world position
                body_dict[body_name]['parent_frame_or_in_global_quat'] = [1,0,0,0] #world orientation

            ### get info for the attached local frame
            frame_pos_in_parent_frame = body_info.get('pos', [0,0,0]) #get pos, if it doesn't exist assume 0,0,0
            frame_or_in_parent_frame_quat = body_info.get('quat', [1,0,0,0])

            ### Inertial properties              
            if 'inertial' in body_info:
                inertial = body_info['inertial']
                com_local = inertial['pos'] #with respect to body's local attached frame
                mass = inertial['mass']
                body_inerframe_axes_quat = inertial.get('quat', [1,0,0,0]) #inertial frame with respect to body's local attached frame

                if 'diaginertia' in inertial:
                    MOI_inerframe = inertial.get('diaginertia')
                    MOI_inerframe.append(0.0)
                    MOI_inerframe.append(0.0)
                    MOI_inerframe.append(0.0)

                else:
                    MOI_inerframel = inertial.get('fullinertia')

                if any(orientationtype in inertial for orientationtype in ['axisangle', 'euler', 'xyaxes', 'zaxis']): #if the body has orientations defined using axisangle, euler etc. throw an error.
                    self.report({'ERROR'}, "The body '" + body_name + "' has orientations that aren't defined as quaternions. This is currently not yet supported for MuJoCo import. File an issue on the MuSkeMo Github or contact the developer.")

            if any(orientationtype in body_info for orientationtype in ['axisangle', 'euler', 'xyaxes', 'zaxis']): #if the body has orientations defined using axisangle, euler etc. throw an error.
                self.report({'ERROR'}, "The body '" + body_name + "' has orientations that aren't defined as quaternions. This is currently not yet supported for MuJoCo import. File an issue on the MuSkeMo Github or contact the developer.")

            # Get things in global frame
            ### body-fixed local frame
            parent_frame_pos_in_global = Vector(body_dict[body_name]['parent_frame_pos_in_global'])
            [gRp, pRg] = matrix_from_quaternion(body_dict[body_name]['parent_frame_or_in_global_quat'])  #p stands for parent, g stands for global
            frame_pos_in_glob = gRp @ Vector(frame_pos_in_parent_frame) + parent_frame_pos_in_global
            
            [pRf, fRp] = matrix_from_quaternion(frame_or_in_parent_frame_quat) #p stands for parent, f stands for (current) frame
            gRf = gRp@pRf # frame orientation in global frame
            frame_name = 'frame_of_' + body_name
            

            ### body
            if 'inertial' in body_info:

                COM_in_global = frame_pos_in_glob + gRf @ Vector(com_local)
                
                [fRi, iRf] = matrix_from_quaternion(body_inerframe_axes_quat)
                MOI_inerframe_mat = Matrix([[MOI_inerframe[0], MOI_inerframe[3], MOI_inerframe[4]],
                                            [MOI_inerframe[3],MOI_inerframe[1],MOI_inerframe[5]],
                                            [MOI_inerframe[4],MOI_inerframe[5],MOI_inerframe[2]]])

                MOI_f =  fRi @ MOI_inerframe_mat @ iRf #re-express the moment of inertia from the inertial frame to the body attached local frame

                MOI_glob = gRf @ MOI_f @ gRf.transposed() #re-express MOI from local frame to global frame


                # Call create_body with the prepared geometry string
                create_body(name=body_name, self = self,
                            is_global = True, size = body_axes_size,
                            mass=mass, 
                            COM = COM_in_global, 
                            inertia_COM = [MOI_glob[0][0], MOI_glob[1][1], MOI_glob[2][2], MOI_glob[0][1], MOI_glob[0][2], MOI_glob[1][2]],
                            COM_local=com_local,  
                            inertia_COM_local=[MOI_f[0][0], MOI_f[1][1], MOI_f[2][2], MOI_f[0][1], MOI_f[0][2], MOI_f[1][2]],
                            local_frame = frame_name, 
                            #Geometry=geometry_string, 
                            collection_name=body_colname,  
                            #import_geometry = import_geometry, #the bool property
                            #geometry_parent_dir = geometry_parent_dir,
                            #geometry_pos_in_glob = geometry_pos_in_glob,
                            #geometry_or_in_glob = geometry_or_in_glob,
                            #geometry_scale = geom_scale,
                            )
            
            else:
                print('error - no body data defined')


            #### construct child frame

            create_frame(name = frame_name, size = frame_size , 
                            pos_in_global=frame_pos_in_glob,
                    gRb = gRf, 
                    parent_body = body_name,
                    collection_name = frame_colname) 



            ### joint







            # If the body has children, add them to the stack
            if "children" in body_info:
                for child_name, child_data in reversed(body_info["children"].items()):  # Get both name and data
                    stack.append((child_data, depth + 1))  # Push child onto stack with increased depth
                    body_dict[child_name] = {}
                    body_dict[child_name]['parent_frame_pos_in_global'] = frame_pos_in_glob
                    body_dict[child_name]['parent_frame_or_in_global_quat'] = quat_from_matrix(gRf)





        return {'FINISHED'}

