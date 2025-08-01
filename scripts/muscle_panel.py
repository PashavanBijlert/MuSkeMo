
# give Python access to Blender's functionality
import bpy

from math import nan
import numpy as np

from bpy.types import (Panel,
                        Operator,
                        )

import os
import csv
import time

from .. import VIEW3D_PT_MuSkeMo



class CreateNewMuscleOperator(Operator):
    bl_idname = "muscle.create_new_muscle"
    bl_label = "Creates a new muscle, with a single point the 3D cursor location. Select the body to parent the new point to, then press the button."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Creates a new muscle, with a single point the 3D cursor location. Select the body to parent the new point to, then press the button."
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo

        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to
        colname = muskemo.muscle_collection #the collection in which the muscle should be placed
        active_obj =  bpy.context.view_layer.objects.active
        
        muscle_name = muskemo.musclename

        #error if no name
        if not muscle_name:
            self.report({'ERROR'}, "You forgot to enter a name for the new muscle. Operation cancelled")
            return {'FINISHED'}
        #error if non unique name
        if muscle_name in bpy.data.objects:
            self.report({'ERROR'}, "An object with the name '" + muscle_name + "' already exists in the scene. Please choose a different (unique) name for the new muscle. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "No objects selected. Select the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) < 1):
            self.report({'ERROR'}, "The selected object was not created by MuSkeMo. Select the target body to parent the new muscle point to and try again. Operation cancelled")
            return {'FINISHED'}

        selected_bodies = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='BODY']

        
        # throw an error if no objects are selected     
        if (len(selected_bodies) < 1):
            self.report({'ERROR'}, "You didn't select a body. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}    

        body = selected_bodies[0]

        body_name = body.name

        
        for obj in sel_obj:
            obj.select_set(False)

        from .create_muscle_func import create_muscle  #import muscle creation function

        point_position = bpy.context.scene.cursor.location
        create_muscle(muscle_name = muscle_name, point_position = point_position, 
                      collection_name=colname,
                          body_name = body_name)
        
               
        # restore saved state of selection
        bpy.context.view_layer.objects.active = active_obj
        for obj in sel_obj:
            obj.select_set(True)

        muskemo.musclename = '' #reset the muscle name after creation    
        
        return {'FINISHED'}


class AddMusclepointOperator(Operator):
    bl_idname = "muscle.add_muscle_point"
    bl_label = "Adds a viapoint to the muscle selected muscle at the 3D cursor location. Select the target muscle, and a body to parent the new point to, then press the button."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Adds a viapoint to the muscle selected muscle at the 3D cursor location. Select the target muscle, and a body to parent the new point to, then press the button."
    
    def execute(self, context):

       
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to
        colname = bpy.context.scene.muskemo.muscle_collection #the collection in which the muscle should be placed
        active_obj =  bpy.context.view_layer.objects.active
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select a muscle, and the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select a muscle, and the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) < 2):
            self.report({'ERROR'}, "One or more of the selected objects was not created by MuSkeMo. Select a muscle, and the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}

        selected_bodies = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='BODY']

        # throw an error if two objects are selected     
        if (len(selected_bodies) > 1):
            self.report({'ERROR'}, "You selected two bodies. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_bodies) < 1):
            self.report({'ERROR'}, "You didn't select a body. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}    

        body = selected_bodies[0]

        body_name = body.name

        selected_muscles = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='MUSCLE']

        # throw an error if two objects are selected     
        if (len(selected_muscles) > 1):
            self.report({'ERROR'}, "You selected two muscles. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_muscles) < 1):
            self.report({'ERROR'}, "You didn't select a muscles. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}    

        muscle = selected_muscles[0]

        muscle_name = muscle.name  
        

        for obj in sel_obj:
            obj.select_set(False)

        from .create_muscle_func import create_muscle  #import muscle creation function

        point_position = bpy.context.scene.cursor.location
        create_muscle(muscle_name = muscle_name, point_position = point_position, 
                      collection_name=colname,
                          body_name = body_name)
        
               
        # restore saved state of selection
        bpy.context.view_layer.objects.active = active_obj
        for obj in sel_obj:
            obj.select_set(True)
        
        return {'FINISHED'}



    
class InsertMusclePointOperator(Operator):
    bl_idname = "muscle.insert_muscle_point"
    bl_label = "Inserts a point in the muscle after the user specified point (starting with 1)"
    bl_description = "Inserts a point in the muscle after the user specified point (starting with 1)"
    
    def execute(self, context):
        
        
        insert_after = bpy.context.scene.muskemo.insert_point_after
        
                
        active_obj = bpy.context.active_object  #should be the body that you want to parent the point to
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to

         # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select a muscle, and the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select a muscle, and the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) < 2):
            self.report({'ERROR'}, "One or more of the selected objects was not created by MuSkeMo. Select a muscle, and the target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}

        selected_bodies = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='BODY']

        # throw an error if two objects are selected     
        if (len(selected_bodies) > 1):
            self.report({'ERROR'}, "You selected two bodies. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_bodies) < 1):
            self.report({'ERROR'}, "You didn't select a body. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}    

        body = selected_bodies[0]

        body_name = body.name

        selected_muscles = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='MUSCLE']

        # throw an error if two objects are selected     
        if (len(selected_muscles) > 1):
            self.report({'ERROR'}, "You selected two muscles. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_muscles) < 1):
            self.report({'ERROR'}, "You didn't select a muscles. Select one muscle, and one target body to parent the new muscle point to. Operation cancelled")
            return {'FINISHED'}    

        muscle = selected_muscles[0]

        muscle_name = muscle.name  

        # throw an error if insert after is bigger or equal to the length of the curve
        if insert_after >= len(muscle.data.splines[0].points): 
            self.report({'ERROR'}, "You are trying to add a point at the end of the curve. Use the 'Add muscle point' button for that. Operation cancelled")
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

class CreateWrappingGeometryOperator(Operator):
    bl_idname = "muscle.create_wrapping_geometry"
    bl_label = "Create a wrapping geometry object which can be assigned to a muscle."
    bl_description = "Create a wrapping geometry object which can be assigned to a muscle."

    def execute(self, context):

        muskemo = bpy.context.scene.muskemo
        name = muskemo.wrap_geom_name
        wrap_geom_type = muskemo.wrap_geom_type
        collection_name = muskemo.wrap_geom_collection

        if not name:
            self.report({'ERROR'}, "Fill in a desired wrapping geometry name before creating one. Operation aborted")
            return {'FINISHED'} 
        
        if name in bpy.data.objects:
            self.report({'ERROR'}, "Object with the name '" + name + "' already exists in the Blender scene. Please choose a unique name for this wrapping geometry. Operation aborted")
            return {'FINISHED'} 
    
        from .create_wrapgeom_func import create_wrapgeom

        if wrap_geom_type == 'Cylinder':

            
            geomtype = 'Cylinder'

            dimensions = {}
            dimensions['radius'] = 0.05
            dimensions['height'] = 0.1

            create_wrapgeom(name, geomtype, collection_name,
                    parent_body='not_assigned', 
                    pos_in_global=[nan] * 3,
                    or_in_global_XYZeuler=[nan] * 3, 
                    or_in_global_quat=[nan] * 4,
                    pos_in_parent_frame=[nan] * 3,
                    or_in_parent_frame_XYZeuler=[nan] * 3, 
                    or_in_parent_frame_quat=[nan] * 4,
                    dimensions = dimensions,
                    )
            
        muskemo.wrap_geom_name = "" #reset the name after object creation.   
        return {'FINISHED'}
    

class AssignWrapGeomParentOperator(Operator):
    bl_idname = "muscle.assign_wrap_parent_body"
    bl_label = "Assigns a parent body to 1+ wrapping geometries. Select both the parent body and the wrapping geometries(s), then press the button."
    bl_description = "Assigns a parent body to 1+ wrapping geometries. Select both the parent body and the wrapping geometries(s), then press the button."
   
    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be the parent body and the wrap
        
        
              
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the parent body and the target wrapping geometry.")
            return {'FINISHED'}
        
              
                
        target_wraps = [s_obj for s_obj in sel_obj if s_obj.get('MuSkeMo_type') == 'WRAP']
        if (len(target_wraps) < 1):
            self.report({'ERROR'}, "You did not select any wrapping geometries. Operation cancelled.")
            return {'FINISHED'}

        
        non_wrap_objects = [s_obj for s_obj in sel_obj if s_obj not in target_wraps]  #get the object that's not the wrap
        if len(non_wrap_objects)<1:
            self.report({'ERROR'}, "You only selected wrapping geometries. You must also select one target body. Operation cancelled.")
            return {'FINISHED'}
        
        if len(non_wrap_objects)>1:
            self.report({'ERROR'}, "You selected more than one object that is not a wrapping geometry. You must select only wrapping geometries and one target body. Operation cancelled.")
            return {'FINISHED'}
        
        parent_body = non_wrap_objects[0] #if len is 1

        if parent_body.get('MuSkeMo_type') != 'BODY':
            self.report({'ERROR'}, "You did not select a target body. Select 1+ wrap objects and a target body. Operation cancelled.")
            return {'FINISHED'}
        
        
            
        ### if none of the previous scenarios triggered an error, set the parent body
        for wrap in target_wraps:
            wrap.parent = parent_body
                
            #this undoes the transformation after parenting
            wrap.matrix_parent_inverse = parent_body.matrix_world.inverted()

            wrap['parent_body'] = parent_body.name


            ### check if parent_body has a local frame, and if yes, compute wrap location in parent frame 
            if parent_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
                
                ## import functions euler angles and quaternions from matrix

                from .quaternions import quat_from_matrix
                from .euler_XYZ_body import euler_XYZbody_from_matrix

                frame = bpy.data.objects[parent_body['local_frame']]

                gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
                bRg = gRb.copy()
                bRg.transpose()
        
                frame_or_g = frame.matrix_world.translation    
             
                wrap_pos_g = wrap.matrix_world.translation #location of the wrap
                gRb_wrap = wrap.matrix_world.to_3x3() #gRb rotation matrix of wrap
                wrap_pos_in_parent = bRg @ (wrap_pos_g - frame_or_g) #location in parent of wrap
                                              
                b_R_wrapframe = bRg @ gRb_wrap #rotation matrix from wrap frame to parent frame - decompose this for orientation in parent
                
                wrap_or_in_parent_euler = euler_XYZbody_from_matrix(b_R_wrapframe) #XYZ body-fixed decomposition of orientation in parent
                wrap_or_in_parent_quat = quat_from_matrix(b_R_wrapframe) #quaternion decomposition of orientation in parent
                
                wrap['pos_in_parent_frame'] = wrap_pos_in_parent
                wrap['or_in_parent_frame_XYZeuler'] = wrap_or_in_parent_euler
                wrap['or_in_parent_frame_quat'] = wrap_or_in_parent_quat 
            
        return {'FINISHED'}    

class ClearWrapGeomParentOperator(Operator):
    bl_idname = "muscle.clear_wrap_parent_body"
    bl_label = "Clears the parent body assigned to selected wrapping geometrie(s). Select the target geometrie(s), then press the button."
    bl_description = "Clears the parent body assigned to selected wrapping geometrie(s). Select the target geometrie(s), then press the button."
    
    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be the parent body and the wrap

        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No wrap selected. Select the target wrap(s) and try again.")
            return {'FINISHED'}
            

        for wrap in sel_obj:
            
            if wrap.get('MuSkeMo_type') != 'WRAP':
                self.report({'ERROR'}, "Object with the name '" + wrap.name + "' is not a wrapping geometry. Skipping this object.")
                continue

            try: wrap.parent.name
            
            except: #throw an error if the wrap has no parent
                self.report({'ERROR'}, "Wrap geometry with the name '" + wrap.name + "' does not have a parent body. Skipping this wrap.")
                continue
            
                                
            ### if none of the previous scenarios triggered an error, clear the parent body
            
            
            #clear the parent, without moving the wrap
            parented_worldmatrix = wrap.matrix_world.copy() 
            wrap.parent = None
            wrap.matrix_world = parented_worldmatrix   
            
            wrap['parent_body'] = 'not_assigned'

            wrap['pos_in_parent_frame'] = [nan, nan, nan]
            wrap['or_in_parent_frame_XYZeuler'] = [nan, nan, nan]
            wrap['or_in_parent_frame_quat'] = [nan, nan, nan, nan]
            


        return {'FINISHED'}





class AssignWrappingOperator(Operator):
    bl_idname = "muscle.assign_wrapping"
    bl_label = "Assign selected wrapping to the active muscle, after the specified point index (starting at 1). Currently only cylinders supported."
    bl_description = "Assign selected wrapping to the active muscle, after the specified point index (starting at 1). Currently only cylinders supported."
    
    def execute(self, context):
        
        #insert_after = bpy.context.scene.muskemo.insert_point_after
        
        sel_obj = bpy.context.selected_objects  #should be the wrap object and the muscle you want to assign it to

        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select a muscle, and the wrap you want to assign to it. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select a muscle, and the wrap you want to assign to it. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) < 2):
            self.report({'ERROR'}, "One or more of the selected objects was not created by MuSkeMo. Select a muscle, and the wrap you want to assign to it. Operation cancelled")
            return {'FINISHED'}

        selected_muscles = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='MUSCLE']

        # throw an error if two objects are selected     
        if (len(selected_muscles) > 1):
            self.report({'ERROR'}, "You selected two muscles. Select one muscle, and the wrap you want to assign to it. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_muscles) < 1):
            self.report({'ERROR'}, "You didn't select a muscle. Select one muscle, and the wrap you want to assign to it. Operation cancelled")
            return {'FINISHED'}    

        muscle_obj = selected_muscles[0]
        muscle_name = muscle_obj.name
       
        selected_wraps = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='WRAP']

        # throw an error if two objects are selected     
        if (len(selected_wraps) > 1):
            self.report({'ERROR'}, "You selected two wraps. Select one muscle, and the wrap you want to assign to it. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_wraps) < 1):
            self.report({'ERROR'}, "You didn't select a wrap. Select one muscle, and the wrap you want to assign to it. Operation cancelled")
            return {'FINISHED'}    

        wrap_obj = selected_wraps[0]
        wrap_obj_name = wrap_obj.name
        

        for obj in sel_obj:
            obj.select_set(False)

        #############

        
        ### everything below here can be a separate function
        ### inputs of the function should include all the inputs of the wrapping node as optional input
        ##inputs: wrap_obj_name (get wrap obj using the name), muscle_name, ,

        #some settings for if I decide to rename node groups:


        cylinder_wrap_node_group_name =   'CylinderWrapNodeGroupShell' #this is used later in the script. Can update when new versions of the wrap node are made  
        sphere_wrap_node_group_name = 'Whatever' #doesn't exist yet, but this is a placeholder to make the intended structure of this script clear
        wrap_nodefilename = 'muscle_wrapper_v7.blend'  

        
        
        

        if wrap_obj['wrap_type'].upper() == 'CYLINDER': #if it's a cylinder
            
            wrap_node_group_name = cylinder_wrap_node_group_name

            radius = wrap_obj.modifiers['WrapObjMesh']['Socket_1']
            height = wrap_obj.modifiers['WrapObjMesh']['Socket_2']
            
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
                #wrap_node_tree_thisobj.interface.items_tree['Wrap Cylinder Radius'].default_value = radius

                #set the cylinder height
                #wrap_node_tree_thisobj.interface.items_tree['Wrap Cylinder Height'].default_value = height

            ## create a modifier for the muscle and set this node group
            
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
                    #we have to account for the possibility of the LiveLengthViewer node.
                    muscle_obj.modifiers.move(n_modifiers-1, n_modifiers-4) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.
                
                else:
                    muscle_obj.modifiers.move(n_modifiers-1, n_modifiers-3) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.
                
                ## Add the muscle to the target_muscles property of the wrap object
                if wrap_obj['target_muscles'] == 'not_assigned': #if the wrap currently has no wrap assigned, assign it
                    wrap_obj['target_muscles'] = muscle_name + ';'

                else: #else, we add it to the end
                    wrap_obj['target_muscles'] = wrap_obj['target_muscles'] +  muscle_name + ';'


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


class ClearWrappingOperator(Operator):
    bl_idname = "muscle.clear_wrapping"
    bl_label = "Clear selected wrapping from the active muscle. Select the wrap geometry, and ensure the muscle is filled into the panel."
    bl_description = "Clear selected wrapping from the active muscle. Select the wrap geometry, and ensure the muscle is filled into the panel."
    
    def execute(self, context):
                
        #insert_after = bpy.context.scene.muskemo.insert_point_after

        sel_obj = bpy.context.selected_objects  #should be the wrap object and the muscle you want to assign it to

        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select a muscle, and a wrap that is assigned to it. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select a muscle, and a wrap that is assigned to it. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) < 2):
            self.report({'ERROR'}, "One or more of the selected objects was not created by MuSkeMo. Select a muscle, and a wrap that is assigned to it. Operation cancelled")
            return {'FINISHED'}

        selected_muscles = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='MUSCLE']

        # throw an error if two objects are selected     
        if (len(selected_muscles) > 1):
            self.report({'ERROR'}, "You selected two muscles. Select one muscle, and a wrap that is assigned to it. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_muscles) < 1):
            self.report({'ERROR'}, "You didn't select a muscle. Select one muscle, and a wrap that is assigned to it. Operation cancelled")
            return {'FINISHED'}    

        muscle_obj = selected_muscles[0]
        muscle_name = muscle_obj.name
       
        selected_wraps = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='WRAP']

        # throw an error if two objects are selected     
        if (len(selected_wraps) > 1):
            self.report({'ERROR'}, "You selected two wraps. Select one muscle, and a wrap that is assigned to it. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_wraps) < 1):
            self.report({'ERROR'}, "You didn't select a wrap. Select one muscle, and a wrap that is assigned to it. Operation cancelled")
            return {'FINISHED'}    

        wrap_obj = selected_wraps[0]
        wrap_obj_name = wrap_obj.name
        

        for obj in sel_obj:
            obj.select_set(False)
  

        geonode_name = muscle_name + '_wrap_' + wrap_obj_name #name of the geometry node modifier

       
        if geonode_name not in muscle_obj.modifiers: #if the modifier is not in the modifier stack
            self.report({'ERROR'}, "The wrap object '" + wrap_obj_name + "' is not currently assigned to the muscle '" + muscle_name + "', so it cannot be cleared. Operation cancelled")
            return {'FINISHED'}

        #remove the modifier from the muscle
        muscle_obj.modifiers.remove(muscle_obj.modifiers[geonode_name])

        #update the target_muscles property of the wrapping geometry
        wrap_obj['target_muscles'] = wrap_obj['target_muscles'].replace(muscle_name + ';','') #remove the muscle and the delimiter

        if not wrap_obj['target_muscles']: #if the wrap now has no muscles assigned
            wrap_obj['target_muscles'] = 'not_assigned'


        return{'FINISHED'}



class SingleDOFLengthMomentArmOperator(Operator):
    bl_idname = "muscle.single_dof_length_moment_arm"
    bl_label = "Compute the length and moment arm of the active muscle for a single degree of freedom. You can choose to plot the data, or export it for later analyses."
    bl_description = "Compute the length and moment arm of the active muscle for a single degree of freedom. You can choose to plot the data, or export it for later analyses."
    
    
    def execute(self, context):

        time1 = time.time() 
        #insert_after = bpy.context.scene.muskemo.insert_point_after
        muskemo = bpy.context.scene.muskemo

        
        joint_1_dof = muskemo.joint_1_dof
        joint_1_ranges = muskemo.joint_1_ranges
        angle_step_size = muskemo.angle_step_size

        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to
        ###########
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select a muscle, and a joint you would like to rotate. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select a muscle, and a joint you would like to rotate. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) < 2):
            self.report({'ERROR'}, "One or more of the selected objects was not created by MuSkeMo. Select a muscle, and a joint you would like to rotate. Operation cancelled")
            return {'FINISHED'}

        selected_muscles = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='MUSCLE']

        # throw an error if two objects are selected     
        if (len(selected_muscles) > 1):
            self.report({'ERROR'}, "You selected two muscles. Select one muscle, and a joint you would like to rotate. Operation cancelled")
            return {'FINISHED'}

        # throw an error if no objects are selected     
        if (len(selected_muscles) < 1):
            self.report({'ERROR'}, "You didn't select a muscle. Select one muscle, and a joint you would like to rotate. Operation cancelled")
            return {'FINISHED'}    

        muscle = selected_muscles[0]
        muscle_name = muscle.name
       
        selected_joints = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='JOINT']

       
        # throw an error if no objects are selected     
        if (len(selected_joints) < 1):
            self.report({'ERROR'}, "You didn't select a joint. Select one muscle, and a joint you would like to rotate. Operation cancelled")
            return {'FINISHED'}    

        joint = selected_joints[0]
        active_joint_1 = joint.name
        

        for obj in sel_obj:
            obj.select_set(False)
        

        if joint_1_ranges[0] == joint_1_ranges[1]:
            self.report({'ERROR'}, "Joint 1 ranges should not be equal to each other. Operation cancelled")
            return {'FINISHED'}

        #######

        muscle_with_wrap = False
        if any(['wrap' in x.name.lower() for x in muscle.modifiers]):### if the muscle has a wrap modifier, use the slightly slower approach to calc the muscle length
    
            muscle_with_wrap= True

            #if we have wrapping objects, we up the resolution during moment arm computation for higher accuracy
            wrapmods = [x for x in muscle.modifiers if 'wrap' in x.name.lower()] #the wrap modifiers that this muscle has


            wrap_point_res = []
            wrap_obj_res = []

            for modifier in wrapmods:
                
                # wrap_point_res.append(modifier["Socket_10"]) #resolution of the wrapping curve
                # modifier["Socket_10"] = 250
                # modifier.show_render = not modifier.show_render  # Toggle visibility to refresh
                # modifier.show_render = not modifier.show_render

                wrapobj = modifier["Socket_2"]

                wrapobj.modifiers["WrapObjMesh"]

                if wrapobj['wrap_type'] == 'Cylinder':
                    #wrap object resolution
                    wrap_obj_res.append(wrapobj.modifiers["WrapObjMesh"].node_group.nodes['Cylinder'].inputs['Vertices'].default_value)
                    wrapmod = wrapobj.modifiers["WrapObjMesh"]
                    wrapmod.node_group.nodes['Cylinder'].inputs['Vertices'].default_value = 500
                    
                    wrapmod.show_render =not wrapmod.show_render# Toggle visibility to refresh
                    wrapmod.show_render =not wrapmod.show_render


            #wrap curve resolution doesn't seem to be updating before execution of the script?
            for area in context.screen.areas:
                area.tag_redraw() 
            bpy.context.view_layer.update()
                    


        min_range_angle1 = min(joint_1_ranges) #in degrees
        max_range_angle1 = max(joint_1_ranges)
     
        angle_1_range = np.arange(min_range_angle1, max_range_angle1+ angle_step_size, angle_step_size)  #we pad by one extra step on both sides so the gradient is correct for moment arm computation. We also add one step at the end because range always skips the last
        
        # Convert degrees to radians for each angle
        angle_1_range_rad = np.deg2rad(angle_1_range)

        from .euler_XYZ_body import matrix_from_euler_XYZbody
        from .compute_curve_length import compute_curve_length
        
        ## unit_vec will be multiplied by the instantaneous angle, resulting in a 3,1 vector that contains the angle and 2 zeros
        if joint_1_dof == 'Rx':
            unit_vec= np.array([1,0,0])

        elif joint_1_dof == 'Ry':
            unit_vec= np.array([0,1,0])
        
        elif joint_1_dof == 'Rz':
            unit_vec= np.array([0,0,1])


        length = []

        joint_wm_copy = joint.matrix_world.copy() #copy of the current position of the joint world matrix
        depsgraph = bpy.context.evaluated_depsgraph_get()#get the dependency graph

        for angle in angle_1_range_rad: #loop through each desired angle, set the joint in that orientation, compute the muscle length, then rotate the joint back.

            
            #Local frame rotation
            [gRb, bRg] = matrix_from_euler_XYZbody(angle*unit_vec) #rotation matrix for the desired angle
            
            wm = joint.matrix_world #current world matrix
            joint_gRb = wm.to_3x3() #
            translation = wm.translation

                       
            new_wm = joint_gRb@gRb #post multiply by the desired rotation to get a local rotation

            new_wm = new_wm.to_4x4()       
            new_wm.translation = translation
            joint.matrix_world = new_wm

            #Compute length in this position
            length.append(compute_curve_length(muscle_name, depsgraph))

            #reset to original position.  ### we reset the position each time. This is not costlier than simply progressing from min to max, as long as you don't update the despgraph after resetting the joint position.

            joint.matrix_world = joint_wm_copy

        #restore the wrapping resolutions
        if muscle_with_wrap:

            for i,modifier in enumerate(wrapmods):
                
                #wrap curve res
                # modifier["Socket_10"] = wrap_point_res[i]
                # wrapobj = modifier["Socket_2"]

                wrapobj.modifiers["WrapObjMesh"]

                if wrapobj['wrap_type'] == 'Cylinder':
                    #wrap object resolution
                    wrapobj.modifiers["WrapObjMesh"].node_group.nodes['Cylinder'].inputs['Vertices'].default_value = wrap_obj_res[i]

            #print(wrap_point_res)
            #print(wrap_obj_res)                

        length_data = {
            "plotname": muscle_name + "_length",
            "x_data": angle_1_range_rad,
            "y_data": length,
            "x_label": "Angle",
            "y_label": "Length",
            "x_unit": "rad",
            "y_unit": "m",
        }


        muscle['length_data'] = length_data
        
        moment_arm = [-x/y for x,y in zip(np.gradient(length), np.gradient(angle_1_range_rad))]


        generate_plot_bool = muskemo.generate_plot_bool
        plot_type = muskemo.plot_type
        convert_to_degrees = muskemo.convert_to_degrees

        if generate_plot_bool: #bool user switch
            print('plotting')

            from .create_2D_plot import create_2D_plot

            plot_data = length_data.copy()

            if plot_type == 'moment arm':
    
                plot_data['plotname'] = plot_data['plotname'].replace('length', 'moment_arm') 
                plot_data['y_label'] = plot_data['y_label'].replace('Length', 'Moment Arm')
                
                length = plot_data['y_data']
                angles_rad = plot_data['x_data']
                
                #moment arm is -dL / dphi. Sign is negative by convention
                moment_arm = [-x/y for x,y in zip(np.gradient(length), np.gradient(angles_rad))]
                plot_data['y_data'] = moment_arm
                

                #TO DO:
                #Separate plotting call where user sets their own plotting parameters
                #Resolution is getting changed and reset, but the wrap curve resolution appears not be active until the operator finishes


            if convert_to_degrees:
                
                plot_data['x_unit'] = 'degrees'
                plot_data['x_data'] = np.rad2deg(plot_data['x_data'])
            
            plot_lower_left = muskemo.plot_lower_left
            plot_dimensions = muskemo.plot_dimensions
            plot_font_scale = muskemo.plot_font_scale
            plot_tick_size = muskemo.plot_tick_size
            plot_curve_thickness = muskemo.plot_curve_thickness
            plot_ticknumber = muskemo.plot_ticknumber    

            create_2D_plot(
                plot_params=plot_data,
                x_ticks=plot_ticknumber[0],
                y_ticks=plot_ticknumber[1],
                plot_lower_left=tuple(plot_lower_left),  # Replace 'plot_origin' with 'plot_lower_left'
                plot_dimensions=tuple(plot_dimensions),  # Specify the visualization range as before
                font_scale=plot_font_scale,
                tick_size = plot_tick_size,
                ylim = (0,0), #xlim and ylim not set from the user preferences when first generating a plot
                xlim = (0,0), 
                curve_thickness = plot_curve_thickness,
            )

        export_data = muskemo.export_length_and_moment_arm


        if export_data: #if the user selects to export, but didn't set a directory, throw a warning and don't export data

            export_dir = muskemo.model_export_directory

            if not export_dir:
                self.report({'WARNING'}, "No export directory set, so muscle length and moment arm data was not be exported. Set the directory then try again.")
                export_data = False

        if export_data:
            
            delimiter = muskemo.delimiter
            filetype = muskemo.export_filetype

            filepath = export_dir + '/' + muscle_name + "_" + active_joint_1 + '_length_moment_arm_' +  "." + filetype

            '''
            sig_dig = muskemo.significant_digits
            number_format = muskemo.number_format  #can be 'e', 'g', or '8f'

            if number_format == 'g':
                number_format = f"{sig_dig}{number_format}"  #if it's g, we add the number of sig digits in front

            elif number_format == 'e':
                number_format = f"{sig_dig-1}{number_format}" #if it's e, we remove one digit (because e exports an extra digit)

            number_format = '.' + number_format
            '''

            # Construct headers
            headers = [
                f"{active_joint_1}_{joint_1_dof}(rad)", 
                "length(m)", 
                "moment_arm(m)"
            ]

            # Combine data into rows
            data = zip(angle_1_range_rad, length, moment_arm)

            # Write to CSV
            with open(filepath, mode='w', newline='') as file:
                writer = csv.writer(file, delimiter=delimiter)
                writer.writerow(headers)  # Write headers
                writer.writerows(data)    # Write data rows

        time2 = time.time()

        print(str(time2-time1))    

        return {"FINISHED"}
    
