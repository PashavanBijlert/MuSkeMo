

# give Python access to Blender's functionality
import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )


import numpy as np

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed
    
class CreateNewJointOperator(Operator):
    bl_idname = "joint.create_new_joint"
    bl_label = "creates a new joint at the origin"
    bl_description = "creates a new joint at the origin"
    
    def execute(self,context):
        
        rad = bpy.context.scene.muskemo.jointsphere_size #axis length, in meters
        name = bpy.context.scene.muskemo.jointname  #name of the object
        
        colname = bpy.context.scene.muskemo.joint_collection #name for the collection that will contain the hulls
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the "joints" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]
        
        
        try: bpy.data.objects[name]
        
        except:
            
            bpy.ops.mesh.primitive_uv_sphere_add(radius=rad, enter_editmode=False, align='WORLD', location = (0,0,0)) #create a sphere
            bpy.context.object.name = name #set the name
            bpy.context.object.data.name = name #set the name of the object data
            bpy.context.object.rotation_mode = 'ZYX'    #change rotation sequence
            bpy.ops.object.select_all(action='DESELECT')
                    
            
            
                
            bpy.context.object['coordinate_Tx'] = ''       #add coordinate
            bpy.context.object.id_properties_ui('coordinate_Tx').update(description = 'name of the Translational x coordinate')
            
            bpy.context.object['coordinate_Ty'] = ''       #add coordinate
            bpy.context.object.id_properties_ui('coordinate_Ty').update(description = 'name of the Translational y coordinate')
            
            bpy.context.object['coordinate_Tz'] = ''       #add coordinate
            bpy.context.object.id_properties_ui('coordinate_Tz').update(description = 'name of the Translational z coordinate')
            
            bpy.context.object['coordinate_Rx'] = ''       #add coordinate
            bpy.context.object.id_properties_ui('coordinate_Rx').update(description = 'name of the Rotational x coordinate')
            
            bpy.context.object['coordinate_Ry'] = ''       #add coordinate
            bpy.context.object.id_properties_ui('coordinate_Ry').update(description = 'name of the Rotational y coordinate')
            
            bpy.context.object['coordinate_Rz'] = ''       #add coordinate
            bpy.context.object.id_properties_ui('coordinate_Rz').update(description = 'name of the Rotational z coordinate')


            bpy.context.object['MuSkeMo_type'] = 'JOINT'    #to inform the user what type is created
            bpy.context.object.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  
            
            
            bpy.ops.object.select_all(action='DESELECT')
        
        else:
            
            self.report({'ERROR'}, "Joint with the name " + name + " already exists, please choose a different name")
        
        
        return {'FINISHED'}


class ReflectRightsideJointsOperator(Operator):
    bl_idname = "joint.reflect_rightside_joints"
    bl_label = "Duplicates and reflects bodies across XY plane if they contain '_r' in the name. Automatically mirrors transforms COM and MOI as well."
    bl_description = "Duplicates and reflects bodies across XY plane if they contain '_r' in the name. Automatically mirrors transforms COM and MOI as well."
    
    def execute(self, context):
        colname = bpy.context.scene.muskemo.joint_collection

        collection = bpy.data.collections[colname]


        for obj in (obj for obj in collection.objects if '_r' in obj.name):  #for all the objects if '_r' is in the name
            
            if obj.name.replace('_r','_l') not in (obj.name for obj in collection.objects):  #make sure a left side doesn't already exist
            
            
                new_obj = obj.copy()  #copy object
                new_obj.data = obj.data.copy() #copy object data
                new_obj.name = obj.name.replace('_r','_l') #rename to left
                
                collection.objects.link(new_obj)  #add to Muscles collection
                
                for point in new_obj.data.splines[0].points:   #reflect each point about z
                    point.co = point.co*Vector((1,1,-1,1))
                    
                for mod in new_obj.modifiers: #loop through all modifiers
                    mod.object = bpy.data.objects[mod.object.name.replace('_r','_l')]

        return {'FINISHED'}
    
