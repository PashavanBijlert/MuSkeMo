#This can use errors for if the collections are empty
import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import nan

#from bpy_extras.io_utils import ImportHelper
import numpy as np
import os
import csv

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed

### operators
# customized version of ImportHelper from io_utils (blender source code)


class ImportHelperCustom: #custom helper superclass
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    def invoke(self, context, _event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def read_csv_data(self, context):  #custom super class method
        """Reads CSV data from the specified filepath using the delimiter from context."""
        filepath = self.filepath
        delimiter = context.scene.muskemo.delimiter  # Retrieve the delimiter from the context
        
        with open(filepath, mode='r', newline='') as file:
            csv_reader = csv.reader(file, delimiter=delimiter)
            data = list(csv_reader)
        
        return data


## export bodies


class ImportBodiesOperator(Operator, ImportHelperCustom):  #inherits from ImportHelperCustom class
    bl_description = "Import a MuSkeMo-created bodies file"
    bl_idname = "import.import_bodies"
    bl_label = "Import bodies"

    
       
    def execute(self, context):
        
        # Call the custom superclass method read_CSV_data to read the CSV data
        data = self.read_csv_data(context)

        headers = data[0]
        data = data[1:]
        
        # throw an error if BODY not in the headers     
        if 'BODY' not in headers[0]:
            self.report({'ERROR'}, "The loaded file does not appear to be a 'bodies' file created by MuSkeMo")
            return {'FINISHED'}
            
        for row in data:
            #call create body operator
            return
        


        return {'FINISHED'}



### The panels

## Main export panel
class VIEW3D_PT_import_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
   
    bl_idname = 'VIEW3D_PT_import_panel' #have to define this if you use multiple panels
    bl_label = "Importing"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = layout.row()
       
        #row.operator("export.select_model_export_directory",text = 'Select export directory')
        #row = layout.row()
        #row.prop(muskemo, "model_export_directory")
        return
    
## Import model components
class VIEW3D_PT_import_modelcomponents_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_import_modelcomponents_subpanel'
    bl_parent_id = 'VIEW3D_PT_import_panel'  #have to define this if you use multiple panels
    bl_label = "Import model components"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = layout.row()
        #row.prop(muskemo, "body_collection")
        row.operator("import.import_bodies",text = 'Import bodies')
        return      