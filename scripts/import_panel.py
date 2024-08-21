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


## import bodies


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


        colname = bpy.context.scene.muskemo.body_collection #name for the collection that will contain the hulls
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the "bodies" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]

        from .create_body_func import create_body
                       
        rad = bpy.context.scene.muskemo.axes_size #axis length, in meters

        for row in data:
            
            name = row[0]
            mass = float(row[1])
            COM = [float(x) for x in row[2:5]]
            inertia_COM = [float(x) for x in row[5:11]]
            geometry = row[11]
            local_frame_name = row[12]
            COM_local = [float(x) for x in row[13:16]]
            inertia_COM_local = [float(x) for x in row[16:22]]



            create_body(name = name, size = rad, is_global =True, mass =mass, COM=COM,
                        inertia_COM = inertia_COM, Geometry = geometry, local_frame = local_frame_name,
                         COM_local = COM_local, inertia_COM_local = inertia_COM_local )


        return {'FINISHED'}

## import joints


class ImportJointsOperator(Operator, ImportHelperCustom):  #inherits from ImportHelperCustom class
    bl_description = "Import a MuSkeMo-created joints file"
    bl_idname = "import.import_joints"
    bl_label = "Import joints"

    
       
    def execute(self, context):
        
        # Call the custom superclass method read_CSV_data to read the CSV data
        data = self.read_csv_data(context)

        headers = data[0]
        data = data[1:]
        
        # throw an error if BODY not in the headers     
        if 'JOINT' not in headers[0] and 'joint' not in headers[0]: #the bit after and can be deleted at some point. 
            self.report({'ERROR'}, "The loaded file does not appear to be a 'JOINTS' file created by MuSkeMo")
            return {'FINISHED'}


        colname = bpy.context.scene.muskemo.joint_collection #name for the collection that will contain the hulls
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the correct collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]

        from .create_joint_func import create_joint
                       
        rad = bpy.context.scene.muskemo.jointsphere_size #axis length, in meters

        for row in data:
            
            name = row[0]
            parent_body = row[1]
            child_body = row[2]
            pos_in_global = [float(x) for x in row[3:6]]
            or_in_global_XYZeuler= [float(x) for x in row[6:9]]
            or_in_global_quat= [float(x) for x in row[9:13]]
            parent_frame_name = row[13]
            pos_in_parent_frame = [float(x) for x in row[14:17]]
            or_in_parent_frame_XYZeuler= [float(x) for x in row[17:20]]
            or_in_parent_frame_quat= [float(x) for x in row[20:24]]
            child_frame_name = row[24]
            pos_in_child_frame = [float(x) for x in row[25:28]]
            or_in_child_frame_XYZeuler= [float(x) for x in row[28:31]]
            or_in_child_frame_quat= [float(x) for x in row[31:35]]
            coordinate_Tx = row[35]
            coordinate_Ty = row[36]
            coordinate_Tz = row[37]
            coordinate_Rx = row[38]
            coordinate_Ry = row[39]
            coordinate_Rz = row[40]


            ## check if parent body and frame exist, and if not give a warning
            if parent_body in bpy.data.objects: #if the parent body exists
                parent_body_obj = bpy.data.objects[parent_body]

                if 'BODY' in parent_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body

                    if parent_body_obj['local_frame']!= parent_frame_name: #if there is a mismatch between parent body's local frame and joint's parent frame
                        
                        self.report({'WARNING'}, "Parent BODY with the name " + parent_body + " has a different local frame assigned than defined for the " + name + " JOINT in the imported file. Local transformations will be ignored during import, clear and reassign the parent manually if you need local transformations for this joint.")
                        pos_in_parent_frame   = [nan]*3
                        or_in_parent_frame_XYZeuler = [nan]*3
                        or_in_parent_frame_quat     = [nan]*4
                else:
                    self.report({'WARNING'}, "No BODY with the name " + parent_body + " exists. " + name + " joint will not have a parent in Blender, but the parent body property will be saved for export.")
                
            else:
                self.report({'WARNING'}, "No object with the name " + parent_body + " exists. " + name + " joint will not have a parent in Blender, but the parent body property will be saved for export.")
            
            ## check if child body and frame exist, and if not give a warning
            if child_body in bpy.data.objects: #if the child body exists
                child_body_obj = bpy.data.objects[child_body]

                if 'BODY' in child_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body

                    if child_body_obj['local_frame']!= child_frame_name: #if there is a mismatch between child body's local frame and joint's child frame
                        
                        self.report({'WARNING'}, "Child BODY with the name " + child_body + " has a different local frame assigned than defined for the " + name + " JOINT in the imported file. Local transformations will be ignored during import, clear and reassign the child manually if you need local transformations for this joint.")
                        pos_in_child_frame          = [nan]*3
                        or_in_child_frame_XYZeuler  = [nan]*3
                        or_in_child_frame_quat      = [nan]*4
                else:
                    self.report({'WARNING'}, "No BODY with the name " + child_body + " exists. " + name + " joint will not have a child in Blender, but the child body property will be saved for export.")
                
            else:
                self.report({'WARNING'}, "No object with the name " + child_body + " exists. " + name + " joint will not have a child in Blender, but the child body property will be saved for export.")
            
            create_joint(name = name, radius = rad, 
                         is_global = True,
                         parent_body=parent_body, 
                         child_body=child_body,
                         pos_in_global = pos_in_global, 
                         or_in_global_XYZeuler = or_in_global_XYZeuler,
                         or_in_global_quat= or_in_global_quat,
                         pos_in_parent_frame = pos_in_parent_frame, 
                         or_in_parent_frame_XYZeuler = or_in_parent_frame_XYZeuler,
                         or_in_parent_frame_quat= or_in_parent_frame_quat,
                         pos_in_child_frame = pos_in_child_frame, 
                         or_in_child_frame_XYZeuler = or_in_child_frame_XYZeuler,
                         or_in_child_frame_quat= or_in_child_frame_quat,
                         coordinate_Tx = coordinate_Tx,
                         coordinate_Ty = coordinate_Ty,
                         coordinate_Tz = coordinate_Tz,
                         coordinate_Rx = coordinate_Rx,
                         coordinate_Ry = coordinate_Ry,
                         coordinate_Rz = coordinate_Rz,

                         )


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
        row = layout.row()
        #row.prop(muskemo, "body_collection")
        row.operator("import.import_joints",text = 'Import joints')
        return      