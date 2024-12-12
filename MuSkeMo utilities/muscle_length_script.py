import bpy 
muscle = bpy.data.objects['mymuscle'] #fill in
obj_ev = muscle.object.to_curve(muscle.evaluated_depsgraph_get(),apply_modifiers=True) 
#assumes the target object is selected.
#apparently, geometry nodes and bevel modifiers are ignored
length = obj_ev.splines[0].calc_length()
muscle.object.to_curve_clear()
print(length)