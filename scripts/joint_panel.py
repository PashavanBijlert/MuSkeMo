

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
        
        
        
        
        try: bpy.data.objects[name] #check if the joint exists
        
        except:  #if not, create it
            from .create_joint_func import create_joint
                       
            create_joint(name = name, radius = rad, collection_name = colname,)
            
        else:
            
            self.report({'ERROR'}, "Joint with the name " + name + " already exists, please choose a different name")
        
        
        return {'FINISHED'}


class ReflectRightsideJointsOperator(Operator):
    bl_idname = "joint.reflect_rightside_joints"
    bl_label = "Duplicates and reflects joints across XY plane if they contain '_r' in the name."
    bl_description = "Duplicates and reflects joints across XY plane if they contain '_r' in the name."
    
    def execute(self, context):
        colname = bpy.context.scene.muskemo.joint_collection

        collection = bpy.data.collections[colname]


        for obj in (obj for obj in collection.objects if '_r' in obj.name):  #for all the objects if '_r' is in the name
            
            if obj.name.replace('_r','_l') not in (obj.name for obj in collection.objects):  #make sure a left side doesn't already exist
            
            
                new_obj = obj.copy()  #copy object
                new_obj.data = obj.data.copy() #copy object data
                new_obj.name = obj.name.replace('_r','_l') #rename to left
                
                collection.objects.link(new_obj)  #add to Muscles collection
                
                for point in new_obj.data.splines[0].points:   #reflect each point about z
                    point.co = point.co*Vector((1,1,-1,1))
                    
                for mod in new_obj.modifiers: #loop through all modifiers
                    mod.object = bpy.data.objects[mod.object.name.replace('_r','_l')]

        return {'FINISHED'}
    
class UpdateCoordinateNamesOperator(Operator):
    bl_idname = "joint.update_coordinate_names"
    bl_label = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    bl_description = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    
    def execute(self, context):
        
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if it doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            
        else:
            
            sel_obj = bpy.context.selected_objects  
            
            #ensure that only the relevant body is selected, or no bodies are selected. The operations will use the user input body name, so this prevents that the user selects a different body and expects the button to operate on that body
            if (len(sel_obj) == 0) or ((len(sel_obj) == 1) and sel_obj[0].name == joint_name):  #if no objects are selected, or the only selected object is also the correct body
                
                obj = bpy.data.objects[joint_name]
                
                obj['coordinate_Tx']=bpy.context.scene.muskemo.coor_Tx
                obj['coordinate_Ty']=bpy.context.scene.muskemo.coor_Ty
                obj['coordinate_Tz']=bpy.context.scene.muskemo.coor_Tz
                obj['coordinate_Rx']=bpy.context.scene.muskemo.coor_Rx
                obj['coordinate_Ry']=bpy.context.scene.muskemo.coor_Ry
                obj['coordinate_Rz']=bpy.context.scene.muskemo.coor_Rz
                  
            
            else:
                self.report({'ERROR'}, "Joint with the name '" + joint_name + "' is not the (only) selected joint. Operation cancelled, please either deselect all objects or only select the '" + joint_name + "' joint. This button operates on the joint that corresponds to the user (text) input joint name")
        
        return {'FINISHED'}    
    