class Regenerate2DMusclePlotOperator(Operator):
    bl_idname = "muscle.regenerate_2d_plot"
    bl_label = "(Re)generate a muscle's length or moment arm plot using different plotting parameters"
    bl_description = "(Re)generate a muscle's length or moment arm plot using different plotting parameters"
    
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo

        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "No objects selected. Select one muscle to regenerate a plot. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one muscle to regenerate a plot. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) != 1):
            self.report({'ERROR'}, "The selected object was not created by MuSkeMo. Select one muscle to regenerate a plot. Operation cancelled")
            return {'FINISHED'}

        
        selected_muscles = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='MUSCLE']

        # throw an error if two objects are selected     
        if (len(selected_muscles) != 1):
            self.report({'ERROR'}, "The selected object was not a muscle.Select one muscle to regenerate a plot. Operation cancelled")
            return {'FINISHED'}

       

        muscle = selected_muscles[0]
        muscle_name = muscle.name


        if 'length_data' not in muscle:
            self.report({'ERROR'}, "Target muscle '" + muscle_name + "' does not have any length data associated to it yet which can be plotted. First create this in the Moment arms subpanel. Operation cancelled")
            return {'FINISHED'} 
        
        
        xlim = muskemo.xlim #input as tuple?
        ylim = muskemo.ylim
        plot_lower_left = muskemo.plot_lower_left
        plot_dimensions = muskemo.plot_dimensions
        plot_font_scale = muskemo.plot_font_scale
        plot_tick_size = muskemo.plot_tick_size
        plot_curve_thickness = muskemo.plot_curve_thickness
        plot_ticknumber = muskemo.plot_ticknumber
        plot_type = muskemo.plot_type
        convert_to_degrees = muskemo.convert_to_degrees


        plot_data = muscle['length_data'].to_dict()

        if plot_type == 'moment arm':

            plot_data['plotname'] = plot_data['plotname'].replace('length', 'moment_arm') 
            plot_data['y_label'] = plot_data['y_label'].replace('Length', 'Moment Arm')
            
            length = plot_data['y_data']
            angles_rad = plot_data['x_data']
            
            #moment arm is -dL / dphi. Sign is negative by convention
            moment_arm = [-x/y for x,y in zip(np.gradient(length), np.gradient(angles_rad))]
            plot_data['y_data'] = moment_arm
            

           

        if convert_to_degrees:
            
            plot_data['x_unit'] = 'degrees'
            plot_data['x_data'] = np.rad2deg(plot_data['x_data'])

        from .create_2D_plot import create_2D_plot

                
        create_2D_plot(
            plot_params=plot_data,
            x_ticks=plot_ticknumber[0],
            y_ticks=plot_ticknumber[1],
            plot_lower_left=tuple(plot_lower_left),  # Replace 'plot_origin' with 'plot_lower_left'
            plot_dimensions=tuple(plot_dimensions),  # Specify the visualization range as before
            font_scale=plot_font_scale,
            tick_size = plot_tick_size,
            xlim = tuple(xlim),
            ylim = tuple(ylim),
            curve_thickness = plot_curve_thickness,
        )


        return {'FINISHED'}    
    
