# give Python access to Blender's functionality
import bpy
from mathutils import (Matrix, Vector)


from bpy.types import (Panel,
                        Operator,
                        )

from math import nan

import numpy as np

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed
    

#### operators





#### Panels

class VIEW3D_PT_mesh_tools_panel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_mesh_tools_panel'
    bl_label = "Mesh tools"  # found at the top of the Panel
    bl_context = "objectmode"

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        ### selected meshes

        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('MESH', layout)
        ###
        
                           
        
        row = self.layout.row()



class VIEW3D_PT_mesh_alignment_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_mesh_alignment_subpanel'
    bl_label = "Mesh alignment"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_mesh_tools_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo


        row = self.layout.row()

        selected = [x for x in context.selected_objects if x.type == 'MESH']
        if len(selected) != 2:
            layout.label(text="Select exactly 2 meshes")
            return

        # Target = object not chosen as Free
        target_name = [obj.name for obj in selected if obj.name != muskemo.icp_free_obj]
        target_label = target_name[0] if target_name else "N/A"
        
        row = layout.row()
        split = row.split(factor = 1/2)
        split.label(text = "Target Object (stationary):")
        
        box = split.box()
        box.label(text=target_label)
        
        row = layout.row()
        split = row.split(factor = 1/2)
        split.label(text = "Free Object (is moved):")
        split.prop(muskemo, "icp_free_obj", text = '')
        layout.prop(muskemo, "icp_max_iterations")
        layout.prop(muskemo, "icp_tolerance")
        layout.prop(muskemo, "icp_sample_ratio_start")
        layout.prop(muskemo, "icp_sample_ratio_end")
        layout.prop(muskemo, "icp_max_sample_ratio_after")
