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
                        PropertyGroup,
                        UIList,
                        )

from bpy.props import (EnumProperty,
                        IntProperty,
                        StringProperty,
                        FloatProperty)
from math import (nan, sqrt, log10, exp, log)

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
                

            if any(len(p.vertices) != 3 for p in s_obj.data.polygons):
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
                

           
            if any(len(p.vertices) != 3 for p in s_obj.data.polygons):
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
    bl_idname = "inprop.generate_convex_hull_collection"
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



# Operators for adding and removing segments
class AddSegmentOperator(Operator):
    bl_idname = "inprop.add_segment"
    bl_label = "Add segment to the template"
    bl_description = "Add segment to the template"

    mode: bpy.props.StringProperty()  # This will store which subpanel called the operator
    
    def execute(self, context):
        if self.mode == 'arithmetic':
            context.scene.muskemo.segment_parameter_list_arithmetic.add()

        elif self.mode == 'logarithmic':
            context.scene.muskemo.segment_parameter_list_logarithmic.add()

        elif self.mode == 'logarithmic_wholebodymass':
            context.scene.muskemo.whole_body_mass_logarithmic_parameters.add()  
        
        elif self.mode == 'logarithmic_segmentinprops':
            context.scene.muskemo.segment_inertial_logarithmic_parameters.add()


        return {'FINISHED'}

class RemoveSegmentOperator(Operator):
    bl_idname = "inprop.remove_segment"
    bl_label = "Remove Segment from the template"
    bl_description = "Remove Segment from the template"
    
    index: IntProperty()
    mode: bpy.props.StringProperty()  # This will store which subpanel called the operator

    def execute(self, context):
        if self.mode == 'arithmetic':
            context.scene.muskemo.segment_parameter_list_arithmetic.remove(self.index)

        elif self.mode == 'logarithmic':
            context.scene.muskemo.segment_parameter_list_logarithmic.remove(self.index)

        elif self.mode == 'logarithmic_wholebodymass':
            context.scene.muskemo.whole_body_mass_logarithmic_parameters.remove(self.index)     

        elif self.mode == 'logarithmic_segmentinprops':
            context.scene.muskemo.segment_inertial_logarithmic_parameters.remove(self.index)

        return {'FINISHED'}



# Expand Convex hulls operator

