import bpy
import bmesh
from math import nan
from mathutils import Matrix

def create_landmark(landmark_name, landmark_radius, collection_name,
                    pos_in_global = [nan]*3,
                  is_global = True, 
                 parent_body = 'not_assigned', pos_in_parent_frame = [nan]*3):


    muskemo = bpy.context.scene.muskemo


    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the landmarks

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
   ## Create landmark 
    mesh = bpy.data.meshes.new(landmark_name)
    bm = bmesh.new()

    bmesh.ops.create_icosphere(
        bm,
        subdivisions=2,
        radius=landmark_radius,
        matrix=Matrix.Identity(4)
    )

    bm.to_mesh(mesh)
    bm.free()

    obj = bpy.data.objects.new(landmark_name, mesh)
    obj.location = pos_in_global

    
    coll.objects.link(obj)

    obj.name = landmark_name
    obj.data.name = landmark_name

    obj['MuSkeMo_type'] = 'LANDMARK'
    obj.id_properties_ui('MuSkeMo_type').update(
        description="The object type. Warning: don't modify this!"
    )

    bpy.ops.object.select_all(action='DESELECT')

    obj = bpy.data.objects[landmark_name]
    obj.rotation_mode = 'ZYX'    #change rotation sequence

    parent_body_obj = bpy.data.objects[parent_body]
    obj.parent = parent_body_obj

    #this undoes the transformation after parenting
    obj.matrix_parent_inverse = parent_body_obj.matrix_world.inverted()

    
    ##### Assign a material
    matname = 'marker_material'
    color = tuple(muskemo.marker_color)
    transparency = 0.5
        
            
    if matname not in bpy.data.materials:   #if the material doesn't exist, get it
        from .create_transparent_material_func import create_transparent_material
        create_transparent_material(matname, color, transparency)

    mat = bpy.data.materials[matname]
    obj.data.materials.append(mat)

    ### viewport display color

    obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
            
        