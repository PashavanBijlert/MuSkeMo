# give Python access to Blender's functionality
import bpy
from mathutils import (Vector, Matrix)


from bpy.types import (Panel,
                        Operator)
import numpy as np
import math

from math import nan

array = np.array
norm  = np.linalg.norm 
cross = np.cross


from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed



class AssignOrLandmarkOperator(Operator):
    bl_idname = "arf.assign_origin"
    bl_label = "Assign the selected landmark as the origin of the frame."
    bl_description = "Assign the selected landmark as the origin of the frame."
    
    def execute(self, context):

        bpy.context.scene.muskemo.or_landmark_name = bpy.context.active_object.name  #assigns the name of the active object as the origin landmark
        return {'FINISHED'}
    
    
    
class AssignYDirLandmarkOperator(Operator):
    bl_idname = "arf.assign_ydir_landmark"
    bl_label = "Assign the selected landmark as the Y-direction (long axis) of the frame."
    bl_description = "Assign the selected landmark as the Y-direction (long axis) of the frame."

    def execute(self, context):

        bpy.context.scene.muskemo.ydir_landmark_name = bpy.context.active_object.name  #assigns the name of the active object as the origin landmark
        return {'FINISHED'}    
    
class AssignYZPlaneLandmarkOperator(Operator):
    bl_idname = "arf.assign_yz_plane_landmark"
    bl_label = "Assign the selected landmark as the YZ plane landmark (direction of the temporary Z-axis)"
    bl_description = "Assign the selected landmark as the YZ plane landmark (direction of the temporary Z-axis)"
    
    def execute(self, context):

        bpy.context.scene.muskemo.yz_plane_landmark_name = bpy.context.active_object.name  #assigns the name of the active object as the origin landmark
        return {'FINISHED'}        
    
    
class ReflectSelectedRSideFrames(Operator):
    bl_idname = "arf.reflect_selected_r_arfs"
    bl_label = "Reflect the selected frames about the YZ-plane if they have '_r' in the name"
    bl_description = "Reflect the selected frames about the YZ-plane if they have '_r' in the name"
    
    def execute(self, context):
        
        colname = bpy.context.scene.muskemo.frame_collection  #target collection

        Collection = bpy.data.collections[colname]


        sel_obj = bpy.context.selected_objects  #all selected objects
        
        for obj in (obj for obj in sel_obj if '_r' in obj.name):
            
            
            if obj.name.replace('_r','_l') not in (obj.name for obj in  Collection.objects):  #make sure a left side doesn't already exist
            
            
                new_obj = obj.copy()  #copy object
                
                new_obj.name = obj.name.replace('_r','_l') #rename to left
                
                Collection.objects.link(new_obj)  #add to Collection
                
                new_obj.location = obj.location*Vector([1,1,-1])
                new_obj.rotation_euler = [-1*obj.rotation_euler[0], -1*obj.rotation_euler[1], 1*obj.rotation_euler[2]]
                    
                new_obj['MuSkeMo_type'] = 'FRAME'  #to inform the user what type is created
                new_obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  
        
        
        return {'FINISHED'}       

    

class ConstructARFOperator(Operator):
    bl_idname = "arf.construct_arf"
    bl_label = "Constructs a new anatomical (local) reference frame (arf)"
    bl_description = "Constructs a new anatomical (local) reference frame (arf)"
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo

        origin_landmark_name =  muskemo.or_landmark_name
        ydir_landmark_name = muskemo.ydir_landmark_name
        yzplane_landmark_name = muskemo.yz_plane_landmark_name  #landmark to define YZ plane

        refframe_name = muskemo.framename
        colname = muskemo.frame_collection  #target collection

        size = muskemo.ARF_axes_size

       
        origin = bpy.data.objects[origin_landmark_name].location
        y_axis = bpy.data.objects[ydir_landmark_name].location - origin
        z_axis_temp = bpy.data.objects[yzplane_landmark_name].location - origin

        x_axis = cross(y_axis, z_axis_temp)

        x_axis = x_axis/norm(x_axis)
        y_axis = y_axis/norm(y_axis)
        z_axis = cross(x_axis,y_axis)

        #turn into standing vectors
        x_axis = x_axis.reshape(3,1)
        y_axis = np.array(y_axis).reshape(3,1)  #y_axis is still of type Vector, turn into np.array
        z_axis = z_axis.reshape(3,1)



        #print(z_axis)

        gRl= np.concatenate((x_axis, y_axis, z_axis), axis = 1) # gRl = global from local rotation matrix, is a matrix of [x_vec y_vec z_vec]

        #print(gRl)

        from .create_frame_func import create_frame
        create_frame(name=refframe_name, size = size, 
                     pos_in_global = origin, gRb = gRl,
                     collection_name = colname,
                     parent_body = 'not_assigned',)
        
        
        return {'FINISHED'}


