### This script shows how to programmatically create a Frame, using
### MuSkeMo's api.
### All the component creation scripts could be used in the same
### way, just make sure to check the respective inputs for reach object.


import bpy
from mathutils import (Matrix, Vector)
import os



### import scripts and functions we will need from MuSkeMo's scripts folder
from MuSkeMo.scripts.create_frame_func import create_frame #this imports the create_frame function from the scripts folder in MuSkeMo's installation dir


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

