# give Python access to Blender's functionality
import bpy
from mathutils import (Matrix, Vector)


from bpy.types import (Panel,
                        Operator,
                        )

from math import nan

import numpy as np
import bmesh

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed
    
## Operators
class SetRecommendedSnapSettingsOperator(Operator):
    bl_idname = "pktoolbox.set_recommended_snapping_settings"
    bl_label = "Set the recommend object snapping settings for projecting landmarks using their object centers."
    bl_description = "Set the recommended object snapping settings for projecting landmarks using their object centers."
    bl_options = {"UNDO"} #enable undoing
        
    def execute(self, context):

        bpy.data.scenes['Scene'].tool_settings.use_snap = True
        bpy.data.scenes['Scene'].tool_settings.snap_target = 'CENTER'
        bpy.data.scenes['Scene'].tool_settings.snap_elements_base = {'FACE'}

        return {'FINISHED'}



class CreateSagittalProjectionPlaneOperator(Operator):
    bl_idname = "pktoolbox.create_sagittal_projection_plane"
    bl_label = "Create a sagittal PROJECTION_PLANE from two footfall LANDMARKS and a fitted ground plane."
    bl_description = "Create a sagittal PROJECTION_PLANE from two footfall LANDMARKS and a fitted ground plane."
    bl_options = {"UNDO"} #enable undoing
        
    def execute(self, context):

        muskemo = bpy.context.scene.muskemo

        ## get the desired object name
        plane_name = muskemo.pk_sagittal_projection_plane_name

        if not plane_name:
            self.report({'ERROR'}, "Type in a desired name for the sagittal plane and try again.")
            return {'FINISHED'}
        
        if plane_name in bpy.data.objects:
            self.report({'ERROR'}, "You tried to create a new sagittal plane with the name '" + plane_name + "', but an object with that name already exists. Choose a unique name, or if you're trying to add a stride, use the 'Add stride' button.")
            return {'FINISHED'}

        ## Check if the pk_stride_start_frame was set, and if not, throw an error

        if 'pk_stride_start_frame' not in muskemo:
            self.report({'ERROR'}, "You didn't specify at what frame the stride starts.")
            return {'CANCELLED'}
        else:
            frame_number = muskemo.pk_stride_start_frame


        ## get the ground plane
        groundPlane = muskemo.pk_ground_plane #fitted ground plane from photogrammetry
        if not groundPlane:
            self.report({'ERROR'}, "You did not select a fitted ground plane")
            return {'FINISHED'}
        
        if groundPlane.scale != Vector((1,1,1)):
            self.report({'ERROR'}, "Ground plane object with name '" + groundPlane.name + "' has non-unit scale. Select it, hit control + A, and select 'Apply scale'. Operation cancelled.")
            return {'FINISHED'}

        #get landmark for footfall 1
        FootFall1LM = muskemo.pk_FF1_landmark #landmark of first footfall (projected on ground plane)

        if not FootFall1LM:
            self.report({'ERROR'}, "You did not select a landmark for the first footfall")
            return {'FINISHED'}

        #get landmark for footfall 2
        FootFall2LM = muskemo.pk_FF2_landmark #landmark of second footfall (projected on ground plane)

        if not FootFall2LM:
            self.report({'ERROR'}, "You did not select a landmark for the second footfall")
            return {'FINISHED'}
        
        if FootFall1LM == FootFall2LM:
            self.report({'ERROR'}, "The first and second footfall landmarks are the same object")
            return {'FINISHED'}
        
        if ((FootFall1LM == groundPlane) or (FootFall2LM == groundPlane)):
            self.report({'ERROR'}, "The fitted ground plane is the same object as one of the footfall landmarks")
            return {'FINISHED'}

        if not groundPlane.get('plane_dimensions'): #If the object is not a MuSkeMo fitted geometry plane, throw an error.
            self.report({'ERROR'},'The object designated as the ground plane does not appear to be a Plane mesh fitted by MuSkeMo.')
            return {'FINISHED'}
        

        ## The footfall landmarks must be coplanar with the groundplane, this means that their Z position in the ground plane frame must be zero. We check this explicitly.
        groundPlane_wm = groundPlane.matrix_world

        tolerance = 1e-6 #
        if abs((groundPlane_wm.transposed() @ (FootFall1LM.matrix_world.translation - groundPlane_wm.translation))[2]) > tolerance:
            self.report({'ERROR'}, "Footfall landmark 1 does not appear to be projected onto the fitted groundplane. Double check its position and ensure center snapping is on.")
            return {'FINISHED'}
        
        if abs((groundPlane_wm.transposed() @ (FootFall2LM.matrix_world.translation - groundPlane_wm.translation))[2]) > tolerance:
            self.report({'ERROR'}, "Footfall landmark 2 does not appear to be projected onto the fitted groundplane. Double check its position and ensure center snapping is on.")
            return {'FINISHED'}


        # Check for or create a collection for Projection planes
        collection_name = 'Projection planes'
        if collection_name not in bpy.data.collections:
            bpy.data.collections.new(collection_name)
            
        coll = bpy.data.collections[collection_name] #Collection which will recieve the frames

        if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]
    
        #global positions of the landmarks
        FF1pos = FootFall1LM.matrix_world.translation
        FF2pos = FootFall2LM.matrix_world.translation

        ## Construct the orientation of the sagittal plane
        x_dir = (FF2pos - FF1pos)
        x_dir.normalize()

        y_dir = groundPlane.matrix_world.to_3x3().col[2] #ground plane Z-dir will be y dir of the sagittal plane
        y_dir.normalize()

        z_dir = x_dir.cross(y_dir)

        if y_dir.dot(Vector((0,0,1)))<0:
            self.report({'ERROR'}, "Your ground plane may be upside down. Check whether the y-axis of your new sagittal plane is 'up'. If not, undo, and use 'flip plane' on your ground plane.")
       
        # Build 3×3 rotation matrix with columns = axes
        rot_mat = Matrix((
            x_dir,
            y_dir,
            z_dir,
        )).transposed()


        plane_origin = (FF1pos + FF2pos)/2 #set plane origin mat to the first footfall
        world_mat = rot_mat.to_4x4()
        world_mat.translation = plane_origin

        #global size of the sagittal plane. Can expose this to the user?
        size = 4*(FF2pos - FF1pos).length

        ## Create the plane
        bpy.ops.mesh.primitive_plane_add(size=size)
        bpy.context.active_object.name = plane_name

        sagittal_plane = bpy.data.objects[plane_name]
        sagittal_plane.rotation_mode = 'ZYX'  # Change rotation sequence
        sagittal_plane.matrix_world = world_mat


        ## Create the frame and assign parent body

        from .create_frame_func import create_frame

        frame_name = sagittal_plane.name + '_frame'

        create_frame(name = frame_name, size = muskemo.axes_size, pos_in_global = plane_origin, 
                     gRb = rot_mat)
        
        bpy.ops.object.select_all(action='DESELECT')
        
        frame_obj = bpy.data.objects[frame_name]
        frame_obj['MuSkeMo_type'] = 'PROJECTION_PLANE_FRAME'

        frame_obj.parent = sagittal_plane
            
        #this undoes the transformation after parenting
        frame_obj.matrix_parent_inverse = sagittal_plane.matrix_world.inverted()

        # Write the parent object
        frame_obj['parent_plane'] = sagittal_plane.name
        del frame_obj['parent_body']
        #make it always in front
        frame_obj.show_in_front = True

        ## Assign custom properties

        sagittal_plane['MuSkeMo_type'] = 'PROJECTION_PLANE'    #to inform the user what type is created
        sagittal_plane.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        sagittal_plane['current_stride'] =  1   
        sagittal_plane.id_properties_ui('current_stride').update(description = "The current stride number. If you have multiple strides, this changes if you navigate through the timeline.")

        sagittal_plane['stride_start_frames'] =  [frame_number]   
        sagittal_plane.id_properties_ui('stride_start_frames').update(description = "The starting frame of each stride.")


        #set keyframes for the plane
        keyframe_datapaths_plane = ['["current_stride"]', 'location', 'rotation_euler']

        for dp in keyframe_datapaths_plane:
            sagittal_plane.keyframe_insert(data_path=dp, frame=frame_number)


        action = sagittal_plane.animation_data.action
        if action:  # make sure the object has keyframes
            for fcurve in action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'CONSTANT'

        ## reset the plane name input
        muskemo.pk_sagittal_projection_plane_name = ''

        ## unset the pk_stride_start_frame input
        muskemo.property_unset("pk_stride_start_frame")
        
        ## reset FF1 and FF2 landmark objects
        muskemo.pk_FF1_landmark = None
        muskemo.pk_FF2_landmark = None
        return {'FINISHED'}

