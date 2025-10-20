import bpy
import addon_utils
import os
import numpy as np
import sys
from mathutils import (Matrix, Vector)
import csv

# This script will perform a moment arm hyperplane analysis for the van Bijlert et al. 2024 emu models, available from:
# https://simtk.org/projects/emily_project
# Also available in the MuSkeMo sample dataset: https://github.com/PashavanBijlert/MuSkeMo/releases/tag/v0.x-sampledataset1
# The script assumes the OpenSim model is imported into the blend file, and that the blend file has been saved somewhere.
# You can use this script as a starting point to plot the moment arms in your own model.
# Go to https://github.com/PashavanBijlert/MuSkeMo/releases/tag/v0.x-momentarmhyperplane for a Matlab script that plots the result


# A moment arm hyperplane is the moment arm of a muscle, computed for different combinations of two degrees of freedom.
# In this case, we will loop over hip Rx and hip Rz (abduction and flexion).
# The results are exported as a CSV.
# See the manual for a plotted figure of the results.


##########
########## User switches
##########

desired_subdirectory_name = "muscle_analysis" #This will be a subdir of the blend file's directory

# Define ranges, all in degrees 

joint_ranges = {}

joint_ranges['hip_r'] = {              #should be exactly 2 coordinates per joint.
        'Rx': (-20, 20),               #Should by Rx, Ry, or Rz
        'Rz': (0, 45)
    }

angle_step_size = 1 #in degrees



#It would be possible to extend this to replace joint_ranges by coordinate_ranges, match each coordinate to a specific joint,
#and then specify the dof that way

##########
##########
##########


### import scripts and functions we will need

muskemo_module = next((mod for mod in addon_utils.modules() if mod.__name__ == 'MuSkeMo'), None) #assumes MuSkeMo addon is installed
MuSkeMo_folder =  os.path.dirname(muskemo_module.__file__) #parent folder of MuSkeMo, which also includes the 'MuSkeMo utilities' folder
scripts = os.path.join(MuSkeMo_folder, 'scripts')
sys.path.append(scripts) #append the muskemo scripts folder to sys, so we can directly import from the folder

## now we can import from the muskemo scripts folder
from compute_curve_length import compute_curve_length #from the .py file import the function
from euler_XYZ_body import matrix_from_euler_XYZbody



#### Get all the joints and muscles

muskemo_objects = [x for x in bpy.data.objects if 'MuSkeMo_type' in x]
joints = [x for x in muskemo_objects if x['MuSkeMo_type']=='JOINT']
muscles = [x for x in muskemo_objects if x['MuSkeMo_type']=='MUSCLE']


'''
paste code back later

'''
depsgraph = bpy.context.evaluated_depsgraph_get()#get the dependency graph

### Find out which muscles cross each joint.
### First, compute all the lengths in neutral posture
### Loop through each joint, rotate it once to see which muscles change length.
### if the lengths change, add that muscle to a dict for that joint

depsgraph.update()


muscle_lengths_neutral = [] #list of muscle lengths in neutral position
for muscle in muscles:
    
    #Compute length in this position
    muscle_lengths_neutral.append(compute_curve_length(muscle.name, depsgraph))
  
joint_crossing_muscles = {} #dict with for each joint, a list of muscles that cross it

test_rotation = Vector([np.pi/2]*3)  #(45, 45, 45) deg rot
'''
removed the autodetect muscle crossing loop here and the wrap resolution setter, because we are hardcoding this script for HF_r.
See moment_arm_analysis.py
 
'''
joint_crossing_muscles['hip_r'] = [bpy.data.objects['HF_r']]    

#### now we have a dict which contains, for each joint, which muscles cross it. We can now start computing moment arms for each joint.
#### Approach:
#### Loop through each joint
#### For each joint, loop through the desired joint range
#### At each angle, loop through each of the joint's crossing muscles, compute length in that position
#### At the end of the joint range, reset the joint's original orientation
#### Compute moment arms as r = -dL/dphi for each muscle, add it to a dict
#### At the end, export the dict as a CSV or something equivalent


#loop through each joint
#rotate it through the specified range
#then compute the moment arm for all of the muscles that cross it


muscle_lengths = {}
moment_arms = {}
joint_angles = {}


