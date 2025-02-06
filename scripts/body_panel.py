# give Python access to Blender's functionality
import bpy

import mathutils
from mathutils import (Vector, Matrix)

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
    bl_label = "Creates a new body at the origin. Choose a unique name and press the button."
    bl_description = "Creates a new body at the origin. Choose a unique name and press the button."
    
    def execute(self,context):
        
        rad = bpy.context.scene.muskemo.axes_size #axis length, in meters
        name = bpy.context.scene.muskemo.bodyname  #name of the object

        

        if not name: #if the user didn't fill out a name
            self.report({'ERROR'}, "Fill in a body name first. Operation aborted")
            return {'FINISHED'}

        
        colname = bpy.context.scene.muskemo.body_collection #name for the collection that will contain the hulls
        
                
        try: bpy.data.objects[name] #try out if an object with the new body's name already exists
        
        except: #if not, create the new body
            
            from .create_body_func import create_body
                       
            create_body(name = name, self= self, size = rad, is_global =True, collection_name=colname)

        
        else: #if it already exists, throw an error
            
            self.report({'ERROR'}, "Body with the name " + name + " already exists, please choose a different name")
        
        

        bpy.context.scene.muskemo.bodyname = '' #set the name to be empty again.        
        return {'FINISHED'}

 
class UpdateLocationFromCOMOperator(Operator):
    bl_idname = "body.update_location_from_com"
    bl_label = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    bl_description = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    
    def execute(self, context):
        

        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "No body selected. Select a body and try again.")
            return {'FINISHED'}
        
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select a single body and try again.")
            return {'FINISHED'}
        

        muskemo_objects = [ob for ob in sel_obj if 'MuSkeMo_type' in ob]
        sel_bodies = [ob for ob in muskemo_objects if ob['MuSkeMo_type'] == 'BODY']

        # throw an error if no objects are selected     
        if (len(sel_bodies) != 1):
            self.report({'ERROR'}, "The object you selected is not a body. Select a single body and try again.")
            return {'FINISHED'}
    
        
        target_body = sel_bodies[0] #the target body
        COM = target_body['COM'].to_list()
        
        if np.isnan(COM).any():
            self.report({'ERROR'}, "Body with the name '" + target_body.name + "' has NANs in de COM property, define a COM first")
        else:
            
            ## Check whether a local frame is attached to the body, and if so, compute the local frame attributes

            if target_body['local_frame'] != 'not_assigned': #if the target body has a local frame assigned


                frame = bpy.data.objects[target_body['local_frame']] #get the frame
                
                ### COM extra properties COM_local, inertia_COM_local

                gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
                bRg = gRb.copy()
                bRg.transpose()
                
                frame_or_g = frame.matrix_world.translation   #frame origin in global frame
                COM_g = Vector(target_body['COM'])  #COM loc in global frame

                relCOM_g = COM_g - frame_or_g  #Relative COM location from the local frame origin, aligned in global frame
                relCOM_b = bRg @ relCOM_g #COM of the body, expressed in the local frame

                target_body['COM_local'] = list(relCOM_b)  #set COM in local frame

                MOI_glob_vec = target_body['inertia_COM']  #vector of MOI about COM, in global frame. Ixx Iyy Izz Ixy Ixz Iyz
                MOI_g = Matrix(((MOI_glob_vec[0], MOI_glob_vec[3], MOI_glob_vec[4]), #MOI tensor about COM in global
                                (MOI_glob_vec[3],MOI_glob_vec[1],MOI_glob_vec[5]),
                                (MOI_glob_vec[4],MOI_glob_vec[5],MOI_glob_vec[2])))
                
                MOI_b = bRg @ MOI_g @ gRb #Vallery & Schwab, Advanced Dynamics 2018, eq. 5.53

                MOI_b_vec = [MOI_b[0][0],  #Ixx, about COM, in local frame
                            MOI_b[1][1],  #Iyy
                            MOI_b[2][2],  #Izz
                            MOI_b[0][1],  #Ixy
                            MOI_b[0][2],  #Ixz
                            MOI_b[1][2]]  #Iyz


                target_body['inertia_COM_local'] = MOI_b_vec  

            children = target_body.children
            
            if len(children)==0: #if the object has no children
                target_body.matrix_world.translation = COM

                target_body['default_pose'] = target_body.matrix_world #track the default pose to ensure the exported values are in the same pose
                
            else:    #if the object has children, loop through them and ensure they don't change their location
                                    
                for chil in children:
                    parented_worldmatrix = chil.matrix_world.copy() 
                    chil.parent = None
                    chil.matrix_world = parented_worldmatrix

                pos_old = target_body.matrix_world.translation.copy()
                target_body.matrix_world.translation = target_body['COM']

                target_body['default_pose'] = target_body.matrix_world #track the default pose to ensure the exported values are in the same pose
                
                                
                for chil in children:
                    #global_transform = chil.matrix_world.copy()
                    #local_transform = obj.matrix_world.inverted() @ global_transform
                    chil.parent = target_body
                    
                    #this undoes the transformation after parenting
                    chil.matrix_parent_inverse = target_body.matrix_world.inverted()
                            
        return {'FINISHED'}    
    
