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
                body_dict[body_name]['parent_body_name'] = 'world'
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

            #add frame data to frame dict for easy access

            frame_dict[frame_name] = {}
            frame_dict[frame_name]['pos_in_global'] = frame_pos_in_glob
            frame_dict[frame_name]['gRb'] = gRf
            frame_dict[frame_name]['parent_body_name'] = body_name

            ### joint
            joints = body_info.get('joint') 
            if joints: #if sites are in body info, add them to the dict
                
                joint_pbody_name = body_dict[body_name]['parent_body_name']
                joint_cbody_name = body_name
                joint_name = joint_pbody_name + '_' + joint_cbody_name + '_joint' 
                    


                ## some MuJoCo joints have "user" defined in them, which appears to be a default pose
                ## Find the user value (which is just a user in put coordinate value apparently), 
                # multiply it by the axis, and add this to the joint position in body frame
                ### Doing this only for slide_joints, it may be necessary to do a similar thing for pin joints in the future.

                coordinate_offset = Vector([0,0,0]) #if 'user' is defined in a mujoco joint, which appears to be a coordinate offset, we save it in the joint dict and apply it to the model after model construction
                slide_joints = []


                if isinstance(joints, dict): #if the body has a single joint, it's returned as a dict instead of a list
                    
                    joint = joints
                    
                    coordinate = joint['name']

                    ##
                    ## check if there is joint type, and if yes, use that to distinguish between T and R coordinate
                    ## check if the transform axes are one of the unit directions, and if yes, use that to choose x, y, or z
                    ## If transform axes are non-standard, treat like OpenSim
                    ## if no subjoint defined but subbody defined, create a joint (for each body)


                    
                    joint_pos_in_body_frame = joint['pos'] #this is the parent frame in mujoco, but the child frame in MuSkeMo
                    
                    if 'slide' in joint: #if joint type is slide, we check later if 'user' is defined
                        slide_joints = joint 


                else:
                    

                    joint_names = [obj['name'] for obj in joints]
                    
                    ## see if there's a common part for the joint names that we can use to name this new joint.
                    def common_sections(strings):
                        # Split each string into sections based on '_'
                        split_strings = [s.split('_') for s in strings]

                        # Find the shortest list length (to avoid index errors)
                        min_length = min(len(parts) for parts in split_strings)

                        # Track common parts while allowing gaps
                        common_parts = []
                        
                        for i in range(min_length):
                            section = split_strings[0][i]  # Take section from first string
                            
                            # Check if this section appears in ALL strings at any position
                            if all(section in parts for parts in split_strings):
                                common_parts.append(section)

                        return '_'.join(common_parts)  # Rejoin with '_'

                    
                    common_part = common_sections(joint_names) ## this is missing the side string
                    if common_part:
                        joint_name = common_part
                        if joint_name in bpy.data.objects: #ensure unique names
                            joint_name = joint_name + '_joint' #

                    
                    #check if all have the same pos defined
                    joint_positions = [obj.get('pos') for obj in joints]

                    if not all(joint_pos == joint_positions[0] for joint_pos in joint_positions):

                        self.report({'WARNING'}, "The body '" + body_name + "' has MuJoCo joints (equivalent to MuSkeMo coordinates) with different positions defined. This is not currently possible in MuSkeMo, so MuSkeMo defaulted to using the first joint's position.")


                    joint_pos_in_body_frame = joint_positions[0]
                    
                    #if joint type is slide, we check later if 'user' is defined
                    slide_joints = [joint for joint in joints if joint.get('type')=='slide']
                                         

                joint_pos_in_glob = gRf@Vector(joint_pos_in_body_frame) + frame_pos_in_glob



                create_joint(name = joint_name, radius = joint_rad, is_global = True, collection_name = joint_colname,
                parent_body=joint_pbody_name, child_body=joint_cbody_name, 
                pos_in_global=joint_pos_in_glob, 
                or_in_global_XYZeuler=[nan] * 3, 
                or_in_global_quat=[nan] * 4,
                pos_in_parent_frame=[nan] * 3,
                or_in_parent_frame_XYZeuler=[nan] * 3, or_in_parent_frame_quat=[nan] * 4,
                pos_in_child_frame=[nan] * 3, 
                or_in_child_frame_XYZeuler=[nan] * 3, or_in_child_frame_quat=[nan] * 4,
                coordinate_Tx='', coordinate_Ty='', coordinate_Tz='', 
                coordinate_Rx='', coordinate_Ry='', coordinate_Rz='',                  
                )    
            
                ### Here we check if "user" is defined in the joints, and if so, we compute the global coordinate offset

                for sj in slide_joints:
                    if 'user' in sj:
                        coordinate_offset += sj['user'][0] * Vector(sj['axis']) #coordinate offset is initially 0,0,0, here we add components to it

                
                ### add joint data to joint_dict
                joint_dict[joint_name]     = {} #create as a new dict
                joint_dict[joint_name]['joint_name'] = joint_name
                joint_dict[joint_name]['parent_body_name'] = joint_pbody_name
                joint_dict[joint_name]['child_body_name'] = joint_cbody_name
                joint_dict[joint_name]['pos_in_global'] = joint_pos_in_glob
                joint_dict[joint_name]['mujoco_bodyframe_gRf'] = gRf

                if coordinate_offset !=  Vector([0,0,0]):
                    coordinate_offset_global = gRf@coordinate_offset
                    joint_dict[joint_name]['coordinate_offset_global'] = coordinate_offset_global



            ### add sites to the sites dict, so they're callable by name during muscle point construction

            sites = body_info.get('site') 
            if sites: #if sites are in body info, add them to the dict
                
                if  not isinstance(sites, dict): #if it's not a dict (so not a single site)
                    for site in sites:

                        
                        site_name = site['name']

                        site_dict[site_name]  = site #add each site in this body to the site dict, using the name as the dict entry   
                        site_dict[site_name]['parent_body_name'] = body_name
                        site_dict[site_name]['parent_frame_name'] = frame_name

                else: #if it's a single site        
                    
                    site_name = site['name']

                    site_dict[site_name]  = site #add each site in this body to the site dict, using the name as the dict entry   
                    site_dict[site_name]['parent_body_name'] = body_name
                    site_dict[site_name]['parent_frame_name'] = frame_name


            # If the body has children, add them to the stack
            if "children" in body_info:
                for child_name, child_data in reversed(body_info["children"].items()):  # Get both name and data
                    stack.append((child_data, depth + 1))  # Push child onto stack with increased depth
                    body_dict[child_name] = {}
                    body_dict[child_name]['parent_frame_pos_in_global'] = frame_pos_in_glob
                    body_dict[child_name]['parent_frame_or_in_global_quat'] = quat_from_matrix(gRf)
                    body_dict[child_name]['parent_body_name'] = body_name

            
        


        #apply the joint coordinate offsets after model construction, if they are defined for a specific joint
        for j, data in joint_dict.items():  # Iterate over keys AND values
            if 'coordinate_offset_global' in data:  # Check if the key exists in the nested dict
                

                joint_obj = bpy.data.objects[data['joint_name']]
                coordinate_offset_global = data['coordinate_offset_global']

                joint_obj.matrix_world.translation += coordinate_offset_global     

        return {'FINISHED'}

