
# give Python access to Blender's functionality
import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

import os

from .. import VIEW3D_PT_MuSkeMo


class AddMusclepointOperator(Operator):
    bl_idname = "muscle.add_muscle_point"
    bl_label = "Adds a viapoint to the muscle (or creates a new muscle) at the 3D cursor location"  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Adds a viapoint to the muscle (or creates a new muscle) at the 3D cursor location"
    
    def execute(self, context):


        muscle_name = bpy.context.scene.muskemo.musclename

        colname = bpy.context.scene.muskemo.muscle_collection #name for the collection that will contain the hulls

        
        active_obj = bpy.context.active_object
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to


        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        body = sel_obj[0]
        body_name = body.name

        if 'MuSkeMo_type' in body:
            if 'BODY' != bpy.data.objects[body_name]['MuSkeMo_type']:
                self.report({'ERROR'}, "Selected object '" + body_name + "' is not a BODY. Muscle point addition cancelled")
                return {'FINISHED'} 
        else:
            self.report({'ERROR'}, "Selected object '" + body_name + "' was not an object created by MuSkeMo. Muscle point addition cancelled")
            return {'FINISHED'}      
        
        

        for obj in sel_obj:
            obj.select_set(False)

        from .create_muscle_func import create_muscle  #import muscle creation function

        point_position = bpy.context.scene.cursor.location
        create_muscle(muscle_name = muscle_name, point_position = point_position, 
                      collection_name=colname,
                          body_name = body_name)
        
        '''
        try: bpy.data.objects[muscle_name]  #throws an error if the muscle doesn't exist, creates it under except

        

        except:
            
            
            point_position = bpy.context.scene.cursor.location
            create_muscle(muscle_name = muscle_name, point_position = point_position,
                          body_name = body_name)

        else: #if the muscle does exist, add a point at the end
            

            
            point_position = bpy.context.scene.cursor.location
            create_muscle(muscle_name = muscle_name, point_position = point_position,
                          body_name = body_name.name)    
                
        '''        
        # restore saved state of selection
        bpy.context.view_layer.objects.active = active_obj
        for obj in sel_obj:
            obj.select_set(True)
        
        return {'FINISHED'}


class ReflectUnilateralMusclesOperator(Operator):
    bl_idname = "muscle.reflect_unilateral_muscles"
    bl_label = "Reflects unilateral muscles across desired reflection plane if they contain the right or left side string in the name."
    bl_description = "Reflects unilateral muscles across desired reflection plane if they contain the right or left side string in the name."
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        colname = muskemo.muscle_collection

        collection = bpy.data.collections[colname]

        muscles = [obj for obj in collection.objects if obj['MuSkeMo_type'] == 'MUSCLE']
        muscle_names = [obj.name for obj in muscles]

       
        right_string = muskemo.right_side_string
        left_string = muskemo.left_side_string

        reflection_plane = muskemo.reflection_plane

        for obj in (obj for obj in muscles if (
            (right_string in obj.name and obj.name.replace(right_string, left_string) not in muscle_names)) or
            (left_string in obj.name and obj.name.replace(left_string, right_string) not in muscle_names)):

            
            if right_string in obj.name: #if right_side_string is in the name, that's the current side of the object.
                  
                currentside = right_string #this is the side we DO have
                otherside = left_string #the side we are creating

            else: #if right_string is not in the name, the current side is the left side.
                currentside = left_string #this is the side we DO have
                otherside = right_string #the side we are creating

        
            new_obj = obj.copy()  #copy object
            new_obj.data = obj.data.copy() #copy object data
            new_obj.name = obj.name.replace(currentside,otherside) #rename to left
            
            collection.objects.link(new_obj)  #add to Muscles collection
            
            for point in new_obj.data.splines[0].points:   #reflect each point about z

                if reflection_plane == 'XY':
                    reflect_vect = Vector((1,1,-1,1)) #negative Z

                elif reflection_plane == 'YZ':
                    reflect_vect = Vector((-1,1,1,1)) #negative X
                
                elif reflection_plane == 'XZ':
                    reflect_vect = Vector((1,-1,1,1)) #negative Y
                
                point.co = point.co*reflect_vect

            ## set material
            oldmatname = new_obj.material_slots[0].name
            new_obj.data.materials.pop(index = 0)
            newmatname = oldmatname.replace(currentside,otherside)
            if newmatname in bpy.data.materials: #if the material already exists
                newmat = bpy.data.materials[newmatname]
                new_obj.material_slots[0].material = newmat

            else:
                from .create_muscle_material_func import create_muscle_material

                newmat = create_muscle_material(new_obj.name)

            for mod in new_obj.modifiers: #loop through all modifiers

                mod.name = mod.name.replace(currentside,otherside)

                if 'HOOK' == mod.type: #if it's a hook, hook the other side body
                    newbodyname = mod.object.name.replace(currentside,otherside)
                    

                    if newbodyname not in bpy.data.objects:# if the body doesn't exist
                        self.report({'WARNING'}, "BODY with the name '" + newbodyname + "' Does not exist. Create it using the body mirroring button. '" +new_obj.name  +  "' MUSCLE currently has unhooked points.")
                        mod.object = None
                    else:
                        mod.object = bpy.data.objects[newbodyname] #point the hook to the left side body
                        

                if 'NODES' == mod.type: #if it's a geometry nodes modifier (the simple muscle viz) 
                    mod.node_group.nodes['Set Material'].inputs['Material'].default_value = newmat   
                
                

        return {'FINISHED'}
    
