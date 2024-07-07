# give Python access to Blender's functionality
import bpy

import mathutils

from bpy.types import (Panel,
                        Operator,
                        )

from math import nan

import numpy as np
import array
import bmesh

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed

    
class CreateNewBodyOperator(Operator):
    bl_idname = "body.create_new_body"
    bl_label = "creates a new body at the origin"
    bl_description = "creates a new body at the origin"
    
    def execute(self,context):
        
        rad = bpy.context.scene.muskemo.axes_size #axis length, in meters
        name = bpy.context.scene.muskemo.bodyname  #name of the object


        if not name: #if the user didn't fill out a name
            self.report({'ERROR'}, "Fill in a body name first. Operation aborted")
            return {'FINISHED'}

        
        colname = bpy.context.scene.muskemo.body_collection #name for the collection that will contain the hulls
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the "bodies" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]
        
        
        try: bpy.data.objects[name]
        
        except:
                
            bpy.ops.object.empty_add(type='ARROWS', radius=rad, align='WORLD',location = (0,0,0))
            bpy.context.object.name = name #set the name
            #bpy.context.object.data.name = name #set the name of the object data
            bpy.context.object.rotation_mode = 'ZYX'    #change rotation sequence
            
            ##### add custom properties to the bodies (see blender documentation for properties)
            bpy.context.object['mass'] = nan       #add mass property
            bpy.context.object.id_properties_ui('mass').update(description = 'mass of the body in kg')
            
            bpy.context.object['inertia_COM'] = [nan, nan, nan, nan, nan, nan]    #add inertia property
            bpy.context.object.id_properties_ui('inertia_COM').update(description = 'Ixx Iyy Izz Ixy Ixz Iyz (in kg*m^2) about body COM in global frame')
                    
            bpy.context.object['COM'] = [nan, nan, nan]
            bpy.context.object.id_properties_ui('COM').update(description = 'COM location (in global frame)')
        
            bpy.context.object['Geometry'] = 'no geometry'    #add list of mesh files
            bpy.context.object.id_properties_ui('Geometry').update(description = 'Attached geometry for visualization (eg. bone meshes)')  

            bpy.context.object['MuSkeMo_type'] = 'BODY'    #to inform the user what type is created
            bpy.context.object.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")

            bpy.context.object['local_frame'] = 'not yet assigned'    #pre-allocate the Local_frame property
            bpy.context.object.id_properties_ui('local_frame').update(description = "Name of the local reference frame. You can create and assign these in the anatomical local reference frame panel. Optional")  

            bpy.ops.object.select_all(action='DESELECT')
        
        else:
            
            self.report({'ERROR'}, "Body with the name " + name + " already exists, please choose a different name")
        
        
        return {'FINISHED'}