class AssignInertialPropertiesOperator(Operator):
    bl_idname = "body.assign_inertial_properties"
    bl_label = "Assign mass, COM & inertia, precomputed by the Inertial Properties panel. Select 1+ source objects, and the target body. Applies the parallel axes theorem when selecting multiple source objects"
    bl_description = "Assign mass, COM & inertia, precomputed by the Inertial Properties panel. Select 1+ source objects, and the target body. Applies the parallel axes theorem when selecting multiple source objects"
   
    def execute(self, context):
        
        
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        if (len(sel_obj) <= 1):
            self.report({'ERROR'}, "Not enough objects selected. You must select the target body and 1+ source objects with mass properties precomputed in the Inertial properties panel.")
            return {'FINISHED'}
        
        muskemo_objects = [ob for ob in sel_obj if 'MuSkeMo_type' in ob]
        sel_bodies = [ob for ob in muskemo_objects if ob['MuSkeMo_type'] == 'BODY']

        # throw an error if no objects are selected     
        if (len(sel_bodies) == 0):
            self.report({'ERROR'}, "No bodies selected. You must select select a body to which you would like to assign inertial properties")
            return {'FINISHED'}
        
        # throw an error if multiple bodies are selected     
        if (len(sel_bodies) > 1):
            self.report({'ERROR'}, "Multiple bodies selected. You must select select one body to which you would like to assign inertial properties")
            return {'FINISHED'}
        
        target_body = sel_bodies[0]
        ## source objects are all the selected objects, except the target body
        source_objects = [ob for ob in sel_obj if ob != target_body]
  
        #Check if the source objects all have precomputed in props
        for s_obj in source_objects:
            try: s_obj['mass']
            except:
                self.report({'ERROR'}, "Source object with the name '" + s_obj.name + "' has no precomputed inertial properties. Compute these first in the Inertial properties panel.")
                return {'FINISHED'}
              
        #Check if all the source objects are still in the default pose (in which the inprops were computed)
        for s_obj in source_objects:
            if s_obj.matrix_world != Matrix(s_obj['default_pose']):
                self.report({'ERROR'}, "Inertial properties of '" + s_obj.name + "' were computed in a different pose than the current pose. Reset the model to the default pose, or recompute the inertial properties. Operation cancelled")
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


        ## Check whether a local frame is attached to the body, and if so, compute the local frame attributes

        if target_body['local_frame'] != 'not_assigned': #if the target body has a local frame assigned


            frame = bpy.data.objects[target_body['local_frame']] #get the frame
            
            ### COM extra properties COM_local, inertia_COM_local

            gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
            bRg = gRb.copy()
            bRg.transpose()
            
            frame_or_g = frame.matrix_world.translation   #frame origin in global frame
            COM_g = Vector(target_body['COM'])  #COM loc in global frame

            relCOM_g = COM_g - frame_or_g  #Relative COM location from the local frame origin, aligned in global frame
            relCOM_b = bRg @ relCOM_g #COM of the body, expressed in the local frame

            target_body['COM_local'] = list(relCOM_b)  #set COM in local frame

            MOI_glob_vec = target_body['inertia_COM']  #vector of MOI about COM, in global frame. Ixx Iyy Izz Ixy Ixz Iyz
            MOI_g = Matrix(((MOI_glob_vec[0], MOI_glob_vec[3], MOI_glob_vec[4]), #MOI tensor about COM in global
                            (MOI_glob_vec[3],MOI_glob_vec[1],MOI_glob_vec[5]),
                            (MOI_glob_vec[4],MOI_glob_vec[5],MOI_glob_vec[2])))
            
            MOI_b = bRg @ MOI_g @ gRb #Vallery & Schwab, Advanced Dynamics 2018, eq. 5.53

            MOI_b_vec = [MOI_b[0][0],  #Ixx, about COM, in local frame
                        MOI_b[1][1],  #Iyy
                        MOI_b[2][2],  #Izz
                        MOI_b[0][1],  #Ixy
                        MOI_b[0][2],  #Ixz
                        MOI_b[1][2]]  #Iyz


            target_body['inertia_COM_local'] = MOI_b_vec  #add moment of inertia in local frame to the body


        ## update the location of the body so that it matches the new COM
        
                            
        children = target_body.children

        
        if len(children)==0: #if the object has no children
            target_body.location = target_body['COM']
            target_body['default_pose'] = target_body.matrix_world #track the default pose to ensure the exported values are in the same pose
                
            
        else:    #if the object has children, loop through them and ensure they don't change their location
                                
            for chil in children:
                parented_worldmatrix = chil.matrix_world.copy() 
                chil.parent = None
                chil.matrix_world = parented_worldmatrix
            
            pos_old = target_body.matrix_world.translation.copy()
            target_body.matrix_world.translation = target_body['COM']

            target_body['default_pose'] = target_body.matrix_world
            
                        
            for chil in children:
                #global_transform = chil.matrix_world.copy()
                #local_transform = obj.matrix_world.inverted() @ global_transform
                chil.parent = target_body
                
                #this undoes the transformation after parenting
                chil.matrix_parent_inverse = target_body.matrix_world.inverted()
            
            
            
            
        return {'FINISHED'}
    