class UpdateCoordinateNamesOperator(Operator):
    bl_idname = "joint.update_coordinate_names"
    bl_label = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    bl_description = "Updates the display location of the body, using the COM property that was previously assigned (useful if you manually edit the COM property)"
    
    def execute(self, context):
        
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if it doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            
        else:
            
            sel_obj = bpy.context.selected_objects  
            
            #ensure that only the relevant body is selected, or no bodies are selected. The operations will use the user input body name, so this prevents that the user selects a different body and expects the button to operate on that body
            if (len(sel_obj) == 0) or ((len(sel_obj) == 1) and sel_obj[0].name == joint_name):  #if no objects are selected, or the only selected object is also the correct body
                
                obj = bpy.data.objects[joint_name]
                
                obj['coordinate_Tx']=bpy.context.scene.muskemo.coor_Tx
                obj['coordinate_Ty']=bpy.context.scene.muskemo.coor_Ty
                obj['coordinate_Tz']=bpy.context.scene.muskemo.coor_Tz
                obj['coordinate_Rx']=bpy.context.scene.muskemo.coor_Rx
                obj['coordinate_Ry']=bpy.context.scene.muskemo.coor_Ry
                obj['coordinate_Rz']=bpy.context.scene.muskemo.coor_Rz
                  
               
                
                            
        
        
            else:
                self.report({'ERROR'}, "Joint with the name '" + joint_name + "' is not the (only) selected joint. Operation cancelled, please either deselect all objects or only select the '" + joint_name + "' joint. This button operates on the joint that corresponds to the user (text) input joint name")
        
        return {'FINISHED'}    
    
class AssignParentBodyOperator(Operator):
    bl_idname = "joint.assign_parent_body"
    bl_label = "Assigns a parent body to a joint. Select both the parent body and the joint, then press the button."
    bl_description = "Assigns a parent body to a joint. Select both the parent body and the joint, then press the button."
   
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the parent body and the joint
        
        colname = bpy.context.scene.muskemo.joint_collection
        bodycolname = bpy.context.scene.muskemo.body_collection
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the parent body and the target joint.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select the parent body and the target joint.")
            return {'FINISHED'}
        
        if bpy.data.objects[joint_name] not in sel_obj:
            self.report({'ERROR'}, "Neither of the selected objects is the target joint. Selected joint and joint_name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        parent_body = [s_obj for s_obj in sel_obj if s_obj.name not in bpy.data.collections[colname].objects][0]  #get the object that's not the joint
        
        
        if parent_body.name not in bpy.data.collections[bodycolname].objects:
            self.report({'ERROR'}, "The parent body is not in the '" + bodycolname + "' collection. Make sure one of the two selected objects is a 'Body' as created by the bodies panel")
            return {'FINISHED'}
            
        ### if none of the previous scenarios triggered an error, set the parent body
        
        bpy.data.objects[joint_name].parent = parent_body
            
        #this undoes the transformation after parenting
        bpy.data.objects[joint_name].matrix_parent_inverse = parent_body.matrix_world.inverted()
            
        return {'FINISHED'}
        
class AssignChildBodyOperator(Operator):
    bl_idname = "joint.assign_child_body"
    bl_label = "Assigns a child body to a joint. Select both the child body and the joint, then press the button."
    bl_description = "Assigns a child body to a joint. Select both the child body and the joint, then press the button."
   
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        colname = bpy.context.scene.muskemo.joint_collection
        bodycolname = bpy.context.scene.muskemo.body_collection

        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the parent body and the joint
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the child body and the target joint.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 2):
            self.report({'ERROR'}, "Too many objects selected. Select the child body and the target joint.")
            return {'FINISHED'}
        
        if bpy.data.objects[joint_name] not in sel_obj:
            self.report({'ERROR'}, "Neither of the selected objects is the target joint. Selected joint and joint_name (input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        child_body = [s_obj for s_obj in sel_obj if s_obj.name not in bpy.data.collections[colname].objects][0]  #get the object that's not the joint
        
        
        if child_body.name not in bpy.data.collections[bodycolname].objects:
            self.report({'ERROR'}, "The child body is not in the '" + bodycolname + "' collection. Make sure one of the two selected objects is a 'Body' as created by the bodies panel")
            return {'FINISHED'}

        if len(bpy.data.objects[joint_name].children)>0:
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' already has a child body. Clear it first, before assigning a new one")
            return {'FINISHED'}


        ### if none of the previous scenarios triggered an error, set the parent body
        
        child_body.parent = bpy.data.objects[joint_name]
        
            
        #this undoes the transformation after parenting
        child_body.matrix_parent_inverse = bpy.data.objects[joint_name].matrix_world.inverted()
            
        #parented_wm = childObject.matrix_world.copy()
        #childObject.parent = None
        #childObject.matrix_world = parented_wm         
         
            
        return {'FINISHED'}
    
class ClearParentBodyOperator(bpy.types.Operator):
    bl_idname = "joint.clear_parent_body"
    bl_label = "Clears the parent body assigned to a joint. Select the joint, then press the button."
    bl_description = "Clears the parent body assigned to a joint. Select the joint, then press the button."
    
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname
        
        colname = bpy.context.scene.muskemo.joint_collection


        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        try: bpy.data.objects[joint_name].parent.name
        
        except: #throw an error if the joint has no parent
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not have a parent body")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No joint selected. Select the target joint and try again.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target joint.")
            return {'FINISHED'}
        
        if bpy.data.objects[joint_name].name != active_obj.name:
            self.report({'ERROR'}, "Selected joint and joint_name (text input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if bpy.data.objects[joint_name].name not in bpy.data.collections[colname].objects:
            self.report({'ERROR'}, "Selected object is not in the '" + colname + "' collection. Make sure you have selected a joint in that collection.")
            return {'FINISHED'}
        
        
                
        ### if none of the previous scenarios triggered an error, clear the parent body
        
        
        #clear the parent, without moving the joint
        parented_worldmatrix = bpy.data.objects[joint_name].matrix_world.copy() 
        bpy.data.objects[joint_name].parent = None
        bpy.data.objects[joint_name].matrix_world = parented_worldmatrix   
        
        return {'FINISHED'}
    
    
class ClearChildBodyOperator(bpy.types.Operator):
    bl_idname = "joint.clear_child_body"
    bl_label = "Clears the child body assigned to a joint. Select the joint, then press the button."
    bl_description = "Clears the child body assigned to a joint. Select the joint, then press the button."
    
    def execute(self, context):
        
        joint_name = bpy.context.scene.muskemo.jointname
        colname = bpy.context.scene.muskemo.joint_collection

        active_obj = bpy.context.active_object  #should be the joint
        sel_obj = bpy.context.selected_objects  #should be the only the joint
        
        
        try: bpy.data.objects[joint_name]  #check if the body exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        if len(bpy.data.objects[joint_name].children)==0:
            self.report({'ERROR'}, "Joint with the name '" + joint_name + "' does not have a child body")
            return {'FINISHED'}

        
        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No joint selected. Select the target joint and try again.")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Only select the target joint.")
            return {'FINISHED'}
        
        if bpy.data.objects[joint_name].name != active_obj.name:
            self.report({'ERROR'}, "Selected joint and joint_name (text input at the top) must correspond to prevent ambiguity. Operation cancelled.")
            return {'FINISHED'}
        
        if bpy.data.objects[joint_name].name not in bpy.data.collections[colname].objects:
            self.report({'ERROR'}, "Selected object is not in the '" + colname + "' collection. Make sure you have selected a joint in that collection.")
            return {'FINISHED'}
        
        
                
        ### if none of the previous scenarios triggered an error, clear the child body
        
        child_body = bpy.data.objects[joint_name].children[0]
        #clear the parent, without moving the joint
        parented_worldmatrix =child_body.matrix_world.copy() 
        child_body.parent = None
        child_body.matrix_world = parented_worldmatrix   
        
        return {'FINISHED'}        

