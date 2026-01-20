import bpy
import os
import numpy as np

def assign_muscle_wrap(wrap_obj_name, muscle_name, self):
    #Inputs: wrap_obj_name (should exist, and be a MuSkeMo WRAP)
    # muscle_name (should exist, and be a MuSkeMo MUSCLE)
    #self (from the operator that calls this function)


    #some settings for if I decide to rename node group files:

    cylinder_wrap_node_group_name =   'CylinderWrapNodeGroupShell' #this is used later in the script. Can update when new versions of the wrap node are made  
    sphere_wrap_node_group_name = 'Whatever' #doesn't exist yet, but this is a placeholder to make the intended structure of this script clear
    wrap_nodefilename = 'muscle_wrapper_v7.blend'  

    wrap_obj = bpy.data.objects[wrap_obj_name]
    


    if wrap_obj['wrap_type'].upper() == 'CYLINDER': #if it's a cylinder
        
        wrap_node_group_name = cylinder_wrap_node_group_name

        radius = wrap_obj.modifiers['WrapObjMesh']['Socket_1']
        height = wrap_obj.modifiers['WrapObjMesh']['Socket_2']

    else: #not cylinder

        self.report({'ERROR'},'Only cylindric wrapping is currently supported.')
        return{'FINISHED'}

        
    ## load the node group template if necessary
    if wrap_node_group_name in bpy.data.node_groups: #if the node group template is already added to the scene
        wrap_node_tree_template = bpy.data.node_groups[wrap_node_group_name]
        
    else: #load the node group from the blend file wrap_nodefilename
    
        directory = os.path.dirname(os.path.realpath(__file__)) + '\\'  #realpath__file__ gets the path to the current script

        with bpy.data.libraries.load(directory + wrap_nodefilename) as (data_from, data_to):  #see blender documentation, this loads in data from another library/blend file
            data_to.node_groups = data_from.node_groups

        wrap_node_tree_template = [x for x in data_to.node_groups if wrap_node_group_name in x.name][0] #node tree template


    ## create the dedicated node group for this object if necessary
    wrap_node_group_name_thisobj = wrap_node_group_name + '_' + wrap_obj_name #the node group specific to this wrap object. So that we can reuse the node group for multiple muscles

    if wrap_node_group_name_thisobj in bpy.data.node_groups: #if the wrap node group for this specific wrap obj is already in the scene
        wrap_node_tree_thisobj = bpy.data.node_groups[wrap_node_group_name_thisobj]
        print('not copying')
    else: #if it's not already in the scene, copy it over from the template and create it using the wrap object's dimensions

        wrap_node_tree_thisobj = wrap_node_tree_template.copy()
        wrap_node_tree_thisobj.name = wrap_node_group_name_thisobj
        #set the wrap object
        wrap_node_tree_thisobj.interface.items_tree['Object'].default_value = wrap_obj #the wrap geometry

                  

    ## create a modifier for the muscle and set this node group
    muscle_obj = bpy.data.objects[muscle_name]
    geonode_name = muscle_name + '_wrap_' + wrap_obj_name
    
    if geonode_name in muscle_obj.modifiers: #if the object already has this wrap, we quit the code
        self.report({'ERROR'}, "Wrap object with name '" + wrap_obj_name + "' is already assigned to the MUSCLE with name '" + muscle_name + "'. Wrap assignment cancelled")
        return {"FINISHED"}

    else:
            
        #create a new geometry node for the curve, and set the node tree we just made
        geonode = muscle_obj.modifiers.new(name = geonode_name, type = 'NODES') #add modifier to curve
        geonode.node_group = bpy.data.node_groups[wrap_node_group_name_thisobj]
        #geonode['Socket_4'] = np.deg2rad(180)  #socket two is the volume input slider

        #Ensure the last two modifiers are always the Visualization and then the bevel modifier
        n_modifiers = len(muscle_obj.modifiers)

        if 'LiveLengthViewer' in muscle_obj.modifiers: #new modifiers are placed by default at the end. We want the wrap to be after the hooks, but before the visualization nodes
            #we have to account for the possibility of the LiveLengthViewer node being in the mod stack.
            muscle_obj.modifiers.move(n_modifiers-1, n_modifiers-4) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.
        
        else:
            muscle_obj.modifiers.move(n_modifiers-1, n_modifiers-3) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.
        
        ## Add the muscle to the target_muscles property of the wrap object
        if wrap_obj['target_muscles'] == 'not_assigned': #if the wrap currently has no wrap assigned, assign it
            wrap_obj['target_muscles'] = muscle_name + ';'

        else: #else, we add it to the end
            wrap_obj['target_muscles'] = wrap_obj['target_muscles'] +  muscle_name + ';'

    
        ## Here we crudely estimate what the pre-wrap index should be. 
        # #as a first guess for which two successive points span the wrap, we check which pair of points has the lowest total distance to the wrap object.
       
        # wrap_obj_pos_glob = wrap_obj.matrix_world.translation


        # ## get all the muscle points and their parent bodies
        # muscle_obj = bpy.data.objects[muscle_name]
        # modifier_list = [x.name for x in muscle_obj.modifiers if 'Hook'.casefold() in x.name.casefold()] #list of all the hook modifiers that are added to this muscle_obj

        # ### loop through points
        # point_positions = []
        # parent_bodies = []
        # for i in range(0, len(muscle_obj.data.splines[0].points)): #for each point
    
        # ### find which body each point is attached through, you have to loop through all the modifiers for this
        #     for h in range(len(modifier_list)):               #for each hook modifier that is added to this muscle_obj
        #         modifier = muscle_obj.modifiers[modifier_list[h]]  #modifier is the h'th modifier in the list
        #         for j in range(len(modifier.vertex_indices)): #vertex index = connected curve point, so for each connected curve point j, which starts counting at 0
        #             if i == modifier.vertex_indices[j]:       
        #                 body_name = modifier.object.name 
        #                 parent_bodies.append(body_name)  

        #                 point_pos_world = muscle_obj.matrix_world @ muscle_obj.data.splines[0].points[i].co.xyz
        #                 point_positions.append(point_pos_world)


        # total_dist_to_wrap = []  #this is the summed distance between current point and next point to the wrap object center.
                
        # for i, (position, parent) in enumerate(zip(point_positions[:-1], parent_bodies[:-1])): #loop through n points-1
        #     #if the current point and the next point are attached to the same body, they can't span the wrap, so we set distance to inf
        #     if parent == parent_bodies[i+1]:
        #         total_dist_to_wrap.append(np.inf)
        #     else:
        #         dpoint0_wrap = (position-wrap_obj_pos_glob).length #distance of current point to wrap
        #         dpoint1_wrap = (point_positions[i+1]-wrap_obj_pos_glob).length #distance of next point to wrap
                
        #         #
        #         total_dist_to_wrap.append(dpoint0_wrap+dpoint1_wrap)
        
        # index_of_pre_wrap_point = total_dist_to_wrap.index(min(total_dist_to_wrap)) +1 #get the index where the two points have minimal distance to the wrap, while also having different frames. Add 1 because the index count starts at 1
        # geonode['Socket_6']  = index_of_pre_wrap_point #socket for setting the index

        
        
    return {'FINISHED'}    
