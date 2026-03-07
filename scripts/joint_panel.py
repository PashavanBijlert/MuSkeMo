# give Python access to Blender's functionality
import bpy
from mathutils import (Matrix, Vector)


from bpy.types import (Panel,
                        Operator,
                        )

from math import nan

import numpy as np

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed
    
class CreateNewJointOperator(Operator):
    bl_idname = "joint.create_new_joint"
    bl_label = "creates a new joint at the origin"
    bl_description = "creates a new joint at the origin"
    
    def execute(self,context):
        
        rad = bpy.context.scene.muskemo.jointsphere_size #axis length, in meters
        name = bpy.context.scene.muskemo.jointname  #name of the object
        
        colname = bpy.context.scene.muskemo.joint_collection #name for the collection that will contain the hulls
        
        
        if not name:
            self.report({'ERROR'}, "You didn't type a joint name. Type the desired name into the panel and try again. Operation cancelled.")
            return {'FINISHED'}

        
        try: bpy.data.objects[name] #check if the joint exists
        
        except:  #if not, create it
            from .create_joint_func import create_joint
                       
            create_joint(name = name, radius = rad, collection_name = colname,)
            
        else:
            
            self.report({'ERROR'}, "Object with the name " + name + " already exists, please choose a different (unique) name")

            
        bpy.context.scene.muskemo.jointname = '' #reset joint name prop
        
        return {'FINISHED'}


    
class UpdateCoordinateNamesOperator(Operator):
    bl_idname = "joint.update_coordinate_names"
    bl_label = "Updates the coordinate names of the joint. Type the desired coordinate names into fields, select the target joint, then press the button"
    bl_description = "Updates the coordinate names of the joint. Type the desired coordinate names into fields, select the target joint, then press the button"
    
    def execute(self, context):
        
        
        sel_obj = bpy.context.selected_objects  
            
        #ensure that only the relevant body is selected, or no bodies are selected. The operations will use the user input body name, so this prevents that the user selects a different body and expects the button to operate on that body
        if (len(sel_obj) != 1):  #if anything else than one joint is selected
            self.report({'ERROR'}, "Incorrect number of objects selected. Please select only one target joint. Operation cancelled.")
            return {'FINISHED'}
        

        target_obj = sel_obj[0]

        if 'MuSkeMo_type' not in target_obj:
            self.report({'ERROR'}, "Object with the name '" + target_obj.name + "' was not created by MuSkeMo. This operator only works on joints created by MuSkeMo. Operation cancelled.")
            return {'FINISHED'}
            
        if target_obj['MuSkeMo_type']!= 'JOINT':
            self.report({'ERROR'}, "Object with the name '" + target_obj.name + "' is not a JOINT. This operator only works on joints created by MuSkeMo. Operation cancelled.")
            return {'FINISHED'}
        
        target_obj['coordinate_Tx']=bpy.context.scene.muskemo.coor_Tx
        target_obj['coordinate_Ty']=bpy.context.scene.muskemo.coor_Ty
        target_obj['coordinate_Tz']=bpy.context.scene.muskemo.coor_Tz
        target_obj['coordinate_Rx']=bpy.context.scene.muskemo.coor_Rx
        target_obj['coordinate_Ry']=bpy.context.scene.muskemo.coor_Ry
        target_obj['coordinate_Rz']=bpy.context.scene.muskemo.coor_Rz
                
       
        return {'FINISHED'}    
    