class ExpandConvexHullCollectionOperator (Operator):
    bl_idname = "inprop.expand_convex_hull_collection"
    bl_label = "Expand all the convex hulls in a designated collection. Expanded convex hulls get placed in a new collection"
    bl_description = "Expand all the convex hulls in a designated collection. Expanded convex hulls get placed in a new collection"
    
    # Custom property to store whether the operator should use arithmetic or logarithmic behavior
    arithmetic_or_logarithmic: StringProperty()

    def execute(self, context):
        from .. import inertial_properties #import the function that computes inertial properties from a mesh

        arithmetic_or_logarithmic = self.arithmetic_or_logarithmic

        muskemo = bpy.context.scene.muskemo

        CH_colname = muskemo.convex_hull_collection #Collection that will contain the convex hulls
        eCH_colname = muskemo.expanded_hull_collection #Collection that will contain the expanded convex hulls

        apply_bias_correction = muskemo.apply_bias_correction #bool for if we should correct for retransformation bias using 10**(log(10)/2 * MSE)

        if CH_colname not in bpy.data.collections:
            self.report({'ERROR'}, "A collection with the name '" + CH_colname + "' does not exist. Which collection contains the convex hulls? Type that into the 'Convex hull collection' field")
            return {'FINISHED'}
        
         #check if the collection name exists, and if not create it
        if eCH_colname not in bpy.data.collections:
            bpy.data.collections.new(eCH_colname)
            
        eCH_coll = bpy.data.collections[eCH_colname] #Collection which will recieve the scaled  hulls

        if eCH_colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(eCH_coll)     #add it to the scene
        
        #Make sure the collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[eCH_colname]

        ## get names of the convex hull objects
        CH_name = [x.name for x in bpy.data.collections[CH_colname].objects if 'MESH' in x.id_data.type] #get the name for each object in collection 'Convex Hulls', if the data type is a 'MESH'

        if arithmetic_or_logarithmic == 'arithmetic':

            arithmetic_parameters = []  #list of dicts
            for item in muskemo.segment_parameter_list_arithmetic:
                arithmetic_parameters.append({
                    "body_segment": item.body_segment,
                    "scale_factor": item.scale_factor,
                })
            
            segment_types = [x['body_segment'] for x in arithmetic_parameters]
            expansions = [x['scale_factor'] for x in arithmetic_parameters]

        elif arithmetic_or_logarithmic == 'logarithmic':
            
            logarithmic_parameters = []  #list of dicts
            for item in muskemo.segment_parameter_list_logarithmic:
                logarithmic_parameters.append({
                    "body_segment": item.body_segment,
                    "log_intercept": item.log_intercept,
                    "log_slope": item.log_slope,
                    "log_MSE": item.log_MSE,
                })

            segment_types = [x['body_segment'] for x in logarithmic_parameters]    
            log_intercepts = [x['log_intercept'] for x in logarithmic_parameters] 
            log_slopes = [x['log_slope'] for x in logarithmic_parameters] 
            log_MSEs = [x['log_MSE'] for x in logarithmic_parameters] #mean squared errors


        #inform the user about the behaviour    
        if len(segment_types)==1 and segment_types[0]=='whole_body': #if we do the same expansion for all segments
            if arithmetic_or_logarithmic == 'arithmetic':
                self.report({'WARNING'}, "Expanding the whole body with a constant factor of " +  f"{expansions[0]:.3f}" + ", on a per segment basis.")
                    
            elif arithmetic_or_logarithmic == 'logarithmic':
                self.report({'WARNING'}, "Logarithmic whole body expansion currently not yet supported. Eventually, this mode will sum all the volumes together, determine the whole-body expansion factor, and then expand on a per-segment basis.")          

        for h in range(len(CH_name)):   # loop through each mesh in 'Convex Hulls' collection     
            
            if len(segment_types)==1 and segment_types[0]=='whole_body': #if we do the same expansion for all segments
                segment_type = 'whole_body'  

            else: #if we try to match segment types to the object names
                if any(s in CH_name[h] for s in segment_types): #check if any of the segment types are in the object's name
                    segment_type = [s for s in segment_types if s in CH_name[h]][0] #check which entry in labels matches the current segment name. Make sure all objects in Collection "Skeleton" contain an entry from labels
                else: #if not, this object doesn't have a corresponding segment type, so we don't know the scale factor. Throw a warning and skip.
                    self.report({'WARNING'}, "Object with the name '" + CH_name[h] + "' does not contain any of the segment types in its name. Skipping this object during expansion.")
                    continue

            hull = bpy.data.objects[CH_name[h]]
            bpy.context.view_layer.objects.active = hull
            hull.select_set(True)
            bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
            hull.select_set(False)


            eCH_name = CH_name[h] + "_expanded" #expanded convex hull object name

            if eCH_name in bpy.data.objects: #ensure a unique name, just in case the name is already in use.
                base_name = eCH_name
                counter = 1
                new_name = f"{base_name}_{counter}"
                
                while new_name in bpy.data.objects:
                    counter += 1
                    new_name = f"{base_name}_{counter}"

                eCH_name = new_name  # Update eCH_name to the unique name
            
        
            hull_copy = copy_object(hull, eCH_name) #copy the mesh
            eCH_coll.objects.link(hull_copy)  #add the new mesh to the eCH collection

            
            ## ADD a check for if it already exists
        
            obj = bpy.data.objects[eCH_name]   #

            obj['density'] = 1000   #density in kg*m^-3
            obj.id_properties_ui('density').update(description = 'density (in kg*m^-3)')

            bpy.ops.object.select_all(action='DESELECT') #Deselect all, then select desired object  
            obj.select_set(True)               # select the hull
            bpy.ops.object.transform_apply()
            mass, CoM_book, mass_I_com, vol_before, volumetric_I_com   = inertial_properties(obj)            
            vol_mirrored = vol_before #vol mirrored gets overwritten if it's an axial segment
            #### symmetrization ####
            if any([s in obj.name for s in ['head', 'neck', 'torso', 'tail']]):     #If head, neck, torso or tail are in the name
                bpy.ops.object.select_all(action='DESELECT') #Deselect all, then select desired object  
                obj.select_set(True)               # select the hull
                bpy.ops.object.transform_apply()
                
                obj.modifiers.new('mirror','MIRROR')     #add a mirror modifier to generate a symmetric hull
                obj.modifiers['mirror'].use_axis[0] = False
                obj.modifiers['mirror'].use_axis[2] = True # set to 1 if z up
                obj.modifiers['mirror'].merge_threshold = 0.001
                bpy.context.view_layer.objects.active = None
                bpy.context.view_layer.objects.active = obj    
                bpy.ops.object.modifier_apply(modifier="mirror")    #apply the modifier
            
                convex_hull(obj) #convex hulls the mirrored object
                mass, CoM_book, mass_I_com, vol_mirrored, volumetric_I_com   = inertial_properties(obj) #this recomputes the volume of the mirrored duplicated object, which is probably larger
            
            
            bpy.ops.object.select_all(action='DESELECT') #Deselect all, then select desired object 
            obj.select_set(True)
            bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')    

            ind = segment_types.index(segment_type) #index number (starting at zero) in labels of the current segment

            if arithmetic_or_logarithmic == 'arithmetic':

                expansion_factor = expansions[ind] #how much are you scaling the volume
                
            elif arithmetic_or_logarithmic == 'logarithmic':
                
                intercept = log_intercepts[ind]
                slope = log_slopes[ind]
                MSE = log_MSEs[ind]

                if not apply_bias_correction: #if apply_bias_correction is False, we set MSE to zero
                    MSE = 0

                uncorrected_vol = 10**intercept *vol_before**slope #volume without MSE correction
                MSE_corr_vol = uncorrected_vol*10**(log(10)/2 * MSE) #MSE corrected volume
                expansion_factor_allo = MSE_corr_vol / vol_before
                expansion_factor = expansion_factor_allo

                self.report({'WARNING'}, "Logarithmic per-segment expansion is currently experimental, pending clarification from the lead authors. It is recommended you double-check the acquired results")
                #return {'FINISHED'}
                

                
            correction_factor = vol_mirrored/vol_before #correct for symmetrization. If the segment isn't symmetrized, this equals 1
            #scale factor
            sf = sqrt(expansion_factor/correction_factor) #square root to scale in two directions, correcting for the increased volume due to mirroring
            
            
            #### directional scaling ####
            if any([s in obj.name for s in ['head', 'neck', 'torso', 'tail', 'forearm', 'hand', 'toe']]):        
                obj.scale = (1, sf, sf)
                #bpy.ops.transform.resize(value=(1,sf,sf))   # scale along y and z
                
            else:
                obj.scale = (sf, 1, sf)
                #bpy.ops.transform.resize(value=(sf,1,sf))   # scale along x and z
                
            bpy.ops.object.transform_apply()        
            mass, CoM_book, mass_I_com, vol_after, volumetric_I_com   = inertial_properties(obj) #this recomputes the volume of the mirrored duplicated object, which is probably larger

        return {'FINISHED'}        