class AttachVizGeometryOperator(Operator):
    bl_idname = "body.attach_visual_geometry"
    bl_label = "Select 1+ meshes and the target body. Attaches visual geometry (eg. bone meshes) to a body.  Geometry is placed in the designated collection"
    bl_description = "Select 1+ meshes and the target body. Attaches visual geometry (eg. bone meshes) to a body.  Geometry is placed in the designated collection"


    def execute(self, context):
        body_name = bpy.context.scene.muskemo.bodyname
        colname = bpy.context.scene.muskemo.body_collection
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        geom_colname = bpy.context.scene.muskemo.geometry_collection    

        
               
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        if (len(sel_obj) <= 1):
            self.report({'ERROR'}, "Not enough objects selected. You must select the target body and 1+ visual geometry meshes to attach to the target body.")
            return {'FINISHED'}
        
        muskemo_objects = [ob for ob in sel_obj if 'MuSkeMo_type' in ob]
        sel_bodies = [ob for ob in muskemo_objects if ob['MuSkeMo_type'] == 'BODY']

        # throw an error if no objects are selected     
        if (len(sel_bodies) == 0):
            self.report({'ERROR'}, "No bodies selected. You must select a body to which you would like to attach visual geometry meshes")
            return {'FINISHED'}
        
        # throw an error if multiple bodies are selected     
        if (len(sel_bodies) > 1):
            self.report({'ERROR'}, "Multiple bodies selected. You must select select one body to which you would like to attach visual geometry meshes")
            return {'FINISHED'}
        
        target_body = sel_bodies[0]
        ## geom objects are all the selected objects, except the target body
        geom_objects = [ob for ob in sel_obj if ob != target_body]

        geom_objects_MuSkeMo = [ob for ob in geom_objects if 'MuSkeMo_type' in ob]
        error_check = []  #check if there are non-mesh data types, visualization geometry can only be of the type mesh

        for ob in geom_objects_MuSkeMo: #if any of the prospective geom objects are already a different muskemo type (e.g., joint), don't allow geometry assignment
            if ob['MuSkeMo_type'] != 'GEOMETRY':
                error_check.append([1])
                self.report({'ERROR'}, "The selected object '" + ob.name +  "' is of the MuSkeMo type '" + ob['MuSkeMo_type'] + "', which cannot act as visualization geometry. Operation cancelled.")
 
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

            all_MuSkeMo_objects = [obj for obj in bpy.data.objects if 'MuSkeMo_type' in obj]
            all_bodies = [obj for obj in all_MuSkeMo_objects if obj['MuSkeMo_type'] == 'BODY']

            for obj in [obj for obj in all_bodies if obj != target_body]: #for all the bodies in the scene that aren't the target body
                
                if geom_relpath in obj['Geometry']:
                    self.report({'ERROR'}, "The selected geometry '" + geom.name +  "' is already attached to a different body with the name '" + obj.name + "'. Detach it from that body first. Skipped this geometry object.")
                    skip_geom = True
                    break

            if skip_geom:
                continue


            if geom_relpath in target_body['Geometry']:
                self.report({'ERROR'}, "The selected geometry '" + geom.name +  "' is already attached to target body with name '" + obj.name + "'. Skipped this geometry object.")    
                continue
            
            

            ### if nothing throws an error, assign the body as the parent
            geom.parent = target_body
            
            #this undoes the transformation after parenting
            geom.matrix_parent_inverse = target_body.matrix_world.inverted()

            geom_list.append(geom_relpath)

            ## Assign a MuSkeMo_type if it doesn't already exist:
            try:
                geom['MuSkeMo_type']
            except:
                geom['MuSkeMo_type'] = 'GEOMETRY'    #to inform the user what type is created
                geom.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  

            geom['Attached to'] = target_body.name
            geom.id_properties_ui('Attached to').update(description = "The body that this geometry is attached to")
            
            ##### Assign a material
            ## if not exists bone material
            matname = 'visual_geometry_material'
            bone_color = tuple(bpy.context.scene.muskemo.bone_color)

            if matname not in bpy.data.materials:  
                bpy.data.materials.new(name = matname)
                mat = bpy.data.materials[matname]
                mat.use_nodes = True
                matnode_tree =mat.node_tree
                #matnode_tree.nodes["Principled BSDF"].inputs['Roughness'].default_value = 0
                matnode_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = bone_color

            mat = bpy.data.materials[matname]
            geom.data.materials.append(mat)

        geom_delimiter = ';'

        if geom_list:  #if the geom_list is nonempty
            
            geom_list_str = geom_delimiter.join(geom_list) + geom_delimiter
            
            if target_body['Geometry'] == 'no geometry':
                target_body['Geometry'] = geom_list_str
            else:
                target_body['Geometry'] = target_body['Geometry'] + geom_list_str  


        
        return {'FINISHED'}
    

