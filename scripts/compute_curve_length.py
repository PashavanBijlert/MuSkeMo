import bpy
#inputs: name of the curve, reference to depsgraph, and a boolean to determine whether or not the curve has a wrap assigned to it

def compute_curve_length(curve_name, depsgraph, muscle_with_wrap = False):
    obj = bpy.data.objects[curve_name]
    depsgraph.update() #update the depsgraph
    
    if not muscle_with_wrap:
        obj_ev = obj.to_curve(depsgraph,apply_modifiers=True) 
        #apparently, geometry nodes and bevel modifiers are ignored
        length = obj_ev.splines[0].calc_length()
        obj.to_curve_clear()
        
    else:
        obj_ev = obj.evaluated_get(depsgraph) #
        obj_ev_mesh = obj_ev.to_mesh()
        length = obj_ev_mesh.attributes['length'].data[0].value
        obj_ev.to_mesh_clear()
            
    return length