class AddStrideSagittalProjectionPlaneOperator(Operator):
    bl_idname = "pktoolbox.add_stride_sagittal_projection_plane"
    bl_label = "Add a stride to a PROJECTION_PLANE from two footfall LANDMARKS and a fitted ground plane."
    bl_description = "Add a stride to a PROJECTION_PLANE from two footfall LANDMARKS and a fitted ground plane."
    bl_options = {"UNDO"} #enable undoing
        
    def execute(self, context):

        muskemo = bpy.context.scene.muskemo
        
        sagittal_plane = muskemo.pk_target_projection_plane

        if not sagittal_plane:
            self.report({'ERROR'}, "You forgot to designate a target sagittal projection plane. Operation cancelled")
            return {'FINISHED'}

        ## Check if the pk_stride_start_frame was set, and if not, throw an error

        if 'pk_stride_start_frame' not in muskemo:
            self.report({'ERROR'}, "You didn't specify at what frame the stride starts.")
            return {'CANCELLED'}
        else:
            frame_number = muskemo.pk_stride_start_frame


        ## get the ground plane
        groundPlane = muskemo.pk_ground_plane #fitted ground plane from photogrammetry
        if not groundPlane:
            self.report({'ERROR'}, "You did not select a fitted ground plane")
            return {'FINISHED'}
        
        if groundPlane.scale != Vector((1,1,1)):
            self.report({'ERROR'}, "Ground plane object with name '" + groundPlane.name + "' has non-unit scale. Select it, hit control + A, and select 'Apply scale'. Operation cancelled.")
            return {'FINISHED'}

        #get landmark for footfall 1
        FootFall1LM = muskemo.pk_FF1_landmark #landmark of first footfall (projected on ground plane)

        if not FootFall1LM:
            self.report({'ERROR'}, "You did not select a landmark for the first footfall")
            return {'FINISHED'}

        #get landmark for footfall 2
        FootFall2LM = muskemo.pk_FF2_landmark #landmark of second footfall (projected on ground plane)

        if not FootFall2LM:
            self.report({'ERROR'}, "You did not select a landmark for the second footfall")
            return {'FINISHED'}
        
        if FootFall1LM == FootFall2LM:
            self.report({'ERROR'}, "The first and second footfall landmarks are the same object")
            return {'FINISHED'}
        
        if ((FootFall1LM == groundPlane) or (FootFall2LM == groundPlane)):
            self.report({'ERROR'}, "The fitted ground plane is the same object as one of the footfall landmarks")
            return {'FINISHED'}

        if not groundPlane.get('plane_dimensions'): #If the object is not a MuSkeMo fitted geometry plane, throw an error.
            self.report({'ERROR'},'The object designated as the ground plane does not appear to be a Plane mesh fitted by MuSkeMo.')
            return {'FINISHED'}
        

        ## The footfall landmarks must be coplanar with the groundplane, this means that their Z position in the ground plane frame must be zero. We check this explicitly.
        groundPlane_wm = groundPlane.matrix_world

        tolerance = 1e-6 #
        if abs((groundPlane_wm.transposed() @ (FootFall1LM.matrix_world.translation - groundPlane_wm.translation))[2]) > tolerance:
            self.report({'ERROR'}, "Footfall landmark 1 does not appear to be projected onto the fitted groundplane. Double check its position and ensure center snapping is on.")
            return {'FINISHED'}
        
        if abs((groundPlane_wm.transposed() @ (FootFall2LM.matrix_world.translation - groundPlane_wm.translation))[2]) > tolerance:
            self.report({'ERROR'}, "Footfall landmark 2 does not appear to be projected onto the fitted groundplane. Double check its position and ensure center snapping is on.")
            return {'FINISHED'}
        
        # set current frame

        if frame_number in list(sagittal_plane['stride_start_frames']):
            self.report({'ERROR'}, "You selected the same frame number for this new stride start as one of the previous strides. Double check your stride frame start. Operation cancelled.")
            return {'FINISHED'}

        bpy.context.scene.frame_set(frame_number)

        #global positions of the landmarks
        FF1pos = FootFall1LM.matrix_world.translation
        FF2pos = FootFall2LM.matrix_world.translation

        ## Construct the orientation of the sagittal plane
        x_dir = (FF2pos - FF1pos)
        x_dir.normalize()

        y_dir = groundPlane.matrix_world.to_3x3().col[2] #ground plane Z-dir will be y dir of the sagittal plane
        y_dir.normalize()

        z_dir = x_dir.cross(y_dir)

        if y_dir.dot(Vector((0,0,1)))<0:
            self.report({'ERROR'}, "Your ground plane may be upside down. Check whether the y-axis of your new sagittal plane is 'up'. If not, undo, and use 'flip plane' on your ground plane.")
       
        # Build 3×3 rotation matrix with columns = axes
        rot_mat = Matrix((
            x_dir,
            y_dir,
            z_dir,
        )).transposed()


        plane_origin = (FF1pos + FF2pos)/2 #set plane origin mat to the first footfall
        world_mat = rot_mat.to_4x4()
        world_mat.translation = plane_origin

        ## Check if the old world mat is the same as the new one, in which case we throw an error.
  

        if np.allclose(np.array(world_mat), np.array(sagittal_plane.matrix_world), atol = 1e-4): #compare matrices with abstol of 1e-6, to account for single precision in Blender
       
            self.report({'ERROR'}, "The desired new stride plane has the same target orientation and position as the previous stride. Make sure you selected the correct new set of footfalls. Operation cancelled.")
            return {'FINISHED'}


        ## set transformation mat sagittal plane and frame to the new world mat
        sagittal_plane.matrix_world = world_mat

       
        # set current_stride custom property

        sagittal_plane['current_stride'] = sagittal_plane['current_stride'] +1

        # append stride start frames
        pk_stride_start_frames = list(sagittal_plane['stride_start_frames'])
        pk_stride_start_frames.append(frame_number)
        sagittal_plane['stride_start_frames'] = pk_stride_start_frames
        

        #set keyframes for the plane
        keyframe_datapaths_plane = ['["current_stride"]', 'location', 'rotation_euler']

        for dp in keyframe_datapaths_plane:
            sagittal_plane.keyframe_insert(data_path=dp, frame=frame_number)

       
        action = sagittal_plane.animation_data.action
        if action:  # make sure the object has keyframes
            for fcurve in action.fcurves:
                for kp in fcurve.keyframe_points:
                    kp.interpolation = 'CONSTANT'

        

        ## unset the pk_stride_start_frame input
        muskemo.property_unset("pk_stride_start_frame")

        ## reset FF1 and FF2 landmark objects
        muskemo.pk_FF1_landmark = None
        muskemo.pk_FF2_landmark = None
        return {'FINISHED'}
    

