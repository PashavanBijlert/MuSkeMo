
# give Python access to Blender's functionality
import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

from .. import VIEW3D_PT_MuSkeMo


class AddMusclepointOperator(Operator):
    bl_idname = "muscle.add_muscle_point"
    bl_label = "Adds a viapoint to the muscle (or creates a new muscle)"  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Adds a viapoint to the muscle (or creates a new muscle)"
    
    def execute(self, context):


        muscle_name = bpy.context.scene.muskemo.musclename

        colname = bpy.context.scene.muskemo.muscle_collection #name for the collection that will contain the hulls

        if colname not in bpy.data.collections:
            bpy.data.collections.new(colname)
            
        coll = bpy.data.collections[colname] #Collection which will recieve the scaled  hulls

        if colname not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
            bpy.context.scene.collection.children.link(coll)     #add it to the scene
            


        active_obj = bpy.context.active_object  #should be the body that you want to parent the point to
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to


        for obj in sel_obj:
            obj.select_set(False)
            
            



        try: bpy.data.objects[muscle_name]  #throws an error if the muscle doesn't exist, creates it under except

        except:
            
            curve = bpy.data.curves.new(muscle_name,'CURVE')
            curve.dimensions = '3D'
            spline = curve.splines.new(type='POLY')
            spline.points[0].co = bpy.context.scene.cursor.location.to_4d()
            obj = bpy.data.objects.new(muscle_name, curve)
            bpy.data.collections[colname].objects.link(obj)
                
            ## define MuSkeMo type
            obj['MuSkeMo_type'] = 'MUSCLE'    #to inform the user what type is created
            obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")  


            ##
            obj['F_max'] = 0    #In Newtons
            obj.id_properties_ui('F_max').update(description = "Maximal isometric force of the muscle fiber (in N)")

            obj['pennation_angle'] = 0    #In degrees
            obj.id_properties_ui('[pennation_angle').update(description = "Pennation angle (in degrees)")

            obj['optimal_fiber_length'] = 0    #In meters
            obj.id_properties_ui('optimal_fiber_length').update(description = "Optimal fiber length (in m)")

            obj['tendon_length'] = 0    #In meters
            obj.id_properties_ui('tendon_length').update(description = "Tendon length (in m)")




            ### hook point to body
            
            curve = bpy.data.objects[muscle_name]
            curve.select_set(True)
            bpy.context.view_layer.objects.active = curve  #make curve the active object
                
                    
            modname = 'hook' + str(0) + '_' + active_obj.name  #remember that active_obj is the body, not the current active object that was changed above within this script
            obj = curve
                    
            obj.modifiers.new(name=modname, type='HOOK')
            obj.modifiers[modname].object = active_obj #remember that active_obj is the body, not the current active object that was changed above within this script       
            
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.select_all(action='DESELECT') 
            
            curve.data.splines[0].points[0].select = True
            
          
            bpy.ops.object.hook_assign(modifier = modname)
            
            bpy.ops.curve.select_all(action='DESELECT') 
            
            #for point in spline.points:
            #    point.select = False
            
            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            
            
        else: #if the muscle does exist, add a point at the end
            
                    
            curve = bpy.data.objects[muscle_name]
            
            curve.select_set(True)
            bpy.context.view_layer.objects.active = curve  #make curve the active object
            
            

            spline = curve.data.splines[0]
            spline.points.add(1) 

            last_point =  len(spline.points)-1

            spline.points[last_point].co = bpy.context.scene.cursor.location.to_4d()  ## change to user input using mouse
                
            ### hook point to body
                
            modname = 'hook' + str(last_point) + '_' + active_obj.name #remember that active_obj is the body, not the current active object that was changed above within this script
            obj = curve
                    
            obj.modifiers.new(name=modname, type='HOOK')
            obj.modifiers[modname].object = active_obj        
            
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.curve.select_all(action='DESELECT') 
            
            curve.data.splines[0].points[last_point].select = True
            
          
            bpy.ops.object.hook_assign(modifier = modname)
            
            #bpy.ops.curve.select_all(action='DESELECT') 
            
            for point in spline.points:
                point.select = False
            
            
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.object.select_all(action='DESELECT')
            
                
                
                
        # restore saved state of selection
        bpy.context.view_layer.objects.active = active_obj
        for obj in sel_obj:
            obj.select_set(True)
        
        return {'FINISHED'}


