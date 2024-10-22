### desired features:

### 2)
### generate minimal convex hulls
### Generate symmetric expanded convex hulls, using:
### per-segment expansion factors. Prefab buttons for: average bird, reptile, or rote average between the two. Logarithmic bird, reptile, or geometric average between the two. Expansions from Coatham

### "average bird"
### "average reptile"
### "custom"



import bpy
import mathutils
import array
import bmesh


from bpy.types import (Panel,
                        Operator,
                        )

from math import nan

import numpy as np

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed
#from .. import inertial_properties #the rigid body parameters function

### Small helper functions

def copy_object(object, new_name): ## inputs: object (with a mesh) to be copied, string of the desired name
    object_copy = object.copy() #copy the object
    object_copy.name = new_name
    object_copy.data = object_copy.data.copy() #originally the data is linked to the original object. Here we give the copy its own instance of object data
    return object_copy
    

def convex_hull(object): ## inputs: object (with a mesh)
    bm = bmesh.new()
    bm.from_mesh(object.data) # create a bmesh using mesh data
    bmesh.ops.delete(bm, geom=bm.edges[:] + bm.faces[:], context='EDGES_FACES')
    ch = bmesh.ops.convex_hull(bm, input=bm.verts, use_existing_faces=False)
    bmesh.ops.delete(bm, geom=ch["geom_interior"], context='VERTS')
    bm.to_mesh(object.data)
    bm.free()


### the operators

class SelMeshesInertialProperties(Operator):
    bl_idname = "inprop.inertial_properties_selected_meshes"
    bl_label = "Compute mass, COM, & mass moment of inertia of the selected meshes, using the specified density. Only works on triangulated meshes. Parameters are stored as custom properties"
    bl_description = "Compute mass, COM, & mass moment of inertia of the selected meshes, using the specified density. Only works on triangulated meshes. Parameters are stored as custom properties"
   
    def execute(self, context):
        from .. import inertial_properties #import the function that computes inertial properties from a mesh
        
        density = bpy.context.scene.muskemo.segment_density #user assigned
        
        sel_obj = bpy.context.selected_objects.copy()  #should be the source objects (e.g. skin outlines) that we want to compute inertial properties for. We're copying this because the inertial properties func resets the selections
                
              
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No meshes selected. You must select at least 1 target mesh to compute inertial properties")
            return {'FINISHED'}

        total_mesh_errors = [] #instantiate a variable that tracks mesh errors
        for s_obj in sel_obj:  #for all the selected objects, error check loop
                
            if s_obj.type != 'MESH':  #check if the type is 'MESH'. If not, throw an error and abort
                
                self.report({'ERROR'}, "Source object with the name '" + s_obj.name + "' is not a 'MESH'. This button computes inertial properties for meshes. If you're defining rigid bodies, use the Body Panel. Operation cancelled.")
                return {'FINISHED'}

            ### check if all objects are triangulated. If not, throw an error and abort
                

            for p in s_obj.data.polygons:
                if len(p.vertices) != 3:
                    self.report({'ERROR'}, "Source object with the name '" + s_obj.name + "' has non-triangular mesh faces. You must manually triangulate this mesh before computing inertial properties. Operation cancelled.")
                    total_mesh_errors.append([1])
                    #return {'FINISHED'}
                    
            ### Check if the mesh is manifold (does it have holes, or self-intersections?)
            ### Adapted from Blender built-in 3D-Print Toolbox
            
            bm = bmesh.new()
            bm.from_mesh(s_obj.data)

            edges_non_manifold = array.array('i', (i for i, ele in enumerate(bm.edges) if not ele.is_manifold))
            edges_non_contig = array.array(
                'i',
                (i for i, ele in enumerate(bm.edges) if ele.is_manifold and (not ele.is_contiguous)),
            )

            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=0.00001)
            overlap = tree.overlap(tree)
            faces_error = {i for i_pair in overlap for i in i_pair}
            
            bm.free()

            errors_list = [edges_non_manifold, edges_non_contig, faces_error]

            if any(len(errors)!=0 for errors in errors_list):
                self.report({'ERROR'}, s_obj.name + " is not a solid (airtight) mesh, it has " + str(len(edges_non_manifold)) + " non-manifold edges, " + str(len(edges_non_contig)) 
                            + " non-contiguous edges, and " + str(len(faces_error)) + " self-intersections. Repair this mesh first, eg. with the 3D-Print Toolbox in Blender. Operation cancelled.")
                
                total_mesh_errors.append([1])
                #return {'FINISHED'} 
            
        if len(total_mesh_errors)>0:  #if we caught non-triangular meshes, or bad meshes, abort operation
            return {'FINISHED'}

        for s_obj in sel_obj:  #for all the selected objects, assign density and compute inertial properties

            ### assign density

            s_obj['density'] = density  #density in kg m^-3
            s_obj.id_properties_ui('density').update(description = 'density (in kg*m^-3)')    
            inertial_properties(s_obj)
                
                
        for obj in sel_obj:  #restore selection
            obj.select_set(True)

        
        del sel_obj
        return {'FINISHED'}    