class InsertMusclePointOperator(Operator):
    bl_idname = "muscle.insert_muscle_point"
    bl_label = "Inserts a point in the muscle after the user specified point (starting with 1)"
    bl_description = "Inserts a point in the muscle after the user specified point (starting with 1)"
    
    def execute(self, context):
        
        
        insert_after = bpy.context.scene.muskemo.insert_point_after
        
        muscle_name = bpy.context.scene.muskemo.musclename
        
        active_obj = bpy.context.active_object  #should be the body that you want to parent the point to
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to

        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        body = sel_obj[0]
        body_name = body.name

        if 'MuSkeMo_type' in body:
            if 'BODY' != bpy.data.objects[body_name]['MuSkeMo_type']:
                self.report({'ERROR'}, "Selected object '" + body_name + "' is not a BODY. Muscle point addition cancelled")
                return {'FINISHED'} 
        else:
            self.report({'ERROR'}, "Selected object '" + body_name + "' was not an object created by MuSkeMo. Muscle point addition cancelled")
            return {'FINISHED'}      


        for obj in sel_obj:
            obj.select_set(False)

        curve = bpy.data.objects[muscle_name]
        curve.select_set(True)
        bpy.context.view_layer.objects.active = curve  #make curve the active object
        bpy.ops.object.mode_set(mode='EDIT', toggle=False) 
        points = curve.data.splines[0].points

        bpy.ops.curve.select_all(action='DESELECT') # new

        points[insert_after-1].select = True
        points[insert_after].select = True
        bpy.ops.curve.subdivide()

        points[insert_after].co = bpy.context.scene.cursor.location.to_4d()

        bpy.ops.curve.select_all(action='DESELECT') # new
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False) 

        ### hook point to body
        obj = curve
        modnamelist = [x.name for x in obj.modifiers]
        
        p_number = 1                    
        modname = 'hook' + '_ins_point_' + str(p_number) + '_' + body_name
        while modname in modnamelist:
            p_number = p_number+1
            modname = 'hook' + '_ins_point_' + str(p_number) + '_' + body_name
        
                
        obj.modifiers.new(name=modname, type='HOOK')
        obj.modifiers[modname].object = body        

        

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT') 

        curve.data.splines[0].points[insert_after].select = True

          
        bpy.ops.object.hook_assign(modifier = modname)

        #bpy.ops.curve.select_all(action='DESELECT') 

        for point in curve.data.splines[0].points:
            point.select = False


        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
                        
        #Ensure the last two modifiers are always the Visualization and then the bevel modifier
        n_modifiers = len(obj.modifiers)
        obj.modifiers.move(n_modifiers-1, insert_after) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.

        ### restore selection state
        bpy.context.view_layer.objects.active = active_obj
        for obj in sel_obj:
            obj.select_set(True)        
                
        
        return {'FINISHED'}    
    
class UpdateMuscleVizRadiusOperator(Operator):
    bl_idname = "muscle.update_muscle_viz_radius"
    bl_label = "Update the muscle visualization radius of the muscle line segments (not the volumetric muscles)"
    bl_description = "Update the muscle visualization radius of the muscle line segments (not the volumetric muscles)"

    def execute(self, context):

        MuSkeMo_objects = [x for x in bpy.data.objects if 'MuSkeMo_type' in x]
        muscles = [x for x in MuSkeMo_objects if x['MuSkeMo_type']=='MUSCLE']
        
        muscle_visualization_radius = bpy.context.scene.muskemo.muscle_visualization_radius

        for muscle in muscles:
            muscle.modifiers[muscle.name + '_SimpleMuscleViz']['Socket_1']=  muscle_visualization_radius
            muscle.modifiers[muscle.name + '_SimpleMuscleViz'].node_group.interface_update(bpy.context)
        
        #update the merge by distance value based on the desired radius
        bpy.data.node_groups['SimpleMuscleNode'].nodes['Merge by Distance'].inputs['Distance'].default_value = muscle_visualization_radius * 0.13
        
        return {'FINISHED'}


