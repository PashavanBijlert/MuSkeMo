import bpy
#Prints out each muscle's volume into the workspace, as long as the Volumetric Muscle Visualisation is used.

collection_name = "Muscles"
mod_suffix = "_VolumetricMuscleViz"

for obj in bpy.data.collections[collection_name].objects:
    mod = obj.modifiers.get(obj.name + mod_suffix)
    if mod:
        
        vol = mod[mod.node_group.interface.items_tree["MuscleVolume"].identifier]
        
        print(mod.name)
        print(vol)