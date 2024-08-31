import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import nan


import numpy as np
import os
import csv

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed



from .import_trajectory import ImportTrajectorySTO

### The panels


class VIEW3D_PT_visualization_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
   
    bl_idname = 'VIEW3D_PT_visualization_panel' #have to define this if you use multiple panels
    bl_label = "Visualization"  # found at the top of the Panel
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

    
    
    ## Visualization options
class VIEW3D_PT_visualization_options_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_visualization_options_subpanel'
    bl_parent_id = 'VIEW3D_PT_visualization_panel'  #have to define this if you use multiple panels
    bl_label = "Visualization options"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = self.layout.row()
        row.operator("visualization.generate_volumetric_muscles",text = 'Generate volumetric muscles')

        row = self.layout.row()
        row.operator("visualization.create_ground_plane", text = 'Create a ground plane')

        row = self.layout.row()
        row.operator("visualization.set_recommended_render_settings", text = 'Set visual falloff distance in renders')

        row = self.layout.row()
        row.operator("visualization.set_compositor_fallof", text = 'Set visual falloff distance in renders')



        return 




    ## Import Trajectory
class VIEW3D_PT_import_trajectory_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_import_trajectory_subpanel'
    bl_parent_id = 'VIEW3D_PT_visualization_panel'  #have to define this if you use multiple panels
    bl_label = "Import trajectory"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        row = self.layout.row()
        row.label(text = "Imported trajectories are stored as keyframe animations.")
        row = self.layout.row()
        row.label(text = "Do not import trajectories into your main .blend file, make a backup first.")
        row = layout.row()
        row.operator("visualization.import_trajectory_sto",text = 'Import .sto trajectory')

        row = layout.row()
        row.prop(muskemo, "number_of_repetitions")

        row = layout.row()
        row.prop(muskemo, "fps")

        row = layout.row()
        row.prop(muskemo, "root_joint_name")

        row = layout.row()
        row.prop(muskemo, "forward_progression_coordinate")


        
        return    
    

