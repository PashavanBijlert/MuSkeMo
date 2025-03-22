import bpy
import addon_utils
import os
import numpy as np
import sys
from mathutils import (Matrix, Vector)
import csv

# This script will perform a moment arm analysis for the van Bijlert et al. 2024 emu models, available from:
# https://simtk.org/projects/emily_project
# Also available in the MuSkeMo sample dataset: https://github.com/PashavanBijlert/MuSkeMo/releases/tag/v0.x-sampledataset1
# The script assumes the OpenSim model is imported into the blend file, and that the blend file has been saved somewhere.
# You can this script as a starting point to plot the moment arms in your own model.


##########
########## User switches
##########

desired_subdirectory_name = "muscle_analysis" #This will be a subdir of the blend file's directory

# Define ranges, all in degrees
joint_ranges = {}


joint_ranges['hip_r'] = tuple([0, 45])
joint_ranges['knee_r'] = tuple([-15, -80])
joint_ranges['ankle_r'] = tuple([5, 75]) #you can add more

#joint_ranges['my_joint'] = tuple([min_angle, max_angle]) 

angle_step_size = 1 #in degrees


joint_1_dof = 'Rz' #we only rotate about Rz for this script
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


##### Set the wrap object resolutions to be higher, for more accurate length computations.
## This won't affect results in the current analysis, but could impact the results in situations where the muscle also comes away from the wrap in certain poses

wrap_obj_res = 500


for muscle in muscles:
    
    wrapmods = [x for x in muscle.modifiers if 'wrap' in x.name.lower()] #the wrap modifiers that this muscle has

    
    for modifier in wrapmods:
        
        wrapobj = modifier["Socket_2"]

        wrapobj.modifiers["WrapObjMesh"]

        if wrapobj['wrap_type'] == 'Cylinder':
            #wrap object resolution
            wrapobj.modifiers["WrapObjMesh"].node_group.nodes['Cylinder'].inputs['Vertices'].default_value = wrap_obj_res
            
            modifier.show_render = not modifier.show_render  # Toggle visibility to refresh
            modifier.show_render = not modifier.show_render



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

