#This script checks the neck joint range of motions for the modified emu model in sample dataset 2.
#That version of the model has the neck positions modified with respect to the original publication,
#because the model was not initially developed with neck joint range of motions in mind. If this is your goal, the emu model will require more extensive modifications.
#This script assumes the starting pose is viable, and will keep checking the ultimate range of motion
#around a single axis, until it hits an intersection, or until it hits "end_phi".
#If the starting pose is not viable, it will immediately move on to the next joint.
#The script progresses from the designated root joint, checks the intersections between the geometry 
#immediately distal to the joint, with all the geometries proximal to it.
# It will move on to the next most distal joint sequentially.
#It is written specifically with necks and tails in mind (so each body should only have one child joint),
# but it could easily be extended.

# Download the blend file from sample dataset 2 to try out this script: https://github.com/PashavanBijlert/MuSkeMo/releases/tag/v0.x-sampledataset2

import bpy
import addon_utils
from mathutils import Matrix
from math import (cos, sin, pi)
import bmesh
import numpy as np
import csv
import os
import sys
import time

start_time = time.time()

# ------------------------
# SETTINGS
# ------------------------


root_joint_name = "neck_18_joint"  # Root joint. 
#Script will traverse distally from the root.
#For each joint, it keeps rotating until the vert distal to it
#intersects with any mesh proximal to it. Then it moves on to the
#first joint distal to it, and repeats this till the end.


keyframe_number = 1            # The final posture is keyframed in this frame in the timeline.
#Change this so you can save the end result of different analyses


export_results_as_CSV = True #If you want to export the results of the analysis as a CSV. Requires saving the blend file first.
output_filename = 'joint_rom_flexion_v1' #careful that it can overwrite previous results

# If export requested but no saved file, stop immediately
if export_results_as_CSV and not bpy.data.filepath:
    raise ValueError("Cannot export results as CSV because the Blender file has not been saved. Save the Blend file first and try again")


csv_output_path = os.path.join(os.path.dirname(bpy.data.filepath), output_filename + ".csv")



d_phi = -1 #check intersections in steps of how many degrees? Don't make this too small or the script will take forever
end_phi = -25 # maximum ROM before we stop, in degrees
#if you want to check ROM in the other direction, make both d_phi and end_phi negative
axis = 'Z' #Rotate about which local axis of the joint?
    

### import scripts and functions we will need

muskemo_module = next((mod for mod in addon_utils.modules() if mod.__name__ == 'MuSkeMo'), None) #assumes MuSkeMo addon is installed
MuSkeMo_folder =  os.path.dirname(muskemo_module.__file__) #parent folder of MuSkeMo, which also includes the 'MuSkeMo utilities' folder
scripts = os.path.join(MuSkeMo_folder, 'scripts')
sys.path.append(scripts) #append the muskemo scripts folder to sys, so we can directly import from the folder

## now we can import from the muskemo scripts folder
from compute_curve_length import compute_curve_length #from the .py file import the function
from euler_XYZ_body import matrix_from_euler_XYZbody
from two_object_intersection_func import check_bvh_intersection



# ------------------------
# HELPER FUNCTIONS TO GET MODEL GEOMETRY LISTS
# ------------------------


def collect_proximal_geometry_names(joint_obj):
    """
    Walks upward through the joint hierarchy starting from the given JOINT object,
    collecting names of immediate GEOMETRY-type children of each parent body.

    The result is ordered with the closest (most proximal) geometries first.
    """
    geometry_names = []

    current_joint = joint_obj

    while True:
        # Get the parent body name from the current joint
        parent_body_name = current_joint.get('parent_body')
        if not parent_body_name:
            break

        # Get the parent body object
        parent_body = bpy.data.objects.get(parent_body_name)
        if not parent_body:
            break

        # Collect only direct children of the body with MuSkeMo_type == 'GEOMETRY'
        for child in parent_body.children:
            if child.get('MuSkeMo_type') == 'GEOMETRY':
                geometry_names.append(child.name)

        # Move up to the next joint if it exists
        parent_joint = parent_body.parent
        if parent_joint and parent_joint.get('MuSkeMo_type') == 'JOINT':
            current_joint = parent_joint
        else:
            break

    return geometry_names

# ------------------------
# Build List of All Joints (Non-Recursive)
# ------------------------

