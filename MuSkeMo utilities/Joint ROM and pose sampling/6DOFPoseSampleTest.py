# Download the blend file from the pose sampling stress test dataset to try out this script: https://github.com/PashavanBijlert/MuSkeMo/releases/tag/v0.x-posesamplestresstest
# 

#The script will move the the target joint over the specified angle and position ranges, and checks if it is viable.
#If the pose does not result in intersections between geometries of the parent body and the child body,
#The pose is treated as viable. The landmark position is sampled and a small sphere is placed at that position
#The default sample densities find no viable poses, because the test is intentionally designed to require very high
#sample densities. See the manual for details. Viable poses can be found by setting sample densities to 3, at which point the code will take several hours to complete.


import bpy
import addon_utils
from mathutils import (Matrix, Vector)
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

target_joint_name = "screw_joint"  #the joint you would like to move
target_landmark_name = 'screw_central_landmark' #The landmark position that we will use for the ROM visualization

visualize_endpoint_markers = True #if you want to actually create markers for the segment endpoints
marker_radius = 0.25 #radius in meters of the endpoint markers

use_soft_tissue_constraint = False #if you want to distinguish between skeletally viable but soft tissue non viable
#ligament_name = "CranCruciateLig_r" #the ligament (implemented as MuSkeMo MUSCLE) that we will use as a soft tissue constraint, by using its length as a cut off
#lig_length_threshold = 0.055 # in meters. If the length is longer than this, we treat the pose as not viable.

export_results_as_CSV = True #If you want to export the results of the analysis as a CSV. Requires saving the blend file first.
output_filename = 'screw_pose_sample_test_v1' #careful that it can overwrite previous results

only_keyframe_viable = True #or False, if you want to keyframe all poses. False gives a performance hit.

print_each_pose_to_console = False #or False. Gives a minor performance hit if true.
#system console is accessible via Window>toggle system console

sample_density_rot = 2 #The default sample density will converge quickly, but only find one viable pose, because of the way this test is designed (see Bishop et al. 2023, and the manual)
sample_density_pos = 1 #The default sample density will converge quickly, but only find one viable pose, because of the way this test is designed (see Bishop et al. 2023, and the manual)
#Set sample densities higher (e.g., to 3) if you want to perform the full test. This will take several hours

d_phi = 60 / sample_density_rot #check intersections in steps of how many degrees? Don't make this too small or the script will take forever

x_range = [-180, 175]# degrees, x-rotation range. Second number has to be bigger than the first number, or the same
y_range = [-60, 80]# degrees, y-rotation range. Second number has to be bigger than the first number, or the same
z_range = [-60, 100]# degrees, z-rotation range. Second number has to be bigger than the first number, or the same

d_pos = 4/sample_density_pos # meters, check intersections in steps of how many meters?

xpos_range = [-8, 8]# meters, x-position range. Second number has to be bigger than the first number, or the same
ypos_range = [-6, 6]# meters, y-position range. Second number has to be bigger than the first number, or the same
zpos_range = [-6, 6]# meters, z-position range. Second number has to be bigger than the first number, or the same


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


#
# Node group for visualization of endpoint markers
#

