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

        def get_body_data(element, index=0):
            """ Extracts data from a body element, ensuring only nested <body> elements are considered children. """
            element_data = {key: parse_numerical(value) for key, value in element.attrib.items()}
            
            # Get body name from 'name' attribute, or generate a fallback
            body_name = element_data.get("name", f"unnamed_body_{index}")
            
            children = {}
            child_index = 0

            for child in element:
                if child.tag == "body":
                    child_data = get_body_data(child, child_index)
                    child_name = list(child_data.keys())[0]  # Extract the actual name from child_data
                    children[child_name] = child_data[child_name]
                    child_index += 1
                else:
                    # Non-body elements are attributes of the body itself
                    if child.tag not in element_data:
                        element_data[child.tag] = []
                    element_data[child.tag].append({key: parse_numerical(value) for key, value in child.attrib.items()})

            if children:
                element_data["children"] = children  # Store children only if present

            return {body_name: element_data}


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

        # Find the worldbody (where all bodies are defined)
        worldbody = root.find("worldbody")

        # Extract body hierarchy
        if worldbody is not None:
            body_hierarchy = [get_body_data(body) for body in worldbody.findall("body")]
            print("Body Hierarchy:", body_hierarchy)
        else:
            print("No worldbody found in the XML file.")

        # Extract muscle data
        muscle_data = get_muscle_data(root)
        print("Muscle Data:", muscle_data)
                
        

        return {'FINISHED'}