def get_all_distal_joints(root_joint):
    """
    Returns a list of all joints connected downstream from the root_joint
    by following child_body -> parent_body relationships.
    """
    joint_queue = [root_joint]
    joint_list = []

    while joint_queue:
        joint = joint_queue.pop(0)
        joint_list.append(joint)

        child_body_name = joint.get('child_body')
        if not child_body_name:
            continue

        for obj in bpy.data.objects:
            if obj.get('MuSkeMo_type') == 'JOINT' and obj.get('parent_body') == child_body_name:
                joint_queue.append(obj)

    return joint_list


# ------------------------
# Merge a list of objects so that we don't have to check the intersections one at a time
# ------------------------


def merge_objects(obj_names):
    """Duplicate a list of objects, join them, and return the merged object."""
    dupes = []
    temp_meshes = []
    for name in obj_names:
        src = bpy.data.objects[name]
        dup = src.copy()
        dup.data = src.data.copy()  # duplicate mesh data
        temp_meshes.append(dup.data)  # keep track of these
        bpy.context.collection.objects.link(dup)
        dupes.append(dup)

    # select duplicates and make first one active
    bpy.ops.object.select_all(action='DESELECT')
    for o in dupes:
        o.select_set(True)
    bpy.context.view_layer.objects.active = dupes[0]

    # join duplicates into one object if indeed there are multiple
    if len(dupes)>1:
        bpy.ops.object.join()
    merged = dupes[0]

    # delete all old duplicate meshes except the merged one
    for m in temp_meshes:
        if m != merged.data and m.users == 0:
            bpy.data.meshes.remove(m)

    return merged


# ------------------------
# Delete the merged objects
# ------------------------

def delete_merged(merged_obj):
    """Delete a merged object and its mesh data to clean up."""
    mesh = merged_obj.data
    bpy.data.objects.remove(merged_obj)
    bpy.data.meshes.remove(mesh)




# ------------------------
# MAX Rotation Computation
# ------------------------
# We loop through a set of angles. Each step of the loop, we check whether the current pose is viable.
# If it is, we accept this pose, and rotate it one step further to check in the next iteration whether that pose is also viable.
# Once we find a non-viable degree of rotation, we stop the loop for this specific joint.
# Viability is checked by seeing if the geometries attached to the joint's child body intersect with any of the geometries proximal to it.
# Note that this loop checks for intersections between all geometries proximal to the joint with geometries attached to the child body - nothing more distal than the child body is evaluated.
# To save computation time, all proximal meshes are merged for the computation, and all the child body's geometry are merged.