class ReflectBilateralBodiesOperator(Operator):
    bl_idname = "body.reflect_bilateral_bodies"
    bl_label = "Duplicates and reflects bodies across the specified plane (def: XY), if they contain the specified suffix (def: '_r') in the name. Transforms COM and MOI as well"
    bl_description = "Duplicates and reflects bodies across the specified plane (def: XY), if they contain the specified suffix (def: '_r') in the name. Transforms COM and MOI as well"
    
    
    
    def execute(self, context):
        colname = bpy.context.scene.muskemo.body_collection

        collection = bpy.data.collections[colname]
        
        
        side_suffix = bpy.context.scene.muskemo.side_suffix
        otherside_suffix = bpy.context.scene.muskemo.otherside_suffix
        reflection_plane = bpy.context.scene.muskemo.reflection_plane
        
        
        source_bodies = [obj for obj in collection.objects if side_suffix in obj.name]
        
        if len(source_bodies) == 0:
            self.report({'ERROR'}, "There are no bodies with the suffix " + side_suffix + " in the '" + colname + "' collection")
            return {'FINISHED'}
       
        unilateral_source_bodies = []  #bodies that have the side_suffix in the name, and don't have a mirrored counterpart with otherside_suffix in the name
        

        for obj in source_bodies:  #
            
            if obj.name.replace(side_suffix,otherside_suffix) not in (obj.name for obj in collection.objects):  #make sure a left side doesn't already exist
            
                unilateral_source_bodies.append(obj)
                
        
        if len(unilateral_source_bodies) == 0:
            self.report({'ERROR'}, "All the bodies with the suffix " + side_suffix + " already have a mirrored counterpart. Delete those first")
            return {'FINISHED'}    
                
        
        
        for obj in unilateral_source_bodies:
            
                    
            new_obj = obj.copy()  #copy object
            new_obj.name = obj.name.replace(side_suffix,otherside_suffix) #rename to left
            
            collection.objects.link(new_obj)  #add to collection
            
            
            try:
                new_obj.parent.name
            except:
                pass
            else:
                new_obj.parent = None
                
            
            if reflection_plane == 'XY':  #so Z becomes -Z
            
                new_obj['COM'][2] = -new_obj['COM'][2]  #COM_z
                new_obj['inertia_COM'][4] = -new_obj['inertia_COM'][4]  #Ixz
                new_obj['inertia_COM'][5] = -new_obj['inertia_COM'][5]  #Iyz
        
                new_obj.location = new_obj['COM']
                
            elif reflection_plane == 'XZ':  #so Y becomes -Y
            
                new_obj['COM'][1] = -new_obj['COM'][1]  #COM_y
                new_obj['inertia_COM'][3] = -new_obj['inertia_COM'][3]  #Ixy
                new_obj['inertia_COM'][5] = -new_obj['inertia_COM'][5]  #Iyz
        
                new_obj.location = new_obj['COM']
                
            elif reflection_plane == 'YZ':  #so X becomes -X
        
                new_obj['COM'][0] = -new_obj['COM'][0]  #COM_x
                new_obj['inertia_COM'][3] = -new_obj['inertia_COM'][3]  #Ixy
                new_obj['inertia_COM'][4] = -new_obj['inertia_COM'][4]  #Ixz
        
                new_obj.location = new_obj['COM']        

        return {'FINISHED'}
    
class UpdateLocationFromCOMOperator(Operator):
    bl_idname = "body.update_location_from_com"
    bl_label = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    bl_description = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    
    def execute(self, context):
        
        
        body_name = bpy.context.scene.muskemo.bodyname
        
        if not body_name: #if the user didn't fill out a name
            self.report({'ERROR'}, "You must type in the correct body name, and ensure it is the same as the selected body to prevent ambiguity. Operation aborted")
            return {'FINISHED'}
        
        try: bpy.data.objects[body_name]  #check if the body exists
        
        except:  #throw an error if it doesn't exist
            self.report({'ERROR'}, "Body with the name '" + body_name + "' does not exist yet, create it first")
            
        else:
            
            sel_obj = bpy.context.selected_objects  
            
            #ensure that only the relevant body is selected, or no bodies are selected. The operations will use the user input body name, so this prevents that the user selects a different body and expects the button to operate on that body
            if (len(sel_obj) == 0) or ((len(sel_obj) == 1) and sel_obj[0].name == body_name):  #if no objects are selected, or the only selected object is also the correct body
                
                obj = bpy.data.objects[body_name]
                COM = obj['COM'].to_list()
                
                if np.isnan(COM).any():
                    self.report({'ERROR'}, "Body with the name '" + body_name + "' has NANs in de COM property, define a COM first")
                else:
                    
                    children = obj.children
                    
                    if len(children)==0: #if the object has no children
                        obj.location = COM
                        
                    else:    #if the object has children, loop through them and ensure they don't change their location
                                            
                        for chil in children:
                            global_transform = chil.matrix_world.copy() 
                            chil.parent = None
                            #chil.matrix_world = global_transform
                        
                        loc_old = obj.location.copy()
                        obj.location = COM
                        
                        difference = obj.location-loc_old
                        
                        for chil in children:
                            #global_transform = chil.matrix_world.copy()
                            #local_transform = obj.matrix_world.inverted() @ global_transform
                            chil.parent = obj
                            #chil.matrix_local = local_transform
                            chil.location = chil.location-difference
                                
                    
        
        
            else:
                self.report({'ERROR'}, "Body with the name '" + body_name + "' is not the (only) selected body. Operation cancelled, please either deselect all objects or only select the '" + body_name + "' body. This button operates on the body that corresponds to the user (text) input Body name")
        
        return {'FINISHED'}    
    