class WholeBodyMassFromConvexHullsOperator (Operator):
    bl_idname = "inprop.compute_whole_body_mass_ch"
    bl_label = "Use published equations to compute whole body mass, using convex hulls designated in a specific collection"
    bl_description = "Use published equations to compute whole body mass, using convex hulls designated in a specific collection"


    total_body_mass: bpy.props.FloatProperty(precision=6)

    def invoke(self, context, event): #this
        self.execute(context)  # Run execute() before showing the dialog
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        estimation_type = context.scene.muskemo.mass_from_CH_template_logarithmic
        layout.label(text='Computed total body mass from convex hulls')
        row = layout.row()
        row.label(text = 'Estimation type :"' + estimation_type + '"')
        layout.prop(self, "total_body_mass", text="Total body mass (kg)")  # Copyable float property

    def execute(self, context):
        from .. import inertial_properties #import the function that computes inertial properties from a mesh

        #arithmetic_or_logarithmic = self.arithmetic_or_logarithmic

        muskemo = bpy.context.scene.muskemo

        CH_colname = muskemo.convex_hull_collection #Collection that will contain the convex hulls
        #eCH_colname = muskemo.expanded_hull_collection #Collection that will contain the expanded convex hulls

        apply_bias_correction = muskemo.apply_bias_correction #bool for if we should correct for retransformation bias using 10**(log(10)/2 * MSE)


        if CH_colname not in bpy.data.collections:
            self.report({'ERROR'}, "A collection with the name '" + CH_colname + "' does not exist. Which collection contains the convex hulls? Type that into the 'Convex hull collection' field")
            return {'FINISHED'}
        
        ## get the convex hull objects
        convex_hulls = [x for x in bpy.data.collections[CH_colname].objects if 'MESH' in x.id_data.type] #get each object in collection 'Convex Hulls', if the data type is a 'MESH'
        volumes = []
        # get the volumes
        for ch in convex_hulls:
            bm = bmesh.new()
            bm.from_mesh(ch.data) # create a bmesh using mesh data
            volumes.append(bm.calc_volume())
            bm.free()

        vol = sum(volumes) #total volume in m3

        logarithmic_parameters = muskemo.whole_body_mass_logarithmic_parameters
        
        if len(logarithmic_parameters)!= 1:
            self.report({'ERROR'}, "This button only works with a single allometric equation for the whole body. You can only define one segment, and it has to be named 'whole_body'.")
            return {'FINISHED'}
        
        if logarithmic_parameters[0].body_segment != 'whole_body':
            self.report({'ERROR'}, "This button only works with a single allometric equation for the whole body. You can only define one segment, and it has to be named 'whole_body'.")
            return {'FINISHED'}

        logarithmic_parameters = logarithmic_parameters[0]

        log_intercept = logarithmic_parameters['log_intercept']
        log_slope = logarithmic_parameters['log_slope']
        log_MSE = logarithmic_parameters['log_MSE']

        if not apply_bias_correction: #if apply_bias_correction is False, we set MSE to zero
            log_MSE = 0
        
        total_body_mass = 10**log_intercept * vol**log_slope * 10**(log(10)/2 * log_MSE)

        if muskemo.mass_from_CH_template_logarithmic == 'Wright 2024 Logarithmic Tetrapods': 
            density = muskemo.segment_density
            total_body_mass = total_body_mass * density **log_slope #Wright's equation assumes volume is multiplied by density before placing it in the power function.

        self.total_body_mass = total_body_mass
        
        ### insert code to compute inertial properties from convex hulls.
        ### mass = volume ratio * total mass.
        ### density = mass/volume
        ### assign density to obj
        ### run inertial_properties_func
        

        return {'FINISHED'}