class AssignParentBodyOperator(Operator):
    bl_idname = "joint.assign_parent_body"
    bl_label = "Assigns a parent body to a joint. Select both the parent body and the joint, then press the button."
    bl_description = "Assigns a parent body to a joint. Select both the parent body and the joint, then press the button."
   
    def execute(self, context):
        
              
        sel_obj = bpy.context.selected_objects  #should be the parent body and the joint
                    
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the parent body and the target joint.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select the parent body and the target joint.")
            return {'FINISHED'}
        

        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        joints = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='JOINT'] #get the joint

        
        if len(joints)!=1:
            self.report({'ERROR'}, "Incorrect number of joints selected. Select one target joint and one parent body. Operation cancelled.")
            return {'FINISHED'}
        
        joint = joints[0]
                
        parent_body = [obj for obj in muskemo_objects if obj!=joint][0]  #get the object that's not the joint

        if parent_body['MuSkeMo_type']!= 'BODY':
            self.report({'ERROR'}, "You didn't select a target body. Select one target joint and one parent body. Operation cancelled")
            return {'FINISHED'}
        
        try:
            joint.children[0]
        except:
            pass
        else:
            if joint.children[0] == parent_body:
                self.report({'ERROR'}, "You are attempting to assign body '" + parent_body.name + "' as the parent body, but it is already the child body. Operation cancelled.")
                return {'FINISHED'}

        if joint['parent_body'] != 'not_assigned':
            self.report({'ERROR'}, "You are attempting to assign a parent body to joint '" + joint.name + "', but it already has a parent body. Unparent it first. Operation cancelled.")
            return {'FINISHED'}
           

        if 'default_pose' in joint:

            if Matrix(joint['default_pose'])!= joint.matrix_world:
                self.report({'ERROR'}, "You are attempting to assign a parent body to joint '" + joint.name + "', but it's not in its default pose. Either reposition the joint, or clear its current child body. Operation cancelled.")
                return {'FINISHED'}

        ### if none of the previous scenarios triggered an error, set the parent body
        
        joint.parent = parent_body
            
        #this undoes the transformation after parenting
        joint.matrix_parent_inverse = parent_body.matrix_world.inverted()

        joint['parent_body'] = parent_body.name

        joint['default_pose'] = list(joint.matrix_world) #track the default pose to ensure the exported values are in the same pose. This overwrites it with the same existing value (or it would have been caught by the error check above, or creates it anew)


        from .quaternions import quat_from_matrix
        from .euler_XYZ_body import euler_XYZbody_from_matrix
        
        #global pos and or
        #if global pos is NaN or simply incorrect
        gRb_joint = joint.matrix_world.to_3x3() 

        joint_or_in_global_quat = quat_from_matrix(gRb_joint)
        joint_or_in_global_euler = euler_XYZbody_from_matrix(gRb_joint)

        joint['pos_in_global'] = joint.matrix_world.translation
        joint['or_in_global_quat'] = joint_or_in_global_quat
        joint['or_in_global_XYZeuler'] = joint_or_in_global_euler


        if parent_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
            
            ## import functions euler angles and quaternions from matrix

            
            
            frame = bpy.data.objects[parent_body['local_frame']]
            gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
            bRg = gRb.copy()
            bRg.transpose()
    
            frame_or_g = frame.matrix_world.translation                 
            
            joint_pos_g = joint.matrix_world.translation #position of the joint
            gRb_joint = joint.matrix_world.to_3x3() #gRb rotation matrix of joint
            joint_pos_in_parent = bRg @ (joint_pos_g - frame_or_g) #position in parent of joint
            b_R_jointframe = bRg @ gRb_joint #rotation matrix from joint frame to parent frame - decompose this for orientation in parent
            
            joint_or_in_parent_euler = euler_XYZbody_from_matrix(b_R_jointframe) #XYZ body-fixed decomposition of orientation in parent
            joint_or_in_parent_quat = quat_from_matrix(b_R_jointframe) #quaternion decomposition of orientation in parent
            
            joint['pos_in_parent_frame'] = joint_pos_in_parent
            joint['or_in_parent_frame_XYZeuler'] = joint_or_in_parent_euler
            joint['or_in_parent_frame_quat'] = joint_or_in_parent_quat 


            

        return {'FINISHED'}
        