class CollectionMeshInertialProperties(Operator):
    bl_idname = "inprop.inertial_properties_collection"
    bl_label = "Compute mass, COM, & mass moment of inertia of all the meshes in the collection, using the specified density. Only works on triangulated meshes. Parameters are stored as custom properties"
    bl_description = "Compute mass, COM, & mass moment of inertia of all the meshes in the collection, using the specified density. Only works on triangulated meshes. Parameters are stored as custom properties"
   
    def execute(self, context):
        from .. import inertial_properties #import the function that computes inertial properties from a mesh
        density = bpy.context.scene.muskemo.segment_density #user assigned
        colname = bpy.context.scene.muskemo.source_object_collection #user assigned 

        try: bpy.data.collections[colname]
        
        except:
            self.report({'ERROR'}, "Collection with the name '" + colname + "' does not exist.")
            return {'FINISHED'}

        col_obj = [obj for obj in bpy.data.collections[colname].objects]  #collection objects

            
              
        # throw an error if no objects are selected     
        if (len(col_obj) == 0):
            self.report({'ERROR'}, "Target collection is empty. Type the name of the collection that contains the target meshes")
            return {'FINISHED'}

        total_mesh_errors = []  #instantiate a variable that tracks mesh errors
        for s_obj in col_obj:  #for all the selected objects, error check loop
                
            if s_obj.type != 'MESH':  #check if the type is 'MESH'. If not, throw an error and abort
                
                self.report({'ERROR'}, "Source object with the name '" + s_obj.name + "' is not a 'MESH'. Remove it from collection '" + colname + "' and try again. If defining rigid bodies, use the Body Panel instead.")
                return {'FINISHED'}

            ### check if all objects are triangulated. If not, throw an error and abort
                

            for p in s_obj.data.polygons:
                if len(p.vertices) != 3:
                    self.report({'ERROR'}, "Source object with the name '" + s_obj.name + "' has non-triangular mesh faces. You must manually triangulate this mesh before computing inertial properties. Operation cancelled.")
                    total_mesh_errors.append([1])
                    
                    
            ### Check if the mesh is manifold (does it have holes, or self-intersections?)
            ### Adapted from Blender built-in 3D-Print Toolbox

            bm = bmesh.new()
            bm.from_mesh(s_obj.data)

            edges_non_manifold = array.array('i', (i for i, ele in enumerate(bm.edges) if not ele.is_manifold))
            edges_non_contig = array.array(
                'i',
                (i for i, ele in enumerate(bm.edges) if ele.is_manifold and (not ele.is_contiguous)),
            )

            tree = mathutils.bvhtree.BVHTree.FromBMesh(bm, epsilon=0.00001)
            overlap = tree.overlap(tree)
            faces_error = {i for i_pair in overlap for i in i_pair}
            
            bm.free()

            errors_list = [edges_non_manifold, edges_non_contig, faces_error]

            if any(len(errors)!=0 for errors in errors_list):
                self.report({'ERROR'}, s_obj.name + " is not a solid (airtight) mesh, it has " + str(len(edges_non_manifold)) + " non-manifold edges, " + str(len(edges_non_contig)) 
                            + " non-contiguous edges, and " + str(len(faces_error)) + " self-intersections. Repair this mesh first, eg. with the 3D-Print Toolbox in Blender. Operation cancelled.")
                total_mesh_errors.append([1])
                        
        if len(total_mesh_errors)>0:  #if we caught non-triangular meshes, or bad meshes, abort operation
            return {'FINISHED'}



        for s_obj in col_obj:  #for all the selected objects, assign density and compute inertial properties

            ### assign density

            s_obj['density'] = density  #density in kg m^-3
            s_obj.id_properties_ui('density').update(description = 'density (in kg*m^-3)')    
            inertial_properties(s_obj)
            


        return {'FINISHED'}