class AssignInertialPropertiesOperator(Operator):
    bl_idname = "body.assign_inertial_properties"
    bl_label = "Assign mass, COM & inertia, precomputed by the Inertial Properties panel. Select 1+ source objects, and the target body last (which should turn yellow). Applies the parallel axes theorem when selecting multiple source objects"
    bl_description = "Assign mass, COM & inertia, precomputed by the Inertial Properties panel. Select 1+ source objects, and the target body last (which should turn yellow). Applies the parallel axes theorem when selecting multiple source objects"
   
    def execute(self, context):
        
        body_name = bpy.context.scene.muskemo.bodyname
        colname = bpy.context.scene.muskemo.body_collection

        active_obj = bpy.context.active_object  #should be the body
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        if not body_name: #if the user didn't fill out a name
            self.report({'ERROR'}, "You must type in the correct body name, and ensure it is the same as the selected body to prevent ambiguity. Operation aborted")
            return {'FINISHED'}


        try: bpy.data.objects[body_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Body with the name '" + body_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No objects selected. You must select 1+ source objects with mass properties precomputed in the Inertial properties panel, and the target body (which should correspond to the text input at the top)")
            return {'FINISHED'}
        
        if (len(sel_obj) == 1):
            self.report({'ERROR'}, "Not enough objects selected. You must 1+ source objects with mass properties precomputed in the Inertial properties panel, and the target body (which should correspond to the text input at the top)")
            return {'FINISHED'}
        
        if bpy.data.objects[body_name] not in sel_obj:
            self.report({'ERROR'}, "None of the selected objects is the target body. The target body and body name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if len([ob for ob in sel_obj if ob.name in bpy.data.collections[colname].objects])>1: #if multiple bodies selected
            self.report({'ERROR'}, "More than one selected object is a 'Body' in the '" + colname +  "' collection. You can selected multiple source objects, but only one target body. Operation cancelled.")
            return {'FINISHED'}
        
        
                
        ## source objects are all the selected objects, except the active object (which is the target body)
        source_objects = [ob for ob in sel_obj if ob.name != body_name]
        target_body = bpy.data.objects[body_name]
        
        for s_obj in source_objects:
            try: s_obj['mass']
            except:
                self.report({'ERROR'}, "Source object with the name '" + s_obj.name + "' has no precomputed inertial properties.")
                return {'FINISHED'}
        
        
        if len(source_objects)==1: #trivial case, one source object provides the target body inertial parameters
            
            s_obj = source_objects[0]
            target_body['COM'] = s_obj['COM']
            target_body['mass'] = s_obj['mass']
            target_body['inertia_COM'] = s_obj['inertia_COM']
            
                        
        else: #multiple source objects, sum the masses, & apply parallel axes theorem.    
        
            masses = [x['mass'] for x in source_objects]  #indiv masses
            mass = sum(masses)  #combined mass
            inertia_COM_indiv = [x['inertia_COM'] for x in source_objects]  #inertia about source object COM, per body
            
            COM = sum([np.array(x['COM']) * x['mass'] for x in source_objects]) / mass  #combined COM
                
            r_CO = [np.array(x['COM']) - COM for x in source_objects] ## vector from combined COM to body COM, list of one for each body
            
            
            Ixx_co = []  ## Ixx of body, about combined COM, in global frame
            Iyy_co = []
            Izz_co = []
            Ixy_co = []
            Ixz_co = []
            Iyz_co = []
            
            ### parallel axes theorem
            for b in range(len(masses)):
                Ixx_co.append(masses[b]*(r_CO[b][1]**2 + r_CO[b][2]**2) + inertia_COM_indiv[b][0])
                Iyy_co.append(masses[b]*(r_CO[b][0]**2 + r_CO[b][2]**2) + inertia_COM_indiv[b][1])
                Izz_co.append(masses[b]*(r_CO[b][0]**2 + r_CO[b][1]**2) + inertia_COM_indiv[b][2])
                
                Ixy_co.append(-masses[b]*(r_CO[b][0] * r_CO[b][1]) + inertia_COM_indiv[b][3])
                Ixz_co.append(-masses[b]*(r_CO[b][0] * r_CO[b][2]) + inertia_COM_indiv[b][4])
                Iyz_co.append(-masses[b]*(r_CO[b][1] * r_CO[b][2]) + inertia_COM_indiv[b][5])
                
            
            inertia_COM = [sum(Ixx_co), sum(Iyy_co), sum(Izz_co), sum(Ixy_co), sum(Ixz_co), sum(Iyz_co)]
            target_body['COM'] = COM
            target_body['mass'] = mass
            target_body['inertia_COM'] = inertia_COM
            
        ## update the location of the body so that it matches the new COM
        
                            
        children = target_body.children
        
        if len(children)==0: #if the object has no children
            target_body.location = target_body['COM']
            
        else:    #if the object has children, loop through them and ensure they don't change their location
                                
            for chil in children:
                global_transform = chil.matrix_world.copy() 
                chil.parent = None
                #chil.matrix_world = global_transform
            
            loc_old = target_body.location.copy()
            target_body.location = COM
            
            difference = target_body.location-loc_old
            
            for chil in children:
                #global_transform = chil.matrix_world.copy()
                #local_transform = obj.matrix_world.inverted() @ global_transform
                chil.parent = target_body
                #chil.matrix_local = local_transform
                chil.location = chil.location-difference
            
            
            
            
        return {'FINISHED'}
    
    
class ComputeInertialPropertiesOperator(Operator):
    bl_idname = "body.compute_inertial_properties"
    bl_label = "Compute mass, COM & inertia from triangulated meshes (with densities defined). Select 1+ source objects, and the target body. Applies the parallel axes theorem when selecting multiple source objects"
    bl_description = "Compute mass, COM & inertia from triangulated meshes (with densities defined). Select 1+ source objects, and the target body. Applies the parallel axes theorem when selecting multiple source objects"
    
    def execute(self, context):
        from .. import inertial_properties


        body_name = bpy.context.scene.muskemo.bodyname
        colname = bpy.context.scene.muskemo.body_collection
        active_obj = bpy.context.active_object  #should be the body
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        
        if not body_name: #if the user didn't fill out a name
            self.report({'ERROR'}, "You must type in the correct body name, and ensure it is the same as the selected body to prevent ambiguity. Operation aborted")
            return {'FINISHED'}


        try: bpy.data.objects[body_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Body with the name '" + body_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No objects selected. You must select 1+ source objects and a target body (which corresponds to the body name text input at the top)")
            return {'FINISHED'}
        
        if (len(sel_obj) == 1):
            self.report({'ERROR'}, "Only 1 object selected. You must select 1+ source objects and a target body (which corresponds to the body name text input at the top)")
            return {'FINISHED'}
        
        if bpy.data.objects[body_name] not in sel_obj:
            self.report({'ERROR'}, "None of the selected objects is the target body. The target body and body name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if len([ob for ob in sel_obj if ob.name in bpy.data.collections[colname].objects])>1: #if multiple bodies selected
            self.report({'ERROR'}, "More than one selected object is a 'Body' in the '" + colname +  "' collection. You can selected multiple source objects, but only one target body. Operation cancelled.")
            return {'FINISHED'}
        
            
        ## source objects are all the selected objects, except the active object (which is the target body)
        source_objects = [ob for ob in sel_obj if ob.name != body_name]
        target_body = bpy.data.objects[body_name]
        

        total_mesh_errors = [] #instantiate a variable that tracks mesh errors
        
        for s_obj in source_objects:
            ### check if all objects are triangulated. If not, throw an error            
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




                     
        ### check if all objects have an assigned density, if not, automatically assume the density of water        
        for s_obj in source_objects:
            try: s_obj['density']
            except:
                self.report({'ERROR'}, "Source object with the name '" + s_obj.name + "' has no precomputed density. Automatically assigning a density of 1000 kg m^-3. If you modify the density, recompute the inertial parameters.")
                s_obj['density'] = 1000  #density in kg m^-3
                s_obj.id_properties_ui('density').update(description = 'density (in kg*m^-3)')
                
                #return {'FINISHED'}
        
        
        
        if len(source_objects)==1: #trivial case, one source object provides the target body inertial parameters
            
            s_obj = source_objects[0]
            
            
            #[mass, CoM, mass_I_com, vol, volumetric_I_com] = InProp.inertial_properties(s_obj)
            [mass, CoM, mass_I_com, vol, volumetric_I_com] = inertial_properties(s_obj)
            


            target_body['COM'] = CoM
            target_body['mass'] = mass
            target_body['inertia_COM'] = mass_I_com
            
        else: #multiple source objects. First compute the inertial properties of the bodies, then & apply parallel axes theorem.    
            
            
            masses = []  #mass of the individual source objects
            inertia_COM_indiv = [] # mass MOI about individual COM of indiv source objects
            COM_indiv = []  #COM of indiv source objects
            
                
            for s_obj in source_objects:
                #[mass, CoM, mass_I_com, vol, volumetric_I_com] = InProp.inertial_properties(s_obj)
                [mass, CoM, mass_I_com, vol, volumetric_I_com] = inertial_properties(s_obj)
                
                
                masses.append(mass)
                inertia_COM_indiv.append(mass_I_com)
                COM_indiv.append(CoM)
                            
            
            mass = sum(masses)  #combined mass
             
            COM = sum([np.array(x) * y for x,y in zip(COM_indiv,masses)]) / mass  #combined COM
                
            r_CO = [np.array(x) - COM for x in COM_indiv] ## vector from combined COM to body COM, list of one for each body
            
            
            Ixx_co = []  ## Ixx of body, about combined COM, in global frame
            Iyy_co = []
            Izz_co = []
            Ixy_co = []
            Ixz_co = []
            Iyz_co = []
            
            ### parallel axes theorem
            for b in range(len(masses)):
                Ixx_co.append(masses[b]*(r_CO[b][1]**2 + r_CO[b][2]**2) + inertia_COM_indiv[b][0])
                Iyy_co.append(masses[b]*(r_CO[b][0]**2 + r_CO[b][2]**2) + inertia_COM_indiv[b][1])
                Izz_co.append(masses[b]*(r_CO[b][0]**2 + r_CO[b][1]**2) + inertia_COM_indiv[b][2])
                
                Ixy_co.append(-masses[b]*(r_CO[b][0] * r_CO[b][1]) + inertia_COM_indiv[b][3])
                Ixz_co.append(-masses[b]*(r_CO[b][0] * r_CO[b][2]) + inertia_COM_indiv[b][4])
                Iyz_co.append(-masses[b]*(r_CO[b][1] * r_CO[b][2]) + inertia_COM_indiv[b][5])
                
            
            inertia_COM = [sum(Ixx_co), sum(Iyy_co), sum(Izz_co), sum(Ixy_co), sum(Ixz_co), sum(Iyz_co)]
            target_body['COM'] = COM
            target_body['mass'] = mass
            target_body['inertia_COM'] = inertia_COM
            
        ## update the location of the body so that it matches the new COM
        
        children = target_body.children
        
        if len(children)==0: #if the object has no children
            target_body.location = target_body['COM']
            
        else:    #if the object has children, loop through them and ensure they don't change their location
                                
            for chil in children:
                global_transform = chil.matrix_world.copy() 
                chil.parent = None
                #chil.matrix_world = global_transform
            
            loc_old = target_body.location.copy()
            target_body.location = COM
            
            difference = target_body.location-loc_old
            
            for chil in children:
                #global_transform = chil.matrix_world.copy()
                #local_transform = obj.matrix_world.inverted() @ global_transform
                chil.parent = target_body
                #chil.matrix_local = local_transform
                chil.location = chil.location-difference
            
            
        for obj in sel_obj:  #restore selection
            obj.select_set(True)
                
            
        return {'FINISHED'}    


class AttachVizGeometryOperator(Operator):
    bl_idname = "body.attach_visual_geometry"
    bl_label = "Select 1+ meshes and the target body. Attaches visual geometry (eg. bone meshes) to a body.  Geometry is placed in the designated collection"
    bl_description = "Select 1+ meshes and the target body. Attaches visual geometry (eg. bone meshes) to a body.  Geometry is placed in the designated collection"


    def execute(self, context):
        body_name = bpy.context.scene.muskemo.bodyname
        colname = bpy.context.scene.muskemo.body_collection
        active_obj = bpy.context.active_object  #should be the body
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        geom_colname = bpy.context.scene.muskemo.geometry_collection    

        
        if not body_name: #if the user didn't fill out a name
            self.report({'ERROR'}, "You must type in the correct body name, and ensure it is the same as the selected body to prevent ambiguity to prevent ambiguity. Operation aborted")
            return {'FINISHED'}


        try: bpy.data.objects[body_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Body with the name '" + body_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No objects selected. You must select 1+ source objects and the target body (which corresponds to the body name text input at the top)")
            return {'FINISHED'}
        
        if (len(sel_obj) == 1):
            self.report({'ERROR'}, "Only 1 object selected. You must select 1+ source objects and the target body (which corresponds to the body name text input at the top)")
            return {'FINISHED'}
        
        if bpy.data.objects[body_name] not in sel_obj:
            self.report({'ERROR'}, "None of the selected objects is the target body. The target body and body name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if len([ob for ob in sel_obj if ob.name in bpy.data.collections[colname].objects])>1: #if multiple bodies selected
            self.report({'ERROR'}, "More than one selected object is a 'Body' in the '" + colname +  "' collection. You can selected multiple source objects, but only one target body. Operation cancelled.")
            return {'FINISHED'}
        
        ## source objects are all the selected objects, except the active object (which is the target body)
        geom_objects = [ob for ob in sel_obj if ob.name != body_name]
        target_body = bpy.data.objects[body_name]

        error_check = []  #check if there are non-mesh data types, visualization geometry can only be of the type mesh

        for geom in geom_objects:
            if geom.type != 'MESH':
                error_check.append([1])
                self.report({'ERROR'}, "The selected object '" + geom.name +  "' is not a 'MESH'. Only meshes can act as visualization geometry. Operation cancelled.")

        
        if len(error_check)>1:
            return {'FINISHED'}
            
        ### if none of the previous scenarios triggered an error, we can actually set geometry

        #check if the collection name exists, and if not create it
        if geom_colname not in bpy.data.collections:
            bpy.data.collections.new(geom_colname)
            self.report({'INFO'},"Collection with the name '" + geom_colname + "' doesn't exist yet, automatically creating it. Visualization geometry will be moved to this collection.")


        coll = bpy.data.collections[geom_colname] #Collection which will recieve the scaled  hulls

        if geom_colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the geom collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[geom_colname]
        

        ##target body:
        body = bpy.data.objects[body_name]

        for geom in geom_objects:
            
            if coll not in geom.users_collection:
        
                for old_coll in geom.users_collection:
                    # Unlink the object
                    old_coll.objects.unlink(geom)

            # Link each object to the geom collection
                coll.objects.link(geom)
    
        
        ## instantiate geom list, and append each geometry to it with the folder name

        geom_list = []


        for geom in geom_objects:
            

            ## construct the relative directory in the geometry folder (to be used in the model)
            geom_relpath = geom_colname + '/' + geom.name + '.obj'
            
            ### check if geom_relpath is already attached to another body
            skip_geom = False
            for obj in [obj for obj in bpy.data.collections[colname].objects if obj != body]: #for all the bodies in the body collection that aren't the target body
                
                
                if geom_relpath in obj['Geometry']:
                    self.report({'ERROR'}, "The selected geometry '" + geom.name +  "' is already attached to a different body with the name '" + obj.name + "'. Detach it from that body first. Skipped this geometry object.")
                    skip_geom = True
                    break

            if skip_geom:
                continue


            if geom_relpath in body['Geometry']:
                self.report({'ERROR'}, "The selected geometry '" + geom.name +  "' is already attached to target body with name '" + obj.name + "'. Skipped this geometry object.")    
                continue
            
            

            ### if nothing throws an error, assign the body as the parent
            geom.parent = body
            
            #this undoes the transformation after parenting
            geom.matrix_parent_inverse = body.matrix_world.inverted()

            geom_list.append(geom_relpath)

            ## Assign a MuSkeMo_type if it doesn't already exist:
            try:
                geom['MuSkeMo_type']
            except:
                geom['MuSkeMo_type'] = 'GEOMETRY'    #to inform the user what type is created
                geom.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  

            geom['Attached to'] = body.name
            geom.id_properties_ui('Attached to').update(description = "The body that this geometry is attached to")


        geom_delimiter = ';'

        if geom_list:  #if the geom_list is nonempty
            
            geom_list_str = geom_delimiter.join(geom_list) + geom_delimiter
            
            if body['Geometry'] == 'no geometry':
                body['Geometry'] = geom_list_str
            else:
                body['Geometry'] = body['Geometry'] + geom_list_str  


        
        return {'FINISHED'}
    

class DetachVizGeometryOperator(Operator):
    bl_idname = "body.detach_visual_geometry"
    bl_label = "Select 1+ meshes and the target body. Detaches visual geometry (eg. bone meshes) from a body."
    bl_description = "Select 1+ meshes and the target body. Detaches visual geometry (eg. bone meshes) from a body."


    def execute(self, context):
        body_name = bpy.context.scene.muskemo.bodyname
        colname = bpy.context.scene.muskemo.body_collection
        active_obj = bpy.context.active_object  #should be the body
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        geom_colname = bpy.context.scene.muskemo.geometry_collection    

        if not body_name: #if the user didn't fill out a name
            self.report({'ERROR'}, "You must type in the correct body name, and ensure it is the same as the selected body to prevent ambiguity to prevent ambiguity. Operation aborted")
            return {'FINISHED'}


        try: bpy.data.objects[body_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Body with the name '" + body_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No objects selected. You must select 1+ source objects and the target body (which corresponds to the body name text input at the top)")
            return {'FINISHED'}
        
        if (len(sel_obj) == 1):
            self.report({'ERROR'}, "Only 1 object selected. You must select 1+ source objects and the target body (which corresponds to the body name text input at the top)")
            return {'FINISHED'}
        
        if bpy.data.objects[body_name] not in sel_obj:
            self.report({'ERROR'}, "None of the selected objects is the target body. The target body and body name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if len([ob for ob in sel_obj if ob.name in bpy.data.collections[colname].objects])>1: #if multiple bodies selected
            self.report({'ERROR'}, "More than one selected object is a 'Body' in the '" + colname +  "' collection. You can selected multiple source objects, but only one target body. Operation cancelled.")
            return {'FINISHED'}
        
        if len([ob for ob in sel_obj if ob.name in bpy.data.collections[geom_colname].objects])<1: #if less than 1 object is in the geometry collection
            self.report({'ERROR'}, "None of the selected objects are a geometry file in the '" + colname +  "' collection. Operation cancelled.")
            return {'FINISHED'}

        ## source objects are all the selected objects, except the active object (which is the target body)
        geom_objects = [ob for ob in sel_obj if ob.name != body_name]
        target_body = bpy.data.objects[body_name]

        geom_delimiter = ';'
        for geom in geom_objects:
            geom_relpath = geom_colname + '/' + geom.name + '.obj'

            if geom_relpath in target_body['Geometry']:  #if geom is attached to the body
                
                target_body['Geometry'] = target_body['Geometry'].replace(geom_relpath + geom_delimiter,'')  #remove the geom path from the body
                geom['Attached to'] = 'no body'  #update the "attached to" state of the geometry


                ## unparent the geometry in blender, without moving the geometry
                parented_worldmatrix =geom.matrix_world.copy() 
                geom.parent = None
                geom.matrix_world = parented_worldmatrix

                
                

            else: 
                
                self.report({'ERROR'}, "Geometry file '" + geom.name +  "' does not appear to be attached to body '" + target_body.name + "'. Operation cancelled.")




        if not target_body['Geometry']: #if the geometry list is now empty, state so explicitly
            target_body['Geometry'] = 'no geometry'


        return {'FINISHED'}



    

class VIEW3D_PT_body_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    #Multiple inheritance, body_panel as a class inherits attributes from MuSkeMo class, but also from the "Panel" class, turning this into a panel
    #This is the first (main) subpanel in the parent class VIEW3D_PT_MuSkeMo.
    #The first layer of panels doesn't need a bl_parentid, but if you want multiple, you will need a 'bl_idname' for each.
    #Subpanels to this one need to be placed under VIEW3D_PT_MuSkeMo, but using the VIEW3D_PT_body_panel as the parentid
    bl_idname = 'VIEW3D_PT_body_panel'
    
    
    #bl_category = "Body panel"  # found in the Sidebar
    bl_label = "Body panel"  # found at the top of the Panel
    bl_context = "objectmode"
    
    bl_options = {'DEFAULT_CLOSED'}
    
    #bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        
        
        ## user input body name    
        layout.prop(muskemo, "bodyname")
        row = self.layout.row()
       
        row.prop(muskemo, "body_collection")
        row = self.layout.row()


        ## Create new body
        row = self.layout.row()
        row.operator("body.create_new_body", text="Create new body")
        row = self.layout.row()
                
        
        ## compute inertial properties from other meshes
        
        row = self.layout.row()
        row.label(text = "This button computes the mass properties using source objects with assigned densities")
        row = self.layout.row()
        row.operator("body.compute_inertial_properties", text="Compute inertial properties")
        
            
        ## assign precomputed inertial properties from other meshes
        self.layout.row()
        
        row = self.layout.row()
        
        row = self.layout.row()
        row.label(text = "This button assigns the mass properties using source objects with precomputed mass properties")
         
        row = self.layout.row()
        row.operator("body.assign_inertial_properties", text="Assign precomputed inertial properties")
        row = self.layout.row()
        row.label(text = "Properties are not dynamic, recompute them if you move source objects around")


        
class VIEW3D_PT_vizgeometry_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # 
    bl_idname = 'VIEW3D_PT_vizgeometry_subpanel'
    bl_parent_id = 'VIEW3D_PT_body_panel'
    
    #bl_category = "Body panel"  # found in the Sidebar
    bl_label = "Attach visual (bone) geometry"  # found at the top of the Panel
    bl_context = "objectmode"
    
    bl_options = {'DEFAULT_CLOSED'}
    
    #bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        ## user input body name    
        layout.prop(muskemo, "geometry_collection")
        row = self.layout.row()

        row.operator("body.attach_visual_geometry", text = "Attach visual (bone) geometry")
        row = self.layout.row()
        row.operator("body.detach_visual_geometry", text = "Detach visual (bone) geometry")
        return


class VIEW3D_PT_body_utilities_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # 
    bl_idname = 'VIEW3D_PT_body_utilities_subpanel'
    bl_parent_id = 'VIEW3D_PT_body_panel'
    
    #bl_category = "Body panel"  # found in the Sidebar
    bl_label = "Body utilities"  # found at the top of the Panel
    bl_context = "objectmode"
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        ## update display location using COM
        row = self.layout.row()
        row.operator("body.update_location_from_com", text="Update display location using COM")
        
         
        
        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.operator("body.reflect_bilateral_bodies", text="Reflect bilateral bodies")
        
        
        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.prop(muskemo, "side_suffix")
        row = self.layout.row()
        row.prop(muskemo, "otherside_suffix")
        row = self.layout.row()
        row.prop(muskemo, "reflection_plane")
        
        
        
        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.prop(muskemo, "axes_size")