class ReflectRightsideMusclesOperator(Operator):
    bl_idname = "muscle.reflect_rightside_muscles"
    bl_label = "Duplicates and reflects muscles across XY plane if they contain '_r' in the name"
    bl_description = "Duplicates and reflects muscles across XY plane if they contain '_r' in the name. This creates the muscle on the left side if the left side muscle does not exist already"
    
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
    
class InsertMusclePointOperator(Operator):
    bl_idname = "muscle.insert_muscle_point"
    bl_label = "Inserts a point in the muscle after the user specified point (starting with 1)"
    bl_description = "Inserts a point in the muscle after the user specified point (starting with 1)"
    
    def execute(self, context):
        
        
        insert_after = bpy.context.scene.muskemo.insert_point_after
        
        muscle_name = bpy.context.scene.muskemo.musclename
        
        active_obj = bpy.context.active_object  #should be the body that you want to parent the point to
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to


        for obj in sel_obj:
            obj.select_set(False)

        curve = bpy.data.objects[muscle_name]
        curve.select_set(True)
        bpy.context.view_layer.objects.active = curve  #make curve the active object
        bpy.ops.object.mode_set(mode='EDIT', toggle=False) 
        points = curve.data.splines[0].points

        bpy.ops.curve.select_all(action='DESELECT') # new

        points[insert_after-1].select = True
        points[insert_after].select = True
        bpy.ops.curve.subdivide()

        points[insert_after].co = bpy.context.scene.cursor.location.to_4d()

        bpy.ops.curve.select_all(action='DESELECT') # new
        bpy.ops.object.mode_set(mode='OBJECT', toggle=False) 

        ### hook point to body
        obj = curve
        modnamelist = [x.name for x in obj.modifiers]
        
        p_number = 1                    
        modname = 'hook' + '_ins_point_' + str(p_number) + '_' + active_obj.name
        while modname in modnamelist:
            p_number = p_number+1
            modname = 'hook' + '_ins_point_' + str(p_number) + '_' + active_obj.name
        
                
        obj.modifiers.new(name=modname, type='HOOK')
        obj.modifiers[modname].object = active_obj        


        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT') 

        curve.data.splines[0].points[insert_after].select = True

          
        bpy.ops.object.hook_assign(modifier = modname)

        #bpy.ops.curve.select_all(action='DESELECT') 

        for point in curve.data.splines[0].points:
            point.select = False


        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
                        


        ### restore selection state
        bpy.context.view_layer.objects.active = active_obj
        for obj in sel_obj:
            obj.select_set(True)        
                
        
        return {'FINISHED'}    
    
    
    

class VIEW3D_PT_muscle_panel(VIEW3D_PT_MuSkeMo, Panel):  # class naming convention ‘CATEGORY_PT_name’

    
    
    bl_label = "Muscle panel"  # found at the top of the Panel
    bl_context = "objectmode"
    bl_idname = 'VIEW3D_PT_muscle_panel'

    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        """define the layout of the panel"""
        
            
        layout = self.layout
        scene = context.scene
        muskemo = scene.muskemo
        
        row = self.layout.row()
        row.label(text ='Muscle points are added at the 3D cursor location')
        row = self.layout.row()
        row.label(text = 'Shift + right click moves the 3D cursor to your mouse location')
        row = self.layout.row()
        row.label(text = 'Hover over the buttons for an extra tooltip')
        
        
            
        layout.prop(muskemo, "musclename")
        row = self.layout.row()
        row.prop(muskemo, "muscle_collection")

        row = self.layout.row()

        row.operator("muscle.add_muscle_point", text="Add muscle point")
        
        self.layout.row()
        self.layout.row()
        
        row = self.layout.row()
        row.operator("muscle.insert_muscle_point", text="Insert muscle point")
        row.prop(muskemo, "insert_point_after")
        
        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.operator("muscle.reflect_rightside_muscles", text="Reflect right-side muscles")
        
        
        
        
        
        #row = self.layout.row()
        #self.layout.prop(muskemo, "musclename_string")