class AssignParentBodyOperator(Operator):
    bl_idname = "joint.assign_parent_body"
    bl_label = "Assigns a parent body to a joint. Select both the parent body and the joint, then press the button."
    bl_description = "Assigns a parent body to a joint. Select both the parent body and the joint, then press the button."
   
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the parent body and the joint
        
        colname = bpy.context.scene.muskemo.joint_collection
        bodycolname = bpy.context.scene.muskemo.body_collection
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        joint = bpy.data.objects[joint_name]
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the parent body and the target joint.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select the parent body and the target joint.")
            return {'FINISHED'}
        
        if joint not in sel_obj:
            self.report({'ERROR'}, "Neither of the selected objects is the target joint. Selected joint and joint_name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        parent_body = [s_obj for s_obj in sel_obj if s_obj.name not in bpy.data.collections[colname].objects][0]  #get the object that's not the joint
        
        
        
        try:
            joint.children[0]
        except:
            pass
        else:
            if joint.children[0] == parent_body:
                self.report({'ERROR'}, "You are attempting to assign body '" + parent_body.name + "' as the parent body, but it is already the child body. Operation cancelled.")
                return {'FINISHED'}


        
        if parent_body.name not in bpy.data.collections[bodycolname].objects:
            self.report({'ERROR'}, "The parent body is not in the '" + bodycolname + "' collection. Make sure one of the two selected objects is a 'Body' as created by the bodies panel")
            return {'FINISHED'}
            
        ### if none of the previous scenarios triggered an error, set the parent body
        
        joint.parent = parent_body
            
        #this undoes the transformation after parenting
        joint.matrix_parent_inverse = parent_body.matrix_world.inverted()

        joint['parent_body'] = parent_body.name

        if parent_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
            
            ## import functions euler angles and quaternions from matrix

            from .quaternions import quat_from_matrix
            from .euler_XYZ_body import euler_XYZbody_from_matrix
            
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
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        colname = bpy.context.scene.muskemo.joint_collection
        bodycolname = bpy.context.scene.muskemo.body_collection

        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the parent body and the joint
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        joint = bpy.data.objects[joint_name]
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the child body and the target joint.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select the child body and the target joint.")
            return {'FINISHED'}
        
        if joint not in sel_obj:
            self.report({'ERROR'}, "Neither of the selected objects is the target joint. Selected joint and joint_name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        child_body = [s_obj for s_obj in sel_obj if s_obj.name not in bpy.data.collections[colname].objects][0]  #get the object that's not the joint
        
        
        if child_body.name not in bpy.data.collections[bodycolname].objects:
            self.report({'ERROR'}, "The child body is not in the '" + bodycolname + "' collection. Make sure one of the two selected objects is a 'Body' as created by the bodies panel")
            return {'FINISHED'}

        if len(joint.children)>0:
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' already has a child body. Clear it first, before assigning a new one")
            return {'FINISHED'}
        
        if joint.parent == child_body:
            self.report({'ERROR'}, "You are attempting to assign body '" + child_body.name + "' as the child body, but it is already the parent body. Operation cancelled.")
            return {'FINISHED'}


        ### if none of the previous scenarios triggered an error, set the parent body
        
        child_body.parent = joint
        
            
        #this undoes the transformation after parenting
        child_body.matrix_parent_inverse = joint.matrix_world.inverted()

        joint['child_body'] = child_body.name

        if child_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in child
            ## import functions euler angles and quaternions from matrix

            from .quaternions import quat_from_matrix
            from .euler_XYZ_body import euler_XYZbody_from_matrix
            
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
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        colname = bpy.context.scene.muskemo.joint_collection


        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        joint = bpy.data.objects[joint_name]

        try: joint.parent.name
        
        except: #throw an error if the joint has no parent
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not have a parent body")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No joint selected. Select the target joint and try again.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target joint.")
            return {'FINISHED'}
        
        if joint.name != active_obj.name:
            self.report({'ERROR'}, "Selected joint and joint_name (text input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if joint.name not in bpy.data.collections[colname].objects:
            self.report({'ERROR'}, "Selected object is not in the '" + colname + "' collection. Make sure you have selected a joint in that collection.")
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



        return {'FINISHED'}
    
    
class ClearChildBodyOperator(Operator):
    bl_idname = "joint.clear_child_body"
    bl_label = "Clears the child body assigned to a joint. Select the joint, then press the button."
    bl_description = "Clears the child body assigned to a joint. Select the joint, then press the button."
    
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname
        colname = bpy.context.scene.muskemo.joint_collection

        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        

        joint = bpy.data.objects[joint_name]
        if len(joint.children)==0:
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not have a child body")
            return {'FINISHED'}

        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No joint selected. Select the target joint and try again.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target joint.")
            return {'FINISHED'}
        
        if joint.name != active_obj.name:
            self.report({'ERROR'}, "Selected joint and joint_name (text input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if joint.name not in bpy.data.collections[colname].objects:
            self.report({'ERROR'}, "Selected object is not in the '" + colname + "' collection. Make sure you have selected a joint in that collection.")
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
        
        return {'FINISHED'}        
    

class FitSphereGeomOperator(Operator):
    bl_idname = "joint.fit_sphere_geometric"
    bl_label = "Fit a sphere to a selected mesh, using Yesudesan geometric fit"
    bl_description = "Fit a sphere to a selected mesh, using Yesudesan geometric fit"
    #Based on sumith_fit - https://doi.org/10.48550/arXiv.1506.02776
  
    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, input  = verts_x, verts_y, verts_z
        x = verts_x
        y = verts_y
        z = verts_z



        N = len(x)
    
        Sx = sum(x)
        Sy = sum(y)     
        Sz = sum(z)
        Sxx = sum(x*x)    
        Syy = sum(y*y)    
        Szz = sum(z*z)
        Sxy = sum(x*y)
        Sxz = sum(x*z)
        Syz = sum(y*z)
        Sxxx = sum(x*x*x)
        Syyy = sum(y*y*y)
        Szzz = sum(z*z*z)
        Sxyy = sum(x*y*y)
        Sxzz = sum(x*z*z)
        Sxxy = sum(x*x*y)
        Sxxz = sum(x*x*z)
        Syyz = sum(y*y*z)
        Syzz = sum(y*z*z)
        A1 = Sxx +Syy +Szz
        a = 2*Sx*Sx-2*N*Sxx
        b = 2*Sx*Sy-2*N*Sxy
        c = 2*Sx*Sz-2*N*Sxz
        d = -N*(Sxxx +Sxyy +Sxzz)+A1*Sx
        e = b  # this is equal to 2*Sx*Sy-2*N*Sxy
        f = 2*Sy*Sy-2*N*Syy
        g = 2*Sy*Sz-2*N*Syz;
        h = -N*(Sxxy +Syyy +Syzz)+A1*Sy;
        j = c; #this is equal to 2*Sx*Sz-2*N*Sxz
        k = g; # this is equal to 2*Sy*Sz-2*N*Syz;
        l = 2*Sz*Sz-2*N*Szz
        m = -N*(Sxxz +Syyz + Szzz)+A1*Sz;
        delta = a*(f*l - g*k)-e*(b*l-c*k) + j*(b*g-c*f);
        xc = (d*(f*l-g*k) -h*(b*l-c*k) +m*(b*g-c*f))/delta;
        yc = (a*(h*l-m*g) -e*(d*l-m*c) +j*(d*g-h*c))/delta;
        zc = (a*(f*m-h*k) -e*(b*m-d*k) +j*(b*h-d*f))/delta;
        Radius = np.sqrt(xc**2 + yc**2 + zc**2 + (A1 -2*(xc*Sx+yc*Sy+zc*Sz))/N);

        center = [xc, yc, zc]

        ### fitting ends here, output = Radius, xc, yc, zc

        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=Radius, align='WORLD', location=(xc, yc, zc))
        fit_obj_name = obj_name + '_SphereGeoFit'
        bpy.context.active_object.name = fit_obj_name

        obj = bpy.data.objects[fit_obj_name]

        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['sphere_radius'] =  Radius   #to inform the user what type is created
        obj.id_properties_ui('sphere_radius').update(description = "Radius of the fitted sphere (in m)") 
        

        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)


        return {'FINISHED'}

class FitSphereLSOperator(Operator):
    bl_idname = "joint.fit_sphere_ls"
    bl_label = "Fit a sphere to a selected mesh, using Jekel least-squares fit"
    bl_description = "Fit a sphere to a selected mesh, using Jekel least-squares fit"
    #based on: https://jekel.me/2015/Least-Squares-Sphere-Fit/, originally from Jekel's PhD thesis
        
    def execute(self, context):
        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, inputs = verts_x, verts_y, verts_z

        spX = verts_x
        spY = verts_y
        spZ = verts_z

        A = np.zeros((len(spX),4))
        A[:,0] = spX*2
        A[:,1] = spY*2
        A[:,2] = spZ*2
        A[:,3] = 1

        #   Assemble the f matrix
        f = np.zeros((len(spX),1))
        f[:,0] = (spX*spX) + (spY*spY) + (spZ*spZ)
        C, residules, rank, singval = np.linalg.lstsq(A,f,rcond=None)

        #   solve for the radius
        t = (C[0]*C[0])+(C[1]*C[1])+(C[2]*C[2])+C[3]
        Radius = np.sqrt(t)

        center = [C[0], C[1], C[2]]
        ### fitting ends here, output = Radius, center

        
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=Radius, align='WORLD', location=(C[0], C[1], C[2]))
        fit_obj_name = obj_name + '_SphereLSFit'
        bpy.context.active_object.name = fit_obj_name

        obj = bpy.data.objects[fit_obj_name]

        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['sphere_radius'] =  Radius   #to inform the user what type is created
        obj.id_properties_ui('sphere_radius').update(description = "Radius of the fitted sphere (in m)") 


        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)    

        return {'FINISHED'}

