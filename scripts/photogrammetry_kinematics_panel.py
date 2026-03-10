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
class CreateSagittalProjectionPlaneOperator(Operator):
    bl_idname = "pktoolbox.create_sagittal_projection_plane"
    bl_label = "Create a sagittal PROJECTION_PLANE from two footfall LANDMARKS and a fitted ground plane."
    bl_description = "Create a sagittal PROJECTION_PLANE from two footfall LANDMARKS and a fitted ground plane."
    bl_options = {"UNDO"} #enable undoing
        
    def execute(self, context):

        muskemo = bpy.context.scene.muskemo

        ## get the desired object name
        plane_name = muskemo.sagittal_projection_plane_name

        if not plane_name:
            self.report({'ERROR'}, "Type in a desired name for the sagittal plane and try again.")
            return {'FINISHED'}
        
        if plane_name in bpy.data.objects:
            self.report({'ERROR'}, "You tried to create a new sagittal plane with the name '" + plane_name + "', but an object with than name already exists. Choose a unique name, or if you're trying to add a stride, use the 'Add stride' button.")
            return {'FINISHED'}

        ## Check if the stride_start_frame was set, and if not, throw an error

        if 'stride_start_frame' not in muskemo:
            self.report({'ERROR'}, "You didn't specify at what frame the stride starts.")
            return {'CANCELLED'}
        else:
            frame_number = muskemo.stride_start_frame


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

        tolerance = 1e-4 #
        if abs((groundPlane.matrix_world.transposed() @ FootFall1LM.matrix_world.translation)[2]) > tolerance:
            self.report({'ERROR'}, "Footfall landmark 1 does not appear to be projected onto the fitted groundplane. Double check its position and ensure center snapping is on.")
            return {'FINISHED'}
        
        if abs((groundPlane.matrix_world.transposed() @ FootFall2LM.matrix_world.translation)[2]) > tolerance:
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

        ## Create the parent body and attach the ground plane to it

        from .create_body_func import create_body

        pbodyname = sagittal_plane.name + '_pbody'

        if not pbodyname in bpy.data.objects:
        
            create_body(name= pbodyname, size = muskemo.axes_size, self = self)

        bpy.ops.object.select_all(action='DESELECT')
            
        pbody = bpy.data.objects[pbodyname] 
        pbody.select_set(True) #select the parent body. 
        sagittal_plane.select_set(True) #Now a BODY and a mesh are selected
        bpy.ops.body.attach_visual_geometry() #attach visual geometry

        ## Add sagittal plane to the Projection planes collection
        bpy.data.collections['Geometry'].objects.unlink(sagittal_plane)
        bpy.data.collections[collection_name].objects.link(sagittal_plane)

        ## Create the frame and assign parent body

        from .create_frame_func import create_frame

        frame_name = sagittal_plane.name + '_frame'

        create_frame(name = frame_name, size = muskemo.axes_size, pos_in_global = plane_origin, 
                     gRb = rot_mat)
        
        bpy.ops.object.select_all(action='DESELECT')
        frame_obj = bpy.data.objects[frame_name]
        frame_obj.select_set(True)
        pbody.select_set(True)
        bpy.ops.frame.assign_parent_body()

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

        #set keyframes for the frame
        keyframe_datapaths_frame = [ 'location', 'rotation_euler']

        for dp in keyframe_datapaths_frame:
           frame_obj.keyframe_insert(data_path=dp, frame=frame_number)


        for obj in [sagittal_plane, frame_obj]:
            action = obj.animation_data.action
            if action:  # make sure the object has keyframes
                for fcurve in action.fcurves:
                    for kp in fcurve.keyframe_points:
                        kp.interpolation = 'CONSTANT'

        ## reset the plane name input
        muskemo.sagittal_projection_plane_name = ''

        ## unset the stride_start_frame input
        muskemo.property_unset("stride_start_frame")
        
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

        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No objects selected. Select the target sagittal projection plane and try again. Operation cancelled")
            return {'FINISHED'}
        
        # throw an error if too many objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target sagittal projection plane and try again. Operation cancelled")
            return {'FINISHED'}
        
        sagittal_plane = sel_obj[0]

        if sagittal_plane.get('MuSkeMo_type') != 'PROJECTION_PLANE':
            self.report({'ERROR'}, "Selected object is not a PROJECTION_PLANE. Select the target sagittal projection plane and try again. Operation cancelled")
            return {'FINISHED'}

        ## Check if the stride_start_frame was set, and if not, throw an error

        if 'stride_start_frame' not in muskemo:
            self.report({'ERROR'}, "You didn't specify at what frame the stride starts.")
            return {'CANCELLED'}
        else:
            frame_number = muskemo.stride_start_frame


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

        tolerance = 1e-4 #
        if abs((groundPlane.matrix_world.transposed() @ FootFall1LM.matrix_world.translation)[2]) > tolerance:
            self.report({'ERROR'}, "Footfall landmark 1 does not appear to be projected onto the fitted groundplane. Double check its position and ensure center snapping is on.")
            return {'FINISHED'}
        
        if abs((groundPlane.matrix_world.transposed() @ FootFall2LM.matrix_world.translation)[2]) > tolerance:
            self.report({'ERROR'}, "Footfall landmark 2 does not appear to be projected onto the fitted groundplane. Double check its position and ensure center snapping is on.")
            return {'FINISHED'}
        
        # set current frame

        if frame_number in list(sagittal_plane['stride_start_frames']):
            self.report({'ERROR'}, "You selected the same frame number for the stride start as one of the previous strides. Double check your stride frame start. Operation cancelled.")
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

        frame_obj = bpy.data.objects[bpy.data.objects[sagittal_plane['Attached to']]['local_frame']]
        
        frame_obj.matrix_world = world_mat
        
        # set current_stride custom property

        sagittal_plane['current_stride'] = frame_number

        # append stride start frames
        stride_start_frames = list(sagittal_plane['stride_start_frames'])
        stride_start_frames.append(frame_number)
        sagittal_plane['stride_start_frames'] = stride_start_frames
        

        #set keyframes for the plane
        keyframe_datapaths_plane = ['["current_stride"]', 'location', 'rotation_euler']

        for dp in keyframe_datapaths_plane:
            sagittal_plane.keyframe_insert(data_path=dp, frame=frame_number)

        #set keyframes for the frame
        keyframe_datapaths_frame = [ 'location', 'rotation_euler']

        for dp in keyframe_datapaths_frame:
           frame_obj.keyframe_insert(data_path=dp, frame=frame_number)


        for obj in [sagittal_plane, frame_obj]:
            action = obj.animation_data.action
            if action:  # make sure the object has keyframes
                for fcurve in action.fcurves:
                    for kp in fcurve.keyframe_points:
                        kp.interpolation = 'CONSTANT'

        

        ## unset the stride_start_frame input
        muskemo.property_unset("stride_start_frame")

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
        
        ### selected meshes

        from .selected_objects_panel_row_func import CreateSelectedObjRow


        
        
        ### Create sagittal projection plane

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
        split.prop(muskemo, "sagittal_projection_plane_name", text = "Name")
        
        if 'stride_start_frame' not in muskemo:
            split.alert = True
        split.prop(muskemo, "stride_start_frame", text = "Stride starts at frame")
        split.alert = False

        row = box.row()
        row.operator("pktoolbox.create_sagittal_projection_plane", text = "Create sagittal projection plane")


        ### Add stride to sagittal projection plane


        ### Create sagittal projection plane

        ## Footfall 1 landmark
        box = layout.box()
        row = box.row()
        CreateSelectedObjRow('PROJECTION_PLANE', row)
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
        
        if 'stride_start_frame' not in muskemo:
            row.alert = True
        row.prop(muskemo, "stride_start_frame", text = "Stride starts at frame")
        row.alert = False

        row = box.row()
        row.operator("pktoolbox.add_stride_sagittal_projection_plane", text = "Add stride to sagittal projection plane")

        
       