class DetachVizGeometryOperator(Operator):
    bl_idname = "body.detach_visual_geometry"
    bl_label = "Select 1+ meshes and the target body. Detaches visual geometry (eg. bone meshes) from a body."
    bl_description = "Select 1+ meshes and the target body. Detaches visual geometry (eg. bone meshes) from a body."


    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        geom_colname = bpy.context.scene.muskemo.geometry_collection    

                
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No objects selected. You must select 1+ geometry objects and their parent body")
            return {'FINISHED'}
        
        if (len(sel_obj) == 1):
            self.report({'ERROR'}, "Only 1 object selected. You must select 1+ geometry objects and their parent body")
            return {'FINISHED'}
        
        muskemo_objects = [obj for obj in sel_obj if 'MuSkeMo_type' in obj]
        
        bodies = [obj for obj in muskemo_objects if obj['MuSkeMo_type']=='BODY']

        if len(bodies)>1: #if multiple bodies selected
            self.report({'ERROR'}, "More than one selected object is a 'BODY'. You can selected multiple geometry objects, but only one body (their parent). Operation cancelled.")
            return {'FINISHED'}
        
        if len(bodies)<1: #if multiple bodies selected
            self.report({'ERROR'}, "None of the selected object is a 'BODY'. Select multiple geometry objects and their parent body, and try again. Operation cancelled.")
            return {'FINISHED'}
        
        parent_body = bodies[0]
        geom_objects = [obj for obj in muskemo_objects if obj['MuSkeMo_type'] == 'GEOMETRY']
                
        if len(geom_objects)<1: #if less than 1 object is in the geometry collection
            self.report({'ERROR'}, "None of the selected objects are of the MuSkeMo type 'GEOMETRY'. Operation cancelled.")
            return {'FINISHED'}

        geom_delimiter = ';'
        for geom in geom_objects:
            geom_relpath = geom_colname + '/' + geom.name + '.obj'

            if geom_relpath in parent_body['Geometry']:  #if geom is attached to the body
                
                parent_body['Geometry'] = parent_body['Geometry'].replace(geom_relpath + geom_delimiter,'')  #remove the geom path from the body
                geom['Attached to'] = 'no body'  #update the "attached to" state of the geometry


                ## unparent the geometry in blender, without moving the geometry
                parented_worldmatrix =geom.matrix_world.copy() 
                geom.parent = None
                geom.matrix_world = parented_worldmatrix

                

            else: 
                
                self.report({'WARNING'}, "Geometry file '" + geom.name +  "' does not appear to be attached to body '" + parent_body.name + "'. Geometry skipped.")




        if not parent_body['Geometry']: #if the geometry list is now empty, state so explicitly
            parent_body['Geometry'] = 'no geometry'


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
        
         ### selected joints and bodies

        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('BODY', layout)
        

        ## user input body name    
        row = self.layout.row()
        split = row.split(factor=1/3)
        split.label(text = "Body Name:")
        ## Create new body
        split = split.split(factor = 1/2)
        split.prop(muskemo, "bodyname", text = "")
        split.operator("body.create_new_body", text="Create new body")
        
        ## body collection
        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Body collection:")
        split.prop(muskemo, "body_collection", text = "")
        row = self.layout.row()


       
        row = self.layout.row()
        row.prop(muskemo, "axes_size")
             
        row = self.layout.row()
                   
        ## assign precomputed inertial properties from other meshes
        self.layout.row()
        
        row = self.layout.row()
        row = self.layout.row()
        row.label(text = "Source objects (Geometry) with precomputed inertial properties")
        CreateSelectedObjRow('GEOMETRY_withdensity', layout)

                 
        row = self.layout.row()
        row.operator("body.assign_inertial_properties", text="Assign precomputed inertial properties")
        
        
        
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
        row = self.layout.row()
        split = row.split(factor=1/2)
        split.label(text = "Geometry collection")
        split.prop(muskemo, "geometry_collection", text = "")
        row = self.layout.row()

        row.operator("body.attach_visual_geometry", text = "Attach visual (bone) geometry")
        row = self.layout.row()
        row.operator("body.detach_visual_geometry", text = "Detach visual (bone) geometry")
        return


class VIEW3D_PT_body_manual_inprop_assignment_subpanel(VIEW3D_PT_MuSkeMo, Panel):  # 
    bl_idname = 'VIEW3D_PT_body_utilities_subpanel'
    bl_parent_id = 'VIEW3D_PT_body_panel'
    
    #bl_category = "Body panel"  # found in the Sidebar
    bl_label = "Assign inertial properties manually"  # found at the top of the Panel
    bl_context = "objectmode"
    
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        row = layout.row()
        
        row.label(text = "If you manually type in inertial properties, use the below button to update the display location")
        row = layout.row()
        row.operator("body.update_location_from_com", text="Update display location using COM")
         
        
        