class CreateAnimatedLandmarkOperator(Operator):
    bl_idname = "pktoolbox.create_animated_landmark"
    bl_label = "Create an ANIMATED_LANDMARK which can be animated using keyframe animation to digitize kinematics."
    bl_description = "Create an ANIMATED_LANDMARK which can be animated using keyframe animation to digitize kinematics."
    bl_options = {"UNDO"} #enable undoing
        
    def execute(self, context):

        muskemo = bpy.context.scene.muskemo

        landmark_radius = muskemo.landmark_radius
        colname =muskemo.pk_animated_landmark_collection
        
        sagittal_plane = muskemo.pk_target_projection_plane

        if not sagittal_plane:
            self.report({'ERROR'}, "You forgot to designate a target sagittal projection plane. Operation cancelled")
            return {'FINISHED'}

        ## get the desired object name
        landmark_name = muskemo.pk_animated_landmark_name

        number_of_landmarks = muskemo.pk_number_of_landmarks


        if not landmark_name:
            self.report({'ERROR'}, "Type in a desired name for the animated landmark and try again.")
            return {'FINISHED'}
        
        if number_of_landmarks == 1: #if one landmark
            
            landmark_names = [landmark_name]
        else: #multiple landmarks
            landmark_names = [landmark_name + str(x+1) for x in range(number_of_landmarks)]    
            
        for lm_name in landmark_names:
            if lm_name in bpy.data.objects:
                self.report({'ERROR'}, "You tried to create a new animated landmark with the name '" + lm_name + "', but an object with that name already exists. Choose a unique name.")
                return {'FINISHED'}
        
        base_loc = sagittal_plane.matrix_world.translation
        x_dir = sagittal_plane.matrix_world.to_3x3().col[0]
        spacing = 3 * landmark_radius
        

        from .create_animated_landmark_func import create_animated_landmark

        for ind,lm_name in enumerate(landmark_names):
            
            offset = (ind - (number_of_landmarks - 1) / 2) * spacing #equally space around midpoint of the plane.
            target_loc = base_loc + offset*x_dir

            create_animated_landmark(landmark_name = lm_name, 
                            landmark_radius =landmark_radius, 
                            collection_name = colname, 
                            pos_in_global = target_loc, 
                            is_global = True, 
                            parent_body = sagittal_plane.name)
        
        ###  
        
        
        ### Empty the landmark name input

        muskemo.pk_animated_landmark_name = ''

        
        return {'FINISHED'}


