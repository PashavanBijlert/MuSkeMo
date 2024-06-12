import bpy

from bpy.types import (Panel,
                        Operator)

from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed



class CreateContactOperator(Operator):
    
    bl_idname = "contact.create_contact"
    bl_label = "Select a target body"
    bl_description = "Assign the selected landmark as the origin of the frame."

    def execute(self,context):

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
        self.layout.row()

