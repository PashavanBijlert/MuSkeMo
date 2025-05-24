import bpy
from mathutils import (Vector, Matrix)


from bpy.types import (Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import nan


import numpy as np
import os
import csv

import colorsys

class ImportTrajectorySTO(Operator):
    bl_description = "Import a trajectory in .sto file format to create an animation"
    bl_idname = "visualization.import_trajectory_sto"
    bl_label = "Import .sto strajectory to create an animation"


    # This section is based on importhelper
    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    #this filters other filetypes from the window during export. The actual value is set in invoke, by setting the filetype
    filter_glob: bpy.props.StringProperty(default = "",options={'HIDDEN'}, maxlen=255)

    #run the file select window manager, with a filter for .osim extension files
    def invoke(self, context, _event):

        self.filter_glob = "*.sto"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
    
    def parse_sto(self, context):#custom super class method
        """Reads .STO file data from the specified filepath using the CSV importer and tab delimiters."""
        filepath = self.filepath
        with open(filepath, mode = 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            file_header = [] #all the extra header lines including "endheader"
            column_headers = [] #the actual headers of the data columns
            data = []
            is_data = False #remains false until we've looped through the file_header rows

            in_degrees = 'not_defined'

            for row in reader:
                if 'inDegrees' in row[0]: #if it's defined in the header, we set the muskemo prop
                    if 'no' in row[0]:
                        in_degrees = False

                    elif 'yes' in row[0]:
                        in_degrees = True

                    bpy.context.scene.muskemo.in_degrees = in_degrees
                

                if 'endheader' in row:
                    is_data = True
                    continue
                
                if is_data:
                    if not column_headers:  # The first row after endheader contains the column headers
                        column_headers = row
                    else:
                        data.append([float(x) for x in row if x.strip() != ''])
                else:
                    file_header.append(row)

            if in_degrees == 'not_defined': #if it's not defined, throw a warning
                self.report({'WARNING'}, "Your .sto file does not have an 'inDegrees' line in the header. Default behavior is to assume radians, if you want degrees, specify so below before import.")
    
        
        return column_headers, data
    
    def execute(self, context):
        
        # Call the custom superclass method parse_sto to read the sto data
        column_headers, traj_data = self.parse_sto(context)
        
        traj_data = np.array(traj_data)
        time = traj_data[:,0] #time is the first column

        #### First we get the joint parameters in the model. Because a joint can have multiple coordinates, this is slightly involved

        # get the joints and associated joint coordinates in the model
        joint_col = bpy.data.collections[bpy.context.scene.muskemo.joint_collection]
        joints = [x for x in joint_col.objects if 'MuSkeMo_type' in x and x['MuSkeMo_type']=='JOINT']

        coordinate_types = ['coordinate_Rx', 'coordinate_Ry', 'coordinate_Rz', 'coordinate_Tx', 'coordinate_Ty', 'coordinate_Tz'] #the six possibilities
        model_coordinates = [] #the actual coordinate names in the model
        model_coordinate_types = [] #the corresponding coordinate type (eg Rz)
        model_coordinate_joints = [] #the joints that own the coordinates (because one joint can have multiple coordinates)

        
        for joint in joints:
            
            for coordinate_type in coordinate_types:
                if joint[coordinate_type]:#if the coordinate is nonempty, add it to the model coordinates list. E.g. if hip_r['coordinate_Tx'] is nonempty
                    model_coordinates.append(joint[coordinate_type])
                    model_coordinate_types.append(coordinate_type)
                    model_coordinate_joints.append(joint)


        # get the joint coordinates in the trajectory
        traj_coordinate_headers = [] #headers of the coordinate names in the traj data
        traj_coordinate_ind = [] #column indices
        traj_joints = [] #joints used in the trajectory
        traj_model_coordinates = [] #model coordinates actually used in the traj
        traj_model_coordinate_types = [] #model coordinate types used in the traj

        model_coor_not_found = [] #for skip reporting later on
        model_coor_non_unique = []
        for idx, coordinate in enumerate(model_coordinates):
            
            ind = [i for i, x in enumerate(column_headers) if coordinate in x and ('value' in x or coordinate==x)] #indices of the joint angles. #OpenSim outputs have /value at the end, Hyfydy outputs simply have only the coordinate as the header
            traj_coor = [x for i, x in enumerate(column_headers) if coordinate in x and ('value' in x or coordinate==x)] #coordinate name in the trajectory data

            if not traj_coor:
                model_coor_not_found.append(coordinate)
            elif len(traj_coor)>1:
                model_coor_non_unique.append(coordinate)
            else:
                traj_coordinate_headers.append(traj_coor[0])
                traj_coordinate_ind.append(ind[0])
                traj_joints.append(model_coordinate_joints[idx])
                traj_model_coordinates.append(coordinate)
                traj_model_coordinate_types.append(model_coordinate_types[idx])

        #skip reporting
        if model_coor_not_found:
            model_coor_nf_str = ', '.join(model_coor_not_found)
            self.report({'WARNING'}, "Model coordinate '" + model_coor_nf_str + "' was not found in the imported trajectory. This coordinate will be skipped during trajectory import")
        
        if model_coor_non_unique:
            model_coor_nu_str = ', '.join(model_coor_non_unique)   
            self.report({'WARNING'}, "Model coordinate '" + model_coor_nu_str + "' has a non-unique mapping in the trajectory data. This coordinate will be skipped during trajectory import")
                

        coordinate_trajectories = traj_data[:,traj_coordinate_ind]

            

        ## get the muscles in the model
        # get the joints and associated joint coordinates in the model
        muscle_col = bpy.data.collections.get(bpy.context.scene.muskemo.muscle_collection)
        if muscle_col: #if the muscle col is not an empty object
            muscles = [x for x in muscle_col.objects if 'MuSkeMo_type' in x and x['MuSkeMo_type']=='MUSCLE']
        else:
            muscles = []


        ## get the muscle activations in the trajectory

        traj_muscle_act_headers = [] #trajectory headers of the muscle activations
        traj_muscle_act_ind = [] #column indices to the respective muscle activations
        traj_muscles = [] #model muscles actually in the trajectory activations
        
        musnames_not_found = [] #for skip reporting later on
        musnames_non_unique = [] #for skip reporting later on

        for idx, muscle in enumerate(muscles):
            
            ind = [i for i, x in enumerate(column_headers) if ('/' + muscle.name + '/' +'activation' in x) or (muscle.name + '.activation' in x)] #indices of the activations. #OpenSim delimits with '/', hyfydy with '.'
            traj_act = [x for i, x in enumerate(column_headers) if ('/' + muscle.name + '/' +'activation' in x) or (muscle.name + '.activation' in x)] #headers of the activation data

            if not traj_act:
                muscle.hide_set(True)
                muscle.hide_render = True
                musnames_not_found.append(muscle.name)

            elif len(traj_act)>1:
                muscle.hide_set(True)
                muscle.hide_render = True
                musnames_non_unique.append(muscle.name)

            else: 
                traj_muscle_act_headers.append(traj_act[0])
                traj_muscle_act_ind.append(ind[0])
                traj_muscles.append(muscle)
        #skip reporting
        if musnames_not_found:
            musnames_nf_str = ', '.join(musnames_not_found)
            self.report({'WARNING'}, "Activations for model muscle(s) '" + musnames_nf_str + "' were not found in the imported trajectory. This muscle will be skipped during trajectory import, and hidden during the visualizations")
                
        if musnames_non_unique:
            musnames_nu_str = ', '.join(musnames_not_found)
            self.report({'WARNING'}, "Model muscle(s) '" + musnames_nu_str + "' have a non-unique mapping in the trajectory data activations. This muscle will be skipped during trajectory import, and hidden during the visualizations")
                


        activation_trajectories = traj_data[:,traj_muscle_act_ind]

        #### USER SWITCHES
        number_of_repeats = bpy.context.scene.muskemo.number_of_repetitions # number of strides. Should be a user switch. Assumes final state is equal to initial state, except pelvis x translation, so a full stride.
        fps = bpy.context.scene.muskemo.fps #set to 60 if you want 50% slow motion (for a run)
        root_joint_name = bpy.context.scene.muskemo.root_joint_name
        forward_progression_coordinate = bpy.context.scene.muskemo.forward_progression_coordinate

        #### SET SOME RENDER SETTINGS

        bpy.context.scene.render.fps = fps #set the render fps
        bpy.context.scene.sync_mode = 'FRAME_DROP' 



        ## IF ROOT_JOINT_NAME DOESN'T EXIST, SET N_REPEATS TO 0.    

        if root_joint_name in bpy.data.objects:
            root_joint = bpy.data.objects[root_joint_name]
            
        else:
            if number_of_repeats >0:
                self.report({'WARNING'}, "Root joint '" + root_joint_name + "' does not exist. Default is groundPelvis, but did you type in the correct joint name? The trajectory won't be repeated")
                number_of_repeats = 0
                bpy.context.scene.muskemo.number_of_repetitions = 0
      
        root_joint_ind = [i for i,x in enumerate(traj_joints) if root_joint_name == x.name]#these column indices have root joint data in coordinate_trajectories
        root_progression_ind = [x for x in root_joint_ind if traj_model_coordinate_types[x]==forward_progression_coordinate] #this is the index to the coordinate that indicates forward progression (usually pelvis Tx)
        #print(root_joint_ind)
        #print(traj_model_coordinate_types)
        #print(forward_progression_coordinate)
        #print(root_progression_ind)


        if number_of_repeats >0:
                        
            # Initialize the new time array with the original time array
            time_repeated = time.copy()
            coordinate_trajectories[:,root_progression_ind] = coordinate_trajectories[:,root_progression_ind] - coordinate_trajectories[0,root_progression_ind]
            coordinate_trajectories_repeated = coordinate_trajectories.copy() 

            activation_trajectories_repeated = activation_trajectories.copy()

            # Add the repeated sections
            for i in range(1, number_of_repeats + 1):
                time_shifted = time[1:] + time[-1] * i  # Shift the time values by time(end) each repeat
                time_repeated = np.concatenate((time_repeated, time_shifted))

                # Initialize a shifted version of coordinate trajectories for this repeat
                coordinate_trajectories_shifted = coordinate_trajectories[1:, :].copy()

                # Shift only the specified column by its final value from the previous repeat
                shift_value = coordinate_trajectories[-1, root_progression_ind] * i
                coordinate_trajectories_shifted[:, root_progression_ind] += shift_value
                
                coordinate_trajectories_repeated  = np.concatenate((coordinate_trajectories_repeated, coordinate_trajectories_shifted))

                # Repeat the  activation trajectories
                
                activation_trajectories_repeated = np.concatenate((activation_trajectories_repeated, activation_trajectories[1:, :].copy()))

            time = time_repeated
            coordinate_trajectories = coordinate_trajectories_repeated
            activation_trajectories = activation_trajectories_repeated

            
            # fix all other data (coordinates, and muscle activations)
  
        n_times = len(time)
        time_end = time[-1]

        n_frames = round(time_end * fps )#number of frames. We will interpolate between 1 and n_frames+1, to ensure that time_end coincides with the start of n_frames+1

        # set the render timeline to the end of the sequence
        bpy.context.scene.frame_end = n_frames
        
        dt = time_end/(n_times-1)
        #x_p = np.arange(1, n_times + 1)  #List of indices in ascending order in steps of 1, from 1 to n_times (we add +1 at the end because arange stops 1 before the upper number)
        #x = np.linspace(1,n_times,n_frames+1) 
        #x_query = [x[i] for i in range(0,n_frames+1)]

        x = np.linspace(1,n_frames+1,n_times)  # a vector from 1 to n_frames, with length equal to n_times
        x_query = np.arange(1, n_frames+2) #vector from 1 n_frames+1, in steps of 1. These will be the query points for the interpolation. We interpolate between 1 and n_frames+1, adding another +1 because arange clips the last one

      
        ### resample the time vector
        time_rs = np.interp(x_query, x,time) #resampled time using numpy interpolation. This is 1 longer than n_frames
        
        ## resample coordinate trajectories
        # Initialize an empty array to hold the resampled coordinates
        coordinate_trajectories_rs = np.zeros((len(x_query), coordinate_trajectories.shape[1]))  # n_frames+1 x n_coordinates

        # Loop through each column (each coordinate trajectory)
        for i in range(coordinate_trajectories.shape[1]):
            coordinate_trajectories_rs[:, i] = np.interp(x_query, x, coordinate_trajectories[:, i])
                      
        ## resample activation trajectories
        activation_trajectories_rs = np.zeros((len(x_query), activation_trajectories.shape[1]))  # n_frames+1 x n_activations

        # Loop through each column (each coordinate trajectory)
        for i in range(activation_trajectories.shape[1]):
            activation_trajectories_rs[:, i] = np.interp(x_query, x, activation_trajectories[:, i])
        
        
        ##### start adding keyframes
        ##### insert a rest-pose keyframe at frame number 0

        frame_number = 0

   
        
        
        unique_joints_in_traj = list(set(traj_joints)) #unique joints used in the trajectory 

        #Define the global starting position and orientations of the joints, so we can use these as offsets for the trajectory data that are loaded in
        base_position = []  #The global position of the joint, before it is moved.
        base_orientation = []   #Global orientation of the joint, before it is moved.

        for joint in unique_joints_in_traj:
            base_position.append(Vector(joint['pos_in_global']))
            base_orientation.append(Vector(joint['or_in_global_XYZeuler']))
            joint.keyframe_insert('rotation_euler', frame = frame_number)
            joint.keyframe_insert('location', frame = frame_number)


        ## same for muscles

        for muscle in traj_muscles:
            muscle_name = muscle.name

            mat = bpy.data.materials[muscle_name]   #get the right material
            node_tree = mat.node_tree


            if bpy.app.version[0] <4: #if blender version is below 4
                nodename = 'Hue Saturation Value'
            else: #if blender version is above 4:
                nodename = 'Hue/Saturation/Value'

            
            node_tree.nodes[nodename].inputs['Saturation'].default_value = 1
            node_tree.nodes[nodename].inputs['Saturation'].keyframe_insert('default_value', frame = frame_number) #insert a keyframe




        ##### start inserting keyframes per time point
        in_degrees = bpy.context.scene.muskemo.in_degrees

        for i in range(n_frames):                     
            frame_number = i+1 

            coordinate_traj_row = coordinate_trajectories_rs[i,:] #row i of the resampled coordinate trajectory

            
            for joint_ind, joint in enumerate(unique_joints_in_traj):

                entries_in_traj_coor_list = [i for i,x in enumerate(traj_joints) if joint == x] #fill these into traj_coordinate_headers & associated lists
                Tx = 0
                Ty = 0
                Tz = 0

                Rx = 0
                Ry = 0
                Rz = 0

                if 'transform_axes' not in joint: #if the joint doesn't have transform axes from OpenSim, treat it normally

                    for idx in entries_in_traj_coor_list: 
                        
                        #check what type of coordinate it is
                        if traj_model_coordinate_types[idx] == 'coordinate_Tx':
                            #Tx = coordinate_traj_row[traj_coordinate_ind[idx] -1]
                            Tx = coordinate_traj_row[idx]
                        
                        if traj_model_coordinate_types[idx] == 'coordinate_Ty':
                            #Ty = coordinate_traj_row[traj_coordinate_ind[idx]]
                            Ty = coordinate_traj_row[idx]

                        if traj_model_coordinate_types[idx] == 'coordinate_Tz':
                            Tz = coordinate_traj_row[idx]  
                            
                        if traj_model_coordinate_types[idx] == 'coordinate_Rx':
                            if in_degrees:
                                Rx = np.deg2rad(coordinate_traj_row[idx])
                            else:
                                Rx =coordinate_traj_row[idx]

                        if traj_model_coordinate_types[idx] == 'coordinate_Ry':
                            if in_degrees:
                                Ry =np.deg2rad(coordinate_traj_row[idx])
                            else:
                                Ry = coordinate_traj_row[idx]

                        if traj_model_coordinate_types[idx] == 'coordinate_Rz':
                            if in_degrees:
                                Rz = np.deg2rad(coordinate_traj_row[idx])  
                            else:
                                Rz = coordinate_traj_row[idx]

                else:
                    transform_axes = joint['transform_axes'].to_dict()  #dict with the transform axes
                    
                    #pre-allocate translation and identity matrices for rotations
                    translation = Vector([Tx, Ty, Tz])

                    Rmat_x = Matrix([[1,0,0],[0,1,0],[0,0,1]])
                    Rmat_y = Matrix([[1,0,0],[0,1,0],[0,0,1]])
                    Rmat_z = Matrix([[1,0,0],[0,1,0],[0,0,1]])

                    from .axis_angle import matrix_from_axis_angle
                    from .euler_XYZ_body import (matrix_from_euler_XYZbody, euler_XYZbody_from_matrix)

                    for idx in entries_in_traj_coor_list:
                        
                        #for the translation coordinates, multiply the coordinate value by the transform axis vector
                        if traj_model_coordinate_types[idx] == 'coordinate_Tx':
                            #Tx = coordinate_traj_row[traj_coordinate_ind[idx] -1]
                            translation += Vector(transform_axes['transform_axis_Tx'])*coordinate_traj_row[idx]
                        
                        if traj_model_coordinate_types[idx] == 'coordinate_Ty':
                            #Ty = coordinate_traj_row[traj_coordinate_ind[idx]]
                            translation += Vector(transform_axes['transform_axis_Ty'])*coordinate_traj_row[idx]

                        if traj_model_coordinate_types[idx] == 'coordinate_Tz':
                            translation += Vector(transform_axes['transform_axis_Tz'])*coordinate_traj_row[idx]

                        #for the rotation coordinates, set up an axis angle rotation matrix, and replace the ID matrix with it
                        if traj_model_coordinate_types[idx] == 'coordinate_Rx':
                            if in_degrees:
                                angle = np.deg2rad(coordinate_traj_row[idx])
                            else:
                                angle =coordinate_traj_row[idx]

                            axis =  transform_axes['transform_axis_Rx']
                            Rmat_x = matrix_from_axis_angle(axis, angle) 

                        if traj_model_coordinate_types[idx] == 'coordinate_Ry':
                            if in_degrees:
                                angle =np.deg2rad(coordinate_traj_row[idx])
                            else:
                                angle = coordinate_traj_row[idx]

                            axis =  transform_axes['transform_axis_Ry']
                            Rmat_y = matrix_from_axis_angle(axis, angle)    

                        if traj_model_coordinate_types[idx] == 'coordinate_Rz':
                            if in_degrees:
                                angle = np.deg2rad(coordinate_traj_row[idx])  
                            else:
                                angle = coordinate_traj_row[idx]

                            axis =  transform_axes['transform_axis_Rz']
                            Rmat_z = matrix_from_axis_angle(axis, angle)

                    #unpack translations
                    Tx = translation[0]
                    Ty = translation[1]
                    Tz = translation[2]


                    # X Y Z, maybe this should be flipped
                    jRta = Rmat_x @ Rmat_y @ Rmat_z #matrix from transform axis to joint 

                    [gRj, jRg] = matrix_from_euler_XYZbody(base_orientation[joint_ind])

                    # rotate the joint
                    rotated_joint = gRj@jRta
                    
                    #decompose into euler angles
                    rotated_joint_euler = euler_XYZbody_from_matrix(rotated_joint)

                    #Unpack into separate euler angles
                    Rx = rotated_joint_euler[0]
                    Ry = rotated_joint_euler[1]
                    Rz = rotated_joint_euler[2]

                                      
           
                #add the position and orientation, using the original position and orientation as an offset.
                #the above loop should have only added the changed coordinates (e.g. Rz), zo all the other components are simply zero.
                joint.location = Vector((Tx, Ty, Tz)) + base_position[joint_ind]
                joint.rotation_euler = (base_orientation[joint_ind][0] + Rx,
                                        base_orientation[joint_ind][1] + Ry, 
                                        base_orientation[joint_ind][2] + Rz)
               
                joint.keyframe_insert('rotation_euler', frame = frame_number)
                joint.keyframe_insert('location', frame = frame_number)

            activation_traj_row = activation_trajectories_rs[i,:] #row i of the resampled coordinate trajectory
            

            for muscle_ind, muscle in enumerate(traj_muscles):
                muscle_name = muscle.name

                mat = bpy.data.materials[muscle_name]   #get the right material
                node_tree = mat.node_tree


                if bpy.app.version[0] <4: #if blender version is below 4
                    nodename = 'Hue Saturation Value'
                else: #if blender version is above 4:
                    nodename = 'Hue/Saturation/Value'

                activation = activation_traj_row[muscle_ind] #assign the right data point, using the k'th ind_act
                
                #if scale_activations_to_highest == 'yes': #scales the intensity of the activation colours (useful for simulations where muscle activations are low)
                #    activation = activation/data[:,ind_act].max()
                
                #if activation < 0.2:
                #    activation = 0.2
                    
                node_tree.nodes[nodename].inputs['Saturation'].default_value = activation
                node_tree.nodes[nodename].inputs['Saturation'].keyframe_insert('default_value', frame = frame_number) #insert a keyframe

                

        return {'FINISHED'}

    