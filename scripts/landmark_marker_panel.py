import bpy

from bpy.types import (Panel,
                        Operator)


from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed

class CreateLandmarkOperator(Operator):
    bl_idname = "landmark.create_landmark"
    bl_label = "Creates a landmark at the 3D cursor location"  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Creates a landmark at the 3D cursor location"
    
    def execute(self, context):

        muskemo = bpy.context.scene.muskemo

        landmark_name = muskemo.landmark_name
        landmark_radius = muskemo.landmark_radius #in meters

        colname = muskemo.landmark_collection #name for the collection that will contain the landmarks

        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the landmarks

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
            
        #Make sure the landmarks collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]

        active_obj = bpy.context.active_object  #should be the body that you want to parent the point to
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to

        sel_obj_backup = sel_obj.copy() #store this to restore the selected object state after the operator is finished
         #Ensure unique name
        if landmark_name in bpy.data.objects:
            self.report({'ERROR'}, "An object with the name '" + landmark_name + "' already exists in the scene. Choose a unique (unused) name for the new LANDMARK. Operation cancelled.")
            return {'FINISHED'}
        
        if not landmark_name:
            self.report({'ERROR'}, "You didn't input a LANDMARK name. Choose a unique (unused) name for the new LANDMARK. Operation cancelled.")
            return {'FINISHED'}

        if len(sel_obj)<1:
            self.report({'ERROR'}, "Landmarks must be parented to a Mesh or a BODY, select one that you would like to parent the landmark to. Operation cancelled")
            return {'FINISHED'}

        if len(sel_obj)>1:
            self.report({'ERROR'}, "Landmarks must be parented to a single mesh or BODY, select one you would like to parent the landmark to. Operation cancelled")
            return {'FINISHED'}
        
        target_obj = sel_obj[0]

        create_parent_body = False #if we encounter a mesh without a parent body, this becomes true and we create one

        if target_obj.get('MuSkeMo_type'): #if it has a MuSkeMo_type, and thus was created by MuSkeMo 

            if target_obj['MuSkeMo_type'] not in ('BODY', 'GEOMETRY'): #if it's not a BODY or a GEOMETRY

                self.report({'ERROR'}, "Selected object '" + target_obj.name + "' is not a BODY or a GEOMETRY (mesh attached to a body). Landmarks must be parented to BODIES or GEOMETRIES. Operation cancelled")
                return {'FINISHED'}
            
            elif target_obj['MuSkeMo_type'] == 'GEOMETRY':
                self.report({'WARNING'}, "The landmark was attached to the target mesh's parent body '" + target_obj.name + "_pbody'.")
                
                target_obj = target_obj.parent



        else: #if it's not a MuSkeMo BODY, it can still get a landmark if it is a Mesh. If the Mesh has no parent body, we create a new body for this purpose.

            if target_obj.type != 'MESH': #if it's not a mesh, throw an error and don't create the landmark

                self.report({'ERROR'}, "Selected object '" + target_obj.name + "' is not a BODY or a mesh. Landmarks must be parented to BODIES or meshes. Operation cancelled")
                return {'FINISHED'}
            
            elif not target_obj.parent: #if the mesh has no parent
                create_parent_body = True
                self.report({'WARNING'}, "A parent BODY was created for the selected mesh with the '" + target_obj.name + "_pbody' and placed at the origin. Landmarks will be attached to that newly created body")
                
            elif target_obj.parent.get('MuSkeMo_type')!= 'BODY': #if target mesh's parent object is not a  BODY, throw an error
                self.report({'ERROR'}, "Selected mesh '" + target_obj.name + "' has a parent that is not a BODY. You must remove the mesh's parent before trying again. Operation cancelled")
                return {'FINISHED'}
            
            else: #target meshes's parent is a MuSkeMo body, and we make that the target object.
                self.report({'WARNING'}, "The landmark was attached to the target mesh's parent body '" + target_obj.name + "_pbody'.")
                
                target_obj = target_obj.parent

        #if we trigger the creation of a parent body for an unparented mesh, we create a new body, and assign the target_obj
        #as visual geometry, and make the parent body the new target_obj
        if create_parent_body: 

            from .create_body_func import create_body

            pbodyname = target_obj.name + '_pbody'

            create_body(name= pbodyname, size = muskemo.axes_size, self = self)

            target_obj.select_set(True) #select the mesh
            target_obj = bpy.data.objects[pbodyname] #set the parent body as the target_obj
            target_obj.select_set(True) #select the parent body. Now a BODY and a mesh are selected
            bpy.ops.body.attach_visual_geometry() #attach visual geometry



        #### All of this should be moved over to a separate creation function

        target_loc = bpy.context.scene.cursor.location
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=landmark_radius, enter_editmode=False, align='WORLD', location = target_loc) #create a sphere
        bpy.context.object.name = landmark_name #set the name
        bpy.context.object.data.name = landmark_name #set the name of the object data
        
        landmark_name = bpy.context.object.name ### because duplicate names get automatically numbered in Blender
        bpy.context.object['MuSkeMo_type'] = 'LANDMARK'    #to inform the user what type is created
        bpy.context.object.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  
        
        bpy.ops.object.select_all(action='DESELECT')



        obj = bpy.data.objects[landmark_name]
        
        obj.parent = target_obj
        
        #this undoes the transformation after parenting
        obj.matrix_parent_inverse = target_obj.matrix_world.inverted()


        #restore selection status
        target_obj.select_set(True)
                    

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
        
        
        ### Empty the landmark name input

        muskemo.landmark_name = ''

        #Restore selection state
        sel_obj_backup[0].select_set(True)
        return {'FINISHED'}
            

class VIEW3D_PT_landmark_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’

    bl_context = "objectmode"
    bl_idname = 'VIEW3D_PT_landmark_panel'
    
    
    bl_label = "Landmark & marker panel"  # found at the top of the Panel
    
    
    bl_options = {'DEFAULT_CLOSED'}
    

    def draw(self, context):
       
        
        scene = context.scene
        muskemo = scene.muskemo

        # Row for landmark name
        row = self.layout.row()
        split = row.split(factor=0.5)
        split.label(text="Landmark Name")
        split.prop(muskemo, "landmark_name", text="")

        # Row for landmark collection
        row = self.layout.row()
        split = row.split(factor=0.5)
        split.label(text="Landmark Collection")
        split.prop(muskemo, "landmark_collection", text="")


        self.layout.row()
        row = self.layout.row()
        row.operator("landmark.create_landmark", text="Create landmark")
       

        self.layout.row()
        row = self.layout.row()
        row.prop(muskemo, "landmark_radius")