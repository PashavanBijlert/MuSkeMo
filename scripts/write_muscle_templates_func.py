import bpy
from mathutils import Vector
from math import nan
import pprint

### This can use some proper error messages

def write_muscle_templates(context, filepath, collection_name, delimiter, number_format):
    
    file = open(filepath, 'w', encoding='utf-8') #create or open a file, "w" means it's writeable
    
    depsgraph = bpy.context.evaluated_depsgraph_get()#get the dependency graph. If you change things in the scene, update this using depsgraph.update()


    coll = bpy.data.collections[collection_name]   
    
    ### Hardcoded fallbacks for now, replace with muskemoprops later
    global_up = (0.0, 1.0, 0.0)
    global_forward = (1.0, 0.0, 0.0)
    
    muskemo = bpy.context.scene.muskemo

    # Error check for if the root joint doesn't exist
    if muskemo.root_joint_name not in bpy.data.objects:
        print(f"ERROR: Root joint '{muskemo.root_joint_name}' not found.")
        return {'CANCELLED'}
        
    root_joint = bpy.data.objects[muskemo.root_joint_name]
    
    if 'child_body' not in root_joint:
        print("ERROR: Root joint has no 'child_body' custom property.")
        return {'CANCELLED'}
        
    root_body_name = root_joint['child_body']

    header = ('muscle_point' + delimiter + 'pbody' + delimiter + 'proxjoint' + delimiter + 'distjoint' + delimiter + #headers
    'frametype' + delimiter + 'frame_origin' + delimiter + 'pos_x_norm' + delimiter + 'pos_y_norm' + delimiter + 'pos_z_norm' + delimiter + 
    'F_max_norm' + delimiter + 'optimal_fiber_length_norm' + delimiter + 'tendon_slack_length_norm' + delimiter + 'pennation_angle' )
       
    file.write(header) #headers
    file.write('\n') 

### Map out the parent bodies for each point. (e.g., B1, B2, B3, ... Bn)
### Recursive Topology Setup
    
    segments = {}
    model_tree = {} # Nested dictionary for pprint
    
    def crawl_topology(obj, parent_joint=None, tree_dict=None):
        body_name = obj.name
        
        # Bodies can have multiple joints as their children, identify them by MuSkeMo_type
        j_outs = [child for child in obj.children if child.get('MuSkeMo_type') == 'JOINT']
        
        segments[body_name] = {
            'body_obj': obj,
            'J_in': parent_joint,
            'J_out': j_outs if len(j_outs) > 0 else None
        }
        
        for joint in j_outs:
            j_name = joint.name
            tree_dict[j_name] = {}
            
            # Joints have one child body, get its name from the property
            next_body_name = joint.get('child_body')
            
            if next_body_name and next_body_name in bpy.data.objects:
                next_body = bpy.data.objects[next_body_name]
                
                tree_dict[j_name][next_body_name] = {}
                crawl_topology(next_body, parent_joint=joint, tree_dict=tree_dict[j_name][next_body_name])

    root_body = bpy.data.objects.get(root_body_name)
    if root_body:
        model_tree[root_body_name] = {}
        # Pass the root_joint into the topology crawler so the root body has a J_in
        crawl_topology(root_body, parent_joint=root_joint, tree_dict=model_tree[root_body_name]) 
    
    print('--- TOPOLOGY TREE ---')
    pprint.pprint(model_tree)
    
    print(segments)
    
### get the name for each object in bpy.data, if the data type is a 'CURVE'
    curve_names = [x.name for x in coll.objects if 'CURVE' in x.id_data.type] 

### loop through all curves in the scene
    for u in range(len(curve_names)):
        curve = bpy.data.objects[curve_names[u]]
        modifier_list = [x.name for x in curve.modifiers if 'Hook'.casefold() in x.name.casefold()] #list of all the hook modifiers
        

        obj_ev = curve.evaluated_get(depsgraph) #
        obj_ev_mesh = obj_ev.to_mesh()
        #current length of muscle, used for scaling
        current_length = obj_ev_mesh.attributes['length'].data[0].value  #muscle length is stored as an attribute via the muscle geometry nodes.
        obj_ev.to_mesh_clear()
      
        
### Match muscle points to segments
        point_bodies = []
        for i in range(0, len(curve.data.splines[0].points)): #for each point
            body_name = 'ERROR, point not hooked to a body'
            for h in range(len(modifier_list)):
                modifier = curve.modifiers[modifier_list[h]]
                for j in range(len(modifier.vertex_indices)):
                    if i == modifier.vertex_indices[j]:
                        body_name = modifier.object.name
            point_bodies.append(body_name)

### Determine Muscle Directionality (Proximal-to-Distal vs Distal-to-Proximal)
        is_prox_to_dist = True
        if len(point_bodies) >= 2:
            last_body = point_bodies[-1]
            
            # Step backward to find the first body that is DIFFERENT from last_body
            penult_body = None
            for b in reversed(point_bodies[:-1]):
                if b != last_body:
                    penult_body = b
                    break
            
            # If we found a different body, check the joint flow
            if penult_body and last_body in segments and penult_body in segments:
                last_j_in = segments[last_body]['J_in']
                penult_j_outs = segments[penult_body]['J_out']
                
                # If the previous body's out-joints contain the last body's in-joint
                if penult_j_outs and last_j_in in penult_j_outs:
                    is_prox_to_dist = True
                else:
                    is_prox_to_dist = False

