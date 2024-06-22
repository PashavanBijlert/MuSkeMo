#This can use errors for if the collections are empty
import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import nan

from bpy_extras.io_utils import ExportHelper
import numpy as np
import os

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed

## following section is based on this code example: https://blender.stackexchange.com/questions/245005/how-to-create-and-export-a-custom-file-using-python
# I have reverse engineered the built-in blender function "ExportHelper" from io_utils, and removed some unnecessary elements
# ExportHelperCustom is a helper class
### Helper class

class ExportHelperCustom:  ## this is a helper class, that is inherited by all the actual export operators below. This prevents reusing code.

     ###### used to create filepath in invoke
    filename_ext : StringProperty(default = "", maxlen=8)
    
    #### filepath property is implicitly used by window_manager.fileselect_add
    filepath: StringProperty(name="File Path",description="Filepath used for exporting the file", maxlen=1024, subtype='FILE_PATH',)
    
    
    ### check existing is also implicitly used by window_manager, it gives an overwrite warning
    check_existing: BoolProperty(name="Check Existing", description="Check and warn on overwriting existing files", default=True, options={'HIDDEN'},)
    
    #this filters other filetypes from the window during export. The actual value is set in invoke, by setting the filetype
    filter_glob: bpy.props.StringProperty(default = "",options={'HIDDEN'}, maxlen=255)

    def check(self, context):  ### ensure the file extension is not changed by the user
        change_ext = False
        
        filepath = self.filepath
        
        if os.path.basename(filepath):
            
            filepath = bpy.path.ensure_ext(os.path.splitext(filepath)[0], self.filename_ext)
            if filepath != self.filepath:
                self.filepath = filepath
                change_ext = True

        return change_ext
    
    
### filename and path is defined below, in the invoke sections of each Export__Operator
## export bodies

class ExportBodiesOperator(Operator, ExportHelperCustom):  #inherits from ExportHelperCustom class
    bl_description = "Export all the bodies from the designated collection to a csv or other text file"
    bl_idname = "export.export_bodies"
    bl_label = "Export bodies"

    
    
    
    def invoke(self, context, event):  ## set a filepath, and filter out other filetypes from the viewer (via the helper super class)
               
        blend_filepath = context.blend_data.filepath
        if not blend_filepath: ### if the current filepath is empty, default to "untitled"
            blend_filepath = "untitled"
        else:
            blend_filepath = os.path.split(blend_filepath)[0] + "\\" + bpy.context.scene.muskemo.body_collection
            
              
        self.filename_ext = "." + bpy.context.scene.muskemo.export_filetype #user assigned
        self.filepath = blend_filepath + self.filename_ext #this sets the filepath, and the file extension.

        self.filter_glob = "*" + self.filename_ext   #set the filetype filter in the export window
        context.window_manager.fileselect_add(self)
                
             
        return {'RUNNING_MODAL'}

    
    def execute(self, context):
        from .write_bodies_func import write_bodies
        filetype = bpy.context.scene.muskemo.export_filetype #user assigned
        
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        body_colname = bpy.context.scene.muskemo.body_collection
        
        write_bodies(context, self.filepath, body_colname, delimiter)
        return {'FINISHED'}

## export joints
 
class ExportJointsOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the joints from the designated collection to a csv or other text file"
    bl_idname = "export.export_joints"
    bl_label = "Export joints"

   
    
    def invoke(self, context, event): ## set a filepath, and filter out other filetypes from the viewer (via the helper super class)
               
        blend_filepath = context.blend_data.filepath
        if not blend_filepath: ### if the current filepath is empty, default to "untitled"
            blend_filepath = "untitled"
        else:
            blend_filepath = os.path.split(blend_filepath)[0] + "\\" + bpy.context.scene.muskemo.joint_collection
            
              
        self.filename_ext = "." + bpy.context.scene.muskemo.export_filetype #user assigned
        self.filepath = blend_filepath + self.filename_ext #this sets the filepath, and the file extension.
        
        self.filter_glob = "*" + self.filename_ext   #set the filetype filter in the export window
        context.window_manager.fileselect_add(self)
        
        
        return {'RUNNING_MODAL'}
        
    
    
    def execute(self, context):
        from .write_joints_func import write_joints
        filetype = bpy.context.scene.muskemo.export_filetype #user assigned
        
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        joint_colname = bpy.context.scene.muskemo.joint_collection
        
        
        write_joints(context, self.filepath, joint_colname, delimiter)
        return {'FINISHED'}

## export muscles


class ExportMusclesOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the muscles from the designated collection to a csv or other text file"
    bl_idname = "export.export_muscles"
    bl_label = "Export muscles"

   
    
    def invoke(self, context, event): ## set a filepath, and filter out other filetypes from the viewer (via the helper super class)
               
        blend_filepath = context.blend_data.filepath
        if not blend_filepath: ### if the current filepath is empty, default to "untitled"
            blend_filepath = "untitled"
        else:
            blend_filepath = os.path.split(blend_filepath)[0] + "\\" + bpy.context.scene.muskemo.muscle_collection
            
              
        self.filename_ext = "." + bpy.context.scene.muskemo.export_filetype #user assigned
        self.filepath = blend_filepath + self.filename_ext #this sets the filepath, and the file extension.
        
        self.filter_glob = "*" + self.filename_ext   #set the filetype filter in the export window
        context.window_manager.fileselect_add(self)
        
        
        return {'RUNNING_MODAL'}
        
    
    
    def execute(self, context):
        from .write_muscles_func import write_muscles
        filetype = bpy.context.scene.muskemo.export_filetype #user assigned
        
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        muscle_colname = bpy.context.scene.muskemo.muscle_collection
        
        
        write_muscles(context, self.filepath, muscle_colname, delimiter)
        return {'FINISHED'}


## export inertial properties
class ExportMeshInPropsOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the inertial properties computed for meshes in the  the designated collection to a csv or other text file"
    bl_idname = "export.export_mesh_inertial_props"
    bl_label = "Export mesh inertial properties"


## export contacts
class ExportContactsOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the contact sphere locations from the designated collection to a csv or other text file"
    bl_idname = "export.export_contacts"
    bl_label = "Export contacts"


## export landmarks markers
class ExportLandmarksOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the landmarks from the designated collection to a csv or other text file"
    bl_idname = "export.export_landmarks"
    bl_label = "Export landmarks"



## export frames
class ExportFramesOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the local reference frames from the designated collection to a csv or other text file"
    bl_idname = "export.export_frames"
    bl_label = "Export frames"


### The panels


## Main export panel
class VIEW3D_PT_export_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
   
    bl_idname = 'VIEW3D_PT_export_panel' #have to define this if you use multiple panels
    bl_label = "Exporting"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        return

## Export bodies subpanel
class VIEW3D_PT_export_bodies_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_bodies_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export bodies"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = layout.row()
        row.prop(muskemo, "body_collection")
        row.operator("export.export_bodies",text = 'Export bodies')
        return  

## Export joints subpanel
class VIEW3D_PT_export_joints_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_joints_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export joints"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = layout.row()
        row.prop(muskemo, "joint_collection")
        row.operator("export.export_joints",text = 'Export joints')
        return      
    

## Export muscles subpanel
class VIEW3D_PT_export_muscles_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_muscles_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export muscles"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw(self, context):
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.prop(muskemo, "muscle_collection")
        row.operator("export.export_muscles",text = 'Export muscles')
        return     

## Export mesh inertial properties subpanel
class VIEW3D_PT_export_mesh_inprops_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_inprops_mesh_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export mesh inertial properties"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw(self, context):
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.prop(muskemo, "source_object_collection")
        row.operator("export.export_mesh_inertial_props",text = 'Export mesh inertial properties')
        return      

## Export contacts subpanel
class VIEW3D_PT_export_contacts_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_contacts_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export contact locations"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw(self, context):
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.prop(muskemo, "contact_collection")
        row.operator("export.export_contacts",text = 'Export contact locations')
        return     

## Export landmarks subpanel
class VIEW3D_PT_export_landmarks_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_landmarks_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export landmarks"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw(self, context):
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.prop(muskemo, "landmark_collection")
        row.operator("export.export_mesh_inertial_props",text = 'Export mesh inertial properties')
        return 
    

## Export frames subpanel
class VIEW3D_PT_export_frames_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_frames_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export reference frames"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw(self, context):
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.prop(muskemo, "frame_collection")
        row.operator("export.export_frames",text = 'Export frames')
        return    

## File export options
class VIEW3D_PT_export_options_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_options_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "File export options"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        row = self.layout.row()
        row.label(text = "Default behavior is to export as a csv file, using ',' as the delimiter.")
        row  = self.layout.row()
        row.label(text = "You can export to other text filetypes (eg. txt, json) and customize the delimiter")
        
        row  = self.layout.row()
        row.prop(muskemo, "export_filetype")
        row  = self.layout.row()
        row  = self.layout.row()
        row.prop(muskemo, "delimiter")
        return     
        
    
