# give Python access to Blender's functionality
import bpy
from mathutils import (Matrix, Vector)


from bpy.types import (Panel,
                        Operator,
                        )

from math import nan

import numpy as np
import bmesh

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed
    

#### operators


class MeshAlignnmentICPPointToPlaneOperator(Operator):
    bl_idname = "mesh.align_icp_point_to_plane"
    bl_label = "Rigid mesh alignment using iterative closest point - point to plane. Select two meshes, designate the free object, and then press the button."
    bl_description = "Rigid mesh alignment using iterative closest point - point to plane. Select two meshes, designate the free object, and then press the button."
    bl_options = {"UNDO"} #enable undoing
    
    def execute(self, context):
        


        sel_obj = [x for x in bpy.context.selected_objects if x.type == 'MESH']  #should be the source objects (e.g. skin outlines) with precomputed inertial parameters
        
        
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Less than 2 meshes selected. Select exactly 2 meshes, and try again")
            return {'FINISHED'}
        
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "More than 2 meshes selected. Select exactly 2 meshes, and try again")
            return {'FINISHED'}
        
        muskemo = bpy.context.scene.muskemo

        free_obj = bpy.data.objects[muskemo.icp_free_obj]
        target_obj = [obj for obj in sel_obj if obj!=free_obj][0] #target obj is the other selected object


        alignment_mode = muskemo.icp_alignment_mode


        if alignment_mode == 'Selected mesh portions':

            if not [v for v in  free_obj.data.vertices if v.select]:
                self.report({'ERROR'}, free_obj.name + "Free Object has no selected portions. Select the mesh, hit TAB to go into edit mode, and then select the mesh portion you would like to align. Alternatively, align the entire mesh.")
                return {'FINISHED'}

            if not [v for v in  target_obj.data.vertices if v.select]:
                self.report({'ERROR'}, target_obj.name + " has no selected portions. Select the mesh, hit TAB to go into edit mode, and then select the mesh portion you would like to align. Alternatively, align the entire mesh.")
                return {'FINISHED'}

        max_iter = muskemo.icp_max_iterations
        tol = muskemo.icp_tolerance
        sample_ratio_start = muskemo.icp_sample_ratio_start
        sample_ratio_end = muskemo.icp_sample_ratio_end
        max_sample_ratio_after = muskemo.icp_max_sample_ratio_after

        from .icp_point_to_plane import point_to_plane_icp_subsample

        point_to_plane_icp_subsample(free_obj = free_obj,
                                     target_obj=  target_obj,
                                     max_iterations=max_iter,
                                     tolerance=tol,
                                     sample_ratio_start=sample_ratio_start,
                                     sample_ratio_end=sample_ratio_end,
                                    sample_ratio_ramp_iters = max_sample_ratio_after,
                                    alignment_mode = alignment_mode)
        
        return {'FINISHED'}




class MeshIntersectionCheckerOperator(Operator):
    bl_idname = "mesh.intersection_checker"
    bl_label = "Select 2 meshes and check for intersections between them."
    bl_description = "Select 2 meshes and check for intersections between them."

    result_message: bpy.props.StringProperty(default="")

    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be two meshes

        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "No objects selected. You must select 2 meshes to check whether they are intersecting.")
            return {'FINISHED'}
        
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. You must select 2 meshes to check whether they are intersecting.")
            return {'FINISHED'}
        
        sel_meshes = [x for x in sel_obj if x.type == 'MESH'] #check that the objects are all meshes

        if len(sel_meshes)==1: #If only one object is a mesh
            self.report({'ERROR'}, "Only one of the two objects is a MESH. The mesh intersection checker only works on meshes. Select 2 meshes and try again.")
            return {'FINISHED'}
        

        if len(sel_meshes)==0: #If no mesh
            self.report({'ERROR'}, "Neither of the selected objects is a MESH. The mesh intersection checker only works on meshes. Select 2 meshes and try again.")
            return {'FINISHED'}


        #### check for intersections

        from .two_object_intersection_func import check_bvh_intersection
        #Get the dependency graph
        depsgraph = bpy.context.evaluated_depsgraph_get()

        mesh_1_name = sel_meshes[0].name
        mesh_2_name = sel_meshes[1].name

        intersections = check_bvh_intersection(mesh_1_name, mesh_2_name, depsgraph)
        #The output is pairs of intersecting polygons (if indeed these exist)

                
        if intersections:
            self.result_message = mesh_1_name + " and " + mesh_2_name + " intersect with each other."
        else:
            self.result_message = mesh_1_name + " and " + mesh_2_name + " do not intersect with each other."

        # Show popup after setting the message
        return context.window_manager.invoke_popup(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text=self.result_message)

    def invoke(self, context, event):
        
        return self.execute(context)
    