class PerSegmentInpropsFromConvexHullsOperator (Operator):
    bl_idname = "inprop.compute_segment_inprops_ch"
    bl_label = "Use published equations to compute inertial properties directly from segment convex hulls, on a per-segment basis"
    bl_description = "Use published equations to compute inertial properties directly from segment convex hulls, on a per-segment basis"

    def execute(self, context):

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
        row = self.layout.row()
        row.operator("inprop.inertial_properties_collection", text="Compute for all meshes in collection")

        row = self.layout.row()
        row = self.layout.row()
        row = self.layout.row()
        row.operator("muskemo.reset_model_default_pose", text = 'Reset to default pose')

        return




## Generate Convex Hull panel
class VIEW3D_PT_convex_hull_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_convex_hull_subpanel'
    bl_parent_id = 'VIEW3D_PT_inertial_properties_panel'  #have to define this if you use multiple panels
    bl_label = "Generate minimal convex hulls"  # found at the top of the Panel
    bl_options = {'DEFAULT_CLOSED'} 
    
    def draw(self, context):
        
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        #### skeletal mesh collection
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = "Skeletal Mesh Collection")
        split.prop(muskemo, "skeletal_mesh_collection", text = "")

        #### convex hull collection
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Convex Hull Collection')
        split.prop(muskemo, "convex_hull_collection", text = "")

        #### create convex hulls
        row = layout.row()
        row.operator("inprop.generate_convex_hull_collection", text="Generate convex hulls")

        return          


# Panel for Arithmetic scaling
class VIEW3D_PT_expand_convex_hulls_arith_subpanel(VIEW3D_PT_MuSkeMo, Panel):
    bl_parent_id = 'VIEW3D_PT_inertial_properties_panel'  #have to define this if you use multiple panels
    bl_idname = "VIEW3D_PT_expand_convex_hulls_arith_subpanel"
    bl_label = "Expand convex hulls - arithmetic"
    bl_options = {'DEFAULT_CLOSED'} 

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        #### convex hull collection
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Convex Hull Collection')
        split.prop(muskemo, "convex_hull_collection", text = "")

        ### dynamically sized panel
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Expansion Template:')
        split.prop(muskemo, "expansion_template_arithmetic", text = "")
        
        ### Column labels
        row = layout.row()
        row = layout.row()
        row = layout.row()
        split = row.split(factor = 1/15)
        split.label(text = "No")
        split = split.split(factor = 1/4)
        split.label(text = "Segment name")
        split = split.split(factor = 5/6)
        split.label(text = "Scale factor")

        for i, item in enumerate(muskemo.segment_parameter_list_arithmetic):
            row = layout.row()
            split = row.split(factor = 1/15)
            split.label(text = f"{i+1}")
            split = split.split(factor = 1/4)
            split.prop(item, "body_segment", text="")
            split = split.split(factor = 5/6)
            split.prop(item, "scale_factor", text="Scale Factor")
            oper = split.operator("inprop.remove_segment", text="", icon='REMOVE')
            oper.index = i
            oper.mode = 'arithmetic'
        layout.operator("inprop.add_segment", text="Add Segment", icon='ADD').mode = 'arithmetic'
        ### dynamically sized panel

        #### expanded hull collection
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Expanded Hull Collection')
        split.prop(muskemo, "expanded_hull_collection", text = "")    
        
        #### expand hulls operator
        row = self.layout.row()
        op = row.operator("inprop.expand_convex_hull_collection", text="Expand convex hulls")
        op.arithmetic_or_logarithmic = 'arithmetic' #set the custom property