def compute_max_joint_rotation(joint_obj, axis, frame_number, d_phi=1, end_phi=15):
    """
    Rotate the joint in steps of d_phi until an intersection is detected.
    The last feasible pose (just before the intersection) is keyframed.
    Returns the last feasible rotation angle in degrees.
    """


    joint_name = joint_obj.name
    child_body_name = joint_obj.get('child_body')
    if not child_body_name:
        print(f"{joint_name} missing 'child_body'")
        return 0

    child_body = bpy.data.objects[child_body_name]

    # Collect geometry directly attached to the child body
    child_geom_names = [
        c.name for c in child_body.children
        if c.get('MuSkeMo_type') == 'GEOMETRY'
    ]

    # Collect all proximal geometry
    all_proximal_mesh_names = collect_proximal_geometry_names(joint_obj)
    
    # Merge proximal objects ONCE (they don't move relative to the root of the check)
    prox_obj_merged = merge_objects(all_proximal_mesh_names)

    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    # --- SAVE INITIAL STATE ---
    # Save the exact starting matrix to restore later (avoids floating point drift)
    start_matrix_world = joint_obj.matrix_world.copy() 
    start_translation = joint_obj.matrix_world.translation.copy()

    # Track valid states
    last_feasible_angle = 0
    # Initialize valid matrix as the starting one
    last_feasible_worldmatrix = start_matrix_world.copy() 

    # We iterate through the angles
    # Note: We use a while loop or manual step handling to ensure clean updates
    current_phi = 0
    
    # Determine step direction for the range function
    step_sign = 1 if end_phi >= 0 else -1
    
    # Create range including the 0 (start) and the end_phi
    # We add d_phi to the 'stop' parameter to ensure the final value is included
    range_steps = range(0, end_phi + d_phi, d_phi) if d_phi != 0 else [0]

    intersection_found = False

    for steps in range_steps:
        # 1. FORCE SCENE UPDATE
        # This ensures the child objects move to the new joint position 
        # BEFORE we copy them in merge_objects.
        bpy.context.view_layer.update()

        # 2. Merge child mesh (Now they are at the correct location)
        child_obj_merged = merge_objects(child_geom_names)
        
        # 3. Update depsgraph for the new merged object
        depsgraph.update()
        
        # 4. Check intersection
        intersections = check_bvh_intersection(child_obj_merged.name, prox_obj_merged.name, depsgraph)
        
        # Clean up the temp child merge immediately
        delete_merged(child_obj_merged)

        print(f"Angle: {steps}, Intersect: {bool(intersections)}")

        if intersections:
            # Intersection found! 
            intersection_found = True
            
            if steps == 0:
                last_feasible_angle = 'start_pose_not_viable'
                # If start is bad, we rely on the logic below to restore start_matrix (or keep as is)
            
            # Stop checking further
            break

        else:
            # NO intersection. This pose is safe.
            last_feasible_angle = current_phi
            last_feasible_worldmatrix = joint_obj.matrix_world.copy()

        # ------------------------------------------------------------------
        # PREPARE NEXT ROTATION
        # ------------------------------------------------------------------
        # If we haven't reached the end, apply rotation for the *next* loop iteration
        
        # Calculate rotation matrix for d_phi
        wm = joint_obj.matrix_world
        gRj = wm.to_3x3()
        d_phi_rad = np.deg2rad(d_phi)

        if axis == 'Z':
            euler_angles = [0, 0, d_phi_rad]
        elif axis == 'X':
            euler_angles = [d_phi_rad, 0, 0]
        elif axis == 'Y':
            euler_angles = [0, d_phi_rad, 0]

        gRb, bRg = matrix_from_euler_XYZbody(euler_angles)
        new_gRj = gRj @ gRb

        # Apply new matrix
        joint_obj.matrix_world = new_gRj.to_4x4()
        joint_obj.matrix_world.translation = start_translation # Keep original position

        # Increment tracker
        current_phi += d_phi

    # ----------------------------------------------------------------------
    # APPLY RESULT
    # ----------------------------------------------------------------------
    
    # 1. Restore the LAST KNOWN SAFE matrix
    joint_obj.matrix_world = last_feasible_worldmatrix
    
    # 2. Keyframe this safe pose
    joint_obj.keyframe_insert(data_path="rotation_euler", frame=frame_number)

    # 3. RESET joint to ORIGINAL starting pose for the next joint in the chain
    # This prevents error accumulation for subsequent joints
    joint_obj.matrix_world = start_matrix_world

    # Cleanup proximal merge
    delete_merged(prox_obj_merged)

    return last_feasible_angle


# ------------------------
# MAIN SCRIPT
# ------------------------

root_joint = bpy.data.objects.get(root_joint_name)
if not root_joint:
    raise ValueError(f"Root joint '{root_joint_name}' not found.")

all_joints = get_all_distal_joints(root_joint)


bpy.context.scene.frame_set(0) #set the frame to 0, assuming we have a base posture at frame 0
# Store results
rom_data = []

for joint in all_joints:
    joint_name = joint.name
    
    print(f"Processing joint {joint_name} (axis: {axis})")
    
    joint.keyframe_insert(data_path="rotation_euler", frame=0)
    
    last_feasible_angle = compute_max_joint_rotation(
        joint_obj=joint,
        axis=axis,
        frame_number=keyframe_number,
        d_phi=d_phi,
        end_phi=end_phi
    )

    rom_data.append((joint_name, axis, last_feasible_angle))

# ------------------------
# EXPORT TO CSV
# ------------------------

with open(csv_output_path, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(["Joint Name", "Axis", "Total Rotation (degrees)"])
    for row in rom_data:
        writer.writerow(row)
        print(row)
    writer.writerow([])  # Empty row for spacing (optional)
    writer.writerow([f"saved to keyframe: {keyframe_number}"])

print(f"Exported ROM data to {csv_output_path}")

end_time = time.time()
elapsed = end_time - start_time
print(f"Time elapsed: {elapsed:.2f} seconds")