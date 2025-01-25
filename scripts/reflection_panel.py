import bpy
from bpy.types import (Panel,
                        Operator,
                        )
from mathutils import (Vector,
                       Matrix)

from math import nan

from .. import VIEW3D_PT_MuSkeMo


class ReflectionMixinClass: #mixin class to share functionality across all the reflection operators
    
    def get_reflection_vector(self, plane):
        """Returns the reflection vector based on the selected plane that gets passed to this function."""
        if plane == 'XY':
            return Vector((1, 1, -1, 1))  # Negative Z
        elif plane == 'YZ':
            return Vector((-1, 1, 1, 1))  # Negative X
        elif plane == 'XZ':
            return Vector((1, -1, 1, 1))  # Negative Y
        

    def get_reflection_matrix(self, plane):
        """Returns the reflection vector based on the selected plane that gets passed to this function."""
        if plane == 'XY':
            return Matrix([(1, 0, 0,),(0, 1, 0), (0, 0, -1)])  # Negative Z
        elif plane == 'YZ':
            return Matrix([(-1, 0, 0,),(0, 1, 0), (0, 0, 1)])  # Negative X
        elif plane == 'XZ':
            return Matrix([(1, 0, 0,),(0, -1, 0), (0, 0, 1)])  # Negative Y    

    
    def get_unilateral_objects(self, objects, object_names, left_string, right_string):
        "Returns the unilateral objects based on whether or not they end with the left or right side string"
        unilateral_objects = (obj for obj in objects if 
            (obj.name.endswith(right_string) and obj.name[0:-len(right_string)]+left_string not in object_names) or
            (obj.name.endswith(left_string) and obj.name[0:-len(left_string)]+right_string not in object_names)
            )

        return unilateral_objects
class ReflectUnilateralBodiesOperator(Operator, ReflectionMixinClass): #inherits functions from the mixin class
    bl_idname = "body.reflect_unilateral_bodies"
    bl_label = "Reflects unilateral bodies across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    bl_description = "Reflects unilateral bodies across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        colname = muskemo.body_collection

        collection = bpy.data.collections[colname]

        bodies = [obj for obj in collection.objects if obj['MuSkeMo_type'] == 'BODY']
        body_names = [obj.name for obj in bodies]

       
        right_string = muskemo.right_side_string
        left_string = muskemo.left_side_string

        reflection_plane = muskemo.reflection_plane

        reflect_mat =  self.get_reflection_matrix(reflection_plane) 

        size = bpy.context.scene.muskemo.axes_size #axis length, in meters

        from .create_body_func import create_body

        unilateral_bodies = self.get_unilateral_objects(bodies, body_names, left_string=left_string, right_string=right_string)

        for obj in unilateral_bodies:
            
            if right_string in obj.name: #if right_side_string is in the name, that's the current side of the object.
                  
                currentside = right_string #this is the side we DO have
                otherside = left_string #the side we are creating

            else: #if right_string is not in the name, the current side is the left side.
                currentside = left_string #this is the side we DO have
                otherside = right_string #the side we are creating

            body_name = obj.name[0:-len(currentside)] + otherside #rename to otherside

            inertia_COM_currentside = obj['inertia_COM']
            inertia_COM_currentside_mat = Matrix([
                (inertia_COM_currentside[0],inertia_COM_currentside[3] ,inertia_COM_currentside[4] ),
                (inertia_COM_currentside[3],inertia_COM_currentside[1] ,inertia_COM_currentside[5] ),
                (inertia_COM_currentside[4],inertia_COM_currentside[5] ,inertia_COM_currentside[2] )
                ])

            inertia_COM_otherside_mat = reflect_mat @ inertia_COM_currentside_mat @ reflect_mat.inverted()
            inertia_COM_otherside = [inertia_COM_otherside_mat[0][0],inertia_COM_otherside_mat[1][1], inertia_COM_otherside_mat[2][2],
                                     inertia_COM_otherside_mat[0][1],inertia_COM_otherside_mat[0][2], inertia_COM_otherside_mat[1][2]]
            
            COM_currentside = Vector(obj['COM'])
            COM_otherside = reflect_mat @ COM_currentside

            COM_otherside = [x for x in COM_otherside] #convert vector to list

            create_body(name = body_name, size=size, self = self,
                is_global = True, 
                mass=obj['mass'],
                inertia_COM= inertia_COM_otherside, 
                COM=COM_otherside, 
                inertia_COM_local=[nan]*6, 
                COM_local=[nan]*3, 
                Geometry='no geometry', 
                local_frame='not_assigned', 
                collection_name = colname)
            
        return {"FINISHED"}



                                    