class AddLiveLengthViewerNodeOperator(Operator):
    bl_idname = "muscle.add_live_length_viewer"
    bl_label = "View the muscle's instantaneous length in realtime"
    bl_description = "View the muscle's instantaneous length in realtime"
    
    
    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "No objects selected. Select one muscle to add a live length viewer to. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one muscle to add a live length viewer to. Operation cancelled")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        # throw an error if no objects are selected     
        if (len(muskemo_objects) != 1):
            self.report({'ERROR'}, "The selected object was not created by MuSkeMo. Select one muscle to add a live length viewer to. Operation cancelled")
            return {'FINISHED'}

        
        selected_muscles = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='MUSCLE']

        # throw an error if two objects are selected     
        if (len(selected_muscles) != 1):
            self.report({'ERROR'}, "The selected object was not a muscle. Select one muscle to add a live length viewer to. Operation cancelled")
            return {'FINISHED'}

       

        muscle = selected_muscles[0]

        

        from .live_length_viewer_node import add_live_length_viewer_node

        add_live_length_viewer_node(muscle)


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
        

        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('MUSCLE', layout)
        CreateSelectedObjRow('BODY', layout)

             
        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Muscle Name")
        split.prop(muskemo, "musclename", text = "")
        
        row = self.layout.row()
        row.operator("muscle.create_new_muscle", text="Create new muscle")

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

        
        row = self.layout.row()
        row.operator("muscle.add_live_length_viewer", text = "View length in realtime")

        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Muscle Collection")
        split.prop(muskemo, "muscle_collection", text = "")

         # Toggle button
        layout.prop(muskemo, "show_muscle_tooltips", text="Show Muscle Tooltips")

        if muskemo.show_muscle_tooltips:
            box = layout.box()
            
            
            row  = box.row()
            row.label(text = 'Shift + right click moves the 3D cursor to your mouse location')
            row  = box.row()
            row.label(text ='Muscle points are added at the 3D cursor location')
            row  = box.row()
            row.label(text = 'You must select a body to parent the muscle point to')
            row  = box.row()
            row.label(text = 'Points can be moved in edit mode (select muscle and hit TAB)')



        
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

        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('WRAP', layout)
        CreateSelectedObjRow('BODY', layout)
        CreateSelectedObjRow('MUSCLE', layout)

        row = self.layout.row()

        

        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Desired Geometry name')
        split.prop(muskemo, "wrap_geom_name", text = "")

        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Desired Geometry type')
        split.prop(muskemo, "wrap_geom_type", text = "")
        
        
        row = self.layout.row()
        row.operator("muscle.create_wrapping_geometry", text="Create wrapping geometry")

        row = self.layout.row()
        row.operator("muscle.assign_wrap_parent_body", text="Assign parent body")
        row.operator("muscle.clear_wrap_parent_body", text="Clear parent body")

        row = self.layout.row()
        row.operator("muscle.assign_wrapping", text="Assign muscle wrap")
        row.operator("muscle.clear_wrapping", text="Clear muscle wrap")


        row = self.layout.row()
       

        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Wrap Geometry Collection")
        split.prop(muskemo, "wrap_geom_collection", text = "")


