#This can use errors for if the collections are empty
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


        # Extract body data from the model
        body_data = get_body_data(model)
       

        from .create_body_func import create_body

        rad = bpy.context.scene.muskemo.axes_size #axis length, in meters


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
            create_body(name=name, is_global = True, size = rad,
                        mass=mass, COM=COM,  inertia_COM=inertia_COM, Geometry=geometry_string)
            



        return {'FINISHED'}
