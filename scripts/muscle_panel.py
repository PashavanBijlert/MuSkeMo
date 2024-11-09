
# give Python access to Blender's functionality
import bpy
from mathutils import Vector


from bpy.types import (Panel,
                        Operator,
                        )

from .. import VIEW3D_PT_MuSkeMo


class AddMusclepointOperator(Operator):
    bl_idname = "muscle.add_muscle_point"
    bl_label = "Adds a viapoint to the muscle (or creates a new muscle) at the 3D cursor location"  #not sure what bl_label does, bl_description gives a hover tooltip
    bl_description = "Adds a viapoint to the muscle (or creates a new muscle) at the 3D cursor location"
    
    def execute(self, context):


        muscle_name = bpy.context.scene.muskemo.musclename

        colname = bpy.context.scene.muskemo.muscle_collection #name for the collection that will contain the hulls

        
        active_obj = bpy.context.active_object
        sel_obj = bpy.context.selected_objects  #should be the body that you want to parent the point to


        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        body = sel_obj[0]
        body_name = body.name

        if 'MuSkeMo_type' in body:
            if 'BODY' != bpy.data.objects[body_name]['MuSkeMo_type']:
                self.report({'ERROR'}, "Selected object '" + body_name + "' is not a BODY. Muscle point addition cancelled")
                return {'FINISHED'} 
        else:
            self.report({'ERROR'}, "Selected object '" + body_name + "' was not an object created by MuSkeMo. Muscle point addition cancelled")
            return {'FINISHED'}      
        
        

        for obj in sel_obj:
            obj.select_set(False)

        from .create_muscle_func import create_muscle  #import muscle creation function

        point_position = bpy.context.scene.cursor.location
        create_muscle(muscle_name = muscle_name, point_position = point_position, 
                      collection_name=colname,
                          body_name = body_name)
        
        '''
        try: bpy.data.objects[muscle_name]  #throws an error if the muscle doesn't exist, creates it under except

        

        except:
            
            
            point_position = bpy.context.scene.cursor.location
            create_muscle(muscle_name = muscle_name, point_position = point_position,
                          body_name = body_name)

        else: #if the muscle does exist, add a point at the end
            

            
            point_position = bpy.context.scene.cursor.location
            create_muscle(muscle_name = muscle_name, point_position = point_position,
                          body_name = body_name.name)    
                
        '''        
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
        colname = bpy.context.scene.muskemo.muscle_collection

        collection = bpy.data.collections[colname]

        muscles = [obj for obj in collection.objects if obj['MuSkeMo_type'] == 'MUSCLE']

        for obj in (obj for obj in muscles if '_r' in obj.name):  #for all the objects if '_r' is in the name
            
            if obj.name.replace('_r','_l') not in (obj.name for obj in collection.objects):  #make sure a left side doesn't already exist
            
            
                new_obj = obj.copy()  #copy object
                new_obj.data = obj.data.copy() #copy object data
                new_obj.name = obj.name.replace('_r','_l') #rename to left
                
                collection.objects.link(new_obj)  #add to Muscles collection
                
                for point in new_obj.data.splines[0].points:   #reflect each point about z
                    point.co = point.co*Vector((1,1,-1,1))

                ## set material
                oldmatname = new_obj.material_slots[0].name
                new_obj.data.materials.pop(index = 0)
                newmatname = oldmatname.replace('_r','_l')
                if newmatname in bpy.data.materials: #if the material already exists
                    newmat = bpy.data.materials[newmatname]
                    new_obj.material_slots[0].material = newmat

                else:
                    from .create_muscle_material_func import create_muscle_material

                    newmat = create_muscle_material(new_obj.name)

                for mod in new_obj.modifiers: #loop through all modifiers

                    mod.name = mod.name.replace('_r','_l')

                    if 'HOOK' == mod.type: #if it's a hook, hook the other side body
                        newbodyname = mod.object.name.replace('_r','_l')
                        

                        if newbodyname not in bpy.data.objects:# if the body doesn't exist
                            self.report({'WARNING'}, "BODY with the name '" + newbodyname + "' Does not exist. Create it using the body mirroring button. '" +new_obj.name  +  "' MUSCLE currently has unhooked points.")
                            mod.object = None
                        else:
                            mod.object = bpy.data.objects[newbodyname] #point the hook to the left side body
                            

                    if 'NODES' == mod.type: #if it's a geometry nodes modifier (the simple muscle viz) 
                       mod.node_group.nodes['Set Material'].inputs['Material'].default_value = newmat   
                
                

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

        # throw an error if no objects are selected     
        if (len(sel_obj) < 1):
            self.report({'ERROR'}, "Too few objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        # throw an error if no objects are selected     
        if (len(sel_obj) > 1):
            self.report({'ERROR'}, "Too many objects selected. Select one body to parent the muscle point to")
            return {'FINISHED'}
        
        body = sel_obj[0]
        body_name = body.name

        if 'MuSkeMo_type' in body:
            if 'BODY' != bpy.data.objects[body_name]['MuSkeMo_type']:
                self.report({'ERROR'}, "Selected object '" + body_name + "' is not a BODY. Muscle point addition cancelled")
                return {'FINISHED'} 
        else:
            self.report({'ERROR'}, "Selected object '" + body_name + "' was not an object created by MuSkeMo. Muscle point addition cancelled")
            return {'FINISHED'}      


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
        modname = 'hook' + '_ins_point_' + str(p_number) + '_' + body_name
        while modname in modnamelist:
            p_number = p_number+1
            modname = 'hook' + '_ins_point_' + str(p_number) + '_' + body_name
        
                
        obj.modifiers.new(name=modname, type='HOOK')
        obj.modifiers[modname].object = body        

        

        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.curve.select_all(action='DESELECT') 

        curve.data.splines[0].points[insert_after].select = True

          
        bpy.ops.object.hook_assign(modifier = modname)

        #bpy.ops.curve.select_all(action='DESELECT') 

        for point in curve.data.splines[0].points:
            point.select = False


        bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')
                        
        #Ensure the last two modifiers are always the Visualization and then the bevel modifier
        n_modifiers = len(obj.modifiers)
        obj.modifiers.move(n_modifiers-1, insert_after) #new modifiers are placed at the end, index is n_modifiers-1. Place it at the index of the last curve point.

        ### restore selection state
        bpy.context.view_layer.objects.active = active_obj
        for obj in sel_obj:
            obj.select_set(True)        
                
        
        return {'FINISHED'}    
    
class UpdateMuscleVizRadius(Operator):
    bl_idname = "muscle.update_muscle_viz_radius"
    bl_label = "Update the muscle visualization radius of the muscle line segments (not the volumetric muscles)"
    bl_description = "Update the muscle visualization radius of the muscle line segments (not the volumetric muscles)"

    def execute(self, context):

        MuSkeMo_objects = [x for x in bpy.data.objects if 'MuSkeMo_type' in x]
        muscles = [x for x in MuSkeMo_objects if x['MuSkeMo_type']=='MUSCLE']
        
        muscle_visualization_radius = bpy.context.scene.muskemo.muscle_visualization_radius

        for muscle in muscles:
            muscle.modifiers[muscle.name + '_SimpleMuscleViz']['Socket_1']=  muscle_visualization_radius
            muscle.modifiers[muscle.name + '_SimpleMuscleViz'].node_group.interface_update(bpy.context)
        
        #update the merge by distance value based on the desired radius
        bpy.data.node_groups['SimpleMuscleNode'].nodes['Merge by Distance'].inputs['Distance'].default_value = muscle_visualization_radius * 0.13
        
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
        row.label(text = 'You must select a body before attempting to add a muscle point')
        
        
            
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
        row = self.layout.row()
       
        row.prop(muskemo, "muscle_visualization_radius")
        row.operator("muscle.update_muscle_viz_radius", text = "Update visualization radius")


        self.layout.row()
        self.layout.row()
        row = self.layout.row()
        row.operator("muscle.reflect_rightside_muscles", text="Reflect right-side muscles (experimental)")
        
        
        
        
        
        #row = self.layout.row()
        #self.layout.prop(muskemo, "musclename_string")


