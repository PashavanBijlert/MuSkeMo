import bpy
from mathutils import Vector


from bpy.types import (Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import nan


import numpy as np
import os
import csv


class ImportTrajectorySTO(Operator):
    bl_description = "Import a trajectory in .sto file format"
    bl_idname = "import.import_trajectory_sto"
    bl_label = "Import .sto strajectory"


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

        self.filter_glob = "*.sto"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def parse_sto(self, context):#custom super class method
        """Reads .STO file data from the specified filepath using the CSV importer and tab delimiters."""
        filepath = self.filepath
        with open(filepath, mode = 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            file_header = [] #all the extra header lines including "endheader"
            column_headers = [] #the actual headers of the data columns
            data = []
            is_data = False #remains false until we've looped through the file_header rows

            for row in reader:
                if 'endheader' in row:
                    is_data = True
                    continue
                
                if is_data:
                    if not column_headers:  # The first row after endheader contains the column headers
                        column_headers = row
                    else:
                        data.append([float(x) for x in row])
                else:
                    file_header.append(row)
        
        return column_headers, data
    
    def execute(self, context):
        
        # Call the custom superclass method parse_sto to read the sto data
        column_headers, traj_data = self.parse_sto(context)
        print(column_headers)
        #print(traj_data)
        
        return {'FINISHED'}

    