class ReflectUnilateralMusclesOperator(Operator, ReflectionMixinClass): #inherits functions from the mixin class
    bl_idname = "muscle.reflect_unilateral_muscles"
    bl_label = "Reflects unilateral muscles across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    bl_description = "Reflects unilateral muscles across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        colname = muskemo.muscle_collection

        collection = bpy.data.collections[colname]

        muscles = [obj for obj in collection.objects if obj['MuSkeMo_type'] == 'MUSCLE']
        muscle_names = [obj.name for obj in muscles]

       
        right_string = muskemo.right_side_string
        left_string = muskemo.left_side_string

        reflection_plane = muskemo.reflection_plane

        reflect_vect = self.get_reflection_vector(reflection_plane)   

        from .create_muscle_func import create_muscle


        unilateral_muscles = self.get_unilateral_objects(muscles, muscle_names, left_string=left_string, right_string=right_string)

        for obj in unilateral_muscles:

       
            
            if right_string in obj.name: #if right_side_string is in the name, that's the current side of the object.
                  
                currentside = right_string #this is the side we DO have
                otherside = left_string #the side we are creating

            else: #if right_string is not in the name, the current side is the left side.
                currentside = left_string #this is the side we DO have
                otherside = right_string #the side we are creating

            muscle_name = obj.name[0:-len(currentside)] + otherside #rename to otherside
                                    
            F_max = obj['F_max']
            pennation_angle = obj['pennation_angle'] 
            optimal_fiber_length = obj['optimal_fiber_length']
            tendon_slack_length = obj['tendon_slack_length']

            '''
            new_obj = obj.copy()  #copy object
            new_obj.data = obj.data.copy() #copy object data
            new_obj.name = obj.name.replace(currentside,otherside) #rename to left
            
            collection.objects.link(new_obj)  #add to Muscles collection
            '''
            
            
            modifier_list = [x.name for x in obj.modifiers if 'Hook'.casefold() in x.name.casefold()] #list of all the hook modifiers that are added to this curve

            #if muscle_current_position_export:
            #    curve_ev = curve.to_curve(depsgraph, apply_modifiers=True)
            ### loop through points

            for i in range(0, len(obj.data.splines[0].points)): #for each point
                
                body_name = ''   #this gets overwritten unless a muscle is currently unhooked
                newbodyname = ''
                
                for h in range(len(modifier_list)):               #for each hook modifier that is added to this curve
                    modifier = obj.modifiers[modifier_list[h]]  #modifier is the h'th modifier in the list
                    for j in range(len(modifier.vertex_indices)): #vertex index = connected curve point, so for each connected curve point j, which starts counting at 0
                        if i == modifier.vertex_indices[j]:       
                            body_name_curr = modifier.object.name      #if curve point i equals a connected curve point j in modifier h, get the corresponding body name
                            
                            if body_name_curr.endswith(currentside): #if it is a sided body
                                
                                newbodyname = body_name_curr[0:-len(currentside)] + otherside #rename to otherside
                                                        
                                if newbodyname not in bpy.data.objects:# if the body doesn't exist
                                    self.report({'WARNING'}, "BODY with the name '" + newbodyname + "' Does not exist. Create it using the body mirroring button. '" + muscle_name  +  "' MUSCLE currently has unhooked points.")
                        
                                else: #if the body exists, we pass it to  the muscle point creation function, otherwise the point gets created without hooking it to anything
                                    body_name = newbodyname

                            else: #if it wasn't a sided body, we leave it hooked to the same side
                                body_name = body_name_curr

                #reflect each point about z

                point_position = obj.data.splines[0].points[i].co*reflect_vect

                
                create_muscle(muscle_name=muscle_name,
                            point_position=point_position,
                            body_name = body_name,
                            collection_name= colname,
                            F_max=F_max,
                            pennation_angle=pennation_angle,
                            optimal_fiber_length=optimal_fiber_length,
                            tendon_slack_length=tendon_slack_length)
                    
                
                    
            '''      

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
                        

                if 'NODES' == mod.type: #if it's a geometry nodes modifier
                
                    if 'SimpleMuscleViz' in mod.name:  #(the simple muscle viz) 
                        mod.node_group.nodes['Set Material'].inputs['Material'].default_value = newmat   
                        mod.name.replace(currentside, otherside)
                        #create a new nodegroup.

                    #if VolMuscle
                    # 
                    # 
                    #if wrap in mod.name:    

            '''  
        return {'FINISHED'}
    

