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

### Recursive helper to check if target_body is downstream of current_body
        def is_downstream(current_body_name, target_body_name):
            if not current_body_name or current_body_name not in segments: return False
            for j in segments[current_body_name]['J_out'] or []:
                child = j.get('child_body')
                if child == target_body_name: return True
                if child and is_downstream(child, target_body_name): return True
            return False

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
                
            segment_data = segments[body_name]
            is_distal = (segment_data['J_out'] is None)
            is_root = (body_name == root_body_name)

            # Look locally at the muscle path: find the nearest different bodies
            forward_body = next((b for b in point_bodies[i+1:] if b != body_name), None)
            backward_body = next((b for b in reversed(point_bodies[:i]) if b != body_name), None)

            # Find WHICH branch (J_out) the muscle interacts with locally
            J_out = None
            if segment_data['J_out']:
                # Does the muscle travel forward into a downstream branch?
                for j in segment_data['J_out']:
                    child = j.get('child_body')
                    if child == forward_body or is_downstream(child, forward_body):
                        J_out = j
                        break
                
                # If not, does the muscle come from a downstream branch (e.g. drawn backwards)?
                if not J_out:
                    for j in segment_data['J_out']:
                        child = j.get('child_body')
                        if child == backward_body or is_downstream(child, backward_body):
                            J_out = j
                            break
                            
                # Fallback: if muscle doesn't go downstream (e.g., stays entirely on this body)
                if not J_out:
                    J_out = segment_data['J_out'][0]

### Frame Construction Logic
            J_prox = None
            J_dist = None
            origin_joint = None
            
            if is_root:
                # Root body uses the next segment down based on the active branch we just found
                if J_out:
                    next_body = J_out.get('child_body')
                    if next_body and next_body in segments:
                        next_seg = segments[next_body]
                        J_prox = J_out # which acts as next_seg['J_in']
                        J_dist = next_seg['J_out'][0] if next_seg['J_out'] else None
                        origin_joint = J_prox

            elif is_distal:
                # Distal body uses previous segment
                prev_body = segment_data['J_in'].parent if segment_data['J_in'] else None
                if prev_body and prev_body.name in segments:
                    J_prox = segments[prev_body.name]['J_in']
                    J_dist = segment_data['J_in'] 
                    origin_joint = J_dist

            else:
                # Regular segment uses the specific J_out the muscle goes through
                J_prox = segment_data['J_in']
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
            opt_fib_len_norm = curve['optimal_fiber_length'] / current_length
            tendon_slk_norm = curve['tendon_slack_length'] / current_length
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