for joint in joints:
        
    #check if it is one of the desired joints
    
    if joint_ranges.get(joint.name):
        
        joint_angles[joint.name] = [] #preallocate the list
        
        coordinate_1_dof = list(joint_ranges[joint.name].keys())[0] #Rx, Ry, or Rz, whatever we wrote in joint_ranges earlier
        
        ### dof 1
        dof_1_ranges = joint_ranges[joint.name][coordinate_1_dof] #tuple of range in degrees
        
        min_range_angle1 = min(dof_1_ranges) #in degrees
        max_range_angle1 = max(dof_1_ranges)
     
        angle_1_range = np.arange(min_range_angle1-angle_step_size, max_range_angle1+ 2*angle_step_size, angle_step_size)  #we pad by one extra step on both sides so the gradient is correct for moment arm computation. We also add one step at the end because range always skips the last
        
        # Convert degrees to radians for each angle
        angle_1_range_rad = np.deg2rad(angle_1_range)
        
                
        ## unit_vec will be multiplied by the instantaneous angle, resulting in a 3,1 vector that contains the angle and 2 zeros
        if coordinate_1_dof == 'Rx':
            unit_vec_1 = np.array([1,0,0])

        elif coordinate_1_dof == 'Ry':
            unit_vec_1 = np.array([0,1,0])
        
        elif coordinate_1_dof == 'Rz':
            unit_vec_1 = np.array([0,0,1])
        
        ### dof 2
        
        coordinate_2_dof = list(joint_ranges[joint.name].keys())[1] #Rx, Ry, or Rz, whatever we wrote in joint_ranges earlier
        dof_2_ranges = joint_ranges[joint.name][coordinate_2_dof] #this should be the first tuple we passed earlier
        
        min_range_angle2 = min(dof_2_ranges) #in degrees
        max_range_angle2 = max(dof_2_ranges)
     
        angle_2_range = np.arange(min_range_angle2-angle_step_size, max_range_angle2+ 2*angle_step_size, angle_step_size)  #we pad by one extra step on both sides so the gradient is correct for moment arm computation. We also add one step at the end because range always skips the last
        
        # Convert degrees to radians for each angle
        angle_2_range_rad = np.deg2rad(angle_2_range)
        

        ## unit_vec will be multiplied by the instantaneous angle, resulting in a 3,1 vector that contains the angle and 2 zeros
        if coordinate_2_dof == 'Rx':
            unit_vec_2 = np.array([1,0,0])

        elif coordinate_2_dof == 'Ry':
            unit_vec_2 = np.array([0,1,0])
        
        elif coordinate_2_dof == 'Rz':
            unit_vec_2 = np.array([0,0,1])
        
       
        
        
        ## preallocate the dict entries as lists    
        
        for muscle in joint_crossing_muscles[joint.name]:
            
            dictitem = muscle.name + '_' + joint.name
            muscle_lengths[dictitem] = []
            
           
            
        ## rotate the joint and compute the length of each crossing muscle
        
        joint_wm_copy = joint.matrix_world.copy() #copy of the current position of the joint world matrix
            
        for angle1 in angle_1_range_rad: #loop through each desired angle, set the joint in that orientation, compute the muscle length, then rotate the joint back.
            
            lengths_angle_1 = [] #preallocate. We will get a list of lengths for each angle 1, where we try out all lengths due to angle_2 changes
            
        
            joint_angles[joint.name].append(angle_2_range_rad.tolist())
            for angle2 in angle_2_range_rad:
                
                
                euler_angle = angle1*unit_vec_1 + angle2 *unit_vec_2
                
                #Local frame rotation
                [gRb, bRg] = matrix_from_euler_XYZbody(euler_angle) #rotation matrix for the desired angle combination
                
                wm = joint.matrix_world #current world matrix
                joint_gRb = wm.to_3x3() #
                translation = wm.translation

                           
                new_wm = joint_gRb@gRb #post multiply by the desired rotation to get a local rotation

                new_wm = new_wm.to_4x4()       
                new_wm.translation = translation
                joint.matrix_world = new_wm
                
                for muscle in joint_crossing_muscles[joint.name]:
                    
                    #Compute length in this position
                    length = compute_curve_length(muscle.name, depsgraph)
                    lengths_angle_1.append(length)
                                    

                #reset to original position.  ### we reset the position each time. This is not costlier than simply progressing from min to max, as long as you don't update the despgraph after resetting the joint position.

                joint.matrix_world = joint_wm_copy
            
            muscle_lengths[muscle.name + '_' + joint.name].append(lengths_angle_1)       
            
            
        for muscle in joint_crossing_muscles[joint.name]:
            
            
            #Compute length in this position

            dictitem = muscle.name + '_' + joint.name
            
            moment_arms[dictitem] = []
            
            for length_list, angle_list in zip(muscle_lengths[dictitem],joint_angles[joint.name]):           
                moment_arm_list = [-x/y for x,y in zip(np.gradient(length_list), np.gradient(angle_list))]   
                
                moment_arms[dictitem].append(moment_arm_list)
            
        
    depsgraph.update()


#remove padding


for joint_name in joint_angles:
    joint_angles[joint_name] = np.array(joint_angles[joint_name])[1:-1, 1:-1]

for key in muscle_lengths:
    muscle_lengths[key] = np.array(muscle_lengths[key])[1:-1, 1:-1]
    
for key in moment_arms:
    moment_arms[key] = np.array(moment_arms[key])[1:-1, 1:-1]


     
# ==============================================================
# EXPORT RESULTS TO CSV (1 FILE PER MUSCLE–JOINT PAIR)
# ==============================================================

output_directory = os.path.join(bpy.path.abspath("//"), desired_subdirectory_name)
os.makedirs(output_directory, exist_ok=True) #ensure output directory exists

for key, moment_arm_data in moment_arms.items():
    joint_name = next(j for j in joint_angles if j in key)
    muscle_name = key.replace(f"_{joint_name}", "")

    # Retrieve the two coordinate names, e.g. Rx and Rz
    coords = list(joint_ranges[joint_name].keys())
    coord1, coord2 = coords[0], coords[1]

    # Extract numeric arrays
    L = muscle_lengths[key]
    R = moment_arms[key]
    angle_2_grid = np.array(joint_angles[joint_name])  # shape (n_angle1, n_angle2)

    n_angle1, n_angle2 = angle_2_grid.shape

    # Reconstruct the unpadded range for coord1 (angle_1)
    min1, max1 = joint_ranges[joint_name][coord1]
    angle_1_range = np.linspace(np.deg2rad(min1), np.deg2rad(max1), n_angle1)

    # Tile to create full angle grid
    angle_1_grid = np.tile(angle_1_range[:, np.newaxis], (1, n_angle2))

    # Flatten for export
    rows = zip(
        angle_1_grid.flatten(),
        angle_2_grid.flatten(),
        L.flatten(),
        R.flatten()
    )

    # Write to CSV
    output_path = os.path.join(output_directory, f"{key}.csv")
    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            f"angle_{coord1}_rad",
            f"angle_{coord2}_rad",
            "muscle_length_m",
            "moment_arm_m"
        ])
        writer.writerows(rows)



'''   
removed the resetting of wrap_resolution. See moment_arm_analysis.py
'''