class MeshFromSelectionOperator(Operator):
    bl_idname = "mesh.mesh_from_selection"
    bl_label = "Mesh From Selected Portion"
    bl_description = "Create a new mesh object from the selected mesh portion. You must select a mesh portion by pressing TAB to go into EDIT mode."
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.edit_object
        return (
            obj is not None and
            obj.type == 'MESH' and
            context.mode == 'EDIT_MESH'
        )

    def execute(self, context):
        obj = context.edit_object
        mesh = obj.data

        # Access live Edit Mode mesh
        bm = bmesh.from_edit_mesh(mesh)

        # Try selected faces first
        faces = [f for f in bm.faces if f.select]

        bm_new = bmesh.new()
        vert_map = {}

        if faces:
            # Copy vertices from faces
            for f in faces:
                for v in f.verts:
                    if v not in vert_map:
                        vert_map[v] = bm_new.verts.new(v.co)
            bm_new.verts.ensure_lookup_table()

            # Copy faces
            for f in faces:
                bm_new.faces.new([vert_map[v] for v in f.verts])
        else:
            # No faces: check selected vertices (point cloud)
            verts = [v for v in bm.verts if v.select]
            if not verts:
                # Nothing selected
                self.report({'WARNING'},"No faces or vertices selected")
                return {'FINISHED'}

            # Copy selected vertices
            for v in verts:
                vert_map[v] = bm_new.verts.new(v.co)
            bm_new.verts.ensure_lookup_table()
            # No faces to copy


        # Create new mesh
        new_mesh = bpy.data.meshes.new(obj.name + "_selected_surface")
        bm_new.to_mesh(new_mesh)
        bm_new.free()

        # Create new object
        new_obj = bpy.data.objects.new(new_mesh.name, new_mesh)
        context.collection.objects.link(new_obj)

        # Copy full transform (parent-safe)
        new_obj.matrix_world = obj.matrix_world.copy()

        return {'FINISHED'}
    