class VIEW3D_PT_moment_arm_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo

    bl_idname = 'VIEW3D_PT_moment_arm_subpanel'
    bl_label = "Moment arms"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_muscle_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        row = self.layout.row()
        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('MUSCLE', layout)
        CreateSelectedObjRow('JOINT', layout)
        #row.operator("muscle.assign_wrapping", text="Assign wrap object")
        # row = self.layout.row()
        # split = row.split(factor = 1/2)
        # split.label(text = 'Active Joint 1')
        # split.prop(muskemo, "active_joint_1", text = "")

        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Joint 1 DOF')
        split.prop(muskemo, "joint_1_dof", text = "")

        row = self.layout.row()
        row.prop(muskemo, "joint_1_ranges")

        row = self.layout.row()
        row.prop(muskemo, "angle_step_size")

        row = self.layout.row()
        row.operator("muscle.single_dof_length_moment_arm",text = "Compute length & moment arm (1 DOF)")

        row = self.layout.row()
        row.prop(muskemo, "generate_plot_bool")
        row.prop(muskemo, "plot_type", text = "")


        row = self.layout.row()
        row.prop(muskemo, "export_length_and_moment_arm")

        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Model export directory')
        split.prop(muskemo, "model_export_directory", text = "")
        
        row = layout.row()
        row.operator("export.select_model_export_directory",text = 'Select export directory')