# Panel for Logarithmic scaling
class VIEW3D_PT_expand_convex_hulls_logar_subpanel(VIEW3D_PT_MuSkeMo, Panel):
    bl_parent_id = 'VIEW3D_PT_inertial_properties_panel'  #have to define this if you use multiple panels
    bl_idname = "VIEW3D_PT_expand_convex_hulls_logar_subpanel"
    bl_label = "Expand convex hulls - logarithmic"
    bl_options = {'DEFAULT_CLOSED'} 

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        #### convex hull collection
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Convex Hull Collection')
        split.prop(muskemo, "convex_hull_collection", text = "")

        ### dynamically sized panel
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Expansion Template:')
        split.prop(muskemo, "expansion_template_logarithmic", text = "")


        ### Column labels
        row = layout.row()
        row = layout.row()
        row = layout.row()
        split = row.split(factor = 1/15)
        split.label(text = "No")
        split = split.split(factor = 1/4)
        split.label(text = "Segment name")
        split = split.split(factor = 3/10)
        split.label(text = "Intercept")
        split = split.split(factor = 3/7)
        split.label(text = "Slope")
        split = split.split(factor = 3/4)
        split.label(text = "MSE")



        for i, item in enumerate(muskemo.segment_parameter_list_logarithmic):
            row = layout.row()
            split = row.split(factor = 1/15)
            split.label(text = f"{i+1}")
            split = split.split(factor = 1/4)
            split.prop(item, "body_segment", text="")
            split = split.split(factor = 3/10)
            split.prop(item, "log_intercept", text="")
            split = split.split(factor = 3/7)
            split.prop(item, "log_slope", text="")
            split = split.split(factor = 3/4)
            split.prop(item, "log_MSE", text="")
            oper = split.operator("inprop.remove_segment", text="", icon='REMOVE')
            oper.index = i
            oper.mode = 'logarithmic'
        layout.operator("inprop.add_segment", text="Add Segment", icon='ADD').mode = 'logarithmic'
        ### dynamically sized panel

        #### expanded hull collection
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Expanded Hull Collection')
        split.prop(muskemo, "expanded_hull_collection", text = "")    
           
        
        #### expand hulls operator
        row = self.layout.row()
        op = row.operator("inprop.expand_convex_hull_collection", text="Expand convex hulls")
        op.arithmetic_or_logarithmic = 'logarithmic' #set the custom property

        row = self.layout.row()

        row.prop(muskemo, "apply_bias_correction")

