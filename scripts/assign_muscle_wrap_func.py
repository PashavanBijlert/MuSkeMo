import bpy
import os

def assign_muscle_wrap(wrap_obj_name, muscle_name, self):
    #Inputs: wrap_obj_name (should exist)
    # muscle_name (should exist
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

        print('only cylinders supported currently')

        
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

        if wrap_obj['wrap_type'].upper() == 'CYLINDER':
            #set the cylinder radius
            #wrap_node_tree_thisobj.interface.items_tree['Wrap Cylinder Radius'].default_value = radius
            print('nothing')
            #set the cylinder height
            #wrap_node_tree_thisobj.interface.items_tree['Wrap Cylinder Height'].default_value = height

        else:
            print('only cylinders supported currently')               

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


        ## Add a driver
        # if parametric_wraps:

        #     #radius
        #     driver_str = 'modifiers["' + geonode_name +'"]["Socket_3"]' #wrap geonode cylinder radius socket
        #     driver = muscle_obj.driver_add(driver_str)

        #     var = driver.driver.variables.new()        #make a new variable
        #     var.name = geonode_name + '_' + wrap_obj_name + '_rad_var'            #give the variable a name

        #     #var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

        #     var.targets[0].id = bpy.data.objects[wrap_obj_name] #set the id to target object
        #     var.targets[0].data_path = 'modifiers["WrapObjMesh"]["Socket_1"]' #get the driving property

        #     driver.driver.expression = var.name

        #     #height
        #     driver_str = 'modifiers["' + geonode_name +'"]["Socket_4"]' #wrap geonode cylinder height socket
        #     driver = muscle_obj.driver_add(driver_str)

        #     var = driver.driver.variables.new()        #make a new variable
        #     var.name = geonode_name + '_' + wrap_obj_name + '_height_var'            #give the variable a name

        #     #var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

        #     var.targets[0].id = bpy.data.objects[wrap_obj_name] #set the id to target object
        #     var.targets[0].data_path = 'modifiers["WrapObjMesh"]["Socket_2"]' #get the driving property

        #     driver.driver.expression = var.name

    
        ## Here we crudely estimate what the pre-wrap index should be. 
        # #as a first guess for which two successive points span the wrap, we check which pair of points has the lowest total distance to the wrap object.
        ''' 
        wrap_obj_pos_glob = wrap_obj.matrix_world.translation

        total_dist_to_wrap = []  #this is the summed distance between current point and next point to the wrap object center.
        for ind, point in enumerate(muscle['path_points_data'][:-1]): #loop through n points-1
            
            #if the current point and the next point are attached to the same body, they can't span the wrap, so we set distance to inf
            if point['parent_frame'] == muscle['path_points_data'][ind+1]['parent_frame']:
                total_dist_to_wrap.append(np.inf)
            else:
                dpoint0_wrap = (point['global_position']-wrap_obj_pos_glob).length #distance of current point to wrap
                dpoint1_wrap = (muscle['path_points_data'][ind+1]['global_position']-wrap_obj_pos_glob).length #distance of next point to wrap
                
                #print(dpoint0_wrap)
                #rint(dpoint1_wrap)
                total_dist_to_wrap.append(dpoint0_wrap+dpoint1_wrap)
        
        index_of_pre_wrap_point = total_dist_to_wrap.index(min(total_dist_to_wrap)) +1 #get the index where the two points have minimal distance to the wrap, while also having different frames. Add 1 because the index count starts at 1
        geonode['Socket_6']  = index_of_pre_wrap_point #socket for setting the index

        # Track occurrences of index_of_pre_wrap_point
        pre_wrap_indices_count[index_of_pre_wrap_point] = pre_wrap_indices_count.get(index_of_pre_wrap_point, 0) + 1
        '''
    return {'FINISHED'}    