class AssignARFParentBodyOperator(Operator):
    bl_idname = "arf.assign_parent_body"
    bl_label = "Assigns a parent body to an anatomical (local) reference frame. Select both the parent body and the frame, then press the button."
    bl_description = "Assigns a parent body to an anatomical (local) reference frame. Select both the parent body and the frame, then press the button."
   
    def execute(self, context):
        
        frame_name = bpy.context.scene.muskemo.framename
        
        active_obj = bpy.context.active_object  #
        sel_obj = bpy.context.selected_objects  #should be the parent body and the frame
        
        colname = bpy.context.scene.muskemo.frame_collection
        bodycolname = bpy.context.scene.muskemo.body_collection
        try: bpy.data.objects[frame_name]  #check if the frame exists
        
        except:  #throw an error if the frame doesn't exist
            self.report({'ERROR'}, "Frame with the name '" + frame_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        frame = bpy.data.objects[frame_name]
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the parent body and the target frame.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select the parent body and the target frame.")
            return {'FINISHED'}
        
        if frame not in sel_obj:
            self.report({'ERROR'}, "Neither of the selected objects is the target frame. Selected frame and frame_name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        parent_body = [s_obj for s_obj in sel_obj if s_obj.name not in bpy.data.collections[colname].objects][0]  #get the object that's not the frame
        
        
        
        try:
            frame.children[0]
        except:
            pass
        else:
            
            self.report({'ERROR'}, "You are attempting to assign body '" + parent_body.name + "' as the parent body, but it is already the child body. Operation cancelled.")
            return {'FINISHED'}


        
        if parent_body.name not in bpy.data.collections[bodycolname].objects:
            self.report({'ERROR'}, "The parent body is not in the '" + bodycolname + "' collection. Make sure one of the two selected objects is a 'Body' as created by the bodies panel")
            return {'FINISHED'}
            
        ### if none of the previous scenarios triggered an error, set the parent body
        
        frame.parent = parent_body
            
        #this undoes the transformation after parenting
        frame.matrix_parent_inverse = parent_body.matrix_world.inverted()

        frame['parent_body'] = parent_body.name
        parent_body['local_frame'] = frame.name


        ###### Add all the extra locations and orientations in the local frame of all parent and child objects where it is relevant
        ### COM extra properties COM_local, inertia_COM_local

        gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
        bRg = gRb.copy()
        bRg.transpose()
        
        frame_or_g = frame.matrix_world.translation   #frame origin in global frame
        COM_g = Vector(parent_body['COM'])  #COM loc in global frame

        relCOM_g = COM_g - frame_or_g  #Relative COM location from the local frame origin, aligned in global frame
        relCOM_b = bRg @ relCOM_g #COM of the body, expressed in the local frame

        parent_body['COM_local'] = list(relCOM_b)  #set COM in local frame

        MOI_glob_vec = parent_body['inertia_COM']  #vector of MOI about COM, in global frame. Ixx Iyy Izz Ixy Ixz Iyz
        MOI_g = Matrix(((MOI_glob_vec[0], MOI_glob_vec[3], MOI_glob_vec[4]), #MOI tensor about COM in global
                        (MOI_glob_vec[3],MOI_glob_vec[1],MOI_glob_vec[5]),
                        (MOI_glob_vec[4],MOI_glob_vec[5],MOI_glob_vec[2])))
        
        MOI_b = bRg @ MOI_g @ gRb #Vallery & Schwab, Advanced Dynamics 2018, eq. 5.53

        MOI_b_vec = [MOI_b[0][0],  #Ixx, about COM, in local frame
                     MOI_b[1][1],  #Iyy
                     MOI_b[2][2],  #Izz
                     MOI_b[0][1],  #Ixy
                     MOI_b[0][2],  #Ixz
                     MOI_b[1][2]]  #Iyz


        parent_body['inertia_COM_local'] = MOI_b_vec  #add moment of inertia in local frame to the body

        ## import functions euler angles and quaternions from matrix

        from .quaternions import quat_from_matrix
        from .euler_XYZ_body import euler_XYZbody_from_matrix

        ## parent joint

        parent_joint_bool = False  # a boolean that is true if the parent_body's parent is of the type joint
        if parent_body.parent is not None: #if the parent body has a parent, we check if it is a muskemo type JOINT, and if so, assign location and rotation in child

            parent_joint = parent_body.parent

            if 'MuSkeMo_type' in parent_joint: #if parent_joint actually has a muskemo type
                
                if parent_joint['MuSkeMo_type'] == 'JOINT': #if it's a joint, then we set the bool to true
                    parent_joint_bool = True    
                else: #else we throw an error
                    self.report({'ERROR'}, "The body '" + parent_body.name + "' appears to be the child of the object '" + parent_joint.name + "', which is not a JOINT. Skipping this object when computing local transformations")
            else:
                self.report({'ERROR'}, "The body '" + parent_body.name + "' appears to be the child of the object '" + parent_joint.name + "', which is not a JOINT. Skipping this object when computing local transformations")
                    
        
        if parent_joint_bool:  #if parent joint bool is still true after the previous error 
            
            parent_joint_pos_g = parent_joint.matrix_world.translation #location of the parent joint
            gRb_parent_joint = parent_joint.matrix_world.to_3x3() #gRb rotation matrix of parent joint
            parent_joint_pos_in_child = bRg @ (parent_joint_pos_g - frame_or_g) #location in child of parent joint
            b_R_parentjointframe = bRg @ gRb_parent_joint #rotation matrix from parent joint frame to child frame - decompose this for rotation in child
            
            parent_joint_or_in_child_euler = euler_XYZbody_from_matrix(b_R_parentjointframe) #XYZ body-fixed decomposition of orientation in child
            parent_joint_or_in_child_quat = quat_from_matrix(b_R_parentjointframe) #quaternion decomposition of orientation in child
            
            parent_joint['pos_in_child_frame'] = parent_joint_pos_in_child
            parent_joint['or_in_child_frame_XYZeuler'] = parent_joint_or_in_child_euler
            parent_joint['or_in_child_frame_quat'] = parent_joint_or_in_child_quat
            
            ## convert to euler angles and quats, assign as new custom properties

        ## all children, sort into types

        children = [obj for obj in parent_body.children if 'MuSkeMo_type' in obj]

        joints = [obj for obj in children if 'JOINT' in obj['MuSkeMo_type']]
        contacts = [obj for obj in children if 'CONTACT' in obj['MuSkeMo_type']]
        landmarks = [obj for obj in children if 'LANDMARK' in obj['MuSkeMo_type']]
        geometry = [obj for obj in children if 'GEOMETRY' in obj['MuSkeMo_type']]

        ## for all child joints

        for joint in joints:
            joint_pos_g = joint.matrix_world.translation #location of the joint
            gRb_joint = joint.matrix_world.to_3x3() #gRb rotation matrix of joint
            joint_pos_in_parent = bRg @ (joint_pos_g - frame_or_g) #location in parent of joint
            b_R_jointframe = bRg @ gRb_joint #rotation matrix from joint frame to parent frame - decompose this for orientation in parent
            
            joint_or_in_parent_euler = euler_XYZbody_from_matrix(b_R_jointframe) #XYZ body-fixed decomposition of orientation in parent
            joint_or_in_parent_quat = quat_from_matrix(b_R_jointframe) #quaternion decomposition of orientation in parent
            
            joint['pos_in_parent_frame'] = joint_pos_in_parent
            joint['or_in_parent_frame_XYZeuler'] = joint_or_in_parent_euler
            joint['or_in_parent_frame_quat'] = joint_or_in_parent_quat    

        
        ## for all contacts

        for contact in contacts:
            
            contact_pos_g = contact.matrix_world.translation #location of the contact
            contact_pos_in_parent = bRg @ (contact_pos_g - frame_or_g) #location in parent of contact
            contact['pos_in_parent_frame'] = contact_pos_in_parent
               


        #loop through attached contacts
        #loop through attached geometry?
        
  
        return {'FINISHED'}

class ClearARFParentBodyOperator(Operator):
    bl_idname = "arf.clear_parent_body"
    bl_label = "Clears the parent body assigned to a frame. Select the frame, then press the button."
    bl_description = "Clears the parent body assigned to a frame. Select the frame, then press the button."
    
    def execute(self, context):
        
        frame_name = bpy.context.scene.muskemo.framename
        
        colname = bpy.context.scene.muskemo.frame_collection


        active_obj = bpy.context.active_object  #should be the frame
        sel_obj = bpy.context.selected_objects  #should be the only the frame
        
        
        try: bpy.data.objects[frame_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Frame with the name '" + frame_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        frame = bpy.data.objects[frame_name]

        try: frame.parent.name
        
        except: #throw an error if the frame has no parent
            self.report({'ERROR'}, "Frame with the name '" + frame_name + "' does not have a parent body")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No frame selected. Select the target frame and try again.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target frame.")
            return {'FINISHED'}
        
        if frame.name != active_obj.name:
            self.report({'ERROR'}, "Selected frame and frame_name (text input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if frame.name not in bpy.data.collections[colname].objects:
            self.report({'ERROR'}, "Selected object is not in the '" + colname + "' collection. Make sure you have selected a frame in that collection.")
            return {'FINISHED'}
        
        
                
        ### if none of the previous scenarios triggered an error, clear the parent body
        
        
        #clear the parent, without moving the frame
        parent_body = frame.parent

        parented_worldmatrix = frame.matrix_world.copy() 
        frame.parent = None
        frame.matrix_world = parented_worldmatrix   
        
        frame['parent_body'] = 'not_assigned'
        parent_body['local_frame'] = 'not_assigned'

        parent_body['COM_local'] = [nan, nan, nan]
        parent_body['inertia_COM_local'] = [nan, nan, nan, nan, nan, nan]


        ## parent joint

        parent_joint_bool = False  # a boolean that is true if the parent_body's parent is of the type joint
        if parent_body.parent is not None: #if the parent body has a parent, we check if it is a muskemo type JOINT, and if so, assign location and rotation in child

            parent_joint = parent_body.parent

            if 'MuSkeMo_type' in parent_joint: #if parent_joint actually has a muskemo type
                
                if parent_joint['MuSkeMo_type'] == 'JOINT': #if it's a joint, then we set the bool to true
                    parent_joint_bool = True    
                else: #else we throw an error
                    self.report({'ERROR'}, "The body '" + parent_body.name + "' appears to be the child of the object '" + parent_joint.name + "', which is not a JOINT. Skipping this object when computing local transformations")
            else:
                self.report({'ERROR'}, "The body '" + parent_body.name + "' appears to be the child of the object '" + parent_joint.name + "', which is not a JOINT. Skipping this object when computing local transformations")
                    
        
        if parent_joint_bool:  #if parent joint bool is still true after the previous error 
            
            
            
            parent_joint['pos_in_child_frame'] = [nan, nan, nan]
            parent_joint['or_in_child_frame_XYZeuler'] = [nan, nan, nan]
            parent_joint['or_in_child_frame_quat'] = [nan, nan, nan, nan]
            
            ## convert to euler angles and quats, assign as new custom properties

        ## all children, sort into types

        children = [obj for obj in parent_body.children if 'MuSkeMo_type' in obj]

        joints = [obj for obj in children if 'JOINT' in obj['MuSkeMo_type']]
        contacts = [obj for obj in children if 'CONTACT' in obj['MuSkeMo_type']]
        landmarks = [obj for obj in children if 'LANDMARK' in obj['MuSkeMo_type']]
        geometry = [obj for obj in children if 'GEOMETRY' in obj['MuSkeMo_type']]

        ## for all child joints

        for joint in joints:
            
            
            joint['pos_in_parent_frame'] = [nan, nan, nan]
            joint['or_in_parent_frame_XYZeuler'] = [nan, nan, nan]
            joint['or_in_parent_frame_quat'] = [nan, nan, nan, nan]   

        
        #loop through attached contacts

        for contact in contacts:
            
            
            contact['pos_in_parent_frame'] = [nan, nan, nan]
            
        #loop through attached geometry?
        #loop through landmarks?

        


        return {'FINISHED'}





class VIEW3D_PT_arf_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’

    bl_context = "objectmode"
    bl_idname = 'VIEW3D_PT_ARF_panel'
    
    
    bl_label = "Anatomical & local reference frames panel"  # found at the top of the Panel
    
    
    bl_options = {'DEFAULT_CLOSED'}
    

    def draw(self, context):
        """define the layout of the panel"""
        
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.prop(muskemo, "frame_collection")
        self.layout.row()


        row = self.layout.row()
        row.prop(muskemo, "framename")
        self.layout.row()
        
        
        row = self.layout.row()
        row.operator("arf.assign_origin", text="Assign as frame origin")
        row.prop(muskemo, "or_landmark_name")
        self.layout.row()
        
        
        row = self.layout.row()
        row.operator("arf.assign_ydir_landmark", text="Assign as Y direction")
        row.prop(muskemo, "ydir_landmark_name")
        self.layout.row()
        
        row = self.layout.row()
        row.operator("arf.assign_yz_plane_landmark", text="Assign as YZ plane landmark")
        row.prop(muskemo, "yz_plane_landmark_name")
        self.layout.row()
        
        
        row = self.layout.row()
        row.operator("arf.construct_arf", text="Construct arf from points")
        self.layout.row()
        row = self.layout.row()
        row.operator("arf.assign_parent_body", text="Assign parent body")
        row.operator("arf.clear_parent_body", text="Clear parent body")

        
        row = self.layout.row()
        
        self.layout.row()
        
        row = self.layout.row()
        row.operator("arf.reflect_selected_r_arfs", text="Reflect selected r-side arfs")

        self.layout.row()
        self.layout.row()
        
        row = self.layout.row()
        row.prop(muskemo,  "ARF_axes_size")