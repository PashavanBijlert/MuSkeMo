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


class MeshAlignnmentICPPointToPlaneOperator(Operator):
    bl_idname = "mesh.align_icp_point_to_plane"
    bl_label = "Rigid mesh alignment using iterative closest point - point to plane. Select two meshes, designate the free object, and then press the button."
    bl_description = "Rigid mesh alignment using iterative closest point - point to plane. Select two meshes, designate the free object, and then press the button."
    bl_options = {"UNDO"} #enable undoing
    
    def execute(self, context):
        


        sel_obj = [x for x in bpy.context.selected_objects if x.type == 'MESH']  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Less than 2 meshes selected. Select exactly 2 meshes, and try again")
            return {'FINISHED'}
        
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "More than 2 meshes selected. Select exactly 2 meshes, and try again")
            return {'FINISHED'}
        
        muskemo = bpy.context.scene.muskemo

        free_obj = bpy.data.objects[muskemo.icp_free_obj]
        target_obj = [obj for obj in sel_obj if obj!=free_obj][0] #target obj is the other selected object


        alignment_mode = muskemo.icp_alignment_mode


        if alignment_mode == 'Selected mesh portions':

            if not [v for v in  free_obj.data.vertices if v.select]:
                self.report({'ERROR'}, free_obj.name + "Free Object has no selected portions. Select the mesh, hit TAB to go into edit mode, and then select the mesh portion you would like to align. Alternatively, align the entire mesh.")
                return {'FINISHED'}

            if not [v for v in  target_obj.data.vertices if v.select]:
                self.report({'ERROR'}, target_obj.name + " has no selected portions. Select the mesh, hit TAB to go into edit mode, and then select the mesh portion you would like to align. Alternatively, align the entire mesh.")
                return {'FINISHED'}

        max_iter = muskemo.icp_max_iterations
        tol = muskemo.icp_tolerance
        sample_ratio_start = muskemo.icp_sample_ratio_start
        sample_ratio_end = muskemo.icp_sample_ratio_end
        max_sample_ratio_after = muskemo.icp_max_sample_ratio_after

        from .icp_point_to_plane import point_to_plane_icp_subsample

        point_to_plane_icp_subsample(free_obj = free_obj,
                                     target_obj=  target_obj,
                                     max_iterations=max_iter,
                                     tolerance=tol,
                                     sample_ratio_start=sample_ratio_start,
                                     sample_ratio_end=sample_ratio_end,
                                    sample_ratio_ramp_iters = max_sample_ratio_after,
                                    alignment_mode = alignment_mode)
        
        return {'FINISHED'}


class MeshIntersectionCheckerOperator(Operator):
    bl_idname = "mesh.intersection_checker"
    bl_label = "Select 2 meshes and check for intersections between them."
    bl_description = "Select 2 meshes and check for intersections between them."

    result_message: bpy.props.StringProperty(default="")

    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be two meshes

        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "No objects selected. You must select 2 meshes to check whether they are intersecting.")
            return {'FINISHED'}
        
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. You must select 2 meshes to check whether they are intersecting.")
            return {'FINISHED'}
        
        sel_meshes = [x for x in sel_obj if x.type == 'MESH'] #check that the objects are all meshes

        if len(sel_meshes)==1: #If only one object is a mesh
            self.report({'ERROR'}, "Only one of the two objects is a MESH. The mesh intersection checker only works on meshes. Select 2 meshes and try again.")
            return {'FINISHED'}
        

        if len(sel_meshes)==0: #If no mesh
            self.report({'ERROR'}, "Neither of the selected objects is a MESH. The mesh intersection checker only works on meshes. Select 2 meshes and try again.")
            return {'FINISHED'}


        #### check for intersections

        from .two_object_intersection_func import check_bvh_intersection
        #Get the dependency graph
        depsgraph = bpy.context.evaluated_depsgraph_get()

        mesh_1_name = sel_meshes[0].name
        mesh_2_name = sel_meshes[1].name

        intersections = check_bvh_intersection(mesh_1_name, mesh_2_name, depsgraph)
        #The output is pairs of intersecting polygons (if indeed these exist)

                
        if intersections:
            self.result_message = mesh_1_name + " and " + mesh_2_name + " intersect with each other."
        else:
            self.result_message = mesh_1_name + " and " + mesh_2_name + " do not intersect with each other."

        # Show popup after setting the message
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.result_message)

    def invoke(self, context, event):
        
        return self.execute(context)
    


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
        row = self.layout.row()
        row.operator("mesh.intersection_checker", text = "Check for mesh intersections")



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
        
        row = layout.row()
        row = layout.row()
        row = layout.row()
        layout.operator("mesh.align_icp_point_to_plane", text = 'Align Meshes')


        row = layout.row()
        row = layout.row()
        row = layout.row()
        layout.prop(muskemo, "icp_alignment_mode", expand = True)

        layout.prop(muskemo, "icp_max_iterations")
        layout.prop(muskemo, "icp_tolerance")
        layout.prop(muskemo, "icp_sample_ratio_start")
        layout.prop(muskemo, "icp_sample_ratio_end")
        layout.prop(muskemo, "icp_max_sample_ratio_after")