class AssignWrappingOperator(Operator):
    bl_idname = "muscle.assign_wrapping"
    bl_label = "Assign wrapping to the select muscle, after the specified point index (starting at 1). Currently only cylinders supported."
    bl_description = "Assign wrapping to the select muscle, after the specified point index (starting at 1). Currently only cylinders supported."
    
    def execute(self, context):
        
        #insert_after = bpy.context.scene.muskemo.insert_point_after
        
        muscle_name = bpy.context.scene.muskemo.musclename
        
        active_obj = bpy.context.active_object  #should be the wrap object you want to assign
        sel_obj = bpy.context.selected_objects  #should be the wrap object you want to assign

        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one wrap geometry.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one wrap geometry.")
            return {'FINISHED'}
        
        wrap_obj = sel_obj[0]
        wrap_obj_name = wrap_obj.name

        if 'MuSkeMo_type' in wrap_obj:
            if 'WRAP' != bpy.data.objects[wrap_obj_name]['MuSkeMo_type']:
                self.report({'ERROR'}, "Selected object '" + wrap_obj_name + "' is not a WRAP. Wrap assignment cancelled.")
                return {'FINISHED'} 
        else:
            self.report({'ERROR'}, "Selected object '" + wrap_obj_name + "' was not an object created by MuSkeMo. Wrap assignment cancelled")
            return {'FINISHED'}      


        for obj in sel_obj:
            obj.select_set(False)

        


        ### everything below here can be a separate function
        ### inputs of the function should include all the inputs of the wrapping node as optional input
        #some settings for if I decide to rename node groups:
        cylinder_wrap_node_group_name =   'CylinderWrapNodeGroupShell' #this is used later in the script. Can update when new versions of the wrap node are made  
        wrap_nodefilename = 'muscle_wrapper_v5.blend'  


        if wrap_obj['wrap_type'].upper() == 'CYLINDER': #if it's a cylinder
            
            wrap_node_group_name = cylinder_wrap_node_group_name

            radius = wrap_obj['cylinder_radius']
            height = wrap_obj['cylinder_height']
            
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

                #set the cylinder radius
                wrap_node_tree_thisobj.interface.items_tree['Wrap Cylinder Radius'].default_value = radius

                #set the cylinder height
                wrap_node_tree_thisobj.interface.items_tree['Wrap Cylinder Height'].default_value = height

            ## create a modifier for the muscle and set this node group
            muscle_obj = bpy.data.objects[muscle_name]
            geonode_name = muscle_name + '_wrap' + wrap_obj_name
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
                muscle_obj.modifiers.move(n_modifiers-1, n_modifiers-3) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.
                
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

            
        else:
            self.report({'ERROR'}, "Only Cylinder wrap assignment is currently supported. Wrap assignment cancelled")
            return {'FINISHED'}


        return {'FINISHED'}

class VIEW3D_PT_muscle_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’

    
    
    bl_label = "Muscle panel"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_idname = 'VIEW3D_PT_muscle_panel'

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.label(text ='Muscle points are added at the 3D cursor location')
        row = self.layout.row()
        row.label(text = 'Shift + right click moves the 3D cursor to your mouse location')
        row = self.layout.row()
        row.label(text = 'You must select a body before attempting to add a muscle point')
        
        
        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Muscle Name")
        split.prop(muskemo, "musclename", text = "")
        
        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Muscle Collection")
        split.prop(muskemo, "muscle_collection", text = "")

        row = self.layout.row()

        row.operator("muscle.add_muscle_point", text="Add muscle point")
        
        self.layout.row()
        self.layout.row()
        
        row = self.layout.row()
        row.prop(muskemo, "insert_point_after")
        row.operator("muscle.insert_muscle_point", text="Insert muscle point")
        
        self.layout.row()
        row = self.layout.row()
       
        row.prop(muskemo, "muscle_visualization_radius")
        row.operator("muscle.update_muscle_viz_radius", text = "Update visualization radius")


        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.operator("muscle.reflect_unilateral_muscles", text="Reflect unilateral muscles")
        row = self.layout.row()

        # Split row into four columns with desired proportions
        split = row.split(factor=4/10)  # First split for left label
        split_left_label = split.column()
        split_left_label.label(text="Left Side String")

        split = split.split(factor=1/7)  # Second split for left input field
        split_left_input = split.column()
        split_left_input.prop(muskemo, "left_side_string", text="")

        split = split.split(factor=4/5)  # Third split for right label (remaining space)
        split_right_label = split.column()
        split_right_label.label(text="Right Side String")

        split_right_input = split.column()  # Last column for right input field
        split_right_input.prop(muskemo, "right_side_string", text="")

        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Reflection Plane')
        split.prop(muskemo, "reflection_plane", text = "")
        
        
class VIEW3D_PT_wrap_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_wrap_subpanel'
    bl_label = "Wrapping"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_muscle_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo


        row = self.layout.row()
        
        row.operator("muscle.assign_wrapping", text="Assign wrap object")



