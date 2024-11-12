import bpy
from mathutils.bvhtree import BVHTree
import bmesh

#### Run this script directly in the Blender script editor.
#### The script checks the minimal distance between two designated objects
#### The distance (in meters) is printed to the console.
#### This can be useful to compute articular spacing from a series of XROMM frames, or when articulating a skeleton.
#### See ComputeClosestPointRealExample to see a version of the script that progresses through several frames,
#### computes the distance between two pairs of bone, and outputs everything as a CSV file.



# Define the objects
obj1 = bpy.data.objects['Obj_name1']  # Replace with your actual object names
obj2 = bpy.data.objects['Obj_name2']

def create_bvh_tree_from_object(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.transform(obj.matrix_world)
    bvh = BVHTree.FromBMesh(bm)
    bm.free()
    return bvh

def minimal_distance_between_objects(obj1, obj2):
    # Create BVHTrees for both objects
    bvhtree_obj1 = create_bvh_tree_from_object(obj1)
    bvhtree_obj2 = create_bvh_tree_from_object(obj2)
    
    # Initialize minimum distance and closest points
    min_distance = float('inf')
    closest_point_on_obj1 = None
    closest_point_on_obj2 = None

    # Check from obj1 to obj2
    for vert in obj1.data.vertices:
        co_obj1 = obj1.matrix_world @ vert.co
        location, normal, index, distance = bvhtree_obj2.find_nearest(co_obj1)
        
        if location and distance < min_distance:
            min_distance = distance
            closest_point_on_obj1 = co_obj1
            closest_point_on_obj2 = location

    # Check from obj2 to obj1
    for vert in obj2.data.vertices:
        co_obj2 = obj2.matrix_world @ vert.co
        location, normal, index, distance = bvhtree_obj1.find_nearest(co_obj2)
        
        if location and distance < min_distance:
            min_distance = distance
            closest_point_on_obj1 = location
            closest_point_on_obj2 = co_obj2

    return min_distance, closest_point_on_obj1, closest_point_on_obj2


# Compute the minimal distance
min_distance, point_on_obj1, point_on_obj2 = minimal_distance_between_objects(obj1, obj2)

print(f"Minimal Distance: {min_distance}")
print(f"Closest Point on {obj1.name}: {point_on_obj1}")
print(f"Closest Point on {obj2.name}: {point_on_obj2}")