### loop through points
        for i in range(0, len(curve.data.splines[0].points)):
            if i == 0:                                        
                point_name = '_or'
            elif i == len(curve.data.splines[0].points)-1:    
                point_name = '_ins'
            else:                                             
                point_name = '_via' + str(i)

            body_name = point_bodies[i]
            
            if 'ERROR' in body_name or body_name not in segments:
                print('ERROR! Point number ' + str(i+1) + ' of ' + curve.name + ' is not hooked to a valid body segment')
                continue
                
            # Figure out topological "next" and "prev" bodies along the muscle path based on directionality
            if is_prox_to_dist:
                next_point_body = point_bodies[i+1] if i+1 < len(point_bodies) else None
                prev_point_body = point_bodies[i-1] if i-1 >= 0 else None
            else:
                # If built distal-to-proximal, topological "next" (further down chain) is the previous index
                next_point_body = point_bodies[i-1] if i-1 >= 0 else None
                prev_point_body = point_bodies[i+1] if i+1 < len(point_bodies) else None

            segment_data = segments[body_name]
            is_distal = (segment_data['J_out'] is None)
            is_root = (body_name == root_body_name)

### Frame Construction Logic
            J_prox = None
            J_dist = None
            origin_joint = None
            
            if is_root:
                # Points attached to root_body use the next segment down as their frame, but use j_in as origin.
                if next_point_body and next_point_body in segments:
                    next_seg = segments[next_point_body]
                    J_prox = next_seg['J_in']
                    
                    # Assume the next segment is a regular segment and grab its primary J_out for the frame axis
                    J_dist = next_seg['J_out'][0] if next_seg['J_out'] else None
                    origin_joint = J_prox
                else:
                    continue

            elif is_distal:
                # Points attached to a distal body use the previous segment, using j_out as origin.
                if prev_point_body and prev_point_body in segments:
                    prev_seg = segments[prev_point_body]
                    J_prox = prev_seg['J_in']
                    # The j_out of the previous segment connecting to THIS distal body is exactly this body's J_in
                    J_dist = segment_data['J_in'] 
                    origin_joint = J_dist
                else:
                    continue

            else:
                # All "regular" segments use the j_out as the origin.
                J_prox = segment_data['J_in']
                
                # Path-trace to find WHICH J_out the muscle goes through (if the body branches)
                J_out = None
                if next_point_body and next_point_body in segments:
                    next_j_in = segments[next_point_body]['J_in']
                    if next_j_in in segment_data['J_out']:
                        J_out = next_j_in
                        
                if not J_out: # Fallback
                    J_out = segment_data['J_out'][0]
                    
                J_dist = J_out
                origin_joint = J_out

            if J_prox == None or J_dist == None:
                continue

            p_prox = J_prox.matrix_world.translation
            p_dist = J_dist.matrix_world.translation
            
            vec_prox_to_dist = p_prox - p_dist
            frame_length = vec_prox_to_dist.length
            
            if frame_length == 0:
                continue

            axis_1 = vec_prox_to_dist.normalized()
            g_up = Vector(global_up)
            g_fwd = Vector(global_forward)

            dot_up = abs(axis_1.dot(g_up))
            dot_fwd = abs(axis_1.dot(g_fwd))

            if dot_up > dot_fwd:
                y_axis = axis_1
                z_axis = g_fwd.cross(y_axis).normalized()
                x_axis = y_axis.cross(z_axis).normalized()
                frametype = 'yaxisjoint-ztemp'
            else:
                x_axis = axis_1
                z_axis = x_axis.cross(g_up).normalized()
                y_axis = z_axis.cross(x_axis).normalized()
                frametype = 'xaxisjoint-ztemp'

            import mathutils
            rot_matrix = mathutils.Matrix([
                [x_axis.x, y_axis.x, z_axis.x],
                [x_axis.y, y_axis.y, z_axis.y],
                [x_axis.z, y_axis.z, z_axis.z]
            ]).to_4x4()
            
            frame_origin_pos = origin_joint.matrix_world.translation
            rot_matrix.translation = frame_origin_pos
            
            matrix_world_inv = rot_matrix.inverted_safe()
            point_global_loc = curve.matrix_world @ curve.data.splines[0].points[i].co.xyz
            
            local_pos = matrix_world_inv @ point_global_loc
            
### Normalization
            pos_x_norm = local_pos.x / frame_length
            pos_y_norm = local_pos.y / frame_length
            pos_z_norm = local_pos.z / frame_length

            f_max_norm = curve['F_max'] / (current_length**2)
            opt_fib_len_norm = curve['optimal_fiber_length'] / frame_length
            tendon_slk_norm = curve['tendon_slack_length'] / frame_length
            pen_angle = curve['pennation_angle']

### Muscle Exports
            file.write(curve_names[u] + point_name + delimiter) 
            file.write(body_name + delimiter) 
            file.write(J_prox.name + delimiter) 
            file.write(J_dist.name + delimiter) 
            file.write(frametype + delimiter) 
            file.write(origin_joint.name + delimiter) 
            file.write(f"{pos_x_norm:{number_format}}{delimiter}")     
            file.write(f"{pos_y_norm:{number_format}}{delimiter}")     
            file.write(f"{pos_z_norm:{number_format}}{delimiter}")     
            file.write(f"{f_max_norm:{number_format}}{delimiter}")
            file.write(f"{opt_fib_len_norm:{number_format}}{delimiter}")
            file.write(f"{tendon_slk_norm:{number_format}}{delimiter}")
            file.write(f"{pen_angle:{number_format}}")

            file.write('\n')

    file.close()
    return {'FINISHED'}