# Example script that lets you programmatically reposition all the neck joints in a model.
# Works with the emu model from the Sample Dataset.

import bpy
from mathutils import Matrix
from math import (cos, sin, pi)
import numpy as np



def get_all_distal_joints(root_joint):
    """
    Returns a list of all joints connected downstream from the root_joint
    by following child_body -> parent_body relationships.
    """
    joint_queue = [root_joint]
    joint_list = []

    while joint_queue:
        joint = joint_queue.pop(0)
        joint_list.append(joint)

        child_body_name = joint.get('child_body')
        if not child_body_name:
            continue

        for obj in bpy.data.objects:
            if obj.get('MuSkeMo_type') == 'JOINT' and obj.get('parent_body') == child_body_name:
                joint_queue.append(obj)

    return joint_list


root_joint_name = 'neck_18_joint'

root_joint = bpy.data.objects.get(root_joint_name)
if not root_joint:
    raise ValueError(f"Root joint '{root_joint_name}' not found.")

all_joints = get_all_distal_joints(root_joint)

print(all_joints)

stretch_factor = 1.05

# --- Iterate over joints ---
for i in range(len(all_joints) - 1):
    j1 = all_joints[i]
    j2 = all_joints[i+1]

    # positions in world space
    p1 = j1.matrix_world.translation
    p2 = j2.matrix_world.translation

    # vector and length
    vec = p2 - p1
    dist = vec.length

    # scaled vector
    new_vec = vec.normalized() * dist * stretch_factor

    # new world location
    new_pos = p1 + new_vec

    # move the next joint
    j2.matrix_world.translation =  new_pos