class AssignChildBodyOperator(Operator):
    bl_idname = "joint.assign_child_body"
    bl_label = "Assigns a child body to a joint. Select both the child body and the joint, then press the button."
    bl_description = "Assigns a child body to a joint. Select both the child body and the joint, then press the button."
   
    def execute(self, context):
        

        sel_obj = bpy.context.selected_objects  #should be the parent body and the joint
                    
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the child body and the target joint.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select the child body and the target joint.")
            return {'FINISHED'}
        

        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]

        joints = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='JOINT'] #get the joint

        
        if len(joints)!=1:
            self.report({'ERROR'}, "Incorrect number of joints selected. Select one target joint and one child body. Operation cancelled.")
            return {'FINISHED'}
        
        joint = joints[0]
                
        child_body = [obj for obj in muskemo_objects if obj!=joint][0]  #get the object that's not the joint

        if child_body['MuSkeMo_type']!= 'BODY':
            self.report({'ERROR'}, "You didn't select a body. Select one target joint and one child body. Operation cancelled")
            return {'FINISHED'}
        
        if joint['child_body'] != 'not_assigned':
            self.report({'ERROR'}, "You are attempting to assign a child body to joint '" + joint.name + "', but it already has a child body. Unparent it first. Operation cancelled.")
            return {'FINISHED'}
           
        if len(joint.children)>0:
            self.report({'ERROR'}, "Joint with the name '" + joint.name + "' already has a child body. Clear it first, before assigning a new one")
            return {'FINISHED'}
        
        if joint.parent == child_body:
            self.report({'ERROR'}, "You are attempting to assign body '" + child_body.name + "' as the child body, but it is already the parent body. Operation cancelled.")
            return {'FINISHED'}


        if 'default_pose' in joint:

            if Matrix(joint['default_pose'])!= joint.matrix_world:
                self.report({'ERROR'}, "You are attempting to assign a child body to joint '" + joint.name + "', but the joint is not in its default pose. Either reposition the joint, or clear its current parent body. Operation cancelled.")
                return {'FINISHED'}

             

        ### if none of the previous scenarios triggered an error, set the child body
        
        child_body.parent = joint
        
            
        #this undoes the transformation after parenting
        child_body.matrix_parent_inverse = joint.matrix_world.inverted()

        joint['child_body'] = child_body.name

        joint['default_pose'] = list(joint.matrix_world) #track the default pose to ensure the exported values are in the same pose. This overwrites it with the same existing value (or it would have been caught by the error check above, or creates it anew)

        from .quaternions import quat_from_matrix
        from .euler_XYZ_body import euler_XYZbody_from_matrix      
    
        #update pos and or in global
        gRb_joint = joint.matrix_world.to_3x3() 

        joint_or_in_global_quat = quat_from_matrix(gRb_joint)
        joint_or_in_global_euler = euler_XYZbody_from_matrix(gRb_joint)

        joint['pos_in_global'] = joint.matrix_world.translation
        joint['or_in_global_quat'] = joint_or_in_global_quat
        joint['or_in_global_XYZeuler'] = joint_or_in_global_euler

        if child_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in child
            ## import functions euler angles and quaternions from matrix

                       
            frame = bpy.data.objects[child_body['local_frame']]
            gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
            bRg = gRb.copy()
            bRg.transpose()
    
            frame_or_g = frame.matrix_world.translation                 
            
            joint_pos_g = joint.matrix_world.translation #location of the joint
            gRb_joint = joint.matrix_world.to_3x3() #gRb rotation matrix of joint
            joint_pos_in_child = bRg @ (joint_pos_g - frame_or_g) #location in child of joint
            b_R_jointframe = bRg @ gRb_joint #rotation matrix from joint frame to child frame - decompose this for orientation in child
            
            joint_or_in_child_euler = euler_XYZbody_from_matrix(b_R_jointframe) #XYZ body-fixed decomposition of orientation in child
            joint_or_in_child_quat = quat_from_matrix(b_R_jointframe) #quaternion decomposition of orientation in child
            
            joint['pos_in_child_frame'] = joint_pos_in_child
            joint['or_in_child_frame_XYZeuler'] = joint_or_in_child_euler
            joint['or_in_child_frame_quat'] = joint_or_in_child_quat        
         
            
        return {'FINISHED'}
    
