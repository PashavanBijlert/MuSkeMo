#This can use errors for if the collections are empty
import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import nan

#from bpy_extras.io_utils import ExportHelper
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
    
    def invoke(self, context, event): ## set a filepath using a subclass dependent default filename, and filter out other filetypes from the viewer

        default_filename = self.default_filename       
       
        
        model_export_dir = bpy.context.scene.muskemo.model_export_directory
        
        if not model_export_dir: ### if the user-selected export directory is empty, it defaults to the blend file's parent directory
            model_export_dir = default_filename
        else:
            model_export_dir = os.path.split(model_export_dir)[0] + "\\" + default_filename 
            
              
        self.filename_ext = "." + bpy.context.scene.muskemo.export_filetype #user assigned
        self.filepath = model_export_dir + self.filename_ext #this sets the filepath, and the file extension.
        
        self.filter_glob = "*" + self.filename_ext   #set the filetype filter in the export window
        context.window_manager.fileselect_add(self)
        
        ### add number formatting to self

        sig_dig = bpy.context.scene.muskemo.significant_digits
        number_format = bpy.context.scene.muskemo.number_format  #can be 'e', 'g', or '8f'

        if number_format == 'g':
            number_format = f"{sig_dig}{number_format}"  #if it's g, we add the number of sig digits in front

        elif number_format == 'e':
            number_format = f"{sig_dig-1}{number_format}" #if it's e, we remove one digit (because e exports an extra digit)

        self.number_format = '.' + number_format  #number format needs to be something like '.4e'

        
        return {'RUNNING_MODAL'}
    
    
### filename and path is defined below, in the invoke sections of each Export__Operator


## select the export directory
class SelectModelExportDirectoryOperator(Operator):
    bl_idname = "export.select_model_export_directory"
    bl_label = "Select model export directory"
    bl_description = "Select the directory where you would like to export your model files to"

    #based on this code example: https://blender.stackexchange.com/a/126596

    # Define this to tell 'fileselect_add' that we want a directoy
    directory: StringProperty(
        name="Outdir Path",
        description="User selected output directory"
        )

    # Filters folders, so we don't see files
    filter_folder: BoolProperty(
        default=True,
        options={"HIDDEN"}
        )

    def invoke(self, context, event):
        
        context.window_manager.fileselect_add(self)
        
        return {'RUNNING_MODAL'}

    def execute(self, context):

               
        output_path = self.directory
        output_path = output_path.replace('\\', '/') 
        
        bpy.context.scene.muskemo.model_export_directory = output_path
        return {'FINISHED'}


## export bodies


class ExportBodiesOperator(Operator, ExportHelperCustom):  #inherits from ExportHelperCustom class
    bl_description = "Export all the bodies from the designated collection to a csv or other text file"
    bl_idname = "export.export_bodies"
    bl_label = "Export bodies"

    
    def invoke(self, context, event):
        
        self.default_filename = bpy.context.scene.muskemo.body_collection  #set the default filename to the collection name, make it available for the "invoke" command of super class "exporthelpercustom"

        return super().invoke(context, event)

    
    def execute(self, context):
        from .write_inprop_func import write_inprop
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        body_colname = bpy.context.scene.muskemo.body_collection

        print(self.number_format)
        
        write_inprop(context, self.filepath, body_colname, delimiter,'BODY', self.number_format)
        return {'FINISHED'}

## export joints
 
class ExportJointsOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the joints from the designated collection to a csv or other text file"
    bl_idname = "export.export_joints"
    bl_label = "Export joints"

   
    
    def invoke(self, context, event):
        
        self.default_filename = bpy.context.scene.muskemo.joint_collection  #set the default filename to the collection name, make it available for the "invoke" command of super class "exporthelpercustom"

        return super().invoke(context, event)
        
    
    
    def execute(self, context):
        from .write_joints_func import write_joints
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        joint_colname = bpy.context.scene.muskemo.joint_collection
        
        
        
        write_joints(context, self.filepath, joint_colname, delimiter, self.number_format)
        return {'FINISHED'}

## export muscles


class ExportMusclesOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the muscles from the designated collection to a csv or other text file"
    bl_idname = "export.export_muscles"
    bl_label = "Export muscles"

   
    
    def invoke(self, context, event):
        
        self.default_filename = bpy.context.scene.muskemo.muscle_collection  #set the default filename to the collection name, make it available for the "invoke" command of super class "exporthelpercustom"

        return super().invoke(context, event)
        
    
    
    def execute(self, context):
        from .write_muscles_func import write_muscles
       
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        muscle_colname = bpy.context.scene.muskemo.muscle_collection
        
        
        write_muscles(context, self.filepath, muscle_colname, delimiter, self.number_format)
        return {'FINISHED'}


## export inertial properties
class ExportMeshInPropsOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the inertial properties computed for meshes in the  the designated collection to a csv or other text file"
    bl_idname = "export.export_mesh_inertial_props"
    bl_label = "Export mesh inertial properties"
    
    
    def invoke(self, context, event):
        
        self.default_filename = bpy.context.scene.muskemo.source_object_collection  #set the default filename to the collection name, make it available for the "invoke" command of super class "exporthelpercustom"
        if not self.default_filename: #if the target collection has not been named
            self.report({'ERROR'}, "You did not designate a collection (Blender folder) in which the 3D meshes are located. Place them in a single collection, and type the name in the text box")
            return {'FINISHED'}


        return super().invoke(context, event)

    
    def execute(self, context):
        from .write_inprop_func import write_inprop
         
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        mesh_colname = bpy.context.scene.muskemo.source_object_collection

        

        
        write_inprop(context, self.filepath, mesh_colname, delimiter,'mesh', self.number_format)
        return {'FINISHED'}

