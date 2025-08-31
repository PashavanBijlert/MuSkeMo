import bpy 
muscle = bpy.data.objects['mymuscle'] #fill in
depsgraph = bpy.context.evaluated_depsgraph_get()#get the dependency graph. If you change things in the scene, update this using depsgraph.update()

obj_ev = muscle.evaluated_get(depsgraph) #
obj_ev_mesh = obj_ev.to_mesh()
length = obj_ev_mesh.attributes['length'].data[0].value  #muscle length is stored as an attribute via the muscle geometry nodes.
obj_ev.to_mesh_clear()
print(length)