class ClearParentBodyOperator(Operator):
    bl_idname = "joint.clear_parent_body"
    bl_label = "Clears the parent body assigned to a joint. Select the joint, then press the button."
    bl_description = "Clears the parent body assigned to a joint. Select the joint, then press the button."
    
    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No joint selected. Select the target joint and try again. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target joint. Operation cancelled")
            return {'FINISHED'}
        
        joint = sel_obj[0]

        if 'MuSkeMo_type' not in joint:
            self.report({'ERROR'}, "Selected object '" + joint.name + "' was not created by MuSkeMo. Only select the target joint. Operation cancelled")
            return {'FINISHED'}
        
        if joint['MuSkeMo_type'] != 'JOINT':
            self.report({'ERROR'}, "Selected object '" + joint.name + "' is not a joint. Select the target joint. Operation cancelled")
            return {'FINISHED'}
         
        if joint['parent_body'] == 'not_assigned':
            self.report({'ERROR'}, "Joint with the name '" + joint.name + "' does not have a parent body. Operation cancelled")
            return {'FINISHED'}
        
        
        ### if none of the previous scenarios triggered an error, clear the parent body
        
        
        #clear the parent, without moving the joint
        parented_worldmatrix = joint.matrix_world.copy() 
        joint.parent = None
        joint.matrix_world = parented_worldmatrix   
        
        joint['parent_body'] = 'not_assigned'

        joint['pos_in_parent_frame'] = [nan, nan, nan]
        joint['or_in_parent_frame_XYZeuler'] = [nan, nan, nan]
        joint['or_in_parent_frame_quat'] = [nan, nan, nan, nan]

        ### If the joint is unparented after this, stop tracking default pose and set global or and pos to nan
        if joint['child_body'] == 'not_assigned' and 'default_pose' in joint:
            del joint['default_pose']
            joint['pos_in_global'] = [nan, nan, nan]
            joint['or_in_global_quat'] = [nan, nan, nan, nan]
            joint['or_in_global_XYZeuler'] = [nan, nan, nan]
            

        return {'FINISHED'}
    
    
class ClearChildBodyOperator(Operator):
    bl_idname = "joint.clear_child_body"
    bl_label = "Clears the child body assigned to a joint. Select the joint, then press the button."
    bl_description = "Clears the child body assigned to a joint. Select the joint, then press the button."
    
    def execute(self, context):
        
                       
        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No joint selected. Select the target joint and try again. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target joint. Operation cancelled")
            return {'FINISHED'}
        
        joint = sel_obj[0]

        if 'MuSkeMo_type' not in joint:
            self.report({'ERROR'}, "Selected object '" + joint.name + "' was not created by MuSkeMo. Only select the target joint. Operation cancelled")
            return {'FINISHED'}
        
        if joint['MuSkeMo_type'] != 'JOINT':
            self.report({'ERROR'}, "Selected object '" + joint.name + "' is not a joint. Select the target joint. Operation cancelled")
            return {'FINISHED'}
         
        if joint['child_body'] == 'not_assigned':
            self.report({'ERROR'}, "Joint with the name '" + joint.name + "' does not have a child body. Operation cancelled")
            return {'FINISHED'}
        
        
                       
        ### if none of the previous scenarios triggered an error, clear the child body
        
        child_body = joint.children[0]
        #clear the parent, without moving the joint
        parented_worldmatrix =child_body.matrix_world.copy() 
        child_body.parent = None
        child_body.matrix_world = parented_worldmatrix 

        joint['child_body'] = 'not_assigned'  
        joint['pos_in_child_frame'] = [nan, nan, nan]
        joint['or_in_child_frame_XYZeuler'] = [nan, nan, nan]
        joint['or_in_child_frame_quat'] = [nan, nan, nan, nan]

        ### If the joint is unparented after this, stop tracking default pose and set global or and pos to nan
        if joint['parent_body'] == 'not_assigned' and 'default_pose' in joint:
            del joint['default_pose']
            joint['pos_in_global'] = [nan, nan, nan]
            joint['or_in_global_quat'] = [nan, nan, nan, nan]
            joint['or_in_global_XYZeuler'] = [nan, nan, nan]
        
        return {'FINISHED'}        
    

    
