import bpy
from mathutils import Vector
import numpy as np

def create_muscle (muscle_name, point_position, body_name = '',
                   collection_name = 'Muscles',
                   is_global=True, F_max = 0.0, pennation_angle = 0.0, 
                   optimal_fiber_length = 0.0, tendon_slack_length = 0.0,):
    
    #inputs should be name, isglobal, point loc,(so I can remove the 4d thing) and body
    #point position can be list, array or Vector. It gets cast to a Vector().to_4d() within the script

    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        #If the collection didn't even exist yet, we're probably starting from scratch. Turn off the object children filter to help the user.
        bpy.ops.muskemo.set_child_visibility_outliner()
            
            
    coll = bpy.data.collections[collection_name] #Collection which will recieve the scaled  hulls

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
    #Make sure the "Muscles" collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]


    new_musc = True #assume the Muscle needs to be created anew
    if muscle_name in bpy.data.objects:  #if an object exists with this name
        if 'MUSCLE' == bpy.data.objects[muscle_name]['MuSkeMo_type']: #if the existing object is a MuSkeMo type MUSCLE
            new_musc = False  #new_musc is false, we add a point to the existing muscle

 


    if new_musc:  #if new_musc is true, we first create a new muscle


        if muscle_name in bpy.data.curves:
            #If a muscle was deleted, its curve data can remain until restarting the scene.
            #If the user tries to recreate a muscle with the same name, the existing curve data will cause a conflict. 
            #Here we delete it manually
            old_curve = bpy.data.curves[muscle_name]
            bpy.data.curves.remove(old_curve)

        

        bpy.data.curves.new(muscle_name, type='CURVE') #create new curve data
        curve = bpy.data.curves[muscle_name] #direct reference to the curve

        #create a new object using the curve data
        bpy.data.objects.new(muscle_name, curve)
        
        obj = bpy.data.objects[muscle_name] #get a direct link to the newly named object
        coll.objects.link(obj)

        curve.dimensions = '3D' #make it a 3D curve.
        curve.use_path = False #unnecessary but just in case
        spline = curve.splines.new(type='POLY') #add a poly spline
        
        

             


        ## define MuSkeMo type
        obj['MuSkeMo_type'] = 'MUSCLE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  


        ##
        obj['F_max'] = F_max    #In Newtons
        obj.id_properties_ui('F_max').update(description = "Maximal isometric force of the muscle fiber (in N)")

        obj['pennation_angle'] = pennation_angle    #In degrees
        obj.id_properties_ui('pennation_angle').update(description = "Pennation angle (in degrees)")

        obj['optimal_fiber_length'] = optimal_fiber_length    #In meters
        obj.id_properties_ui('optimal_fiber_length').update(description = "Optimal fiber length (in m)")

        obj['tendon_slack_length'] = tendon_slack_length    #In meters
        obj.id_properties_ui('tendon_slack_length').update(description = "Tendon slack length (in m)")

        '''

        ## add visualization radius via bevel, and driver 
        #adding drivers like this works, but causes instability / crashes.

        
        driver = obj.data.driver_add('bevel_depth').driver  #this adds a driver to obj.data.bevel_depth

        var = driver.variables.new()        #make a new variable
        var.name = 'viz_rad_var'            #give the variable a name

        var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

        var.targets[0].id = bpy.data.scenes['Scene']  #set the id to the active scene
        var.targets[0].data_path = "muskemo.muscle_visualization_radius" #get the driving property

        driver.expression = var.name  #set the expression, in this case only the name of the variable and nothing else
       
        
        ### adding it as curve depth works nicely, but turns the curve into geometry, which doesn't work with geometry nodes wrapping
        obj.data.bevel_depth = bpy.context.scene.muskemo.muscle_visualization_radius
        obj.data.use_fill_caps = True 
        '''
        ### seperate materials for each muscle so that they can be individually animated

        from .create_muscle_material_func import create_muscle_material

        mat = create_muscle_material(muscle_name)

        obj.data.materials.append(mat)
      
        ### add simple muscle visualization modifier
        if "SimpleMuscleNode" not in bpy.data.node_groups:
            from .simple_muscle_viz_node import (create_simple_muscle_node_group, add_simple_muscle_node)
            create_simple_muscle_node_group() #create the node group
            

        else:
            from .simple_muscle_viz_node import add_simple_muscle_node

        add_simple_muscle_node(muscle_name)    



        ### add bevel modifier

      
        obj.modifiers.new(muscle_name + '_bevelmod','BEVEL')
        modifier = obj.modifiers[muscle_name + '_bevelmod']
        modifier.segments = 5
        modifier.angle_limit = np.deg2rad(50)




    #Get the curve and the spline
    curve = bpy.data.objects[muscle_name]
    spline = curve.data.splines[0] #get the spline

    ## set the point location        
    if not new_musc: #add a point to the spline
        #add a point
        spline.points.add(1) 
        #get the point index
    
    last_point =  len(spline.points)-1  #index of the last point. If it's a new curve, this is 0. If not, then it's the point we just added
    
    spline.points[last_point].co = Vector(point_position).to_4d()  ## co has has input a 4d vector (x,y,z,1).

    ### hook point to body
    modname = 'hook' + str(last_point) + '_' + body_name #
    obj = curve
            
    obj.modifiers.new(name=modname, type='HOOK')
    obj.modifiers[modname].vertex_indices_set([last_point])#setting this only updates if you either toggle in and out of edit mode (slow) or add the body afterwards
    
    if body_name: #if the user specifies a body name that exists
        if body_name in bpy.data.objects:
            body = bpy.data.objects[body_name]     
            obj.modifiers[modname].object = body  #      

    #Ensure the last two modifiers are always the Visualization and then the bevel modifier
    n_modifiers = len(obj.modifiers)
    obj.modifiers.move(n_modifiers-1, last_point) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.


  