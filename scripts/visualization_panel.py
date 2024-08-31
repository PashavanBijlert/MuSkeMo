import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import (nan, pi)


import numpy as np
import os
import csv

### The operators

class CreateGroundPlaneOperator(Operator):
    bl_idname = "visualization.create_ground_plane"
    bl_label = "Creates a 100m x 100m ground plane for visualizations"  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Creates a 100m x 100m ground plane for visualizations"
    
    def execute(self, context):
        
        #Add the ground plane to the scene collection
        bpy.context.view_layer.active_layer_collection =  bpy.context.view_layer.layer_collection



        bpy.ops.mesh.primitive_plane_add(size=100, enter_editmode=False, align='WORLD', location=(0, 0, 0), rotation=(-pi/2,0,0), scale=(1, 1, 1))
        bpy.context.active_object.name = 'Ground Plane'

        for obj in bpy.data.objects:
            obj.select_set(False)

        plane = bpy.data.objects['Ground Plane']


        mat = bpy.data.materials.new(name="Ground Plane Mat") 
        mat.use_nodes = True

        texbrick_node = mat.node_tree.nodes.new('ShaderNodeTexBrick')
        texbrick_node.offset = 0


        texbrick_node.squash = 0.5 #make the tiles square shaped
        texbrick_node.squash_frequency = 1


        texbrick_node.inputs['Color1'].default_value = (0.8, 0.8, 0.8, 1)  #make the squares the same colour
        texbrick_node.inputs['Color2'].default_value = (0.8, 0.8, 0.8, 1)

        #colour & sizing of the lines
        texbrick_node.inputs['Mortar'].default_value = (0.279, 0.002, 0.022, 1)

        texbrick_node.inputs['Scale'].default_value = 25  #makes the grid 1x1m if the plane is 100m
        texbrick_node.inputs['Mortar Size'].default_value = 0.0025  #line width

        bsdf_node = mat.node_tree.nodes.get('Principled BSDF')

        mat.node_tree.links.new(texbrick_node.outputs['Color'], bsdf_node.inputs['Base Color'])

        plane.data.materials.append(mat)

        return {"FINISHED"}

from .. import VIEW3D_PT_MuSkeMo  #the super class in which all panels will be placed

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
        row.operator("visualization.set_recommended_render_settings", text = 'Set recommended render settings')

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
    