# Panel for whole body mass estimation from convex hulls
class VIEW3D_PT_whole_body_mass_from_convex_hull_subpanel(VIEW3D_PT_MuSkeMo, Panel):
    bl_parent_id = 'VIEW3D_PT_inertial_properties_panel'  #have to define this if you use multiple panels
    bl_idname = "VIEW3D_PT_body_mass_from_convex_hull_subpanel"
    bl_label = "Whole body mass from convex hulls - logarithmic"
    bl_options = {'DEFAULT_CLOSED'} 

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        #### convex hull collection
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Convex Hull Collection')
        split.prop(muskemo, "convex_hull_collection", text = "")

        ### dynamically sized panel
        row = self.layout.row()
        split = row.split(factor = 1/2)
        split.label(text = 'Mass estimation template:')
        split.prop(muskemo, "mass_from_CH_template_logarithmic", text = "")

        
        
            

        ### Column labels
        row = layout.row()
        row = layout.row()
        row = layout.row()
        split = row.split(factor = 1/15)
        split.label(text = "No")
        split = split.split(factor = 1/4)
        split.label(text = "Segment name")
        split = split.split(factor = 3/10)
        split.label(text = "Intercept")
        split = split.split(factor = 3/7)
        split.label(text = "Slope")
        split = split.split(factor = 3/4)
        split.label(text = "MSE")



        for i, item in enumerate(muskemo.whole_body_mass_logarithmic_parameters):
            row = layout.row()
            split = row.split(factor = 1/15)
            split.label(text = f"{i+1}")
            split = split.split(factor = 1/4)
            split.prop(item, "body_segment", text="")
            split = split.split(factor = 3/10)
            split.prop(item, "log_intercept", text="")
            split = split.split(factor = 3/7)
            split.prop(item, "log_slope", text="")
            split = split.split(factor = 3/4)
            split.prop(item, "log_MSE", text="")
            oper = split.operator("inprop.remove_segment", text="", icon='REMOVE')
            oper.index = i
            oper.mode = 'logarithmic_wholebodymass'
        layout.operator("inprop.add_segment", text="Add Segment", icon='ADD').mode = 'logarithmic_wholebodymass'
        ### dynamically sized panel
        if muskemo.mass_from_CH_template_logarithmic == 'Wright 2024 Logarithmic Tetrapods':
            row = layout.row()
            row = layout.row()
            row = layout.row()
            row.prop(muskemo, "segment_density")
        
        
               
        
        #### Compute whole body mass operator
        row = self.layout.row()
        op = row.operator("inprop.compute_whole_body_mass_ch", text="Compute whole body mass")
        
        row = self.layout.row()
        row.prop(muskemo, "apply_bias_correction")
        #op.arithmetic_or_logarithmic = 'logarithmic' #set the custom property

class MUSKEMO_UL_InPropSegmentList(UIList):
    """Per-segment inertial properties inside a scrollable box"""
    bl_idname = "MUSKEMO_UL_InPropSegmentList"

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        """Draws each row in the UI list"""
        split = layout.split(factor=1/15)
        split.label(text=f"{index + 1}")  # Index
        split = split.split(factor=1/4)
        split.prop(item, "body_segment", text="")  # Body segment
        split = split.split(factor=3/10)
        split.prop(item, "log_intercept", text="")  # Intercept
        split = split.split(factor=3/7)
        split.prop(item, "log_slope", text="")  # Slope
        split = split.split(factor=3/4)
        split.prop(item, "log_MSE", text="")  # MSE
        
        # Remove button
        oper = split.operator("inprop.remove_segment", text="", icon='REMOVE')
        oper.index = index
        oper.mode = 'logarithmic_segmentinprops'


class VIEW3D_PT_segment_inprops_from_convex_hull_subpanel(VIEW3D_PT_MuSkeMo, Panel):
    bl_parent_id = 'VIEW3D_PT_inertial_properties_panel'
    bl_idname = "VIEW3D_PT_segment_inprops_from_convex_hull_subpanel"
    bl_label = "Segment inertial properties from convex hull - logarithmic"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo

        #### Convex hull collection
        row = layout.row()
        split = row.split(factor=1/2)
        split.label(text='Convex Hull Collection')
        split.prop(muskemo, "convex_hull_collection", text="")

        ### Segment properties template
        row = layout.row()
        split = row.split(factor=1/2)
        split.label(text="Segment inertial properties estimation template:")
        split.prop(muskemo, "segment_inprops_from_CH_template_logarithmic", text="")

        ### **Scrollable Box**
        box = layout.box()
        
        # Header row
        row = box.row()
        split = row.split(factor=1/15)
        split.label(text="No")
        split = split.split(factor=1/4)
        split.label(text="Segment name")
        split = split.split(factor=3/10)
        split.label(text="Intercept")
        split = split.split(factor=3/7)
        split.label(text="Slope")
        split = split.split(factor=3/4)
        split.label(text="MSE")

        # **Scrollable list using template_list**
        row = box.row()
        row.template_list("MUSKEMO_UL_InPropSegmentList", "", muskemo, "segment_inertial_logarithmic_parameters", muskemo, "segment_index")

        # Add segment button
        box.operator("inprop.add_segment", text="Add Segment", icon='ADD').mode = 'logarithmic_segmentinprops'

        # Additional property
        if muskemo.mass_from_CH_template_logarithmic == "Wright 2024 Logarithmic Tetrapods":
            row = layout.row()
            row.prop(muskemo, "segment_density")

        #### Compute whole body mass operator
        row = layout.row()
        #row.operator("inprop.compute_segment_inprops_ch", text="Compute segment inertial properties")
