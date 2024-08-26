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
import re  #regular expressions

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
                         COM_local = COM_local, inertia_COM_local = inertia_COM_local , collection_name=colname)


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

## import muscles


class ImportMusclesOperator(Operator, ImportHelperCustom):  #inherits from ImportHelperCustom class
    bl_description = "Import a MuSkeMo-created muscles file"
    bl_idname = "import.import_muscles"
    bl_label = "Import muscles"

    
       
    def execute(self, context):
        
        # Call the custom superclass method read_CSV_data to read the CSV data
        data = self.read_csv_data(context)

        headers = data[0]
        data = data[1:]
        
        # throw an error if BODY not in the headers     
        if 'MUSCLE' not in headers[0] and 'muscle' not in headers[0]:
            self.report({'ERROR'}, "The loaded file does not appear to be a 'muscles' file created by MuSkeMo")
            return {'FINISHED'}


        colname = bpy.context.scene.muskemo.muscle_collection #name for the collection that will contain the hulls
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the "muscles" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]

        from .create_muscle_func import create_muscle


        ### get unique muscle names               
        # Extract the first column (muscle point names)
        muscle_point_names = [row[0] for row in data]

        # Define the pattern to remove suffixes (_or, _ins, _via#)
        pattern = r'_or|_ins|_via\d+'

        # Apply the regex pattern to remove the suffixes and maintain original order
        muscle_names = []
        seen = set()

        for name in muscle_point_names:
            clean_name = re.sub(pattern, '', name)
            if clean_name not in seen:
                seen.add(clean_name)
                muscle_names.append(clean_name)
        

        #muscle_names = muscle_names[0]
        for muscle_name in muscle_names:

            data_onemusc = [x for x in data if x[0].startswith(muscle_name)] #data rows of a single muscle
            

            for point_row in data_onemusc:  #each row of data_onemusc contains data for one muscle point
                parent_body_name = point_row[1]
                
                #error checks for if the object is a valid BODY to parent the muscle point to
                if parent_body_name not in bpy.data.objects:
                    self.report({'ERROR'}, "The " + muscle_name + " MUSCLE has a point that is attached to a body that does not exist yet. Operation cancelled.")
                    return {'FINISHED'}
                
                if 'MuSkeMo_type' not in bpy.data.objects[parent_body_name]:
                    self.report({'ERROR'}, "You are attempting to attach a point of the " + muscle_name + " MUSCLE to " + parent_body_name + ", which is not an object created by MuSkeMo. Operation cancelled.")
                    return {'FINISHED'}
                
                if bpy.data.objects[parent_body_name]['MuSkeMo_type']!='BODY':
                    self.report({'ERROR'}, "You are attempting to attach a point of the " + muscle_name + " MUSCLE to " + parent_body_name + ", which is not a BODY. Operation cancelled.")
                    return {'FINISHED'}
        
            
                point_position = [float(x) for x in point_row[2:5]]

                #parent_frame_name = point_row[5]
                #point_position_loc = [float(x) for x in point_row[6:9]]

                optimal_fiber_length = float(point_row[9])
                tendon_slack_length  = float(point_row[10])
                F_max                = float(point_row[11])
                pennation_angle      = float(point_row[12])
                
                create_muscle(muscle_name = muscle_name, 
                              is_global =True, 
                              body_name = parent_body_name,
                              point_position = point_position,
                              optimal_fiber_length=optimal_fiber_length,
                              tendon_slack_length=tendon_slack_length,
                              F_max = F_max,
                              pennation_angle = pennation_angle)
                

        return {'FINISHED'}
    

## import contacts


