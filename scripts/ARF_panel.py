# give Python access to Blender's functionality
import bpy
from mathutils import (Vector, Matrix)


from bpy.types import (Panel,
                        Operator)
import numpy as np
import math

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
        

        origin_landmark_name =  bpy.context.scene.muskemo.or_landmark_name
        ydir_landmark_name = bpy.context.scene.muskemo.ydir_landmark_name
        yzplane_landmark_name = bpy.context.scene.muskemo.yz_plane_landmark_name  #landmark to define YZ plane

        refframe_name = bpy.context.scene.muskemo.framename
        colname = bpy.context.scene.muskemo.frame_collection  #target collection

        rad = bpy.context.scene.muskemo.ARF_axes_size

        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene

        #make sure the collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]
        


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

        ### construct the transformation matrix
        worldMat = Matrix(gRl).to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

        for i in range(len(origin)):
            
            worldMat[i][3] = origin[i]  #set the fourth column as the location


        name = refframe_name #name of the object
        

        bpy.ops.object.empty_add(type='ARROWS', radius=rad, align='WORLD')
        bpy.context.object.name = name #set the name
        #bpy.context.object.data.name = name #set the name of the object data

        bpy.context.object.rotation_mode = 'ZYX'    #change rotation sequence

        #
        bpy.context.object.matrix_world = worldMat  #set the transformation matrix

        ## it's possible to calculate euler decomposition, but this is prone to gimbal lock.
        # phi_y = np.arcsin(gRl[0,2]) #alternative: phi_y = np.arctan2(gRl[0,2], math.sqrt(1 - (gRl[0,2])**2)) 
        # phi_x = np.arctan2(-gRl[1,2],gRl[2,2])    #angle alpha in wiki
        # phi_z = np.arctan2(-gRl[0,1],gRl[0,0])    #angle gamma in wiki

        #print('Manually computed XYZ Euler angles =')
        #print([phi_x, phi_y, phi_z])
        #bpy.context.object.rotation_euler = [phi_x, phi_y, phi_z]
        #bpy.context.object.location = origin

        bpy.context.object['MuSkeMo_type'] = 'FRAME'  #to inform the user what type is created
        bpy.context.object.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")

        bpy.context.object['parent_body'] = 'not yet assigned'    #to inform the user what type is created
        bpy.context.object.id_properties_ui('parent_body').update(description = "The parent body of this frame")  

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

        if parent_body['local_frame'] == 'not yet assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
     
            self.report({'ERROR'}, "Local transformations cannot be computed yet. Skipping for now")
            #Check for parent joint, set loc and rot in child
            #loop through child joints, set loc and rot in parent
            #Add COM extra properties COM loc_local, MOI_local
  
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
        
        frame['parent_body'] = 'not yet assigned'
        parent_body['local_frame'] = 'not yet assigned'

        if parent_body['local_frame'] != 'not yet assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
     
            self.report({'ERROR'}, "Local transformations cannot be computed yet. Skipping for now")
            #Check for parent joint, set loc and rot in child to NaN
            #loop through child joints, set loc and rot in parent to Nan
            #set COM extra properties COM to loc_local, MOI_local



        


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