## Add keyframe to animated landmarks
class AddKeyframeAnimatedLandmarksOperator(Operator):
    bl_idname = "pktoolbox.add_keyframe_animated_landmark"
    bl_label = "Add keyframes to one or more ANIMATED_LANDMARKs in the current position."
    bl_description = "Add keyframes to one or more ANIMATED_LANDMARKs in the current position."
    bl_options = {"UNDO"} #enable undoing
        
    def execute(self, context):

        muskemo = bpy.context.scene.muskemo

        keyframe_mode = muskemo.pk_keyframe_mode
        colname = muskemo.pk_animated_landmark_collection
        
        target_plane = muskemo.pk_target_projection_plane

        if not target_plane:
            self.report({'ERROR'}, "You forgot to designate a target projection plane. Operation cancelled")
            return {'FINISHED'}


        if keyframe_mode == 'All': #Get all the animated landmarks in the collection
            landmarks = [x for x in bpy.data.collections[colname].objects if x.get("MuSkeMo_type") == 'ANIMATED_LANDMARK']


        elif keyframe_mode == 'Selected only': #Get the selected animated landmarks
            sel_obj = bpy.context.selected_objects  #should be the only the projection plane
            landmarks = [x for x in sel_obj if x.get("MuSkeMo_type") == 'ANIMATED_LANDMARK']

        for landmark in landmarks:
            
            plane_WM = target_plane.matrix_world
       
            plane_pos_glob = plane_WM.translation
            plane_bRg = plane_WM.to_3x3().transposed() #global to local frame of the sagittal plane
            
            target_loc = landmark.matrix_world.translation
            tolerance = 1e-6 #

            if abs((plane_bRg @ (target_loc - plane_pos_glob))[2]) >tolerance:
                self.report({'ERROR'}, "Animated Landmark with name '" + landmark.name +  "' does not appear to be projected onto the target plane. Did you have snapping on when positioning the animated landmark? Operation cancelled.")
                return {'FINISHED'}
            ## keyframe the object

            landmark.keyframe_insert(data_path='location')

        
        return {'FINISHED'}