class FitSphereGeomOperator(Operator):
    bl_idname = "mesh.fit_sphere_geometric"
    bl_label = "Fit a sphere to a selected mesh, using Yesudesan geometric fit"
    bl_description = "Fit a sphere to a selected mesh, using Yesudesan geometric fit"
    bl_options = {"UNDO"} #enable undoing
    #Based on sumith_fit - https://doi.org/10.48550/arXiv.1506.02776
  
    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the mesh
        sel_obj = bpy.context.selected_objects  #should be the only the mesh

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, input  = verts_x, verts_y, verts_z
        x = verts_x
        y = verts_y
        z = verts_z



        N = len(x)
    
        Sx = sum(x)
        Sy = sum(y)     
        Sz = sum(z)
        Sxx = sum(x*x)    
        Syy = sum(y*y)    
        Szz = sum(z*z)
        Sxy = sum(x*y)
        Sxz = sum(x*z)
        Syz = sum(y*z)
        Sxxx = sum(x*x*x)
        Syyy = sum(y*y*y)
        Szzz = sum(z*z*z)
        Sxyy = sum(x*y*y)
        Sxzz = sum(x*z*z)
        Sxxy = sum(x*x*y)
        Sxxz = sum(x*x*z)
        Syyz = sum(y*y*z)
        Syzz = sum(y*z*z)
        A1 = Sxx +Syy +Szz
        a = 2*Sx*Sx-2*N*Sxx
        b = 2*Sx*Sy-2*N*Sxy
        c = 2*Sx*Sz-2*N*Sxz
        d = -N*(Sxxx +Sxyy +Sxzz)+A1*Sx
        e = b  # this is equal to 2*Sx*Sy-2*N*Sxy
        f = 2*Sy*Sy-2*N*Syy
        g = 2*Sy*Sz-2*N*Syz;
        h = -N*(Sxxy +Syyy +Syzz)+A1*Sy;
        j = c; #this is equal to 2*Sx*Sz-2*N*Sxz
        k = g; # this is equal to 2*Sy*Sz-2*N*Syz;
        l = 2*Sz*Sz-2*N*Szz
        m = -N*(Sxxz +Syyz + Szzz)+A1*Sz;
        delta = a*(f*l - g*k)-e*(b*l-c*k) + j*(b*g-c*f);
        xc = (d*(f*l-g*k) -h*(b*l-c*k) +m*(b*g-c*f))/delta;
        yc = (a*(h*l-m*g) -e*(d*l-m*c) +j*(d*g-h*c))/delta;
        zc = (a*(f*m-h*k) -e*(b*m-d*k) +j*(b*h-d*f))/delta;
        Radius = np.sqrt(xc**2 + yc**2 + zc**2 + (A1 -2*(xc*Sx+yc*Sy+zc*Sz))/N);

        center = [xc, yc, zc]

        ### fitting ends here, output = Radius, xc, yc, zc

        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=Radius, align='WORLD', location=(xc, yc, zc))
        fit_obj_name = obj_name + '_SphereGeoFit'

        ## ensure unique name
        i = 1
        while fit_obj_name in bpy.data.objects:
            fit_obj_name = obj_name + '_SphereGeoFit_' + str(i)
            i += 1

        bpy.context.active_object.name = fit_obj_name

        obj = bpy.data.objects[fit_obj_name]
        
        
        obj.rotation_mode = 'ZYX'  # Change rotation sequence
    


        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['sphere_radius'] =  Radius   #to inform the user what type is created
        obj.id_properties_ui('sphere_radius').update(description = "Radius of the fitted sphere (in m)") 
        

        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)


        return {'FINISHED'}

class FitSphereLSOperator(Operator):
    bl_idname = "mesh.fit_sphere_ls"
    bl_label = "Fit a sphere to a selected mesh, using Jekel least-squares fit"
    bl_description = "Fit a sphere to a selected mesh, using Jekel least-squares fit"
    bl_options = {"UNDO"} #enable undoing
    #based on: https://jekel.me/2015/Least-Squares-Sphere-Fit/, originally from Jekel's PhD thesis
        
    def execute(self, context):
        active_obj = bpy.context.active_object  #should be the mesh
        sel_obj = bpy.context.selected_objects  #should be the only the mesh

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, inputs = verts_x, verts_y, verts_z

        spX = verts_x
        spY = verts_y
        spZ = verts_z

        A = np.zeros((len(spX),4))
        A[:,0] = spX*2
        A[:,1] = spY*2
        A[:,2] = spZ*2
        A[:,3] = 1

        #   Assemble the f matrix
        f = np.zeros((len(spX),1))
        f[:,0] = (spX*spX) + (spY*spY) + (spZ*spZ)
        C, residules, rank, singval = np.linalg.lstsq(A,f,rcond=None)

        #   solve for the radius
        t = (C[0]*C[0])+(C[1]*C[1])+(C[2]*C[2])+C[3]
        Radius = np.sqrt(t)

        center = [C[0], C[1], C[2]]
        ### fitting ends here, output = Radius, center

        
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=5, radius=Radius, align='WORLD', location=(C[0], C[1], C[2]))
        fit_obj_name = obj_name + '_SphereLSFit'

        ## ensure unique name
        i = 1
        while fit_obj_name in bpy.data.objects:
            fit_obj_name = obj_name + '_SphereGeoFit_' + str(i)
            i += 1


        bpy.context.active_object.name = fit_obj_name

        obj = bpy.data.objects[fit_obj_name]

        obj.rotation_mode = 'ZYX'  # Change rotation sequence
    

        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['sphere_radius'] =  Radius   #to inform the user what type is created
        obj.id_properties_ui('sphere_radius').update(description = "Radius of the fitted sphere (in m)") 


        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)    

        return {'FINISHED'}

