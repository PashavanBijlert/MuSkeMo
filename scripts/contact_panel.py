import bpy

from bpy.types import (Panel,
                        Operator)

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed

from math import nan

class CreateContactOperator(Operator):
    
    bl_idname = "contact.create_contact"
    bl_label = "Creates a new contact sphere at the 3D cursor location"
    bl_description = "Creates a new contact sphere at the 3D cursor location"

    def execute(self,context):
        
        rad = bpy.context.scene.muskemo.contact_radius #sphere radius, in meters
        name = bpy.context.scene.muskemo.contact_name  #name of the object
        
        colname = bpy.context.scene.muskemo.contact_collection #name for the collection that will contain the contacts
        
        #check if the collection name exists, and if not create it
        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled contacts

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
        
        #Make sure the "contacts" collection is active
        bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[colname]
        
        ## create the actual contact
        target_pos = bpy.context.scene.cursor.location  #3D cursor location is the target position of the contact
        
        from .create_contact_func import create_contact

        create_contact(name = name, radius = rad, pos_in_global = target_pos)
        
        return {'FINISHED'}


class AssignContactParentOperator(Operator):
    bl_idname = "contact.assign_parent_body"
    bl_label = "Assigns a parent body to 1+ contact spheres. Select both the parent body and the contact sphere(s), then press the button."
    bl_description = "Assigns a parent body to 1+ contact spheres. Select both the parent body and the contact sphere(s), then press the button."
   
    def execute(self, context):
        
        contact_name = bpy.context.scene.muskemo.contact_name
        
       
        sel_obj = bpy.context.selected_objects  #should be the parent body and the contact
        
        colname = bpy.context.scene.muskemo.contact_collection
        bodycolname = bpy.context.scene.muskemo.body_collection
        try: bpy.data.objects[contact_name]  #check if the contact exists
        
        except:  #throw an error if the body doesn't exist
            self.report({'ERROR'}, "Contact with the name '" + contact_name + "' does not exist yet, create it first")
            return {'FINISHED'}
        
        
                
        # throw an error if no objects are selected     
        if (len(sel_obj) < 2):
            self.report({'ERROR'}, "Too few objects selected. Select the parent body and the target contact.")
            return {'FINISHED'}
        
                
        target_contacts = [s_obj for s_obj in sel_obj if s_obj['MuSkeMo_type'] == 'CONTACT']
        if (len(target_contacts) < 1):
            self.report({'ERROR'}, "You did not select any contact spheres. Operation cancelled.")
            return {'FINISHED'}

        
        non_contact_objects = [s_obj for s_obj in sel_obj if s_obj not in target_contacts]  #get the object that's not the contact
        if len(non_contact_objects)<1:
            self.report({'ERROR'}, "You only selected contact spheres. You must also select one target body. Operation cancelled.")
            return {'FINISHED'}
        
        if len(non_contact_objects)>1:
            self.report({'ERROR'}, "You selected more than one object that is not a contact sphere. You must select only contact spheres and one target body. Operation cancelled.")
            return {'FINISHED'}
        
        parent_body = non_contact_objects[0] #if len is 1

        if parent_body['MuSkeMo_type'] != 'BODY':
            self.report({'ERROR'}, "You did not select a target body. Operation cancelled.")
            return {'FINISHED'}
        
        
            
        ### if none of the previous scenarios triggered an error, set the parent body
        for contact in target_contacts:
            contact.parent = parent_body
                
            #this undoes the transformation after parenting
            contact.matrix_parent_inverse = parent_body.matrix_world.inverted()

            contact['parent_body'] = parent_body.name


            ### check if parent_body has a local frame, and if yes, compute contact location in parent frame 
            if parent_body['local_frame'] != 'not_assigned':  #if there is a local reference frame assigned, compute location and rotation in parent
                
                frame = bpy.data.objects[parent_body['local_frame']]

                gRb = frame.matrix_world.to_3x3()  #rotation matrix of the frame, local to global
                bRg = gRb.copy()
                bRg.transpose()
        
                frame_or_g = frame.matrix_world.translation                 
                contact_pos_g = contact.matrix_world.translation #location of the contact
                contact_pos_in_parent = bRg @ (contact_pos_g - frame_or_g) #location in parent of contact
                contact['pos_in_parent_frame'] = contact_pos_in_parent
               

            
        return {'FINISHED'}
    
class ClearContactParentOperator(Operator):
    bl_idname = "contact.clear_parent_body"
    bl_label = "Clears the parent body assigned to selected contact sphere(s). Select the target contact(s), then press the button."
    bl_description = "Clears the parent body assigned to selected contact sphere(s). Select the target contact(s), then press the button."
    
    def execute(self, context):
        
        sel_obj = bpy.context.selected_objects  #should be the parent body and the contact

        # throw an error if no objects are selected     
        if (len(sel_obj) == 0):
            self.report({'ERROR'}, "No contact selected. Select the target contact(s) and try again.")
            return {'FINISHED'}
            

        for contact in sel_obj:
            
            if contact['MuSkeMo_type'] != 'CONTACT':
                self.report({'ERROR'}, "Object with the name '" + contact.name + "' is not a contact sphere. Skipping this object.")
                continue

            try: contact.parent.name
            
            except: #throw an error if the contact has no parent
                self.report({'ERROR'}, "Contact with the name '" + contact.name + "' does not have a parent body. Skipping this contact.")
                continue
            
                                
            ### if none of the previous scenarios triggered an error, clear the parent body
            
            
            #clear the parent, without moving the contact
            parented_worldmatrix = contact.matrix_world.copy() 
            contact.parent = None
            contact.matrix_world = parented_worldmatrix   
            
            contact['parent_body'] = 'not_assigned'

            contact['pos_in_parent_frame'] = [nan, nan, nan]
            


        return {'FINISHED'}

class VIEW3D_PT_contact_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’

    bl_context = "objectmode"
    bl_idname = 'VIEW3D_PT_contact_panel'
    
    
    bl_label = "Contact sphere panel"  # found at the top of the Panel
    
    
    bl_options = {'DEFAULT_CLOSED'}
    

    def draw(self, context):

        scene = context.scene
        muskemo = scene.muskemo

        row = self.layout.row()
        row.prop(muskemo, "contact_collection")
        self.layout.row()


        row = self.layout.row()
        row.prop(muskemo, "contact_name")
        
        row = self.layout.row()
        row.operator("contact.create_contact", text = 'Create contact sphere')

        row = self.layout.row()
        row.operator("contact.assign_parent_body", text = 'Assign parent body')

        row.operator("contact.clear_parent_body", text = 'Clear parent body')

        row = self.layout.row()
        row.prop(muskemo, "contact_radius")



