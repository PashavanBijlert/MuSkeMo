import bpy
import mathutils

#### User inputs

target_obj = bpy.data.objects['TargetMuscle']  # Ensure a 3D volumetric mesh with the name 'TargetMuscle' exists. It should be a watertight, good mesh. 
origin_obj = bpy.data.objects['origin']  # Ensure an object named 'origin' exists at the desired origin location
insertion_obj = bpy.data.objects['insertion']  # Ensure an object named 'insertion' exists at the desired insertion location

## This script is currently still experimental, if you run into issues, please contact pasha.vanbijlert at naturalis.nl


#This script slices the target mesh up into n sections (defined by sampling_resolution). These slices are created by computing boolean intersections
#with a cuboid, and connecting the volumetric centroids of the resultant shapes. 
#The first and last cuboid are aligned with the origin and insertion.
#You can set the desired resolution using sampling_resolution, which is used to compute the height of the cuboid.
#If resolution is low, you get fewer points, but sample the whole muscle.
#If resolution is very high, the resultant curve is smoother, but it is possible you ignore parts of the mesh 
#that are above the "origin" or below the "insertion", depending on your placement of those markers and the shape of the mesh.
#You should tune cube_width_depth to ensure that the entire muscle is enveloped by the resultant cuboids.
#By default, the script also outputs the intersecting cuboids, and the slices. This is so that you can double check
#that the mesh was sliced according to your preference. It is possible to turn this behavior off by setting the output switches to False.



# Parameters
sampling_resolution = 4 # Number of volumetric sub-sections
cube_width_depth = 5.0  # Width and depth of the cube

# Output switches
output_intersecting_cubes = True
output_slices = True

# Function to compute the center of volume
def compute_center_of_volume(mesh_obj):
    # Ensure the object is selected and active
    bpy.context.view_layer.objects.active = mesh_obj
    bpy.ops.object.select_all(action='DESELECT')
    mesh_obj.select_set(True)

    # Set the origin to the center of volume (center of mass)
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')

    # Return the object's new origin location (which is the center of volume)
    return mesh_obj.location.copy()

# Function to create a cube with the correct height aligned to direction
def create_aligned_cube(location, rotation, height):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    cube_obj = bpy.context.object  # Get the newly created cube object
    
    # Set the cube's scale to match the width, depth, and the calculated height
    cube_obj.scale = (cube_width_depth , cube_width_depth, height )
    
    # Align the cube with the given rotation
    cube_obj.rotation_euler = rotation
    
    return cube_obj

# Function to create a boolean slice from the original mesh using a cube
def create_slice_from_mesh(original_mesh, cube_obj):
    # Create a duplicate of the original mesh object
    temp_slice_obj = original_mesh.copy()
    temp_slice_obj.data = original_mesh.data.copy()  # Ensure the mesh data is copied
    bpy.context.collection.objects.link(temp_slice_obj)

    # Add a boolean modifier to the temporary slice
    boolean_modifier = temp_slice_obj.modifiers.new(name="Boolean", type='BOOLEAN')
    boolean_modifier.operation = 'INTERSECT'
    boolean_modifier.object = cube_obj

    # Apply the modifier to create the slice
    bpy.context.view_layer.objects.active = temp_slice_obj
    bpy.ops.object.modifier_apply(modifier=boolean_modifier.name)

    # Clean up the cube object
    if not output_intersecting_cubes:
        bpy.data.objects.remove(cube_obj)

    return temp_slice_obj

# Main function to create the fitted curve
def create_fitted_curve(mesh_obj, resolution, origin_obj, insertion_obj):
    origin_loc = origin_obj.location
    insertion_loc = insertion_obj.location
    
    curve_points = [origin_loc]  # Start with the origin point

    # Calculate the total distance and the height of each slice (cube)
    total_distance = (insertion_loc - origin_loc).length
    cube_height = total_distance / (resolution - 1)  # Height of each cube
    
    # Calculate the direction from origin to insertion
    direction = (insertion_loc - origin_loc).normalized()
    # Create a euler rotation aligned with the direction from origin to insertion
    rotation = direction.to_track_quat('Z', 'Y').to_euler() 
        
        
    # Sample sub-sections between origin and insertion
    for i in range(resolution):
        # Calculate the cube position for each step
        cube_center = origin_loc + direction * cube_height * i

         # Align cube's height with the direction
        cube_obj = create_aligned_cube(cube_center, rotation, cube_height)

        # Create a slice from the original mesh using the cube
        temp_slice = create_slice_from_mesh(mesh_obj, cube_obj)

        if temp_slice:
            # Compute center of volume using Blender's built-in function
            center_of_volume = compute_center_of_volume(temp_slice)

            # Append center of volume to curve points
            curve_points.append(center_of_volume)

            # Clean up the temporary slice object after computing its center
            if not output_slices:
                bpy.data.objects.remove(temp_slice)

    curve_points.append(insertion_loc)  # Add the insertion point
    
    # Create a curve from the computed centroids
    curve_data = bpy.data.curves.new(name=mesh_obj.name + 'CurveFit', type='CURVE')
    curve_data.dimensions = '3D'
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(curve_points) - 1)
    
    for i, point in enumerate(curve_points):
        spline.points[i].co = (point.x, point.y, point.z, 1)  # Blender uses 4D coordinates (x, y, z, w)
    
    curve_obj = bpy.data.objects.new(mesh_obj.name + 'CurveFit', curve_data)
    bpy.context.collection.objects.link(curve_obj)


### call the fitting function
create_fitted_curve(target_obj, sampling_resolution, origin_obj, insertion_obj)
