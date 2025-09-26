# Download the blend file from sample dataset 2 to try out this script: https://github.com/PashavanBijlert/MuSkeMo/releases/tag/v0.x-sampledataset2
# 

#The script will move the the target joint over the specified angle ranges, and checks if it is viable.
#If the pose does not result in intersections between geometries of the parent body and the child body,
#The pose is treated as viable. The landmark position is sampled and a small sphere is placed at that position
# The script works in 3D.

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

target_joint_name = "knee_r"  #the joint you would like to move
target_landmark_name = 'shank_dist_marker' #The landmark position that we will use for the ROM visualization

visualize_endpoint_markers = True #if you want to actually create markers for the segment endpoints
marker_radius = 0.01 #radius in meters of the endpoint markers

use_soft_tissue_constraint = True #if you want to distinguish between skeletally viable but soft tissue non viable
ligament_name = "CranCruciateLig_r" #the ligament (implemented as MuSkeMo MUSCLE) that we will use as a soft tissue constraint, by using its length as a cut off
lig_length_threshold = 0.055 # in meters. If the length is longer than this, we treat the pose as not viable.

export_results_as_CSV = True #If you want to export the results of the analysis as a CSV. Requires saving the blend file first.
output_filename = 'joint_pose_sampling_v1' #careful that it can overwrite previous results

d_phi = 5 #check intersections in steps of how many degrees? Don't make this too small or the script will take forever

x_range = [-20, 20]# degrees, x-rotation range. Second number has to be bigger than the first number, or the same
y_range = [-30, 10]# degrees, y-rotation range. Second number has to be bigger than the first number, or the same
z_range = [-100, 0]# degrees, z-rotation range. Second number has to be bigger than the first number, or the same

#if you want to check ROM in the other direction, make both d_phi and end_phi negative
axis = 'Z' #Rotate about which local axis of the joint?


# If export requested but no saved file, stop immediately
if export_results_as_CSV and not bpy.data.filepath:
    raise ValueError("Cannot export results as CSV because the Blender file has not been saved. Save the Blend file first and try again")

csv_output_path = os.path.join(os.path.dirname(bpy.data.filepath), output_filename + ".csv")


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

def collect_proximal_and_distal_geometry_names(joint_obj):
    """
    From the given JOINT object, finds GEOMETRY attached to the parent and child bodies, only.
    
    The result is ordered with the most proximal, geometries first.
    The script will work if either body has more than one GEOMETRY, but it will be faster if geometries are joined into single Blender objects
    """
    parent_geometry_names = []
    child_geometry_names = []
    
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
                parent_geometry_names.append(child.name)

        # Get the child body name from the current joint
        child_body_name = current_joint.get('child_body')
        if not child_body_name:
            break

        # Get the child body object
        child_body = bpy.data.objects.get(child_body_name)
        if not child_body:
            break

        # Collect only direct children of the body with MuSkeMo_type == 'GEOMETRY'
        for child in child_body.children:
            if child.get('MuSkeMo_type') == 'GEOMETRY':
                child_geometry_names.append(child.name)
        
        if len(parent_geometry_names)>1:
            print('Parent body has more than one attached geometries. It would be more performant to join the geometries')
            
        
        if len(child_geometry_names)>1:
            print('Child body has more than one attached geometries. It would be more performant to join the geometries')
            
        
        if (len(parent_geometry_names)==0) or (len(child_geometry_names)==0):
            print('Parent or child body has no GEOMETRY to compare intersections with')
            break
        else:
            break

    return parent_geometry_names, child_geometry_names


def create_uv_sphere(name, position, radius, segments=6, rings=6):
    mesh = bpy.data.meshes.new(name + "_mesh")
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius)
    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    obj.matrix_world.translation = position
    return obj


# ------------------------
# MAIN SCRIPT
# ------------------------

target_joint = bpy.data.objects.get(target_joint_name)
if not target_joint:
    raise ValueError(f"Target joint '{target_joint_name}' not found.")

target_joint_original_wm = target_joint.matrix_world.copy() #copy the transformation matrix

if visualize_endpoint_markers: #If we want to visualize the endpoints
    target_landmark = bpy.data.objects.get(target_landmark_name)
    if not target_landmark:
        raise ValueError(f"Target joint '{target_landmark_name}' not found.")
    
    
    ##  Names for subcollections and materials
    situation_names = ["viable", "soft_tissue_non_viable", "skeletally_non_viable"]
    colors = [(0, 0, 1, 1),    # blue
              ( 1, 0.5, 0, 1), # orange
              (1, 0, 0, 1)]     # red

    ### Create collections that will hold the endpoint markers
    # Parent collection
    parent_name = "endpoint_markers"
    parent_coll = bpy.data.collections.get(parent_name)
    if parent_coll is None:
        parent_coll = bpy.data.collections.new(parent_name)
        bpy.context.scene.collection.children.link(parent_coll)

    for name in situation_names:
        # Check if subcollection already exists under parent
        subcoll = parent_coll.children.get(name)
        if subcoll is None:
            subcoll = bpy.data.collections.new(name)
            parent_coll.children.link(subcoll)

    ### create materials for three different types of endpoint markers
   
    for name, col in zip(situation_names, colors):
        # Get existing material or create new
        mat = bpy.data.materials.get(name)
        if mat is None:
            mat = bpy.data.materials.new(name=name)
            mat.use_nodes = True
        else:
            if not mat.use_nodes:
                mat.use_nodes = True

        # Update Principled BSDF base color
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs['Base Color'].default_value = col

        # Update viewport display
        mat.diffuse_color = col
       
