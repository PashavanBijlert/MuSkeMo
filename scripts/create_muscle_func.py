import bpy

def create_muscle (muscle_name):
    
    #inputs should be name, isglobal, point loc,(so I can remove the 4d thing) and body

    if new_musc:

        bpy.ops.curve.primitive_bezier_curve_add(align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), scale=(0, 0, 0)) 
        bpy.context.object.name = muscle_name #set the name
        obj = bpy.data.objects[muscle_name] #get a direct link to the newly named object
        curve = obj.data #get the curve
        curve.dimensions = '3D' #just in case, make it a 3D curve. Should already be 3D
        curve.splines.remove(curve.splines[0]) #remove the bezier spline
        spline = curve.splines.new(type='POLY') #add a poly spline

        ## define MuSkeMo type
        obj['MuSkeMo_type'] = 'MUSCLE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  


        ##
        obj['F_max'] = 0    #In Newtons
        obj.id_properties_ui('F_max').update(description = "Maximal isometric force of the muscle fiber (in N)")

        obj['pennation_angle'] = 0    #In degrees
        obj.id_properties_ui('pennation_angle').update(description = "Pennation angle (in degrees)")

        obj['optimal_fiber_length'] = 0    #In meters
        obj.id_properties_ui('optimal_fiber_length').update(description = "Optimal fiber length (in m)")

        obj['tendon_slack_length'] = 0    #In meters
        obj.id_properties_ui('tendon_slack_length').update(description = "Tendon slack length (in m)")



        ## add visualization radius via bevel, and driver 


        driver = obj.data.driver_add('bevel_depth').driver  #this adds a driver to obj.data.bevel_depth

        var = driver.variables.new()        #make a new variable
        var.name = 'viz_rad_var'            #give the variable a name

        var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

        var.targets[0].id = bpy.data.scenes['Scene']  #set the id to the active scene
        var.targets[0].data_path = "muskemo.muscle_visualization_radius" #get the driving property

        driver.expression = var.name  #set the expression, in this case only the name of the variable and nothing else
        obj.data.use_fill_caps = True 

        ### add texture here



    
    #Set curve to active object, for hook modifier
    curve = bpy.data.objects[muscle_name]
    spline = curve.data.splines[0] #get the spline

    ## set the point location        
    if not_new_musc: #add a point to the spline
        #add a point
        spline.points.add(1) 
        #get the point index
    last_point =  len(spline.points)-1  #index of the last point. If it's a new curve, this is 0. If not, then it's the point we just added
    
    spline.points[last_point].co = bpy.context.scene.cursor.location.to_4d()  ## change to user input using mouse

    ### hook point to body
    curve.select_set(True)
    bpy.context.view_layer.objects.active = curve  #make curve the active object

    modname = 'hook' + str(last_point) + '_' + active_obj.name #remember that active_obj is the body, not the current active object that was changed above within this script
    obj = curve
            
    obj.modifiers.new(name=modname, type='HOOK')
    obj.modifiers[modname].object = active_obj  #active_obj is the body       


    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.curve.select_all(action='DESELECT') 

    curve.data.splines[0].points[last_point].select = True


    bpy.ops.object.hook_assign(modifier = modname)


    for point in spline.points:
        point.select = False


    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.select_all(action='DESELECT')