if visualize_endpoint_markers:
    
    # Check if node group exists
    node_group_name = "CustomInstanceGroup"
    node_group = bpy.data.node_groups.get(node_group_name)

    if node_group is None:
        # --- Node group creation (your provided code) ---
        geo_group = bpy.data.node_groups.new(node_group_name, 'GeometryNodeTree')

        group_input = geo_group.nodes.new('NodeGroupInput')
        group_input.location = (-600, 0)
        group_output = geo_group.nodes.new('NodeGroupOutput')
        group_output.location = (600, 0)

        geo_group.interface.new_socket(name='Points', in_out='INPUT', socket_type='NodeSocketGeometry')
        geo_group.interface.new_socket(name='Radius', in_out='INPUT', socket_type='NodeSocketFloat')
        geo_group.interface.new_socket(name='Material', in_out='INPUT', socket_type='NodeSocketMaterial')
        geo_group.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')

        ico_sphere = geo_group.nodes.new('GeometryNodeMeshIcoSphere')
        ico_sphere.location = (-200, 0)

        instance_node = geo_group.nodes.new('GeometryNodeInstanceOnPoints')
        instance_node.location = (0, 0)

        set_material = geo_group.nodes.new('GeometryNodeSetMaterial')
        set_material.location = (300, 0)

        geo_group.links.new(group_input.outputs['Points'], instance_node.inputs['Points'])
        geo_group.links.new(ico_sphere.outputs['Mesh'], instance_node.inputs['Instance'])
        geo_group.links.new(group_input.outputs['Radius'], ico_sphere.inputs['Radius'])
        geo_group.links.new(instance_node.outputs['Instances'], set_material.inputs['Geometry'])
        geo_group.links.new(group_input.outputs['Material'], set_material.inputs['Material'])
        geo_group.links.new(set_material.outputs['Geometry'], group_output.inputs['Geometry'])

        node_group = geo_group


# ------------------------
# MAIN SCRIPT
# ------------------------

target_joint = bpy.data.objects.get(target_joint_name)
if not target_joint:
    raise ValueError(f"Target joint '{target_joint_name}' not found.")

target_joint_original_wm = target_joint.matrix_world.copy() #copy the transformation matrix
target_joint_original_gRb = target_joint_original_wm.to_3x3()
target_joint_original_pos = target_joint_original_wm.translation

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

    
    ### create materials for three different types of endpoint markers
   
    for name, col in zip(situation_names, colors):
        # Get existing material or create new
        mat = bpy.data.materials.get(name)
        if mat is None:
            mat = bpy.data.materials.new(name=name)
            
        if mat.node_tree is None: #blender <5 safe
            mat.use_nodes = True  # creates the node tree
        

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
target_joint.keyframe_insert(data_path="location", frame=0) 

# Store results
rom_data = [] 

# Store positions for deferred visualization
all_marker_positions = {
    "viable": [],
    "soft_tissue_non_viable": [],
    "skeletally_non_viable": []
}

#ensure that if start and end range are the same, we still test the start range
ranges = [x_range, y_range, z_range]
angles = [[np.deg2rad(a) for a in np.arange(r[0], r[1] + d_phi, d_phi)]  for r in ranges]

pos_ranges =  [xpos_range, ypos_range, zpos_range]
positions = [[a for a in np.arange(r[0], r[1] + d_pos, d_pos)]  for r in pos_ranges]

x_euler, y_euler, z_euler = angles #lists of euler angles

x_pos, y_pos, z_pos = positions #lists of positions


depsgraph = bpy.context.evaluated_depsgraph_get() #Blender's dependency graph



frame = 2
# clean nested loop