class FitCylinderOperator(Operator):
    bl_idname = "mesh.fit_cylinder"
    bl_label = "Fit a cylinder to a selected mesh"
    bl_description = "Fit a cylinder to a selected mesh"
    bl_options = {"UNDO"} #enable undoing

    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the mesh
        sel_obj = bpy.context.selected_objects  #should be the only the mesh

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)

        n = len(verts_x)  # Number of points
        points = np.stack((verts_x, verts_y, verts_z), axis=-1)  #reorder for the script input


        ### fitting starts here
        from .fit_cylinder_eberly import (preprocess, G, fit_cylinder)
        minError, C, W, rSqr = fit_cylinder(n, points)  #C is the center, W is the cylinder axis direction, rSqr = radius squared

        ### fitting ends here

        Radius = np.sqrt(rSqr)
        # Ensure W is a unit vector
        W = W / np.linalg.norm(W)  #this is the cylinder axis vector
            
            
        z_axis = Vector((0,0,1))
        quat_diff = z_axis.rotation_difference(Vector(W))  #this gives a unit quaternion for a rotation matrix gRb
        
        from .quaternions import matrix_from_quaternion
        gRb, bRg = matrix_from_quaternion(quat_diff)  #get the rotation matrix

              
        #Compute the desired height of the cylinder by checking the extent of the points along the cylinder axis
            
        #vertices in with respect to cylinder center
        verts_x_C = verts_x - C[0]
        verts_y_C = verts_y - C[1]
        verts_z_C = verts_z - C[2]

        vert_b = [] #vertices in the body-fixed frame of the cylinder

        for v in range(len(verts_x_C)):
            vert_b.append(bRg @ Vector([verts_x_C[v],verts_y_C[v],verts_z_C[v]]))  #rotate the vertex positions to body-fixed frame of the fitted cylinder
            
        vertical_cylinder_coordinates = [v[2] for v in vert_b]  #z is the cylinder axis, so this gives all the z-coordinates of the input data, in the frame of the fitted cylinder
            
        max_height = np.max(vertical_cylinder_coordinates)  #wrt cylinder origin, this is always positive
        min_height = np.min(vertical_cylinder_coordinates)  #wrt cylinder origin ,this is always negative


        cylinder_height = max_height - min_height #in meters

        position_offset_local = (max_height + min_height)/2 # the cylinder's position is not centered around the extremes of the data if the data is not symmetric about the z axis. We will acount for this when setting the position

        position_offset_glob = gRb @ Vector([0, 0, position_offset_local])


        # construct a world matrix for the cylinder
        worldMat = gRb.to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

        for i in range(len(C)):
            
            worldMat[i][3] = C[i] + position_offset_glob[i]  #set the fourth column as the location, including the offeset we just computed

        
        bpy.ops.mesh.primitive_cylinder_add(radius=Radius, depth=cylinder_height, end_fill_type='NGON', calc_uvs=True, enter_editmode=False, align='WORLD')
        fit_obj_name = obj_name + '_CylinderFit'

        ## ensure unique name
        i = 1
        while fit_obj_name in bpy.data.objects:
            fit_obj_name = obj_name + '_SphereGeoFit_' + str(i)
            i += 1

        bpy.context.active_object.name = fit_obj_name
       

        obj = bpy.data.objects[fit_obj_name]

        obj.rotation_mode = 'ZYX'  # Change rotation sequence

        obj.matrix_world = worldMat # set the transformation matrix
        obj.rotation_euler[2] = 0 #Set the Z-angle to zero because the Cylinder is rotationally symmetric about its long axis


        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['cylinder_radius'] =  Radius   #to inform the user what type is created
        obj.id_properties_ui('cylinder_radius').update(description = "Radius of the fitted cylinder (in m)")

        obj['cylinder_height'] =  cylinder_height  #to inform the user what type is created
        obj.id_properties_ui('cylinder_height').update(description = "Height of the fitted cylinder (in m)")  


        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
        return {'FINISHED'}