class ReflectUnilateralWrapsOperator(Operator, ReflectionMixinClass): #inherits functions from the mixin class
    bl_idname = "muscle.reflect_unilateral_wraps"
    bl_label = "Reflects unilateral wrapping geometries across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version. If the target muscles exist, also assigns the wraps to designated muscles."
    bl_description = "Reflects unilateral muscles across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version. If the target muscles exist, also assigns the wraps to designated muscles."
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        colname = muskemo.wrap_geom_collection

        collection = bpy.data.collections[colname]

        wraps = [obj for obj in collection.objects if obj['MuSkeMo_type'] == 'WRAP']
        wrap_names = [obj.name for obj in wraps]

       
        right_string = muskemo.right_side_string
        left_string = muskemo.left_side_string

        reflection_plane = muskemo.reflection_plane

        reflect_vect = self.get_reflection_vector(reflection_plane)
        reflect_mat = self.get_reflection_matrix(reflection_plane)   

        from .create_wrapgeom_func import create_wrapgeom
        from .quaternions import quat_from_matrix
        from .euler_XYZ_body import euler_XYZbody_from_matrix


        unilateral_wraps = self.get_unilateral_objects(wraps, wrap_names, left_string=left_string, right_string=right_string)

        for obj in unilateral_wraps:
            
            if right_string in obj.name: #if right_side_string is in the name, that's the current side of the object.
                  
                currentside = right_string #this is the side we DO have
                otherside = left_string #the side we are creating

            else: #if right_string is not in the name, the current side is the left side.
                currentside = left_string #this is the side we DO have
                otherside = right_string #the side we are creating

            #create the reflected wrap name
            wrap_name = obj.name[0:-len(currentside)] + otherside #rename to otherside

            geomtype = obj['wrap_type']
            dimensions = {} #preallocate
            
            #for now only cylinders exist
            if geomtype.lower() == 'cylinder':
                
                dimensions['radius'] = obj.modifiers['WrapObjMesh']["Socket_1"]
                dimensions['height'] = obj.modifiers['WrapObjMesh']["Socket_2"]

            #check if the mirrored parent exists
            if obj['parent_body'] !='not_assigned':
                original_pbname = obj['parent_body']

                if original_pbname.endswith(currentside): #if the pbody is also sided

                    reflected_pbname = original_pbname[0:-len(currentside)] + otherside #get the reflected parent body name

                    if reflected_pbname in bpy.data.objects:
                        parent_body_name = reflected_pbname

                    else:
                        self.report({'WARNING'}, "BODY with the name '" + reflected_pbname + "' Does not exist. Create it using the body mirroring button. '" + wrap_name  +  "' WRAP currently unparented.")
                            
                        parent_body_name = 'not_assigned'

                else:#if not a sided pbody

                    parent_body_name = original_pbname


            #compute the global position and orientation
            obj_wm = obj.matrix_world.copy()

            pos_in_global = reflect_mat @ obj_wm.translation #reflect the vector using the reflection matrix
            or_in_global_mat = reflect_mat @ obj_wm.to_3x3() @ reflect_mat #change of basis transformation
            or_in_global_quat = quat_from_matrix(or_in_global_mat)
            or_in_global_XYZeuler = euler_XYZbody_from_matrix(or_in_global_mat)

            ### check if parent_body has a local frame, and if yes, compute wrap location in parent frame 
            if parent_body_name != 'not_assigned':
                if bpy.data.objects[parent_body_name]['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
                
                ## import functions euler angles and quaternions from matrix

                    
                    local_frame_name = bpy.data.objects[parent_body_name]['local_frame']
                    frame = bpy.data.objects[local_frame_name]

                    gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
                    bRg = gRb.copy()
                    bRg.transpose()
            
                    frame_or_g = frame.matrix_world.translation    
                
                    wrap_pos_g = pos_in_global #location of the wrap
                    gRb_wrap = or_in_global_mat #gRb rotation matrix of wrap
                    wrap_pos_in_parent = bRg @ (wrap_pos_g - frame_or_g) #location in parent of wrap
                                                
                    b_R_wrapframe = bRg @ gRb_wrap #rotation matrix from wrap frame to parent frame - decompose this for orientation in parent
                    
                    wrap_or_in_parent_euler = euler_XYZbody_from_matrix(b_R_wrapframe) #XYZ body-fixed decomposition of orientation in parent
                    wrap_or_in_parent_quat = quat_from_matrix(b_R_wrapframe) #quaternion decomposition of orientation in parent
                else:
                    wrap_pos_in_parent = [nan]*3    
                    wrap_or_in_parent_euler = [nan]*3  
                    wrap_or_in_parent_quat = [nan]*4  


            create_wrapgeom(name = wrap_name, 
                            geomtype = geomtype, 
                            collection_name = colname,
                            parent_body=parent_body_name, 
                            pos_in_global=pos_in_global,
                            or_in_global_XYZeuler=or_in_global_XYZeuler, 
                            or_in_global_quat=or_in_global_quat,
                            pos_in_parent_frame=wrap_pos_in_parent,
                            or_in_parent_frame_XYZeuler=wrap_or_in_parent_euler, 
                            or_in_parent_frame_quat=wrap_or_in_parent_quat,
                            dimensions = dimensions,
                            )
            
            new_wrapobj = bpy.data.objects[wrap_name]

            if obj['target_muscles']!= 'not_assigned': #if the original wrap had muscles assigned

                target_muscles = [x for x in obj['target_muscles'].split(';') if x]

                for muscle_name in target_muscles:
                    
                    muscle_name_refl = muscle_name[0:-len(currentside)] + otherside
                    
                    if muscle_name_refl in bpy.data.objects:
                        bpy.ops.object.select_all(action='DESELECT')
                        new_wrapobj.select_set(True)

                        muskemo.musclename = muscle_name_refl#THIS CAN BE DELETED LATER
                        bpy.ops.muscle.assign_wrapping()
                        bpy.ops.object.select_all(action='DESELECT')

                        #original muscle and wrap
                        muscle = bpy.data.objects[muscle_name]
                        modifier = muscle.modifiers[muscle_name + '_wrap_' + obj.name]
                        
                        muscle_refl = bpy.data.objects[muscle_name_refl] #reflected muscle
                        modifier_refl = muscle_refl.modifiers[muscle_name_refl + '_wrap_' + wrap_name]

                        for x in range(5,11): #automatically generate strings for Socket_5, Socket_6, etc. till 10
                            socket = "Socket_" + str(x)
                            modifier_refl[socket] = modifier[socket]
                        
                        modifier_refl.show_viewport = not modifier_refl.show_viewport  # Toggle visibility to refresh in the viewport
                        modifier_refl.show_viewport = not modifier_refl.show_viewport
                        
                    else:
                        self.report({'WARNING'}, "MUSCLE with the name '" + muscle_name_refl + "' does not exist, so it will not be assigned to '" + wrap_name  +  "' WRAP.")
                    
                             
           
        return {'FINISHED'}    


class ReflectUnilateralFramesOperator(Operator, ReflectionMixinClass): #inherits functions from the mixin class
    bl_idname = "frame.reflect_unilateral_frames"
    bl_label = "Reflects unilateral frames across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    bl_description = "Reflects unilateral frame across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        colname = muskemo.frame_collection

        collection = bpy.data.collections[colname]

        frames = [obj for obj in collection.objects if obj['MuSkeMo_type'] == 'FRAME']
        frame_names = [obj.name for obj in frames]

       
        right_string = muskemo.right_side_string
        left_string = muskemo.left_side_string

        reflection_plane = muskemo.reflection_plane

        reflect_mat =  self.get_reflection_matrix(reflection_plane) 

        size = bpy.context.scene.muskemo.frame_axes_size #axis length, in meters

        from .create_frame_func import create_frame

        unilateral_frames = self.get_unilateral_objects(frames, frame_names, left_string=left_string, right_string=right_string)

        for obj in unilateral_frames:
            
            if right_string in obj.name: #if right_side_string is in the name, that's the current side of the object.
                  
                currentside = right_string #this is the side we DO have
                otherside = left_string #the side we are creating

            else: #if right_string is not in the name, the current side is the left side.
                currentside = left_string #this is the side we DO have
                otherside = right_string #the side we are creating

            frame_name = obj.name[0:-len(currentside)] + otherside #rename to otherside

            current_side_wm = obj.matrix_world.copy()

            pos_in_global_refl = reflect_mat @ current_side_wm.translation #reflect position 

            gRb_refl =  reflect_mat @ current_side_wm.to_3x3() @ reflect_mat.inverted() #change of basis

            create_frame(name = frame_name,
                             size = size,
                 pos_in_global = pos_in_global_refl,
                   gRb = gRb_refl, 
                    collection_name = colname,
                    parent_body = 'not_assigned',)
            
            #check if the mirrored parent exists
            if obj['parent_body'] !='not_assigned':
                original_pbname = obj['parent_body']

                if original_pbname.endswith(currentside): #if the pbody is also sided

                    reflected_pbname = original_pbname[0:-len(currentside)] + otherside #get the reflected parent body name

                else:#if not a sided pbody

                    reflected_pbname = original_pbname   

                if not reflected_pbname in bpy.data.objects:
                        
                    self.report({'WARNING'}, "BODY with the name '" + reflected_pbname + "' does not exist, so it will not be assigned as a parent to '" + frame_name  +  "' FRAME.")
                       
                else:
                        
                    bpy.ops.object.select_all(action='DESELECT')
                    
                    [bpy.data.objects[x].select_set(True) for x in [frame_name, reflected_pbname]] #set the selection for the correct objects
                    muskemo.framename = frame_name #THIS CAN BE DELETED LATER

                    bpy.ops.frame.assign_parent_body()
                    bpy.ops.object.select_all(action='DESELECT')    	        
                
            
        return {"FINISHED"}

class ReflectUnilateralJointsOperator(Operator, ReflectionMixinClass): #inherits functions from the mixin class
    bl_idname = "joint.reflect_unilateral_joints"
    bl_label = "Reflects unilateral joints across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    bl_description = "Reflects unilateral joints across desired reflection plane if their names end with the right or left side string, and there is not already a reflected version."
    
    def execute(self, context):
        
        muskemo = bpy.context.scene.muskemo
        colname = muskemo.joint_collection

        collection = bpy.data.collections[colname]

        joints = [obj for obj in collection.objects if obj['MuSkeMo_type'] == 'JOINT']
        joint_names = [obj.name for obj in joints]

       
        right_string = muskemo.right_side_string
        left_string = muskemo.left_side_string

        reflection_plane = muskemo.reflection_plane

        reflect_mat =  self.get_reflection_matrix(reflection_plane) 

        radius = bpy.context.scene.muskemo.jointsphere_size #axis length, in meters

        from .create_joint_func import create_joint
        from .quaternions import quat_from_matrix
        from .euler_XYZ_body import euler_XYZbody_from_matrix

        unilateral_joints = self.get_unilateral_objects(joints, joint_names, left_string=left_string, right_string=right_string)

        for obj in unilateral_joints:
            
            if right_string in obj.name: #if right_side_string is in the name, that's the current side of the object.
                  
                currentside = right_string #this is the side we DO have
                otherside = left_string #the side we are creating

            else: #if right_string is not in the name, the current side is the left side.
                currentside = left_string #this is the side we DO have
                otherside = right_string #the side we are creating

            joint_name = obj.name[0:-len(currentside)] + otherside #rename to otherside

            current_side_wm = obj.matrix_world.copy()

            pos_in_global_refl = reflect_mat @ current_side_wm.translation #reflect position 

            gRb_refl =  reflect_mat @ current_side_wm.to_3x3() @ reflect_mat.inverted() #change of basis
            or_in_global_quat_refl = quat_from_matrix(gRb_refl)
            or_in_global_XYZeuler_refl = euler_XYZbody_from_matrix(gRb_refl)

            create_joint(name = joint_name,
                             radius = radius,
                 pos_in_global = pos_in_global_refl,
                   or_in_global_quat = or_in_global_quat_refl, 
                   or_in_global_XYZeuler=or_in_global_XYZeuler_refl,
                    collection_name = colname,
                    parent_body = 'not_assigned',)
            
            #check if the mirrored parent exists
            if obj['parent_body'] !='not_assigned':
                original_pbname = obj['parent_body']

                if original_pbname.endswith(currentside): #if the pbody is also sided

                    reflected_pbname = original_pbname[0:-len(currentside)] + otherside #get the reflected parent body name

                else:#if not a sided pbody

                    reflected_pbname = original_pbname   

                if not reflected_pbname in bpy.data.objects:
                        
                    self.report({'WARNING'}, "BODY with the name '" + reflected_pbname + "' does not exist, so it will not be assigned as a parent to '" +  joint_name  +  "' JOINT.")
                       
                else:
                        
                    bpy.ops.object.select_all(action='DESELECT')
                    
                    [bpy.data.objects[x].select_set(True) for x in [joint_name, reflected_pbname]] #set the selection for the correct objects
                    muskemo.jointname = joint_name #THIS CAN BE DELETED LATER

                    bpy.ops.joint.assign_parent_body()
                    bpy.ops.object.select_all(action='DESELECT')    


            #check if the mirrored child exists
            if obj['child_body'] !='not_assigned':
                original_cbname = obj['child_body']

                if original_cbname.endswith(currentside): #if the cbody is also sided

                    reflected_cbname = original_cbname[0:-len(currentside)] + otherside #get the reflected child name

                else:#if not a sided cbody

                    reflected_cbname = original_cbname   

                if not reflected_cbname in bpy.data.objects:
                        
                    self.report({'WARNING'}, "BODY with the name '" + reflected_cbname + "' does not exist, so it will not be assigned as a child to '" +  joint_name  +  "' JOINT.")
                       
                else:
                        
                    bpy.ops.object.select_all(action='DESELECT')
                    
                    [bpy.data.objects[x].select_set(True) for x in [joint_name, reflected_cbname]] #set the selection for the correct objects
                    muskemo.jointname = joint_name #THIS CAN BE DELETED LATER

                    bpy.ops.joint.assign_child_body()
                    bpy.ops.object.select_all(action='DESELECT')    	           	        
                
                        
        return {"FINISHED"}


class VIEW3D_PT_reflection_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
   
    
    bl_label = "Reflection panel"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_idname = 'VIEW3D_PT_reflection_panel'

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
                    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()

        # Split row into four columns with desired proportions
        split = row.split(factor=4/10)  # First split for left label
        split_left_label = split.column()
        split_left_label.label(text="Left Side String")

        split = split.split(factor=1/6)  # Second split for left input field
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


        row = self.layout.row()

        split = row.split(factor = 1/3)
        split.label(text = 'Body collection')
        split = split.split(factor =1/2)
        split.prop(muskemo, "body_collection", text = "")
        split.operator("body.reflect_unilateral_bodies", text="Reflect unilateral bodies")

        row = self.layout.row()

        split = row.split(factor = 1/3)
        split.label(text = 'Frame collection')
        split = split.split(factor =1/2)
        split.prop(muskemo, "frame_collection", text = "")
        split.operator("frame.reflect_unilateral_frames", text="Reflect unilateral frames")

        row = self.layout.row()

        split = row.split(factor = 1/3)
        split.label(text = 'Joint collection')
        split = split.split(factor =1/2)
        split.prop(muskemo, "joint_collection", text = "")
        split.operator("joint.reflect_unilateral_joints", text="Reflect unilateral joints")

        row = self.layout.row()

        split = row.split(factor = 1/3)
        split.label(text = 'Muscle collection')
        split = split.split(factor =1/2)
        split.prop(muskemo, "muscle_collection", text = "")
        split.operator("muscle.reflect_unilateral_muscles", text="Reflect unilateral muscles")
        
        row = self.layout.row()

       
        split = row.split(factor = 1/3)
        split.label(text = 'Wrap Geometry collection')
        split = split.split(factor =1/2)
        split.prop(muskemo, "wrap_geom_collection", text = "")
        split.operator("muscle.reflect_unilateral_wraps", text="Reflect unilateral wraps")
        
        row = self.layout.row()