class VIEW3D_PT_plotting_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo

    bl_idname = 'VIEW3D_PT_plotting_subpanel'
    bl_label = "Plotting"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_muscle_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 

        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        from .selected_objects_panel_row_func import CreateSelectedObjRow
        CreateSelectedObjRow('MUSCLE', layout)

        
        row = self.layout.row()
        row.operator("muscle.regenerate_2d_plot", text = "(Re)generate a muscle plot")


        # Plot type
        row = layout.row()
        split = row.split(factor=1/2)
        split.label(text='Plot type')
        split.prop(muskemo, "plot_type", text="")

        # convert to degrees
        row = self.layout.row()
        row.prop(muskemo, 'convert_to_degrees')

        # Plot curve thickness
        row = layout.row()
        split = row.split(factor=1/2)
        split.label(text='Curve thickness')
        split.prop(muskemo, "plot_curve_thickness", text="")


        # X-axis limits
        row = layout.row()
        row.prop(muskemo, "xlim")
        

        # Y-axis limits
        row = layout.row()
        row.prop(muskemo, "ylim")

        # Plot lower left corner position
        row = layout.row()
        row.prop(muskemo, "plot_lower_left")

        # Plot dimensions
        row = layout.row()
        row.prop(muskemo, "plot_dimensions")

        # Font scale
        row = layout.row()
        split = row.split(factor=1/2)
        split.label(text='Font scale')
        split.prop(muskemo, "plot_font_scale", text="")

        # Tick size
        row = layout.row()
        split = row.split(factor=1/2)
        split.label(text='Tick size')
        split.prop(muskemo, "plot_tick_size", text="")

        # Axes ticks
        row = layout.row()
        row.prop(muskemo, "plot_ticknumber")

        
        

