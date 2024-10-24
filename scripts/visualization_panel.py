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

class SetCompositorBackgroundGradient(Operator):
    bl_idname = "visualization.set_compositor_background_gradient"
    bl_label = "Add nodes to the compositor to add a distance-based black gradient to de-emphasize the background."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Add nodes to the compositor to add a distance-based black gradient to de-emphasize the background."
    
    def execute(self, context):
        
        bpy.context.scene.view_layers["ViewLayer"].use_pass_mist = True

        bpy.context.scene.use_nodes = True

        nodes = bpy.data.scenes['Scene'].node_tree.nodes

        nodes.new("CompositorNodeInvert")

        if bpy.app.version[0] <4: #if blender version is below 4
        
            inv_nodename = 'Invert'

        else: #if blender version is above 4:  
            
            inv_nodename = 'Invert Color'

        nodes[inv_nodename].location = Vector((0,500))

        nodes.new("CompositorNodeMixRGB")
        nodes["Mix"].blend_type = "MULTIPLY"
        nodes["Mix"].location = Vector((300, -200))

        nodes.new("CompositorNodeViewer")
        nodes['Viewer'].location = Vector((500,-700))



        input = nodes[inv_nodename].inputs['Color']
        output =  nodes["Render Layers"].outputs['Mist']


        bpy.data.scenes['Scene'].node_tree.links.new(input,output)


        input = nodes["Mix"].inputs[1]
        output = nodes["Render Layers"].outputs['Image']
        bpy.data.scenes['Scene'].node_tree.links.new(input,output)




        input = nodes["Mix"].inputs[2]
        output = nodes[inv_nodename].outputs['Color']
        bpy.data.scenes['Scene'].node_tree.links.new(input,output)


        input = nodes["Composite"].inputs['Image']
        output = nodes["Mix"].outputs['Image']
        bpy.data.scenes['Scene'].node_tree.links.new(input,output)


        input = nodes["Viewer"].inputs['Image']
        bpy.data.scenes['Scene'].node_tree.links.new(input,output)

        return {'FINISHED'}

class SetRecommendedBlenderSettingsOperator(Operator):
    bl_idname = "muskemo.set_recommended_blender_settings"
    bl_label = "Set recommended Blender settings for using MuSkeMo. Sets view rotation to trackball, rotate around selected, and turns off object children filter in the outliner."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Set recommended Blender settings for using MuSkeMo. Sets view rotation to trackball, rotate around selected, and turns off object children filter in the outliner."
    
    def execute(self, context):

        bpy.context.preferences.inputs.view_rotate_method = 'TRACKBALL' #set rotation method to trackball
        bpy.context.preferences.inputs.use_rotate_around_active = True  #set rotate around selected
        
        bpy.ops.wm.save_userpref() #save these settings

        #Toggle object children filter off in all outliners
        for screen in bpy.data.screens:
            # Loop through all the areas in each screen
            for area in screen.areas:
                if area.type == 'OUTLINER':  # Check if the area is an Outliner
                    for space in area.spaces:
                        if space.type == 'OUTLINER':
                            # Set 'use_filter_children' to False
                            space.use_filter_children = False

        return {'FINISHED'}
        


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
        row.operator("muskemo.set_recommended_blender_settings", text = 'Set recommended Blender settings')


        row = self.layout.row()
        row.operator("visualization.set_compositor_background_gradient", text = 'Set black background gradient for renders')



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

        row = layout.row()
        row.prop(muskemo, "in_degrees")
               
        return    
    

   ## Default colors
class VIEW3D_PT_default_colors_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_default_colors_subpanel'
    bl_parent_id = 'VIEW3D_PT_visualization_panel'  #have to define this if you use multiple panels
    bl_label = "Default colors"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        row = layout.row()
        row.prop(muskemo, "muscle_color")

        row = layout.row()
        row.prop(muskemo, "bone_color")

        row = layout.row()
        row.prop(muskemo, "joint_color")

        row = layout.row()
        row.prop(muskemo, "contact_color")

        row = layout.row()
        row.prop(muskemo, "marker_color")

        row = layout.row()
        row.prop(muskemo, "geom_primitive_color")

        row = layout.row()
        row.prop(muskemo, "wrap_geom_color")

        