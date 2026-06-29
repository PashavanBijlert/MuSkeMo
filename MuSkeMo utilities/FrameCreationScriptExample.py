### This script shows how to programmatically create a Frame, using
### MuSkeMo's api.
### All the component creation scripts could be used in the same
### way, just make sure to check the respective inputs for reach object.


import bpy
import addon_utils
from mathutils import (Matrix, Vector)
import os
import sys


### import scripts and functions we will need

muskemo_module = next((mod for mod in addon_utils.modules() if mod.__name__ == 'MuSkeMo'), None) #assumes MuSkeMo addon is installed
MuSkeMo_folder =  os.path.dirname(muskemo_module.__file__) #parent folder of MuSkeMo, which also includes the 'MuSkeMo utilities' folder
scripts = os.path.join(MuSkeMo_folder, 'scripts')
sys.path.append(scripts) #append the muskemo scripts folder to sys, so we can directly import from the folder


from create_frame_func import create_frame #this imports the create_frame function from the scripts folder in MuSkeMo's installation dir


#example

size = 0.1 #frame display size in meters

worldMat = Matrix([(1.0, 0.0, 0.0, 1.0), #replace with your actual worldmat
        (0.0, 1.0, 0.0, 0.0),
        (0.0, 0.0, 1.0, 0.0),
        (0.0, 0.0, 0.0, 0.0)])
        

posInGlob = worldMat.translation #should be in meters
gRb = worldMat.to_3x3() #rotation matrix from body to global frame  

#next two inputs are optional, can also comment out if you like, in which case it chooses the defaults
target_collection_name = 'Frames'  #can change if you like
parent_body = 'not_assigned' #or replace with an actual BODY name, if it exists. Only one frame per body allowed

       
        
create_frame(name = 'myframename',
            size = size,
            pos_in_global =  posInGlob, 
            gRb = gRb, 
            collection_name = target_collection_name, 
            parent_body = parent_body)