class ImportContactsOperator(Operator, ImportHelperCustom):  #inherits from ImportHelperCustom class
    bl_description = "Import a MuSkeMo-created contacts file"
    bl_idname = "import.import_contacts"
    bl_label = "Import contacts"

    
       
    def execute(self, context):
        
        # Call the custom superclass method read_CSV_data to read the CSV data
        data = self.read_csv_data(context)

        headers = data[0]
        data = data[1:]
        
        # throw an error if BODY not in the headers     
        if 'CONTACT' not in headers[0]:
            self.report({'ERROR'}, "The loaded file does not appear to be a 'contacts' file created by MuSkeMo")
            return {'FINISHED'}


        colname = bpy.context.scene.muskemo.contact_collection #name for the collection
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the "contacts" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]

        from .create_contact_func import create_contact

        radius = bpy.context.scene.muskemo.contact_radius # in meters

        for row in data:
            
            name = row[0]
            pos_in_global = [float(x) for x in row[1:4]]
            parent_body = row[4]
            parent_frame_name = row[5]
            pos_in_parent_frame = [float(x) for x in row[6:9]]
            
            ## check if parent body and frame exist, and if not give a warning
            if parent_body in bpy.data.objects: #if the parent body exists
                parent_body_obj = bpy.data.objects[parent_body]

                if 'BODY' in parent_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body

                    if parent_body_obj['local_frame']!= parent_frame_name: #if there is a mismatch between parent body's local frame and contact's parent frame
                        
                        self.report({'WARNING'}, "Parent BODY with the name " + parent_body + " has a different local frame assigned than defined for the " + name + " contact in the imported file. Local transformations will be ignored during import, clear and reassign the parent manually if you need local transformations for this contact.")
                        pos_in_parent_frame   = [nan]*3
                        
                else:
                    self.report({'WARNING'}, "No BODY with the name " + parent_body + " exists. " + name + " contact will not have a parent in Blender, but the parent body property will be saved for export.")
                
            else:
                self.report({'WARNING'}, "No object with the name " + parent_body + " exists. " + name + " contact will not have a parent in Blender, but the parent body property will be saved for export.")
            
            create_contact(name = name, radius = radius, 
                         is_global = True,
                         parent_body=parent_body, 
                         pos_in_global = pos_in_global, 
                         pos_in_parent_frame = pos_in_parent_frame, 
                         )


        return {'FINISHED'}    
    
## import contacts


class ImportFramesOperator(Operator, ImportHelperCustom):  #inherits from ImportHelperCustom class
    bl_description = "Import a MuSkeMo-created frames file"
    bl_idname = "import.import_frames"
    bl_label = "Import frames"

    
       
    def execute(self, context):
        
        # Call the custom superclass method read_CSV_data to read the CSV data
        data = self.read_csv_data(context)

        headers = data[0]
        data = data[1:]
        
        # throw an error if BODY not in the headers     
        if 'FRAME' not in headers[0] and 'frame' not in headers[0]:
            self.report({'ERROR'}, "The loaded file does not appear to be a 'frames' file created by MuSkeMo")
            return {'FINISHED'}


        colname = bpy.context.scene.muskemo.frame_collection #name for the collection
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the "frames" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]

        from .create_frame_func import create_frame
        from .quaternions import matrix_from_quaternion

        size = bpy.context.scene.muskemo.ARF_axes_size # in meters

        for row in data:
            
            name = row[0]
            parent_body = row[1]
            pos_in_global = [float(x) for x in row[2:5]]
            or_in_global_quat = [float(x) for x in row[5:9]]
            
            [gRb, bRg] = matrix_from_quaternion(or_in_global_quat)


            ## check if parent body and frame exist, and if not give a warning
            if parent_body in bpy.data.objects: #if the parent body exists
                parent_body_obj = bpy.data.objects[parent_body]

                if 'BODY' in parent_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body

                    if parent_body_obj['local_frame']!= name: #if there is a mismatch between parent body's local frame and contact's parent frame
                        
                        self.report({'WARNING'}, "Parent BODY with the name " + parent_body + " has a different local frame assigned than the " + name + " frame in the imported file. This frame will not be parented to that body during import, clear and reassign the parent manually if you want this frame assigned to a body.")
                        parent_body = 'not_assigned'
                        
                else:
                    self.report({'WARNING'}, "No BODY with the name " + parent_body + " exists. " + name + " frame will not have a parent in Blender, but the parent body property will be saved for export.")
                
            else:
                self.report({'WARNING'}, "No object with the name " + parent_body + " exists. " + name + " frame will not have a parent in Blender, but the parent body property will be saved for export.")
            
            create_frame(name = name, size = size, 
                         parent_body=parent_body, 
                         pos_in_global = pos_in_global, 
                         gRb = gRb, 
                         )


        return {'FINISHED'}   

## import OpenSim model

from .import_opensim_model import ImportOpenSimModel

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
        row.prop(muskemo, "body_collection")
        row.operator("import.import_bodies",text = 'Import bodies')

        row = layout.row()
        row.prop(muskemo, "joint_collection")
        row.operator("import.import_joints",text = 'Import joints')

        row = layout.row()
        row.prop(muskemo, "muscle_collection")
        row.operator("import.import_muscles",text = 'Import muscles')

        row = layout.row()
        row.prop(muskemo, "contact_collection")
        row.operator("import.import_contacts",text = 'Import contacts')

        row = layout.row()
        row.prop(muskemo, "frame_collection")
        row.operator("import.import_frames",text = 'Import frames')

        return      
    
## Import full model
class VIEW3D_PT_import_full_model_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_import_full_model_subpanel'
    bl_parent_id = 'VIEW3D_PT_import_panel'  #have to define this if you use multiple panels
    bl_label = "Import full model"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = layout.row()
        row.operator("import.import_opensim_model",text = 'Import OpenSim model')


        row = layout.row()
        row.prop(muskemo, "model_import_style")


        return          