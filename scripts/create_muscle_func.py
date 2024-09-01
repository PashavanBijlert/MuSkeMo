import bpy
from mathutils import Vector

def create_muscle (muscle_name, point_position, body_name,
                   collection_name = 'Muscles',
                   is_global=True, F_max = 0, pennation_angle = 0, 
                   optimal_fiber_length = 0, tendon_slack_length = 0,):
    
    #inputs should be name, isglobal, point loc,(so I can remove the 4d thing) and body
    #point position can be list, array or Vector. It gets cast to a Vector().to_4d() within the script

    if collection_name not in bpy.data.collections:
            bpy.data.collections.new(collection_name)
            
    coll = bpy.data.collections[collection_name] #Collection which will recieve the scaled  hulls

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
    #Make sure the "Muscles" collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]



    body = bpy.data.objects[body_name]     

    new_musc = True #assume the Muscle needs to be created anew
    if muscle_name in bpy.data.objects:  #if an object exists with this name
        if 'MUSCLE' == bpy.data.objects[muscle_name]['MuSkeMo_type']: #if the existing object is a MuSkeMo type MUSCLE
            new_musc = False  #new_musc is false, we add a point to the existing muscle


    


    if new_musc:  #if new_musc is true, we first create a new muscle

        #Add a bezier curve primitive, delete the spline, and replace the spline with a poly curve.
        #By doing it this way, it gets added to the active collection, which enables me to deal with collection allocation outside of the muscle creation function
                

        bpy.ops.curve.primitive_bezier_curve_add(align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), scale=(0, 0, 0)) 
        bpy.context.object.name = muscle_name #set the name
        obj = bpy.data.objects[muscle_name] #get a direct link to the newly named object
        curve = obj.data #get the curve
        curve.dimensions = '3D' #just in case, make it a 3D curve. Should already be 3D
        curve.use_path = False #new bezier curves automatically have path animations enabled. This triggers blender warnings for some reason
        curve.splines.remove(curve.splines[0]) #remove the bezier spline
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



        ## add visualization radius via bevel, and driver 
        #adding drivers like this works, but causes instability / crashes.

        '''
        driver = obj.data.driver_add('bevel_depth').driver  #this adds a driver to obj.data.bevel_depth

        var = driver.variables.new()        #make a new variable
        var.name = 'viz_rad_var'            #give the variable a name

        var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

        var.targets[0].id = bpy.data.scenes['Scene']  #set the id to the active scene
        var.targets[0].data_path = "muskemo.muscle_visualization_radius" #get the driving property

        driver.expression = var.name  #set the expression, in this case only the name of the variable and nothing else
        '''
        obj.data.bevel_depth = bpy.context.scene.muskemo.muscle_visualization_radius
        obj.data.use_fill_caps = True 

        ### seperate materials for each muscle so that they can be individually animated
        bpy.data.materials.new(name = muscle_name)
        
        mat = bpy.data.materials[muscle_name]
        mat.use_nodes = True
        
        matnode_tree =mat.node_tree
        matnode_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0
        matnode_tree.nodes.new(type = "ShaderNodeHueSaturation")
        
        #if blender type >4

        if bpy.app.version[0] <4: #if blender version is below 4
        
            nodename = 'Hue Saturation Value'

        else: #if blender version is above 4:  
            
            nodename = 'Hue/Saturation/Value'

        
        
        #the name should be different depending on Blender 3.0 or 4.0
        matnode_tree.nodes[nodename].inputs['Color'].default_value = (0.22, 0.00, 0.02, 1)
        matnode_tree.nodes[nodename].inputs['Saturation'].default_value = 1
        matnode_tree.links.new(matnode_tree.nodes[nodename].outputs['Color'], matnode_tree.nodes["Principled BSDF"].inputs['Base Color'])
        
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (0.22, 0.00, 0.02, 1)



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
    curve.select_set(True)
    bpy.context.view_layer.objects.active = curve  #make curve the active object

    modname = 'hook' + str(last_point) + '_' + body.name #
    obj = curve
            
    obj.modifiers.new(name=modname, type='HOOK')
    obj.modifiers[modname].object = body  #      


    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT') 

    curve.data.splines[0].points[last_point].select = True


    bpy.ops.object.hook_assign(modifier = modname)


    for point in spline.points:
        point.select = False


    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')

    
  