for joint in joints:
    joint_wm_copy = joint.matrix_world.copy() #copy of the current position of the joint world matrix
     
     #Local frame rotation
    [gRb, bRg] = matrix_from_euler_XYZbody(test_rotation) #rotation matrix for the desired angle
    wm = joint.matrix_world #current world matrix
    joint_gRb = wm.to_3x3() #
    translation = wm.translation

               
    new_wm = joint_gRb@gRb #post multiply by the desired rotation to get a local rotation

    new_wm = new_wm.to_4x4()       
    #new_wm.translation = translation
    joint.matrix_world = new_wm #joint gets rotated and transported to the origin.
    
    changed_length_list = []
    #for all muscles, compute the length
    for muscle, neutral_length in zip(muscles, muscle_lengths_neutral):
        length = compute_curve_length(muscle.name, depsgraph)
        #if the length changed, add it to the dict for that joint
        if round(length,4) != round(neutral_length,4): #rounding because Blender uses single precision digits and python uses double precision
            changed_length_list.append(muscle) #add this muscle to the list of muscles with changed length
            
        joint_crossing_muscles[joint.name]=changed_length_list #add list to the dict entry for this joint
        
        
      
    #reset to original position.  ### we reset the position each time. This is not costlier than simply progressing from min to max, as long as you don't update the despgraph after resetting the joint position.

    joint.matrix_world = joint_wm_copy
    depsgraph.update()
    

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
        joint_1_ranges = joint_ranges[joint.name]
        
        min_range_angle1 = min(joint_1_ranges) #in degrees
        max_range_angle1 = max(joint_1_ranges)
     
        angle_1_range = np.arange(min_range_angle1-angle_step_size, max_range_angle1+ 2*angle_step_size, angle_step_size)  #we pad by one extra step on both sides so the gradient is correct for moment arm computation. We also add one step at the end because range always skips the last
        
        # Convert degrees to radians for each angle
        angle_1_range_rad = np.deg2rad(angle_1_range)
        
        joint_angles[joint.name] = angle_1_range_rad[1:-1] #skip the padded values

        ## unit_vec will be multiplied by the instantaneous angle, resulting in a 3,1 vector that contains the angle and 2 zeros
        if joint_1_dof == 'Rx':
            unit_vec= np.array([1,0,0])

        elif joint_1_dof == 'Ry':
            unit_vec= np.array([0,1,0])
        
        elif joint_1_dof == 'Rz':
            unit_vec= np.array([0,0,1])
        
        
        ## preallocate the dict entries as lists    
        
        for muscle in joint_crossing_muscles[joint.name]:
            
            dictitem = muscle.name + '_' + joint.name
            muscle_lengths[dictitem] = []
           
            
        ## rotate the joint and compute the length of each crossing muscle
        
        joint_wm_copy = joint.matrix_world.copy() #copy of the current position of the joint world matrix
            
        for angle in angle_1_range_rad: #loop through each desired angle, set the joint in that orientation, compute the muscle length, then rotate the joint back.

            
            #Local frame rotation
            [gRb, bRg] = matrix_from_euler_XYZbody(angle*unit_vec) #rotation matrix for the desired angle
            
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
                muscle_lengths[muscle.name + '_' + joint.name].append(length)
                                

            #reset to original position.  ### we reset the position each time. This is not costlier than simply progressing from min to max, as long as you don't update the despgraph after resetting the joint position.

            joint.matrix_world = joint_wm_copy       
        
        for muscle in joint_crossing_muscles[joint.name]:
                
            #Compute length in this position
            
            dictitem = muscle.name + '_' + joint.name
                        
            moment_arm = [-x/y for x,y in zip(np.gradient(muscle_lengths[dictitem]), np.gradient(angle_1_range_rad))]
            moment_arms[dictitem] = moment_arm[1:-1]#skip the padded values
            muscle_lengths[dictitem] = muscle_lengths[dictitem][1:-1] #skip the padded values                   
        
    depsgraph.update()

# Ensure output directory exists
output_directory = os.path.join(bpy.path.abspath("//"), desired_subdirectory_name) 
os.makedirs(output_directory, exist_ok=True)


for key, moment_arm_data in moment_arms.items():
    # Split the key into muscle_name and joint_name
    joint_name = next(joint for joint in joint_angles if joint in key)  # Find matching joint name
    muscle_name = key.replace(f"_{joint_name}", "")  # Remove the joint name to get the muscle name
    
    # Prepare the data for export
    joint_data = joint_angles[joint_name]  # Joint angles for this joint
    muscle_data = muscle_lengths[key]  # Muscle lengths corresponding to this moment arm
    
    # Ensure all arrays have the same length
    num_timepoints = min(len(joint_data), len(muscle_data), len(moment_arm_data))
    
    # File path for this CSV
    output_path = os.path.join(output_directory, f"{key}.csv")
    
    # Write the CSV file
    with open(output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        
        # Write headers
        writer.writerow([joint_name + "_angle(rad)", "muscle_length(m)", "moment_arm(m)"])
        
        # Write rows of data
        for i in range(num_timepoints):
            writer.writerow([joint_data[i], muscle_data[i], moment_arm_data[i]])



##### Reset the wrap object resolutions to default values


for muscle in muscles:
    
    wrapmods = [x for x in muscle.modifiers if 'wrap' in x.name.lower()] #the wrap modifiers that this muscle has

    
    for modifier in wrapmods:
        
    
        wrapobj = modifier["Socket_2"]

        wrapobj.modifiers["WrapObjMesh"]

        if wrapobj['wrap_type'] == 'Cylinder':
            #wrap object resolution
            wrapobj.modifiers["WrapObjMesh"].node_group.nodes['Cylinder'].inputs['Vertices'].default_value = 32