class FitEllipsoidOperator(Operator):
    bl_idname = "mesh.fit_ellipsoid"
    bl_label = "Fit an ellipsoid to a selected mesh"
    bl_description = "Fit a ellipsoid to a selected mesh"
    bl_options = {"UNDO"} #enable undoing
    #source: https://github.com/marksemple/pyEllipsoid_Fit/blob/master/ellipsoid_fit.py #Python implementation by Mark Semple
    #based on: https://nl.mathworks.com/matlabcentral/fileexchange/24693-ellipsoid-fit #Original Matlab implementation by Yuri Petrov
    #Pasha van Bijlert modified this code to add a check for right-handed coordinate systems
    
    """
    Adapted from MATLAB code by Yury Petrov (2015)
    Original source: https://www.mathworks.com/matlabcentral/fileexchange/24693-ellipsoid-fit
    Original license: BSD 2-Clause

    Copyright (c) 2015, Yury Petrov
    All rights reserved.

    Redistribution and use in source and binary forms, with or without
    modification, are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, this
    list of conditions and the following disclaimer.

    * Redistributions in binary form must reproduce the above copyright notice,
    this list of conditions and the following disclaimer in the documentation
    and/or other materials provided with the distribution.

    THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
    AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
    IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
    DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE
    FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
    DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
    SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
    CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
    OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
    OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
    """


    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the mesh
        sel_obj = bpy.context.selected_objects  #should be the only the mesh

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, input verts x, verts_y, verts_z
        mode = '' #set to 0 if you want 6DOF mode, otherwise it's 9 DOF
        X = verts_x
        Y = verts_y
        Z = verts_z

        # AlGEBRAIC EQUATION FOR ELLIPSOID, from CARTESIAN DATA
        if mode == '':  # 9-DOF MODE
            D = np.array([X * X + Y * Y - 2 * Z * Z,
                        X * X + Z * Z - 2 * Y * Y,
                        2 * X * Y, 2 * X * Z, 2 * Y * Z,
                        2 * X, 2 * Y, 2 * Z,
                        1 + 0 * X]).T

        elif mode == 0:  # 6-DOF MODE (no rotation)
            D = np.array([X * X + Y * Y - 2 * Z * Z,
                        X * X + Z * Z - 2 * Y * Y,
                        2 * X, 2 * Y, 2 * Z,
                        1 + 0 * X]).T

        

        # THE RIGHT-HAND-SIDE OF THE LLSQ PROBLEM
        d2 = np.array([X * X + Y * Y + Z * Z]).T

        # SOLUTION TO NORMAL SYSTEM OF EQUATIONS
        u = np.linalg.solve(D.T.dot(D), D.T.dot(d2))
        # chi2 = (1 - (D.dot(u)) / d2) ^ 2

        # CONVERT BACK TO ALGEBRAIC FORM
        if mode == '':  # 9-DOF-MODE
            a = np.array([u[0] + 1 * u[1] - 1])
            b = np.array([u[0] - 2 * u[1] - 1])
            c = np.array([u[1] - 2 * u[0] - 1])
            v = np.concatenate([a, b, c, u[2:, :]], axis=0).flatten()

        elif mode == 0:  # 6-DOF-MODE
            a = u[0] + 1 * u[1] - 1
            b = u[0] - 2 * u[1] - 1
            c = u[1] - 2 * u[0] - 1
            zs = np.array([0, 0, 0])
            v = np.hstack((a, b, c, zs, u[2:, :].flatten()))

        else:
            pass

        # PUT IN ALGEBRAIC FORM FOR ELLIPSOID
        A = np.array([[v[0], v[3], v[4], v[6]],
                    [v[3], v[1], v[5], v[7]],
                    [v[4], v[5], v[2], v[8]],
                    [v[6], v[7], v[8], v[9]]])

        # FIND CENTRE OF ELLIPSOID
        centre = np.linalg.solve(-A[0:3, 0:3], v[6:9])

        # FORM THE CORRESPONDING TRANSLATION MATRIX
        T = np.eye(4)
        T[3, 0:3] = centre

        # TRANSLATE TO THE CENTRE, ROTATE
        R = T.dot(A).dot(T.T)

        # SOLVE THE EIGENPROBLEM
        evals, evecs = np.linalg.eig(R[0:3, 0:3] / -R[3, 3])
        
        
        # addition by PvB: 
        # check if this forms a right-handed coordinate system:
        # cross(vec_x, vec_y) = vec_z in a right-handed coordinate system.
        # If it is minus vec_z, then the magnitude of their difference will be larger than zero. 
        #In that case we flip the eigenvector direction. Eigenvalue remains unchanged.
        
        vec_x = evecs[:,0]#eigenvectors which will form the rotation matrix.
        vec_y = evecs[:,1] 
        vec_z = evecs[:,2]

        
        threshold = 0.0001

        if np.linalg.norm(np.cross(vec_x,vec_y) - vec_z) > threshold:  
            
            evecs[:,2] = -evecs[:,2]
        
        

        # SORT EIGENVECTORS
        # i = np.argsort(evals)
        # evals = evals[i]
        # evecs = evecs[:, i]
        # evals = evals[::-1]
        # evecs = evecs[::-1]

        # CALCULATE SCALE FACTORS AND SIGNS
        radii = np.sqrt(1 / abs(evals))
        sgns = np.sign(evals)
        radii *= sgns
        ### fitting ends here, output evecs (rotation matrix gRb), centre, radii


        worldMat =Matrix(evecs).to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

        for i in range(len(centre)):
            
            worldMat[i][3] = centre[i]  #set the fourth column as the location


        bpy.ops.mesh.primitive_uv_sphere_add()
        fit_obj_name = obj_name + '_EllipsoidFit'

        ## ensure unique name
        i = 1
        while fit_obj_name in bpy.data.objects:
            fit_obj_name = obj_name + '_SphereGeoFit_' + str(i)
            i += 1

        bpy.context.active_object.name = fit_obj_name
        
        bpy.context.active_object.matrix_world = worldMat
        bpy.context.active_object.scale = Vector(radii)  #initial radius of sphere is 1. radii is xyz radius in meters. Ellipsoid scale factor is radii[r]/sphere_radius, so each radius can just be set as the scale factor
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)

        finalWM = bpy.context.active_object.matrix_world # finalWorldMatrix, which we will reapply after setting the rotation mode
        
        obj = bpy.data.objects[fit_obj_name]

        obj.rotation_mode = 'ZYX'  # Change rotation sequence
        obj.matrix_world = finalWM
        
        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['ellipsoid_radii'] =  radii   #Ellipsoid radii
        obj.id_properties_ui('ellipsoid_radii').update(description = "Radii of the fitted ellipsoid (x, y, z, in m)")

        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
        return {'FINISHED'}

