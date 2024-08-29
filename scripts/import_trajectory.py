import bpy
from mathutils import Vector


from bpy.types import (Operator,
                        )

from bpy.props import (StringProperty,   #it appears to matter whether you import these from types or from props
                       BoolProperty)


from math import nan


import numpy as np
import os
import csv


class ImportTrajectorySTO(Operator):
    bl_description = "Import a trajectory in .sto file format"
    bl_idname = "import.import_trajectory_sto"
    bl_label = "Import .sto strajectory"


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

            for row in reader:
                if 'endheader' in row:
                    is_data = True
                    continue
                
                if is_data:
                    if not column_headers:  # The first row after endheader contains the column headers
                        column_headers = row
                    else:
                        data.append([float(x) for x in row])
                else:
                    file_header.append(row)
        
        return column_headers, data
    
    def execute(self, context):
        
        # Call the custom superclass method parse_sto to read the sto data
        column_headers, traj_data = self.parse_sto(context)
        
        traj_data = np.array(traj_data)
        time = traj_data[:,0] #time is the first column


        # get the joint coordinates in the model
        joint_col = bpy.data.collections[bpy.context.scene.muskemo.joint_collection]
        joints = [x for x in joint_col.objects if 'MuSkeMo_type' in x and x['MuSkeMo_type']=='JOINT']

        coordinate_types = ['coordinate_Rx', 'coordinate_Ry', 'coordinate_Rz', 'coordinate_Tx', 'coordinate_Ty', 'coordinate_Tz'] #the six possibilities
        model_coordinates = [] #the actual coordinate names in the model
        model_coordinate_types = [] #the corresponding coordinate type (eg Rz)
        model_coordinate_joints = [] #the joints that own the coordinates

        
        

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


        for idx, coordinate in enumerate(model_coordinates):
            
            ind = [i for i, x in enumerate(column_headers) if coordinate in x and ('value' in x or coordinate==x)] #indices of the joint angles. #OpenSim outputs have /value at the end, Hyfydy outputs simply have only the coordinate as the header
            traj_coor = [x for i, x in enumerate(column_headers) if coordinate in x and ('value' in x or coordinate==x)] #coordinate name in the trajectory data

            if not traj_coor:
                self.report({'WARNING'}, "Model coordinate '" + coordinate + "' was not found in the imported trajectory. This coordinate will be skipped during trajectory import")

            elif len(traj_coor)>1:
                self.report({'WARNING'}, "Model coordinate '" + coordinate + "' has a non-unique mapping in the trajectory data. This coordinate will be skipped during trajectory import")
                
            else:
                traj_coordinate_headers.append(traj_coor[0])
                traj_coordinate_ind.append(ind[0])
                traj_joints.append(model_coordinate_joints[idx])
                traj_model_coordinates.append(coordinate)
                traj_model_coordinate_types.append(model_coordinate_types[idx])


        coordinate_trajectories = traj_data[:,traj_coordinate_ind]

        ## get the muscles in the model
        ## get the muscle activations in the trajectory

        #### MAKE INTO USER SWITCHES
        number_of_repeats = 9 # number of strides. Should be a user switch. Assumes final state is equal to initial state, except pelvis x translation, so a full stride.
        fps = 60 #set to 60 if you want 50% slow motion (for a run)
        root_joint_name = 'groundPelvis'
        forward_progression_coordinate = 'coordinate_Tx'


        root_joint_ind = [i for i,x in enumerate(traj_joints) if root_joint_name == x.name]#these column indices have root joint data in coordinate_trajectories
        root_progression_ind = [x for x in root_joint_ind if traj_model_coordinate_types[x]==forward_progression_coordinate] #this is the index to the coordinate that indicates forward progression (usually pelvis Tx)



        if number_of_repeats >0:
            print('work in progress, only one repeat for now')
            
            # Initialize the new time array with the original time array
            time_repeated = time.copy()
            coordinate_trajectories[:,root_progression_ind] = coordinate_trajectories[:,root_progression_ind] - coordinate_trajectories[0,root_progression_ind]
            coordinate_trajectories_repeated = coordinate_trajectories.copy() 

            

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
            

            time = time_repeated
            coordinate_trajectories = coordinate_trajectories_repeated

            
            # fix all other data (coordinates, and muscle activations)
  
        n_times = len(time)
        time_end = time[-1]

        n_frames = round(time_end * fps )#number of frames. We will interpolate between 1 and n_frames+1, to ensure that time_end coincides with the start of n_frames+1

        
        dt = time_end/(n_times-1)
        #x_p = np.arange(1, n_times + 1)  #List of indices in ascending order in steps of 1, from 1 to n_times (we add +1 at the end because arange stops 1 before the upper number)
        #x = np.linspace(1,n_times,n_frames+1) 
        #x_query = [x[i] for i in range(0,n_frames+1)]

        x = np.linspace(1,n_frames+1,n_times)  # a vector from 1 to n_frames, with length equal to n_times
        x_query = np.arange(1, n_frames+2) #vector from 1 n_frames+1, in steps of 1. These will be the query points for the interpolation. We interpolate between 1 and n_frames+1, adding another +1 because arange clips the last one

        
        #n_cols = (len(data[0])) #number of columns

        ### resample the time vector
        time_rs = np.interp(x_query, x,time) #resampled time using numpy interpolation. This is 1 longer than n_frames
        
        ## resample coordinate trajectories
        # Initialize an empty array to hold the resampled coordinates
        coordinate_trajectories_rs = np.zeros((len(x_query), coordinate_trajectories.shape[1]))  # n_frames+1 x n_coordinates

        # Loop through each column (each coordinate trajectory)
        for i in range(coordinate_trajectories.shape[1]):
            coordinate_trajectories_rs[:, i] = np.interp(x_query, x, coordinate_trajectories[:, i])
                      

        
        
        ##### start adding keyframes
        ##### insert a rest-pose keyframe at frame number 0

        frame_number = 0

        root_joint = bpy.data.objects[root_joint_name]
        
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

        ##### start inserting keyframes per time point


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
                        Rx = coordinate_traj_row[idx]
                    
                    if traj_model_coordinate_types[idx] == 'coordinate_Ry':
                        Ry = coordinate_traj_row[idx]

                    if traj_model_coordinate_types[idx] == 'coordinate_Rz':
                        Rz = coordinate_traj_row[idx]   
           
                #add the position and orientation, using the original position and orientation as an offset.
                #the above loop should have only added the changed coordinates (e.g. Rz), zo all the other components are simply zero.
                joint.location = Vector((Tx, Ty, Tz)) + base_position[joint_ind]
                joint.rotation_euler = (base_orientation[joint_ind][0] + Rx,
                                        base_orientation[joint_ind][1] + Ry, 
                                        base_orientation[joint_ind][2] + Rz)
               
                joint.keyframe_insert('rotation_euler', frame = frame_number)
                joint.keyframe_insert('location', frame = frame_number)

                

        return {'FINISHED'}

    