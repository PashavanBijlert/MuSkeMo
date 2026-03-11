import bpy
from mathutils import (Vector, Matrix)
import numpy as np
def write_animated_landmarks(context, filepath, collection_name, delimiter, obj_type, number_format, self):  #write location and parent body. This is reused for both contacts and landmarks.
    
    #### obj_type is a string, either "contact" or "landmark", or something else if you reuse this further
    #### the script will fail if you don't specify it when calling the function
    coll = bpy.data.collections[collection_name]

    ranges = [obj.animation_data.action.frame_range 
            for obj in coll.objects 
            if obj.animation_data and obj.animation_data.action]

    min_frame = int(min(r[0] for r in ranges))
    max_frame = int(max(r[1] for r in ranges))

    frame_range = range(min_frame, max_frame+1)


    header_parts = []
    first_parent = None

    for alm in coll.objects: #for each animated landmark
        proj_plane = alm.parent

        ## error check, ensure all the ALMs are attached to the same projection plane
        if first_parent is None:
            first_parent = proj_plane
        elif proj_plane != first_parent:
            self.report({'ERROR'}, "All landmarks must share the same parent projection plane. Please move animated landmarks from separate projection planes into separate collections before export.")
            return {'FINISHED'}
        
        landmark_name = alm.name + '_' + proj_plane.name
        
        header_parts.append(landmark_name + "_x")
        header_parts.append(landmark_name + "_y")

    header_parts.append("stride_number")

    header = delimiter.join(header_parts)

  

    file = open(filepath, 'w', encoding='utf-8')
    file.write(header)
    file.write('\n')


    for frame in frame_range:
        context.scene.frame_set(frame)
        stride = int(proj_plane['current_stride'])
        for alm in coll.objects:

            #landmark_name = alm.name + '_' + proj_plane.name

            plane_WM = proj_plane.matrix_world
            landmark_pos_glob = alm.matrix_world.translation
            landmark_pos_reprojected = plane_WM.to_3x3().transposed() @ (landmark_pos_glob - plane_WM.translation)

            tolerance = 1e-6
            if abs(landmark_pos_reprojected[2]) > tolerance:

                self.report({'ERROR'}, "Animated landmark '" + alm.name + "' is not projected onto plane '" + proj_plane.name +  "' at frame no. " + str(frame)  + ". Ensure that object snapping is on when keyframing the animated landmarks. Export cancelled")
                return {'FINISHED'}

            x_pos = landmark_pos_reprojected[0]
            y_pos = landmark_pos_reprojected[1]

            file.write(f"{x_pos:{number_format}}{delimiter}")
            file.write(f"{y_pos:{number_format}}{delimiter}")

            #don't touch these comments
            #stride_start_frames = proj_plane["stride_start_frames"]
            #stride = max(i for i, start in enumerate(stride_start_frames) if start <= frame) +1

        file.write(f"{stride:d}") #integer format
        file.write('\n')

    file.close()
    return {'FINISHED'}