class MatchOrientationOperator(Operator):
    bl_idname = "joint.match_orientation"
    bl_label = "This button matches a joint to a another object's orientation"
    bl_description = "This button matches a joint to a another object's orientation"
    bl_options = {"UNDO"} #enable undoing    
    
    def execute(self, context):
        
        
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select one joint and one (non-joint) object.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select one joint and one (non-joint) object.")
            return {'FINISHED'}
        
        muskemo_objects = [ob for ob in sel_obj if 'MuSkeMo_type' in ob]

        joint_objects = [ob for ob in muskemo_objects if ob['MuSkeMo_type'] == 'JOINT']

        # throw an error if no joints are selected     
        if (len(joint_objects) < 1):
            self.report({'ERROR'}, "You didn't select a joint. Select one joint and one (non-joint) object.")
            return {'FINISHED'}
        
        # throw an error if 2 joints are selected     
        if (len(joint_objects) > 1):
            self.report({'ERROR'}, "You selected more than one joint. Select one joint and one (non-joint) object.")
            return {'FINISHED'}

        joint = joint_objects[0]
        target_obj = [ob for ob in sel_obj if ob != joint][0]

        child_body = False #gets overwritten if there is a child
        parent_body = False #gets overwritten if there is a parent
        
        if joint.parent: #If the joint has a parent, temporarily clear the parent

            parent_body = bpy.data.objects[joint['parent_body']]
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name]] #set the selection for the correct objects
            bpy.ops.joint.clear_parent_body()
            bpy.ops.object.select_all(action='DESELECT') 
        
        
        if len(joint.children) != 0: #if the joint has a child, temporarily clear it
            
            child_body = joint.children[0]
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name]] #set the selection for the correct objects
            bpy.ops.joint.clear_child_body()
            bpy.ops.object.select_all(action='DESELECT') 

       

        worldMatrix = target_obj.matrix_world.copy() #get a copy the target object transformation matrix
        # remove scale
        worldMatrix = worldMatrix.normalized() 
        
        worldMatrix.translation = joint.matrix_world.translation  #ensure the original joints translation doesn't get lost.

        joint.matrix_world = worldMatrix
    

        if parent_body: #Reassign the parent
            
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name, parent_body.name]] #set the selection for the correct objects
            bpy.ops.joint.assign_parent_body()
            bpy.ops.object.select_all(action='DESELECT') 


        if child_body: #reparent the child

            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name, child_body.name]] #set the selection for the correct objects
            bpy.ops.joint.assign_child_body()
            bpy.ops.object.select_all(action='DESELECT') 

         
        return {'FINISHED'}

