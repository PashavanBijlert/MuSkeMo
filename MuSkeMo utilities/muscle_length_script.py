import bpy 
muscle = bpy.data.objects['mymuscle'] #fill in
depsgraph = bpy.context.evaluated_depsgraph_get()#get the dependency graph. If you change things in the scene, update this using depsgraph.update()

obj_ev = muscle.object.to_curve(depsgraph,apply_modifiers=True) 

#geometry nodes and bevel modifiers are ignored, so this doesn't work with wrapping.
length = obj_ev.splines[0].calc_length()
muscle.to_curve_clear()
print(length)