## export contacts
class ExportContactsOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the contact sphere locations from the designated collection to a csv or other text file"
    bl_idname = "export.export_contacts"
    bl_label = "Export contacts"

    def invoke(self, context, event):
        
        self.default_filename = bpy.context.scene.muskemo.contact_collection  #set the default filename to the collection name, make it available for the "invoke" command of super class "exporthelpercustom"

        return super().invoke(context, event)
        
    
    
    def execute(self, context):
        from .write_pos_and_pbody_func import write_pos_and_pbody
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        contact_colname = bpy.context.scene.muskemo.contact_collection
        
        write_pos_and_pbody(context, self.filepath, contact_colname, delimiter, 'CONTACT', self.number_format)
        return {'FINISHED'}

## export landmarks markers
class ExportLandmarksOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the landmarks from the designated collection to a csv or other text file"
    bl_idname = "export.export_landmarks"
    bl_label = "Export landmarks"

    def invoke(self, context, event):
        
        self.default_filename = bpy.context.scene.muskemo.landmark_collection  #set the default filename to the collection name, make it available for the "invoke" command of super class "exporthelpercustom"

        return super().invoke(context, event)
        
    
    
    def execute(self, context):
        from .write_pos_and_pbody_func import write_pos_and_pbody
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        landmark_colname = bpy.context.scene.muskemo.landmark_collection
        
        write_pos_and_pbody(context, self.filepath, landmark_colname, delimiter, 'landmark', self.number_format)
        return {'FINISHED'}



## export frames
class ExportFramesOperator(Operator, ExportHelperCustom): #inherits from ExportHelperCustom class
    bl_description = "Export all the local reference frames from the designated collection to a csv or other text file"
    bl_idname = "export.export_frames"
    bl_label = "Export frames"

    def invoke(self, context, event):
        
        self.default_filename = bpy.context.scene.muskemo.frame_collection  #set the default filename to the collection name, make it available for the "invoke" command of super class "exporthelpercustom"

        return super().invoke(context, event)
        
    
    
    def execute(self, context):
        from .write_frames_func import write_frames
        
        delimiter = bpy.context.scene.muskemo.delimiter #user assigned 
        frame_colname = bpy.context.scene.muskemo.frame_collection
        
        write_frames(context, self.filepath, frame_colname, delimiter, self.number_format)
        return {'FINISHED'}


## Export visual geometry folder

class ExportGeometryFolderOperator(Operator):

    bl_idname = "export.export_geometry_folder"
    bl_label = "Export visual geometry"
    bl_description = "Export all the visual geometry from the designated geometry collection as '.obj' meshes to a subdirectory in the model directory. The folder name will be the same as the geometry collection name."

    def execute(self, context):

        geo_folder = bpy.context.scene.muskemo.geometry_collection
        model_export_directory = bpy.context.scene.muskemo.model_export_directory

        if not model_export_directory:
            self.report({'ERROR'}, "You must first select a model export directory. Press the 'Select export directory' and choose a target folder")
            return {'FINISHED'}


        output_path = model_export_directory + geo_folder + '/'
        
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        bpy.ops.object.select_all(action='DESELECT')

        objects=  [x for x in bpy.data.collections[geo_folder].objects if 'MESH' in x.id_data.type] #get the name for each object in collection 'Convex Hulls', if the data type is a 'MESH'

        #IF STATEMENT FOR CHECKING IF IT IS PARENTED
        #IF STATEMENT IF THE MUSKEMO_PROPS MAKE SENSE

        for obj in objects:
            obj.select_set(True)

            name = obj.name

            if not name.endswith('.obj'):
                name = name + '.obj'

            if bpy.app.version[0] <4: #if blender version is below 4
                                        
                bpy.ops.export_scene.obj(filepath= os.path.join(output_path, name), use_selection = True, axis_forward = 'Y', axis_up = 'Z',use_materials = False)
            else: #if blender version is above 4:

                bpy.ops.wm.obj_export(filepath= os.path.join(output_path, name), export_selected_objects = True, forward_axis = 'Y', up_axis = 'Z',export_materials = False)

            
            self.report({'INFO'}, "Exported geometry with the name '" + name + "' to the '" + geo_folder + "' subdirectory")
                        
            obj.select_set(False)    


        self.report({'INFO'}, "Exported " + str(len(objects)) + " geometries to the '" + geo_folder + "' subdirectory")
        return {'FINISHED'}
    

### The panels


## Main export panel
class VIEW3D_PT_export_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
   
    bl_idname = 'VIEW3D_PT_export_panel' #have to define this if you use multiple panels
    bl_label = "Exporting"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = layout.row()
       
        row.operator("export.select_model_export_directory",text = 'Select export directory')
        row = layout.row()
        row.prop(muskemo, "model_export_directory")
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
        row.operator("export.export_landmarks",text = 'Export landmarks')
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

## Export visual geometry folder subpanel
class VIEW3D_PT_geometry_folder_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_export_geometry_folder_subpanel'
    bl_parent_id = 'VIEW3D_PT_export_panel'  #have to define this if you use multiple panels
    bl_label = "Export visual geometry folder"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'}
    
    
    def draw(self, context):
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.prop(muskemo, "geometry_collection")

        row = self.layout.row()
        row.operator("export.export_geometry_folder",text = 'Export geometry folder')
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

        row  = self.layout.row()
        row  = self.layout.row()
        row.prop(muskemo, "significant_digits")

        row  = self.layout.row()
        row  = self.layout.row()
        row.prop(muskemo, "number_format")
        return     
        
    
