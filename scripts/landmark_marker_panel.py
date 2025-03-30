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

         #Ensure unique name
        if landmark_name in bpy.data.objects:
            self.report({'ERROR'}, "An object with the name '" + landmark_name + "' already exists in the scene. Choose a unique (unused) name for the new LANDMARK. Operation cancelled.")
            return {'FINISHED'}

        if len(sel_obj)<1:
            self.report({'ERROR'}, "Landmarks must be parented to a mesh, select the mesh you would like to parent the landmark to. Operation cancelled")
            return {'FINISHED'}

        if len(sel_obj)>1:
            self.report({'ERROR'}, "Landmarks must be parented to a single mesh, select one mesh you would like to parent the landmark to. Operation cancelled")
            return {'FINISHED'}
        
        target_mesh = sel_obj[0]

        if target_mesh.type != 'MESH':
            self.report({'ERROR'}, "Selected object '" + target_mesh.name + "' is not a MESH. Landmarks must be parented to meshes. Operation cancelled")
            return {'FINISHED'}




        target_loc = bpy.context.scene.cursor.location
        
        bpy.ops.mesh.primitive_uv_sphere_add(radius=landmark_radius, enter_editmode=False, align='WORLD', location = target_loc) #create a sphere
        bpy.context.object.name = landmark_name #set the name
        bpy.context.object.data.name = landmark_name #set the name of the object data
        
        landmark_name = bpy.context.object.name ### because duplicate names get automatically numbered in Blender
        bpy.context.object['MuSkeMo_type'] = 'LANDMARK'    #to inform the user what type is created
        bpy.context.object.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  
        
        bpy.ops.object.select_all(action='DESELECT')



        obj = bpy.data.objects[landmark_name]
        
        obj.parent = target_mesh
        
        #this undoes the transformation after parenting
        obj.matrix_parent_inverse = target_mesh.matrix_world.inverted()


        #restore selection status
        target_mesh.select_set(True)
                    

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