if use_soft_tissue_constraint:
    ligament = bpy.data.objects.get(ligament_name)
    if not ligament:
        raise ValueError(f"Soft tissue constraint '{ligament}' not found.")
    


#list of parent and child geometry names
parent_geometry_names, child_geometry_names = collect_proximal_and_distal_geometry_names(target_joint)

print(parent_geometry_names)
print(child_geometry_names)

bpy.context.scene.frame_set(0) #set the frame to 0, assuming we have a base posture at frame 0
target_joint.keyframe_insert(data_path="rotation_euler", frame=0) 

# Store results
rom_data = [] 

#ensure that if start and end range are the same, we still test the start range
ranges = [x_range, y_range, z_range]
angles = [[np.deg2rad(a) for a in range(r[0], r[1] + d_phi, d_phi)]  for r in ranges]

x_euler, y_euler, z_euler = angles #lists of euler angles

depsgraph = bpy.context.evaluated_depsgraph_get() #Blender's dependency graph



frame = 2
# clean nested loop
for x in x_euler:
    for y in y_euler:
        for z in z_euler:
            
            euler_angles = [x, y, z]
            euler_string = f"{x:.3f}_{y:.3f}_{z:.3f}"
            
            #construct rotation matrix from euler angles
            gRj, jRg = matrix_from_euler_XYZbody(euler_angles)
            
            #construct a new temporary world matrix, and use this to check for intersections
            temp_wm = gRj.to_4x4()
            temp_wm.translation = target_joint_original_wm.translation
            
            target_joint.matrix_world = temp_wm #
            
            #update dependency graph before intersection checking
            
            depsgraph.update()
            bpy.context.view_layer.update()
            
            ### check for intersections
            intersect_found = False
            constrained_by_soft_tissue = False
            
            
            for parent_geom_name in parent_geometry_names:
                for child_geom_name in child_geometry_names:
                    intersections = check_bvh_intersection(parent_geom_name, child_geom_name, depsgraph)
                    if intersections:
                        intersect_found = True
            
            if use_soft_tissue_constraint:
                lig_ev = ligament.evaluated_get(depsgraph) #
                lig_ev_mesh = lig_ev.to_mesh()
                length = lig_ev_mesh.attributes['length'].data[0].value  #muscle length is stored as an attribute via the muscle geometry nodes.
                lig_ev.to_mesh_clear()
                
                if length > lig_length_threshold:
                    constrained_by_soft_tissue = True
                
                lig_length_value = length
                
            else:
                lig_length_value = None        
            
            if not intersect_found: #if no intersections
                
                
                if constrained_by_soft_tissue: 
                    print(f"Pose at euler: {euler_angles} is non viable due to soft tissue constraint")
                    
                    if visualize_endpoint_markers: #if we visualize endpoint markers, check what situation we'e dealing with (viable, soft non viable, skeleton non viable)
                        situation = situation_names[1] #meaning soft tissue non viable
                else: #if not constrained by soft tissue
                    print(f"Pose at euler: {euler_angles} has no skeletal intersections")
                    
                    if visualize_endpoint_markers: #if we visualize endpoint markers, check what situation we'e dealing with (viable, soft non viable, skeleton non viable)
                        situation = situation_names[0] #meaning viable
                    
                                                    
            else: #if there are soft tissue intersections
                print(f"Pose at euler: {euler_angles} has skeletal intersections")    
                
                if visualize_endpoint_markers: #if we visualize endpoint markers, check what situation we'e dealing with (viable, soft non viable, skeleton non viable)
                    situation = situation_names[2] #meaning skeletally non viable
            
            # >>> STORE RESULTS for CSV here <<<
            rom_data.append([
                x,   # radians
                y,
                z,
                situation,
                lig_length_value
            ])
                    
            
            if visualize_endpoint_markers: #if we want endpoint markers, here we create them
                #create the sphere with euler angle and situation in the name
                endpoint_sphere = create_uv_sphere(situation+ '_' + euler_string, target_landmark.matrix_world.translation, marker_radius) 
                    
                #remove existing collections
                for c in endpoint_sphere.users_collection:
                    c.objects.unlink(endpoint_sphere)    
                #call the desired collection
                coll = bpy.data.collections[situation]
                #place the endpoint marker in the correct collection
                coll.objects.link(endpoint_sphere)
                
                #call the correct material
                mat = bpy.data.materials[situation]
                #add the correct material
                endpoint_sphere.data.materials.append(mat)
                
            #keyframe the pose
            target_joint.keyframe_insert(data_path="rotation_euler", frame=frame)        
                
            ### Restore original world matrix
            
            target_joint.matrix_world = target_joint_original_wm
            
            frame += 1
            
            
end_time = time.time()
time_elapsed = end_time-start_time
time_per_frame = time_elapsed/(frame-1) #minus 1 because we start at 2

print(f"time elapsed: {time_elapsed} seconds")
print(f"time per frame: {time_per_frame} seconds")



# ------------------------
# EXPORT TO CSV
# ------------------------

if export_results_as_CSV:
    

    
    csv_output_path = os.path.join(
            os.path.dirname(bpy.data.filepath),
            output_filename + ".csv"
        )

    with open(csv_output_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["X (rad)", "Y (rad)", "Z (rad)", "Pose viability", "Ligament length (m)"])
        writer.writerows(rom_data)

    print(f"Exported ROM data to {csv_output_path}")