class FitPlaneOperator(Operator):
    bl_idname = "mesh.fit_plane"
    bl_label = "Fit a plane to a selected mesh"
    bl_description = "Fit a plane to a selected mesh"
    bl_options = {"UNDO"} #enable undoing
        
    def execute(self, context):
        
        active_obj = bpy.context.active_object  #should be the mesh
        sel_obj = bpy.context.selected_objects  #should be the only the mesh

         # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one target mesh.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one target mesh")
            return {'FINISHED'}
        
        obj = sel_obj[0]
        obj_name = obj.name

        if obj.type != 'MESH':
            self.report({'ERROR'}, "Selected object with the name '" + obj_name + "' is of the type '" + obj.type + "'. Primitive fitting only works on objects with the type MESH. Operation cancelled")
            return {'FINISHED'}
        
        verts = obj.data.vertices #vertex coordinates in local frame
        obj_global = obj.matrix_world  #global position of mesh

        verts_x = []
        verts_y = []
        verts_z = []


        for vert in verts: #loop through vertices
            vert_glob = obj_global @ vert.co #vertex coordinates in global
            verts_x.append(vert_glob[0]) #global x position 
            verts_y.append(vert_glob[1])
            verts_z.append(vert_glob[2])
            

        verts_x = np.array(verts_x)  #turn into numpy array
        verts_y = np.array(verts_y)
        verts_z = np.array(verts_z)


        ### fitting starts here, inputs verts_x, verts_y, verts_z
        point_data = np.array([verts_x, verts_y, verts_z]).T
        centroid = point_data.mean(axis=0)
        verts_centered = point_data - centroid
        cov_mat = np.cov(verts_centered.T)  #covariance matrix
        eval, evec = np.linalg.eig(cov_mat) #eigen values, eigen vectors. #The eigenvector corresponding to the lowest value is the fitted-plane normal.
        new_order = eval.argsort()[::-1]  #descending order by eigenvalue size. 
        eval = eval[new_order]
        evec = evec[:, new_order] #sorted by eigenvalue size

        threshold = 0.0001
        #evec forms a 3x3 gRb rotation matrix. Check if it is right-handed, and otherwise flip z-axis
        if np.linalg.norm(np.cross(evec[:,0],evec[:,1]) - evec[:,2]) > threshold:  
                
            evec[:,2] = -evec[:,2]

        ### fitting ends here outputs evec (rotation matrix gRb)


        gRb = Matrix(evec)  #local to global rotation matrix

        worldMat =gRb.to_4x4() #matrix_world in blender is a 4x4 transformation matrix, with the first three columns and rows representing the orientation, last column the location, and bottom right diagonal 1

        for i in range(len(centroid)):
            worldMat[i][3] = centroid[i] 
            
        bRg = np.array(gRb).T  #global to local transformation matrix


        verts_local = []

        #find the local position of all the plane points
        for v in range(len(verts_centered)):  #loop through all the vertices, transform to local coordinates
            verts_local.append(bRg @ verts_centered[v,:])
            
        verts_local = np.array(verts_local)

        #this will form the dimensions of our new plane
        x_max = np.max(verts_local[:, 0])
        x_min = np.min(verts_local[:, 0])
        y_max = np.max(verts_local[:, 1])
        y_min = np.min(verts_local[:, 1])    
            
        plane_x_dim = x_max - x_min  #x size in meters
        plane_y_dim = y_max - y_min  #y size in meters

        bpy.ops.mesh.primitive_plane_add(size=1, align='WORLD')

        fit_obj_name = obj.name + '_PlaneFit'

        ## ensure unique name
        i = 1
        while fit_obj_name in bpy.data.objects:
            fit_obj_name = obj_name + '_SphereGeoFit_' + str(i)
            i += 1
            
        bpy.context.active_object.name = fit_obj_name
        bpy.context.active_object.matrix_world = worldMat

        bpy.context.active_object.scale = Vector([plane_x_dim, plane_y_dim, 1])

        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True, properties=False)
        finalWM = bpy.context.active_object.matrix_world # finalWorldMatrix, which we will reapply after setting the rotation mode
        
        

        obj = bpy.data.objects[fit_obj_name]
        obj.rotation_mode = 'ZYX'  # Change rotation sequence
        obj.matrix_world = finalWM #reset the world matrix

        obj['MuSkeMo_type'] = 'GEOM_PRIMITIVE'    #to inform the user what type is created
        obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!") 

        obj['plane_dimensions'] =  [plane_x_dim, plane_y_dim]   #Ellipsoid radii
        obj.id_properties_ui('plane_dimensions').update(description = "Dimensions of the fitted plane (x and y, in m)")
        
        ##### Assign a material
        matname = 'geom_primitive_material'
        color = tuple(bpy.context.scene.muskemo.geom_primitive_color)
        transparency = 0.5
            
               
        if matname not in bpy.data.materials:   #if the material doesn't exist, get it
            from .create_transparent_material_func import create_transparent_material
            create_transparent_material(matname, color, transparency)

        mat = bpy.data.materials[matname]
        obj.data.materials.append(mat)

        ### viewport display color

        obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)
        return {'FINISHED'}