class CollectionConvexHull(Operator):
    bl_idname = "inprop.convex_hull_collection"
    bl_label = "Generate a minimal convex hull around each mesh in the skeletal mesh collection. Convex hulls get placed in a new collection."
    bl_description = "Generate a minimal convex hull around each mesh in the skeletal mesh collection. Convex hulls get placed in a new collection"
   
    def execute(self, context):
        muskemo = bpy.context.scene.muskemo


        skel_colname = muskemo.skeletal_mesh_collection #Collection that contains the skeletal meshes
        CH_colname = muskemo.convex_hull_collection #Collection that will contain the convex hulls

         #check if the collection name exists, and if not create it
        if CH_colname not in bpy.data.collections:
            bpy.data.collections.new(CH_colname)
            
        CH_coll = bpy.data.collections[CH_colname] #Collection which will recieve the scaled  hulls

        if CH_colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(CH_coll)     #add it to the scene
        
        #Make sure the collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[CH_colname]

        skel_coll = bpy.data.collections[skel_colname]
        
        meshes = [x for x in skel_coll.objects if 'MESH' in x.id_data.type] #get the objects in target coll, if the data type is a 'MESH'
        ##### Generate minimal convex hulls #####

        for mesh in meshes:   # loop through each mesh 
            
            CH_name = mesh.name + "_CH"

            if CH_name not in bpy.data.objects: #check that the convex hull doesn't already exist
                mesh_copy = copy_object(mesh, CH_name) #copy the mesh
                CH_coll.objects.link(mesh_copy)  #add the new mesh to the CH collection
                convex_hull(mesh_copy)
        
        return {'FINISHED'}





### The panels


## Main panel
class VIEW3D_PT_inertial_prop_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
   
    bl_idname = 'VIEW3D_PT_inertial_properties_panel' #have to define this if you use multiple panels
    bl_label = "Inertial properties panel"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):

        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        ## user segment density   
        layout.prop(muskemo, "segment_density")
        row = self.layout.row()
        row.label(text ="Compute inertial properties")

        ## compute for selected mesh
        row = self.layout.row()
        row.operator("inprop.inertial_properties_selected_meshes", text="Compute for selected meshes")
        
        #compute for entire collection
        row = self.layout.row()
        row.prop(muskemo, "source_object_collection")
        row.operator("inprop.inertial_properties_collection", text="Compute for all meshes in collection")

        return




## Generate Convex Hull panel
class VIEW3D_PT_convex_hull_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_convex_hull_subpanel'
    bl_parent_id = 'VIEW3D_PT_inertial_properties_panel'  #have to define this if you use multiple panels
    bl_label = "Generate minimal convex hulls"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        #self.layout.label(text="Also Small Class")
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        #### skeletal mesh collection
        row = self.layout.row()
        row.prop(muskemo, "skeletal_mesh_collection")

        #### convex hull collection
        row = self.layout.row()
        row.prop(muskemo, "convex_hull_collection")

        #### create convex hulls
        row = layout.row()
        row.operator("inprop.convex_hull_collection", text="Generate convex hulls")

        return          
              