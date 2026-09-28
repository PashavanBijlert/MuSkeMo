import bpy
#Prints out each muscle's volume into the workspace, as long as the Volumetric Muscle Visualisation is used.

collection_name = "Muscles"
mod_suffix = "_VolumetricMuscleViz"

#This helper function is copied over from the muscle_panel.
#  Muscles have many geometry node inputs that are accesible via the modifier input, known as sockets. 
# Pre Blender 5.2, these were hardcoded by number(e.g. modifier["Socket_1"]). After Blender 5.2, this was implemented more gracefully, but to maintain backwards compatibility,
# I've added getter and setter functions that should be used for modifier inputs.

def get_socket(modifier, socket_name): #get the value from a socket / modifier input by inputting the name of the socket
    socket_identifier = modifier.node_group.interface.items_tree[socket_name].identifier #results in e.g. "Socket_0"
    if bpy.app.version >= (5, 2, 0):
        return getattr(modifier.properties.inputs, socket_identifier).value
    else:
        return modifier[socket_identifier]     



for obj in bpy.data.collections[collection_name].objects:
    mod = obj.modifiers.get(obj.name + mod_suffix)
    if mod:
        
        vol = get_socket(mod, "MuscleVolume") 
        print(mod.name)
        print(vol)