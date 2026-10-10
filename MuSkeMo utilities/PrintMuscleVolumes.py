import bpy
#Prints out each muscle's volume into the workspace, as long as the Volumetric Muscle Visualisation is used.

collection_name = "Muscles"
mod_suffix = "_VolumetricMuscleViz"

### import scripts and functions we will need from the muskemo scripts folder

from MuSkeMo.scripts.muscle_panel import get_socket


for obj in bpy.data.collections[collection_name].objects:
    mod = obj.modifiers.get(obj.name + mod_suffix)
    if mod:
        
        vol = get_socket(mod, "MuscleVolume") 
        print(mod.name)
        print(vol)