for xp in x_pos:
    for yp in y_pos:
        for zp in z_pos:
            for x in x_euler:
                for y in y_euler:
                    for z in z_euler:
                        
                        euler_angles = [x, y, z]
                        euler_string = f"{x:.3f}_{y:.3f}_{z:.3f}"
                        
                        #construct rotation matrix from euler angles
                        gRj, jRg = matrix_from_euler_XYZbody(euler_angles)
                        
                        
                        trial_position = Vector([xp, yp, zp])
                        position_string = f"{xp:.3f}_{yp:.3f}_{zp:.3f}"
                        
                        #construct a new temporary world matrix, by post-multiplying the base transformation matrix for a local space rotation
                        temp_wm = (target_joint_original_gRb @ gRj).to_4x4()
                        temp_wm.translation = target_joint_original_pos + target_joint_original_gRb @ trial_position #position offset from base position, in local frame of reference
                        
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
                                if print_each_pose_to_console:
                                    print(f"Pose at euler: {euler_angles} and position: {trial_position} is non viable due to soft tissue constraint")
                                
                                if visualize_endpoint_markers: #if we visualize endpoint markers, check what situation we'e dealing with (viable, soft non viable, skeleton non viable)
                                    situation = situation_names[1] #meaning soft tissue non viable
                            else: #if not constrained by soft tissue
                                if print_each_pose_to_console:
                                    print(f"Pose at euler: {euler_angles} and position: {trial_position} has no skeletal intersections")
                                
                                if visualize_endpoint_markers: #if we visualize endpoint markers, check what situation we'e dealing with (viable, soft non viable, skeleton non viable)
                                    situation = situation_names[0] #meaning viable
                                
                                                                
                        else: #if there are soft tissue intersections
                            if print_each_pose_to_console:
                                    print(f"Pose at euler: {euler_angles} and position: {trial_position} has skeletal intersections")    
                            
                            if visualize_endpoint_markers: #if we visualize endpoint markers, check what situation we'e dealing with (viable, soft non viable, skeleton non viable)
                                situation = situation_names[2] #meaning skeletally non viable
                        
                        ## get the endpoint marker position
                        endpointmarker_pos = target_landmark.matrix_world.translation.copy()
                        
                        # >>> STORE RESULTS for CSV here <<<
                        rom_data.append([
                            x,   # radians
                            y,
                            z,
                            xp, # meters
                            yp,
                            zp,
                            situation,
                            lig_length_value,
                            endpointmarker_pos.x,
                            endpointmarker_pos.y,
                            endpointmarker_pos.z                            
                        ])
                                
                        
                        if visualize_endpoint_markers:
                            all_marker_positions[situation].append(endpointmarker_pos)
                        
                        
                        if ((not only_keyframe_viable) or (situation == 'viable')): #skip non-viable keyframes if user wants to only keyframe viable   
                            #keyframe the pose
                            target_joint.keyframe_insert(data_path="rotation_euler", frame=frame)        
                            target_joint.keyframe_insert(data_path="location", frame=frame)    
                            frame += 1
                        
                        ### Restore original world matrix
                            
                        target_joint.matrix_world = target_joint_original_wm

if visualize_endpoint_markers:
    
    # --- Create fast marker meshes ---
    print("Creating endpoint marker meshes")
    for situation in situation_names:
        points = list(all_marker_positions[situation])  # positions only
        if not points:
            continue

        # Create a mesh with vertices at positions
        mesh_name = f"{situation}_endpoint_mesh"
        mesh = bpy.data.meshes.new(mesh_name)
        mesh.from_pydata(vertices=points, edges=[], faces=[])

        # Create object for the mesh
        obj = bpy.data.objects.new(f"{situation}_endpoint_markers", mesh)
        parent_coll.objects.link(obj)

        # Assign material
        mat = bpy.data.materials.get(situation)
        if mat:
            if len(obj.data.materials) == 0:
                obj.data.materials.append(mat)
            else:
                obj.data.materials[0] = mat

        # Add geometry nodes modifier
        mod = obj.modifiers.new(name="EndpointInstancer", type='NODES')
        mod.node_group = node_group

        # Set modifier inputs
        for item in mod.node_group.interface.items_tree:
            if item.item_type == 'SOCKET':
                if item.name == 'Radius':
                    mod[item.identifier] = marker_radius
                elif item.name == 'Material':
                    mod[item.identifier] = mat
                elif item.name == 'Points':
                    mod[item.identifier] = obj  # feed the vertex mesh itself as Points input

    print("Endpoint marker meshes created.")

            
            
end_time = time.time()
time_elapsed = end_time-start_time
time_per_pose = time_elapsed/(len(rom_data)) #

print(f"time elapsed: {time_elapsed} seconds")
print(f"time per pose: {time_per_pose} seconds")



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
        writer.writerow(["X (rad)", "Y (rad)", "Z (rad)",  "Xpos (m)", "Ypos (m)", "Zpos (m)", "Pose viability", "Ligament length (m)", "Markerpos_x (m)", "Markerpos_y (m)", "Markerpos_z (m)"])
        writer.writerows(rom_data)

    print(f"Exported ROM data to {csv_output_path}")
