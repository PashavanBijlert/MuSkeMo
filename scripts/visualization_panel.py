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


        

class ConvertMusclesToVolumetricViz(Operator):
    bl_idname = "visualization.convert_muscles_to_volumetric"
    bl_label = "Use volumetric visualizations for all the muscles in the model."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Use volumetric visualizations for all the muscles in the model. "
    bl_options = {"UNDO"} #enable undoing

    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        specific_tension = 300000  #convert to muskemoprop

        coll_name = muskemo.muscle_collection
        coll = bpy.data.collections[coll_name]

        
        directory = os.path.dirname(os.path.realpath(__file__)) + '\\'  #realpath__file__ gets the path to the current script

        nodefilename = 'muscle_geonodes_v6.blend'

       
        with bpy.data.libraries.load(directory + nodefilename) as (data_from, data_to):  #see blender documentation, this loads in data from another library/blend file
            data_to.node_groups = data_from.node_groups

            
        node_tree = [x for x in data_to.node_groups if 'MuscleNode' in x.name][0] #node tree template

        for muscle in coll.objects:

            if muscle.get('MuSkeMo_type')== 'MUSCLE':
                muscle_name = muscle.name #eg cfl1_r
                
                if muscle_name + '_VolumetricMuscleViz' in muscle.modifiers: #if it already has volumetric muscles, skip this muscle
                    continue
                # Get modifier index in stack
                mod_index = list(muscle.modifiers).index(muscle.modifiers[muscle_name + '_SimpleMuscleViz'])

                ## remove simple muscle viz node
                muscle.modifiers.remove(muscle.modifiers[muscle_name + '_SimpleMuscleViz'])
                                
                ## get muscle volume
                vol = muscle['F_max']/specific_tension*muscle['optimal_fiber_length']
                
                #
                node_tree_name = muscle_name + '_musclenodetree'

                if node_tree_name not in bpy.data.node_groups: #if the node group doesn't exist (creating it for the first ime)
                    #set up the muscle node tree and set volume 
                    node_tree_copy = node_tree.copy() #copy of node_tree from the template
                    node_tree_copy.name = node_tree_name
                    
                    #node_tree_copy.nodes['Muscle volume'].outputs['Value'].default_value = vol #set volume
                    #print(node_tree_copy)
                    #node_tree_copy.nodes['Group Input'].outputs['MuscleVolume'].default_value = vol #set volume
                    #node_tree_copy.nodes['MuscleVolume'].inputs[0].default_value = vol #set volume
                        
                    ### set the existing muscle material in the node
                    mat = bpy.data.materials[muscle_name]
                    node_tree_copy.nodes['Set muscle material'].inputs['Material'].default_value = mat

                else: #if the node tree already exists (multiple successive conversions from tube to volumetric and back)
                    node_tree_copy = bpy.data.node_groups[node_tree_name]
                    
                #create a new geometry node for the muscle, and set the node tree we just made
                geonode = muscle.modifiers.new(name = muscle_name + '_VolumetricMuscleViz', type = 'NODES') #add modifier to muscle
                geonode.node_group = node_tree_copy
                geonode['Socket_2'] = vol  #socket two is the volume input slider
                #sockets are the user input sliders in the modifier. They have a name (geonode['Socket_2_attribute_name']), but you can't access this easily nor can you iterate through sockets to check, so hardcoding it as the simplest solution
                
                #Ensure the last modifier is the bevel modifier
                n_modifiers = len(muscle.modifiers)
       
                muscle.modifiers.move(n_modifiers-1, mod_index) #new modifiers are placed at the end, place it at where the original visualization modifier was.
        return {"FINISHED"}
    


class ConvertMusclesToSimpleViz(Operator):
    bl_idname = "visualization.convert_muscles_to_simple_tube"
    bl_label = "Use simple tube visualizations for all the muscles in the model."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Use simple tube visualizations for all the muscles in the model."
    bl_options = {"UNDO"} #enable undoing

    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        
        coll_name = muskemo.muscle_collection
        coll = bpy.data.collections[coll_name]

        ### add simple muscle visualization modifier
        if "SimpleMuscleNode" not in bpy.data.node_groups: #if the node group doesn't exist
            from .simple_muscle_viz_node import (create_simple_muscle_node_group, add_simple_muscle_node)
            create_simple_muscle_node_group() #create the node group
            

        else:
            from .simple_muscle_viz_node import add_simple_muscle_node
 
        
        for muscle in coll.objects:

            if muscle.get('MuSkeMo_type')== 'MUSCLE':
                muscle_name = muscle.name #eg cfl1_r
                
                if muscle_name + '_SimpleMuscleViz' in muscle.modifiers: #if it already has simple tube muscles, skip this muscle
                    continue

                # Get modifier index in stack
                mod_index = list(muscle.modifiers).index(muscle.modifiers[muscle_name + '_VolumetricMuscleViz'])

                ## remove simple muscle viz node
                muscle.modifiers.remove(muscle.modifiers[muscle_name + '_VolumetricMuscleViz'])         

                ## add the node group

                add_simple_muscle_node(muscle_name)
                
                #Ensure the last modifier is the bevel modifier
                n_modifiers = len(muscle.modifiers)
       
                muscle.modifiers.move(n_modifiers-1, mod_index) #new modifiers are placed at the end, placs are placed at the end, place it at where the original visualization modifier was.
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
        ### volumetric muscles
        row = self.layout.row()
        split = row.split(factor = 1/4)
        split.label(text = "Muscle collection")
        split = split.split(factor = 1/3)
        split.prop(muskemo, "muscle_collection", text = "")
        split.prop(muskemo, "specific_tension")

        row = self.layout.row()
        row.operator("visualization.convert_muscles_to_volumetric",text = 'Convert to volumetric muscles')

        row = self.layout.row()
        row.operator("visualization.convert_muscles_to_simple_tube",text = 'Convert to simple (tube) muscles')



        ### ground plane
        row = self.layout.row()
        row = self.layout.row()
        row = self.layout.row()
        row.operator("visualization.create_ground_plane", text = 'Create a ground plane')

        row = self.layout.row()
        #row.operator("visualization.set_recommended_render_settings", text = 'Set recommended render settings')

        
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
        split = row.split(factor = 1/2)
        split.label(text = "Root joint name")
        split.prop(muskemo, "root_joint_name", text = '')

        row = layout.row()
        split = row.split(factor = 1/2)
        split.label(text = "Forward progression coordinate")
        split.prop(muskemo, "forward_progression_coordinate", text = '')

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

        