## Panels

class VIEW3D_PT_PKToolbox_panel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo

    bl_idname = 'VIEW3D_PT_PKToolbox_panel'
    bl_label = "Photogrammetry Kinematics Toolbox"  # found at the top of the Panel
    #bl_context = "objectmode"

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        row = layout.row()
        row.operator("pktoolbox.set_recommended_snapping_settings", text = "Set recommended snapping settings")
        row = layout.row()

class VIEW3D_PT_PKToolbox_create_projection_plane_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo

    bl_idname = 'VIEW3D_PT_PKToolbox_create_projection_plane_subpanel'
    bl_label = "Create projection plane"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_PKToolbox_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        
        ## Footfall 1 landmark
        box = layout.box()
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Footfall 1 landmark")
        split.prop(muskemo, "pk_FF1_landmark", text="")
        ## Footfall 2 landmark
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Footfall 2 landmark")
        split.prop(muskemo, "pk_FF2_landmark", text="")
        ## Photogrammetry fitted ground plane
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Fitted ground plane")
        split.prop(muskemo, "pk_ground_plane", text="")
        ## Create sagittal projection plane
        row = box.row()
        split = row.split(factor = 1/2)
        split.prop(muskemo, "pk_sagittal_projection_plane_name", text = "Name")
        
        if 'pk_stride_start_frame' not in muskemo:
            split.alert = True
        split.prop(muskemo, "pk_stride_start_frame", text = "Stride starts at frame")
        split.alert = False

        row = box.row()
        row.operator("pktoolbox.create_sagittal_projection_plane", text = "Create sagittal projection plane")