class FitCylinderOperator(Operator):
    bl_idname = "joint.fit_cylinder"
    bl_label = "Fit a cylinder to a selected mesh"
    bl_description = "Fit a cylinder to a selected mesh"
        
    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)

        n = len(verts_x)  # Number of points
        points = np.stack((verts_x, verts_y, verts_z), axis=-1)  #reorder for the script input


        ### fitting starts here
        from .fit_cylinder_eberly import (preprocess, G, fit_cylinder)
        minError, C, W, rSqr = fit_cylinder(n, points)  #C is the center, W is the cylinder axis direction, rSqr = radius squared

        ### fitting ends here

        Radius = np.sqrt(rSqr)
        # Ensure W is a unit vector
        W = W / np.linalg.norm(W)  #this is the cylinder axis vector
            
            
        z_axis = Vector((0,0,1))
        quat_diff = z_axis.rotation_difference(Vector(W))  #this gives a unit quaternion for a rotation matrix gRb
        
        from .quaternions import matrix_from_quaternion
        gRb, bRg = matrix_from_quaternion(quat_diff)  #get the rotation matrix

              
        #Compute the desired height of the cylinder by checking the extent of the points along the cylinder axis
            
        #vertices in with respect to cylinder center
        verts_x_C = verts_x - C[0]
        verts_y_C = verts_y - C[1]
        verts_z_C = verts_z - C[2]

        vert_b = [] #vertices in the body-fixed frame of the cylinder

        for v in range(len(verts_x_C)):
            vert_b.append(bRg @ Vector([verts_x_C[v],verts_y_C[v],verts_z_C[v]]))  #rotate the vertex positions to body-fixed frame of the fitted cylinder
            
        vertical_cylinder_coordinates = [v[2] for v in vert_b]  #z is the cylinder axis, so this gives all the z-coordinates of the input data, in the frame of the fitted cylinder
            
        max_height = np.max(vertical_cylinder_coordinates)  #wrt cylinder origin, this is always positive
        min_height = np.min(vertical_cylinder_coordinates)  #wrt cylinder origin ,this is always negative


        cylinder_height = max_height - min_height #in meters

        position_offset_local = (max_height + min_height)/2 # the cylinder's position is not centered around the extremes of the data if the data is not symmetric about the z axis. We will acount for this when setting the position

        position_offset_glob = gRb @ Vector([0, 0, position_offset_local])


        # construct a world matrix for the cylinder
        worldMat = gRb.to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

        for i in range(len(C)):
            
            worldMat[i][3] = C[i] + position_offset_glob[i]  #set the fourth column as the location, including the offeset we just computed

        
        bpy.ops.mesh.primitive_cylinder_add(radius=Radius, depth=cylinder_height, end_fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD')
        fit_obj_name = obj_name + '_CylinderFit'
        bpy.context.active_object.name = fit_obj_name
        bpy.context.active_object.matrix_world = worldMat

        obj = bpy.data.objects[fit_obj_name]

        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['cylinder_radius'] =  Radius   #to inform the user what type is created
        obj.id_properties_ui('cylinder_radius').update(description = "Radius of the fitted cylinder (in m)")

        obj['cylinder_height'] =  cylinder_height  #to inform the user what type is created
        obj.id_properties_ui('cylinder_height').update(description = "Height of the fitted cylinder (in m)")  


        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
        return {'FINISHED'}

class FitEllipsoidOperator(Operator):
    bl_idname = "joint.fit_ellipsoid"
    bl_label = "Fit an ellipsoid to a selected mesh"
    bl_description = "Fit a ellipsoid to a selected mesh"
    #source: https://github.com/marksemple/pyEllipsoid_Fit/blob/master/ellipsoid_fit.py
    #based on: https://nl.mathworks.com/matlabcentral/fileexchange/24693-ellipsoid-fit
    #Pasha van Bijlert modified this code to add a check for right-handed coordinate systems
    
    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, input verts x, verts_y, verts_z
        mode = '' #set to 0 if you want 6DOF mode, otherwise it's 9 DOF
        X = verts_x
        Y = verts_y
        Z = verts_z

        # AlGEBRAIC EQUATION FOR ELLIPSOID, from CARTESIAN DATA
        if mode == '':  # 9-DOF MODE
            D = np.array([X * X + Y * Y - 2 * Z * Z,
                        X * X + Z * Z - 2 * Y * Y,
                        2 * X * Y, 2 * X * Z, 2 * Y * Z,
                        2 * X, 2 * Y, 2 * Z,
                        1 + 0 * X]).T

        elif mode == 0:  # 6-DOF MODE (no rotation)
            D = np.array([X * X + Y * Y - 2 * Z * Z,
                        X * X + Z * Z - 2 * Y * Y,
                        2 * X, 2 * Y, 2 * Z,
                        1 + 0 * X]).T

        

        # THE RIGHT-HAND-SIDE OF THE LLSQ PROBLEM
        d2 = np.array([X * X + Y * Y + Z * Z]).T

        # SOLUTION TO NORMAL SYSTEM OF EQUATIONS
        u = np.linalg.solve(D.T.dot(D), D.T.dot(d2))
        # chi2 = (1 - (D.dot(u)) / d2) ^ 2

        # CONVERT BACK TO ALGEBRAIC FORM
        if mode == '':  # 9-DOF-MODE
            a = np.array([u[0] + 1 * u[1] - 1])
            b = np.array([u[0] - 2 * u[1] - 1])
            c = np.array([u[1] - 2 * u[0] - 1])
            v = np.concatenate([a, b, c, u[2:, :]], axis=0).flatten()

        elif mode == 0:  # 6-DOF-MODE
            a = u[0] + 1 * u[1] - 1
            b = u[0] - 2 * u[1] - 1
            c = u[1] - 2 * u[0] - 1
            zs = np.array([0, 0, 0])
            v = np.hstack((a, b, c, zs, u[2:, :].flatten()))

        else:
            pass

        # PUT IN ALGEBRAIC FORM FOR ELLIPSOID
        A = np.array([[v[0], v[3], v[4], v[6]],
                    [v[3], v[1], v[5], v[7]],
                    [v[4], v[5], v[2], v[8]],
                    [v[6], v[7], v[8], v[9]]])

        # FIND CENTRE OF ELLIPSOID
        centre = np.linalg.solve(-A[0:3, 0:3], v[6:9])

        # FORM THE CORRESPONDING TRANSLATION MATRIX
        T = np.eye(4)
        T[3, 0:3] = centre

        # TRANSLATE TO THE CENTRE, ROTATE
        R = T.dot(A).dot(T.T)

        # SOLVE THE EIGENPROBLEM
        evals, evecs = np.linalg.eig(R[0:3, 0:3] / -R[3, 3])
        
        
        # addition by PvB: 
        # check if this forms a right-handed coordinate system:
        # cross(vec_x, vec_y) = vec_z in a right-handed coordinate system.
        # If it is minus vec_z, then the magnitude of their difference will be larger than zero. 
        #In that case we flip the eigenvector direction. Eigenvalue remains unchanged.
        
        vec_x = evecs[:,0]#eigenvectors which will form the rotation matrix.
        vec_y = evecs[:,1] 
        vec_z = evecs[:,2]

        
        threshold = 0.0001

        if np.linalg.norm(np.cross(vec_x,vec_y) - vec_z) > threshold:  
            
            evecs[:,2] = -evecs[:,2]
        
        

        # SORT EIGENVECTORS
        # i = np.argsort(evals)
        # evals = evals[i]
        # evecs = evecs[:, i]
        # evals = evals[::-1]
        # evecs = evecs[::-1]

        # CALCULATE SCALE FACTORS AND SIGNS
        radii = np.sqrt(1 / abs(evals))
        sgns = np.sign(evals)
        radii *= sgns
        ### fitting ends here, output evecs (rotation matrix gRb), centre, radii


        worldMat =Matrix(evecs).to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

        for i in range(len(centre)):
            
            worldMat[i][3] = centre[i]  #set the fourth column as the location


        bpy.ops.mesh.primitive_uv_sphere_add()
        fit_obj_name = obj_name + '_EllipsoidFit'
        bpy.context.active_object.name = fit_obj_name
        
        bpy.context.active_object.matrix_world = worldMat
        bpy.context.active_object.scale = Vector(radii)  #initial radius of sphere is 1. radii is xyz radius in meters. Ellipsoid scale factor is radii[r]/sphere_radius, so each radius can just be set as the scale factor
        bpy.ops.object.transform_apply(scale=True)

        obj = bpy.data.objects[fit_obj_name]

        
        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['ellipsoid_radii'] =  radii   #Ellipsoid radii
        obj.id_properties_ui('ellipsoid_radii').update(description = "Radii of the fitted ellipsoid (x, y, z, in m)")

        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
        return {'FINISHED'}

class FitPlaneOperator(Operator):
    bl_idname = "joint.fit_plane"
    bl_label = "Fit a plane to a selected mesh"
    bl_description = "Fit a plane to a selected mesh"
        
    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, inputs verts_x, verts_y, verts_z
        point_data = np.array([verts_x, verts_y, verts_z]).T
        centroid = point_data.mean(axis=0)
        verts_centered = point_data - centroid
        cov_mat = np.cov(verts_centered.T)  #covariance matrix
        eval, evec = np.linalg.eig(cov_mat) #eigen values, eigen vectors. #The eigenvector corresponding to the lowest value is the fitted-plane normal.
        new_order = eval.argsort()[::-1]  #descending order by eigenvalue size. 
        eval = eval[new_order]
        evec = evec[:, new_order] #sorted by eigenvalue size

        threshold = 0.0001
        #evec forms a 3x3 gRb rotation matrix. Check if it is right-handed, and otherwise flip z-axis
        if np.linalg.norm(np.cross(evec[:,0],evec[:,1]) - evec[:,2]) > threshold:  
                
            evec[:,2] = -evec[:,2]

        ### fitting ends here outputs evec (rotation matrix gRb)


        gRb = Matrix(evec)  #local to global rotation matrix

        worldMat =gRb.to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

        for i in range(len(centroid)):
            worldMat[i][3] = centroid[i] 
            
        bRg = np.array(gRb).T  #global to local transformation matrix


        verts_local = []

        #find the local position of all the plane points
        for v in range(len(verts_centered)):  #loop through all the vertices, transform to local coordinates
            verts_local.append(bRg @ verts_centered[v,:])
            
        verts_local = np.array(verts_local)

        #this will form the dimensions of our new plane
        x_max = np.max(verts_local[:, 0])
        x_min = np.min(verts_local[:, 0])
        y_max = np.max(verts_local[:, 1])
        y_min = np.min(verts_local[:, 1])    
            
        plane_x_dim = x_max - x_min  #x size in meters
        plane_y_dim = y_max - y_min  #y size in meters

        bpy.ops.mesh.primitive_plane_add(size=1, align='WORLD')

        fit_obj_name = obj.name + '_PlaneFit'
        bpy.context.active_object.name = fit_obj_name
        bpy.context.active_object.matrix_world = worldMat

        bpy.context.active_object.scale = Vector([plane_x_dim, plane_y_dim, 1])

        bpy.ops.object.transform_apply(scale=True)

        obj = bpy.data.objects[fit_obj_name]

        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['plane_dimensions'] =  [plane_x_dim, plane_y_dim]   #Ellipsoid radii
        obj.id_properties_ui('plane_dimensions').update(description = "Dimensions of the fitted plane (x and y, in m)")
        
        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
        return {'FINISHED'}
    
class MatchOrientationOperator(Operator):
    bl_idname = "joint.match_orientation"
    bl_label = "This button matches a joint to a another object's orientation"
    bl_description = "This button matches a joint to a another object's orientation"
        
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname


        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select one fitted geometry, and one target joint")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select one fitted geometry, and one target joint")
            return {'FINISHED'}
        joint = bpy.data.objects[joint_name]

        if joint not in sel_obj:
            self.report({'ERROR'}, "Neither of the selected objects is the target joint. Selected joint and joint_name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}

        target_obj = [ob for ob in sel_obj if ob.name != joint_name][0]

        child_body = False #gets overwritten if there is a child

        if len(joint.children) != 0: #if the joint has a child, unparent it before modifying the joint
            
            child_body = joint.children[0]
            #clear the parent, without moving the joint
            parented_worldmatrix =child_body.matrix_world.copy() 
            child_body.parent = None
            child_body.matrix_world = parented_worldmatrix 

              
            joint['pos_in_child_frame'] = [nan, nan, nan]
            joint['or_in_child_frame_XYZeuler'] = [nan, nan, nan]
            joint['or_in_child_frame_quat'] = [nan, nan, nan, nan]  

        
        worldMatrix = target_obj.matrix_world.copy() #get a copy the target object transformation matrix
        worldMatrix.translation = joint.matrix_world.translation  #ensure the original joints translation doesn't get lost.

        joint.matrix_world = worldMatrix
        
        from .quaternions import quat_from_matrix
        from .euler_XYZ_body import euler_XYZbody_from_matrix

        # reset orientations in global

        joint['or_in_global_XYZeuler'] = euler_XYZbody_from_matrix(joint.matrix_world.to_3x3())
        joint['or_in_global_quat'] = quat_from_matrix(joint.matrix_world.to_3x3())



        if child_body: #reparent the child and recompute the transformations in child frame

            
            child_body.parent = joint

            #this undoes the transformation after parenting
            child_body.matrix_parent_inverse = joint.matrix_world.inverted()

            joint['child_body'] = child_body.name

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
       
        if joint.parent: #If the joint has a parent, recompute all the transformations in parent

            parent_body = bpy.data.objects[joint['parent_body']]

            if parent_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
            
                                
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

class MatchPositionOperator(Operator):
    bl_idname = "joint.match_position"
    bl_label = "This button matches a joint to a another object's position"
    bl_description = "This button matches a joint to a another object's position"
        
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname


        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint

         # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select one fitted geometry, and one target joint")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select one fitted geometry, and one target joint")
            return {'FINISHED'}
        joint = bpy.data.objects[joint_name]

        if joint not in sel_obj:
            self.report({'ERROR'}, "Neither of the selected objects is the target joint. Selected joint and joint_name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}

        target_obj = [ob for ob in sel_obj if ob.name != joint_name][0]


        child_body = False #gets overwritten if there is a child

        if len(joint.children) != 0: #if the joint has a child, unparent it before modifying the joint
            
            child_body = joint.children[0]
            #clear the parent, without moving the joint
            parented_worldmatrix =child_body.matrix_world.copy() 
            child_body.parent = None
            child_body.matrix_world = parented_worldmatrix 

              
            joint['pos_in_child_frame'] = [nan, nan, nan]
            joint['or_in_child_frame_XYZeuler'] = [nan, nan, nan]
            joint['or_in_child_frame_quat'] = [nan, nan, nan, nan]  

        position = target_obj.matrix_world.translation.copy() #get a copy the target object transformation matrix
        joint.matrix_world.translation = position

        #Update custom property of global pos
        joint['pos_in_global'] = list(position) #

        if child_body: #reparent the child and recompute the transformations in child frame

            
            child_body.parent = joint

            #this undoes the transformation after parenting
            child_body.matrix_parent_inverse = joint.matrix_world.inverted()

            joint['child_body'] = child_body.name

            if child_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in child
                ## import functions euler angles and quaternions from matrix

                from .quaternions import quat_from_matrix
                from .euler_XYZ_body import euler_XYZbody_from_matrix
                
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
    

        if joint.parent: #If the joint has a parent, recompute all the transformations in parent

            parent_body = bpy.data.objects[joint['parent_body']]

            if parent_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
            
                ## import functions euler angles and quaternions from matrix

                from .quaternions import quat_from_matrix
                from .euler_XYZ_body import euler_XYZbody_from_matrix
                
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
        row.operator("joint.reflect_rightside_joints", text="Reflect right-side joints")

        row = self.layout.row()
        row.operator("joint.fit_sphere_geometric", text="Fit a sphere (geometric)")
        row.operator("joint.fit_sphere_ls", text="Fit a sphere (least-squares)")
        
        row = self.layout.row()
        row.operator("joint.fit_cylinder", text="Fit a cylinder")

        row = self.layout.row()
        row.operator("joint.fit_ellipsoid", text="Fit an ellipsoid")

        row = self.layout.row()
        row.operator("joint.fit_plane", text="Fit a plane")

        row = self.layout.row()
        row.operator("joint.match_position", text="Match position")
        row.operator("joint.match_orientation", text="Match orientation")


       