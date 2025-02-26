# give Python access to Blender's functionality
import bpy


from bpy.types import (Panel,
                        Operator,
                        )


from .. import VIEW3D_PT_MuSkeMo  #the class in which all panels will be placed

#### Operators

class SetRecommendedNavigationSettingsOperator(Operator):
    bl_idname = "muskemo.set_recommended_navigation_settings"
    bl_label = "Set recommended Blender navigation settings for using MuSkeMo with y-up models. Sets view rotation to trackball, and rotate around selected."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Set recommended Blender navigation settings for using MuSkeMo with y-up models. Sets view rotation to trackball, and rotate around selected."
    
    def execute(self, context):

        bpy.context.preferences.inputs.view_rotate_method = 'TRACKBALL' #set rotation method to trackball
        bpy.context.preferences.inputs.use_rotate_around_active = True  #set rotate around selected
        
        bpy.ops.wm.save_userpref() #save these settings

       
        return {'FINISHED'}
    

class SetChildVisibilityInOutlinerOperator(Operator):
    bl_idname = "muskemo.set_child_visibility_outliner"
    bl_label = "Turns off the object children filter in the outliner, so that parented objects remain visible in their respective collections."  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Turns off the object children filter in the outliner, so that parented objects remain visible in their respective collections."
    
    def execute(self, context):

        
        #Toggle object children filter off in all outliners
        for screen in bpy.data.screens:
            # Loop through all the areas in each screen
            for area in screen.areas:
                if area.type == 'OUTLINER':  # Check if the area is an Outliner
                    for space in area.spaces:
                        if space.type == 'OUTLINER':
                            # Set 'use_filter_children' to False
                            space.use_filter_children = False

        return {'FINISHED'}    

#### The panels

class VIEW3D_PT_global_settings_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’
    #Multiple inheritance, body_panel as a class inherits attributes from MuSkeMo class, but also from the "Panel" class, turning this into a panel
    #This is the first (main) subpanel in the parent class VIEW3D_PT_MuSkeMo.
    #The first layer of panels doesn't need a bl_parentid, but if you want multiple, you will need a 'bl_idname' for each.
    #Subpanels to this one need to be placed under VIEW3D_PT_MuSkeMo, but using the VIEW3D_PT_body_panel as the parentid
    bl_idname = 'VIEW3D_PT_global_settings_panel'
    
    
    #bl_category = "Body panel"  # found in the Sidebar
    bl_label = "Global Settings"  # found at the top of the Panel
    bl_context = "objectmode"
    
    bl_options = {'DEFAULT_CLOSED'}
    
    #bl_options = {'HEADER_LAYOUT_EXPAND'}

    def draw(self, context):
        """define the layout of the panel"""
        
        row = self.layout.row()
        row.operator("muskemo.set_recommended_navigation_settings", text = 'Set recommended navigation settings')

        row = self.layout.row()
        row.operator("muskemo.set_child_visibility_outliner", text = 'Set object children visibility')