class VIEW3D_PT_PKToolbox_add_stride_projection_plane_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo

    bl_idname = 'VIEW3D_PT_PKToolbox_add_stride_projection_plane_subpanel'
    bl_label = "Add stride to projection plane"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_PKToolbox_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
        
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
    
        ## Footfall 1 landmark
        box = layout.box()
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Target projection plane")
        split.prop(muskemo, "pk_target_projection_plane", text="")
        
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Footfall 1 landmark")
        split.prop(muskemo, "pk_FF1_landmark", text="")
        ## Footfall 2 landmark
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Footfall 2 landmark")
        split.prop(muskemo, "pk_FF2_landmark", text="")
        ## Photogrammetry fitted ground plane
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Fitted ground plane")
        split.prop(muskemo, "pk_ground_plane", text="")
        ## Create sagittal projection plane
        row = box.row()
        
        if 'pk_stride_start_frame' not in muskemo:
            row.alert = True
        row.prop(muskemo, "pk_stride_start_frame", text = "Stride starts at frame")
        row.alert = False

        row = box.row()
        row.operator("pktoolbox.add_stride_sagittal_projection_plane", text = "Add stride to sagittal projection plane")

class VIEW3D_PT_PKToolbox_Animated_landmark_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo

    bl_idname = 'VIEW3D_PT_PKToolbox_create_animated_landmark_subpanel'
    bl_label = "Animated landmarks"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_PKToolbox_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
        
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo


        box = layout.box()
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Target projection plane")
        split.prop(muskemo, "pk_target_projection_plane", text="")

        row = box.row()
        
        row.prop(muskemo, "pk_animated_landmark_name", text = "Name")
        row = box.row()
        row.operator("pktoolbox.create_animated_landmark", text = "Create animated landmark")
        row = box.row()
        row = box.row()
        row.prop(muskemo, "pk_number_of_landmarks", text = "Number of landmarks")
        row.prop(muskemo, "landmark_radius", text = "Landmark radius")

        ## Add keyframes
        row = layout.row()
        row = layout.row()
        
        row = layout.row()
        row = layout.row()
        box = layout.box()

        ## SEL OBJ ANIMATED LANDMARKS
        row = box.row()
        row = box.row()
        split = row.split(factor = 1/2)
        split.label(text="Target projection plane")
        split.prop(muskemo, "pk_target_projection_plane", text="")

        row = box.row()
        split = row.split(factor = 1/3)
        split.label(text = "Keyframe mode:")
        
        sub = split.row()
        sub.prop(muskemo, "pk_keyframe_mode", expand=True)

        row = box.row()
        row.operator("pktoolbox.add_keyframe_animated_landmark", text = "Add keyframe to animated landmarks")