class MatchPositionOperator(Operator):
    bl_idname = "joint.match_position"
    bl_label = "This button matches a joint to a another object's position"
    bl_description = "This button matches a joint to a another object's position"
    bl_options = {"UNDO"} #enable undoing    

    def execute(self, context):
        
       
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select one joint and one (non-joint) object.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select one joint and one (non-joint) object.")
            return {'FINISHED'}
        
        muskemo_objects = [ob for ob in sel_obj if 'MuSkeMo_type' in ob]

        joint_objects = [ob for ob in muskemo_objects if ob['MuSkeMo_type'] == 'JOINT']

        # throw an error if no joints are selected     
        if (len(joint_objects) < 1):
            self.report({'ERROR'}, "You didn't select a joint. Select one joint and one (non-joint) object.")
            return {'FINISHED'}
        
        # throw an error if 2 joints are selected     
        if (len(joint_objects) > 1):
            self.report({'ERROR'}, "You selected more than one joint. Select one joint and one (non-joint) object.")
            return {'FINISHED'}

        joint = joint_objects[0]
        target_obj = [ob for ob in sel_obj if ob != joint][0]

        child_body = False #gets overwritten if there is a child
        parent_body = False #gets overwritten if there is a parent
        
        if joint.parent: #If the joint has a parent, temporarily clear the parent

            parent_body = bpy.data.objects[joint['parent_body']]
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name]] #set the selection for the correct objects
            bpy.ops.joint.clear_parent_body()
            bpy.ops.object.select_all(action='DESELECT') 
        
        
        if len(joint.children) != 0: #if the joint has a child, temporarily clear it
            
            child_body = joint.children[0]
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name]] #set the selection for the correct objects
            bpy.ops.joint.clear_child_body()
            bpy.ops.object.select_all(action='DESELECT') 

       
        position = target_obj.matrix_world.translation.copy() #get a copy the target object transformation matrix
        joint.matrix_world.translation = position

        if parent_body: #Reassign the parent
            
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name, parent_body.name]] #set the selection for the correct objects
            bpy.ops.joint.assign_parent_body()
            bpy.ops.object.select_all(action='DESELECT') 


        if child_body: #reparent the child

            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name, child_body.name]] #set the selection for the correct objects
            bpy.ops.joint.assign_child_body()
            bpy.ops.object.select_all(action='DESELECT')         

        return {'FINISHED'}        

class CycleThroughJointAxesOperator(Operator):
    bl_idname = "joint.cycle_through_axes"
    bl_label = "Cycle through axes, if you want to switch which axes are X, Y, and Z. Select an unparented joint, then press the button."
    bl_description = "Cycle through axes, if you want to switch which axes are X, Y, and Z. Select an unparented joint, then press the button."
    
    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No joint selected. Select the target joint and try again. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if too many objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target joint. Operation cancelled")
            return {'FINISHED'}
        
        joint = sel_obj[0]

        # Check if it's a MuSkeMo JOINT
        if 'MuSkeMo_type' not in joint:
            self.report({'ERROR'}, "Selected object '" + joint.name + "' was not created by MuSkeMo. Only select the target joint. Operation cancelled")
            return {'FINISHED'}
        
        if joint['MuSkeMo_type'] != 'JOINT':
            self.report({'ERROR'}, "Selected object '" + joint.name + "' is not a joint. Select the target joint. Operation cancelled")
            return {'FINISHED'}
        
        child_body = False #gets overwritten if there is a child
        parent_body = False #gets overwritten if there is a parent
        
        if joint.parent: #If the joint has a parent, temporarily clear the parent

            parent_body = bpy.data.objects[joint['parent_body']]
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name]] #set the selection for the correct objects
            bpy.ops.joint.clear_parent_body()
            bpy.ops.object.select_all(action='DESELECT') 
        
        
        if len(joint.children) != 0: #if the joint has a child, temporarily clear it
            
            child_body = joint.children[0]
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name]] #set the selection for the correct objects
            bpy.ops.joint.clear_child_body()
            bpy.ops.object.select_all(action='DESELECT') 
       

        #If none of the stop conditions are triggered, define a permutation matrix and multiply the joint's orientation by it.

        # permutation matrix: XYZ -> YXZ
        P = Matrix(((0,0,1),
                    (1,0,0),
                    (0,1,0)))


        # extract 3x3 rotation
        gRb = joint.matrix_world.to_3x3()

        # save position
        pos = joint.matrix_world.translation.copy()

        # apply one step of permutation
        R_new = (gRb @ P).to_4x4()

        # put back into world matrix
        joint.matrix_world = R_new
        joint.matrix_world.translation = pos

        if parent_body: #Reassign the parent
            
            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name, parent_body.name]] #set the selection for the correct objects
            bpy.ops.joint.assign_parent_body()
            bpy.ops.object.select_all(action='DESELECT') 


        if child_body: #reparent the child

            bpy.ops.object.select_all(action='DESELECT')
                    
            [bpy.data.objects[x].select_set(True) for x in [joint.name, child_body.name]] #set the selection for the correct objects
            bpy.ops.joint.assign_child_body()
            bpy.ops.object.select_all(action='DESELECT')         


        joint.select_set(True) #reset selection state
        return {'FINISHED'}

         


