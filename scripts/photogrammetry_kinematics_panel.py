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

        groundPlane = muskemo.pk_ground_plane #fitted ground plane from photogrammetry
        if not groundPlane:
            self.report({'ERROR'}, "You did not select a fitted ground plane")
            return {'FINISHED'}
        
        if groundPlane.scale != Vector((1,1,1)):
            self.report({'ERROR'}, "Ground plane object with name '" + groundPlane.name + "' has non-unit scale. Select it, hit control + A, and select 'Apply scale'. Operation cancelled.")
            return {'FINISHED'}

        

        FootFall1LM = muskemo.pk_FF1_landmark #landmark of first footfall (projected on ground plane)

        if not FootFall1LM:
            self.report({'ERROR'}, "You did not select a landmark for the first footfall")
            return {'FINISHED'}

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

        ## ERROR CHECK FOR IF IT'S NOT A PLANE. PROBABLY WE ONLY ALLOW MUSKEMO TYPE FITTED GEOMETRY PLANE?
       
        # What if ground plane Z isn't up? #We probably only give a warning but do nothing else

        #global positions of the landmarks
        FF1pos = FootFall1LM.matrix_world.translation
        FF2pos = FootFall2LM.matrix_world.translation


        x_dir = (FF2pos - FF1pos)
        x_dir.normalize()

        y_dir = groundPlane.matrix_world.to_3x3().col[2] #ground plane Z-dir will be y dir of the sagittal plane
        y_dir.normalize()

        z_dir = x_dir.cross(y_dir)

        # Build 3×3 rotation matrix with columns = axes
        rot_mat = Matrix((
            x_dir,
            y_dir,
            z_dir,
        )).transposed()



        world_mat = rot_mat.to_4x4()
        world_mat.translation = (FF1pos + FF2pos)/2 #set plane origin mat to the first footfall

        size = 4*(FF2pos - FF1pos).length

        bpy.ops.mesh.primitive_plane_add(size=size)

        bpy.data.objects['Plane'].matrix_world = world_mat
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

        CreateSelectedObjRow('MESH', layout)


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
        box.operator("pktoolbox.create_sagittal_projection_plane", text = "Create sagittal projection plane")



        
       
