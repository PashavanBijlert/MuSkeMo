import bpy
#inputs: name of the curve, reference to depsgraph, and a boolean to determine whether or not the curve has a wrap assigned to it

def compute_curve_length(curve_name, depsgraph):
    obj = bpy.data.objects[curve_name]
    depsgraph.update() #update the depsgraph
    
    #this commented out section computes the length using the built in calc_length function of Blender.
    #It ignores geometry nodes, and thus is incompatible with muscle wrapping. The alternative version computes
    #the curve length using a length attribute that is created inside geometry nodes. 
    # Initially, the behavior of this script depended on whether the muscle had a wrap or not, but
    # This version is equally fast, so I decided to remove the direct length computation in favor of current implementation.
    # The length attribute is created inside geometry nodes using the curve length node, so the internal length computation of the straight sections is the same
    # For the wrapped sections, the wrapped lengths are computed manually.

    # if not muscle_with_wrap:
    #     obj_ev = obj.to_curve(depsgraph,apply_modifiers=True) 
    #     #apparently, geometry nodes and bevel modifiers are ignored
    #     length = obj_ev.splines[0].calc_length()
    #     obj.to_curve_clear()
        
    #else:
    obj_ev = obj.evaluated_get(depsgraph) #
    obj_ev_mesh = obj_ev.to_mesh()
    length = obj_ev_mesh.attributes['length'].data[0].value
    obj_ev.to_mesh_clear()
            
    return length