##### The panels ####


class VIEW3D_PT_joint_panel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_joint_panel'
    bl_label = "Joint panel"  # found at the top of the Panel
    bl_context = "objectmode"

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        ### selected joints and bodies

        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('JOINT', layout)
        ###
        
        ## user input joint name    
        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Joint Name")
        split.prop(muskemo, "jointname", text = "")
        

        ## Create new joint
        row = layout.row()
        row.label(text ="Joint centers are initially placed in the world origin")
        row = self.layout.row()
        row.operator("joint.create_new_joint", text="Create new joint")
        
        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Joint Collection")
        split.prop(muskemo, "joint_collection", text = "")
                    
        
        row = self.layout.row()


        
        row = self.layout.row()
        row = self.layout.row()


        CreateSelectedObjRow('BODY', layout)
        ## assign or clear parent and child
        row = self.layout.row()
        row.operator("joint.assign_parent_body", text="Assign parent body")
        row.operator("joint.assign_child_body", text="Assign child body")
        row = self.layout.row()
        row.operator("joint.clear_parent_body", text="Clear parent body")
        row.operator("joint.clear_child_body", text="Clear child body")
        
        
        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.prop(muskemo, "jointsphere_size")
        
        row = self.layout.row()
        row = self.layout.row()
        row = self.layout.row()
        row.operator("muskemo.reset_model_default_pose", text = 'Reset to default pose')
            
        #row = self.layout.row()
        #self.layout.prop(muskemo, "musclename_string")



class VIEW3D_PT_joint_coordinate_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_coordinate_subpanel'
    bl_label = "Joint coordinate names (optional)"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_joint_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo


        row = self.layout.row()
        row.label(text ="Coordinate names (optional)")
        ## user input coordinate names    
        
        layout.prop(muskemo, "coor_Rx")
        layout.prop(muskemo, "coor_Ry")
        layout.prop(muskemo, "coor_Rz")
        layout.prop(muskemo, "coor_Tx")
        layout.prop(muskemo, "coor_Ty")
        layout.prop(muskemo, "coor_Tz")
        
        
        
    
        row = self.layout.row()
        row.operator("joint.update_coordinate_names", text="Update coordinate names")


class VIEW3D_PT_joint_utilities_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_utilities_subpanel'
    bl_label = "Joint utilities"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_joint_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo


        row = self.layout.row()
        
       
        row = self.layout.row()
        row.operator("mesh.fit_sphere_geometric", text="Fit a sphere (geometric)")
        row.operator("mesh.fit_sphere_ls", text="Fit a sphere (least-squares)")
        
        row = self.layout.row()
        row.operator("mesh.fit_cylinder", text="Fit a cylinder")

        row = self.layout.row()
        row.operator("mesh.fit_ellipsoid", text="Fit an ellipsoid")

        row = self.layout.row()
        row.operator("mesh.fit_plane", text="Fit a plane")


        ### selected objects that are not joints

        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('NOTJOINT', layout)
        row = self.layout.row()
        row.operator("joint.match_position", text="Match position")
        row.operator("joint.match_orientation", text="Match orientation")

        row = self.layout.row()
        row.operator("joint.cycle_through_axes", text = "Cycle through joint axes")


       