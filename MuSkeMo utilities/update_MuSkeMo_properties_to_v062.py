import bpy
from math import nan
import pathlib
#this script updates all the existing MuSkeMo properties to the newest version of MuSkeMo

## automatically save a backup
    
blender_file_path = pathlib.Path(bpy.data.filepath)
if bpy.data.filepath == '':
    raise ValueError('You are working from an unsaved Blend file. Save it first')
    
    print(f'You are working from file "{blender_file_path.name}"'
        + f' in directory (folder) {blender_file_path.parent}')
        
new_file_path = blender_file_path.parent / blender_file_path.name.replace('.blend','_backup.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(new_file_path))



### actual code starts here
MuSkeMo_objects = [obj for obj in bpy.data.objects if 'MuSkeMo_type' in obj]

bodies = [obj for obj in MuSkeMo_objects if obj['MuSkeMo_type'] == 'BODY']
joints = [obj for obj in MuSkeMo_objects if obj['MuSkeMo_type'] == 'JOINT']
contacts = [obj for obj in MuSkeMo_objects if obj['MuSkeMo_type'] == 'CONTACT']
frames = [obj for obj in MuSkeMo_objects if obj['MuSkeMo_type'] == 'FRAME']
muscles = [obj for obj in MuSkeMo_objects if obj['MuSkeMo_type'] == 'MUSCLE']



for obj in bodies:
    if obj['local_frame'] == 'not yet assigned':
        obj['local_frame'] = 'not_assigned'
        
    if 'COM_local' not in obj:
        obj['COM_local'] =  [nan, nan, nan]
        obj['inertia_COM_local'] = [nan, nan, nan, nan, nan, nan]   
        
for obj in joints:
    print(obj.name)
    if obj['parent_body'] == 'not yet assigned':
        obj['parent_body'] = 'not_assigned'
        
    if obj['child_body'] == 'not yet assigned':
        obj['child_body'] = 'not_assigned' 
    
    if 'loc_child_frame' in obj:
        obj['pos_in_child_frame'] = obj['loc_child_frame']
        del obj['loc_child_frame']
        
    if 'loc_parent_frame' in obj:        
        obj['pos_in_parent_frame'] = obj['loc_parent_frame']
        del obj['loc_parent_frame']
     
    if 'loc_in_child_frame' in obj:
        obj['pos_in_child_frame'] = obj['loc_in_child_frame']
        del obj['loc_in_child_frame']
        
    if 'loc_in_parent_frame' in obj:        
        obj['pos_in_parent_frame'] = obj['loc_in_parent_frame']
        del obj['loc_in_parent_frame']   
    
        
        
for obj in contacts:
    if obj['parent_body'] == 'not yet assigned':
        obj['parent_body'] = 'not_assigned'
    
    if 'loc_in_parent_frame' in obj:
        obj['pos_in_parent_frame'] = obj['loc_in_parent_frame']
        del obj['loc_in_parent_frame']
        
for obj in frames:
    if obj['parent_body'] == 'not yet assigned':
        obj['parent_body'] = 'not_assigned'


#This was changed in v0.6.2
for obj in muscles:
    if 'tendon_length' in obj:
        obj['tendon_slack_length'] = obj['tendon_length']
        del obj['tendon_length']
    
                            