#### Panels

class VIEW3D_PT_mesh_tools_panel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_mesh_tools_panel'
    bl_label = "Mesh tools"  # found at the top of the Panel
    #bl_context = "objectmode"

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        ### selected meshes

        from .selected_objects_panel_row_func import CreateSelectedObjRow

        CreateSelectedObjRow('MESH', layout)
        ###
        
                           
        
        row = self.layout.row()
        row = self.layout.row()
        row.operator("mesh.intersection_checker", text = "Check for mesh intersections")

        if context.mode == 'EDIT_MESH':
            layout.operator(
                "mesh.mesh_from_selection",
                text="New mesh from selected mesh portion"
            )
        else:
            row = layout.row()
            row.enabled = False
            row.operator(
                "mesh.mesh_from_selection",
                text="New mesh from selected mesh portion (Edit Mode)"
            )

class VIEW3D_PT_mesh_alignment_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_mesh_alignment_subpanel'
    bl_label = "Mesh alignment"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_mesh_tools_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo


        row = self.layout.row()

        selected = [x for x in context.selected_objects if x.type == 'MESH']
        if len(selected) != 2:
            layout.label(text="Select exactly 2 meshes")
            return

        # Target = object not chosen as Free
        target_name = [obj.name for obj in selected if obj.name != muskemo.icp_free_obj]
        target_label = target_name[0] if target_name else "N/A"
        
        row = layout.row()
        split = row.split(factor = 1/2)
        split.label(text = "Target Object (stationary):")
        
        box = split.box()
        box.label(text=target_label)
        
        row = layout.row()
        split = row.split(factor = 1/2)
        split.label(text = "Free Object (is moved):")
        split.prop(muskemo, "icp_free_obj", text = '')
        
        row = layout.row()
        row = layout.row()
        row = layout.row()
        layout.operator("mesh.align_icp_point_to_plane", text = 'Align Meshes')


        row = layout.row()
        row = layout.row()
        row = layout.row()
        layout.prop(muskemo, "icp_alignment_mode", expand = True)

        layout.prop(muskemo, "icp_max_iterations")
        layout.prop(muskemo, "icp_tolerance")
        layout.prop(muskemo, "icp_sample_ratio_start")
        layout.prop(muskemo, "icp_sample_ratio_end")
        layout.prop(muskemo, "icp_max_sample_ratio_after")



class VIEW3D_PT_geom_primitive_fitting_subpanel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_geom_primitive_fitting_subpanel'
    bl_label = "Geometric primitive fitting"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_parent_id = "VIEW3D_PT_mesh_tools_panel"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context): 
    
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo


        row = self.layout.row()
        
       
        row = self.layout.row()
        row.operator("mesh.fit_sphere_geometric", text="Fit a sphere (geometric)")
        row.operator("mesh.fit_sphere_ls", text="Fit a sphere (least-squares)")
        
        row = self.layout.row()
        row.operator("mesh.fit_cylinder", text="Fit a cylinder")

        row = self.layout.row()
        row.operator("mesh.fit_ellipsoid", text="Fit an ellipsoid")

        row = self.layout.row()
        row.operator("mesh.fit_plane", text="Fit a plane")
