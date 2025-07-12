import bpy
from mathutils.bvhtree import BVHTree


def check_bvh_intersection(obj_1_name, obj_2_name, depsgraph):

    #check the number of intersections between two objects using Blender's BVHTree module (bounding volume hierarchy tree)
    #inputs: obj_1_name (string, name of object 1 in the blender scene)
    # obj_2_name (string, name of object 2 in the blender scene)
    # depsgraph (Blender dependency graph). 
    # When scripting joint ROMs,
    # you should give an updated version of the depsgraph each time you change the position/orientation of an object in the scene
    # You can do that using depsgraph.update() (unless it is a fresh copy of the despgraph)

    #Output: pairs of polygons that intersect. 
    
    obj_1 = bpy.data.objects[obj_1_name]
    obj_2 = bpy.data.objects[obj_2_name]
    
    for obj in [obj_1, obj_2]:
        depsgraph.objects[obj.name].data.transform(obj.matrix_world)

    bvh1 = BVHTree.FromObject(obj_1, depsgraph)
    bvh2 = BVHTree.FromObject(obj_2, depsgraph)
    
    for obj in [obj_1, obj_2]:
       depsgraph.objects[obj.name].data.transform(obj.matrix_world.inverted())
    return bvh1.overlap(bvh2)