class VIEW3D_PT_joint_panel(VIEW3D_PT_MuSkeMo,Panel):  # class naming convention ‘CATEGORY_PT_name’
    #This panel inherits from the class VIEW3D_PT_MuSkeMo


    bl_idname = 'VIEW3D_PT_joint_panel'
    bl_label = "Joint panel"  # found at the top of the Panel
    bl_context = "objectmode"

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        
        
        ## user input joint name    
        layout.prop(muskemo, "jointname")
        row = self.layout.row()
       
        row.prop(muskemo, "joint_collection")
                    
        
        row = self.layout.row()


        row.label(text ="Joint centers are initially placed in the world origin")
                
        ## Create new joint
        row = self.layout.row()
        row.operator("joint.create_new_joint", text="Create new joint")
        row = self.layout.row()
        row = self.layout.row()

        ## assign or clear parent and child
        row = self.layout.row()
        row.operator("joint.assign_parent_body", text="Assign parent body")
        row.operator("joint.assign_child_body", text="Assign child body")
        row = self.layout.row()
        row.operator("joint.clear_parent_body", text="Clear parent body")
        row.operator("joint.clear_child_body", text="Clear child body")
        
        row = self.layout.row()
        row.label(text ="Coordinate names (optional)")
        ## user input coordinate names    
        
        layout.prop(muskemo, "coor_Rx")
        layout.prop(muskemo, "coor_Ry")
        layout.prop(muskemo, "coor_Rz")
        layout.prop(muskemo, "coor_Tx")
        layout.prop(muskemo, "coor_Ty")
        layout.prop(muskemo, "coor_Tz")
        
        
        
         
       
         
        
        
    
        row = self.layout.row()
        row.operator("joint.update_coordinate_names", text="Update coordinate names")
        
         
        
        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.operator("joint.reflect_rightside_joints", text="Reflect right-side joints")
        
        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.prop(muskemo, "jointsphere_size")
        
        
            
        #row = self.layout.row()
        #self.layout.prop(muskemo, "musclename_string")


