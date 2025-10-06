"""
Point-to-Plane ICP Implementation in Blender Python

This script aligns a free object to a target object by minimizing point-to-plane
residuals using the iterative closest point (ICP) method. It follows the 
normal-based formulation of Chen & Medioni (1992), where the error is measured 
along the surface normal of each target point:

    r_i ≈ n_iᵀ[(ω × p_i) + t + (p_i - q_i)]

The linearized rotation and translation are solved via a least-squares system
(A x = b, x = [ω, t]). KD-tree acceleration and subsampling strategies are used 
for efficiency, inspired by Zhang (1994) and Rusinkiewicz & Levoy (2001).

Given:
- Source points p_i on the free object
- Closest target points q_i with surface normals n_i
- Small rotation vector ω and translation t

The script iteratively updates the free object transform until convergence.

References:
- Chen, Y., & Medioni, G. (1991). Object modeling by registration of multiple range images
- Zhang, Z. (1994). Iterative point matching for registration of free-form curves and surfaces.
- Rusinkiewicz, S., & Levoy, M. (2001). Efficient Variants of the ICP Algorithm.

Author, copyright: Pasha van Bijlert; 
LIcense: CC-BY-NC
"""


import bpy
import numpy as np
from mathutils import Vector, kdtree, Matrix
import time

def get_vertices_and_normals_world(obj, selection_only):
    mw = obj.matrix_world

    if not selection_only: #if we're aligning whole meshes
        verts = np.array([mw @ v.co for v in obj.data.vertices])
        norms = np.array([mw.to_3x3() @ v.normal for v in obj.data.vertices])

    else:
        verts = np.array([mw @ v.co for v in obj.data.vertices if v.select])
        norms = np.array([mw.to_3x3() @ v.normal for v in obj.data.vertices if v.select])
    
    return verts, norms

def build_kdtree(points):
    tree = kdtree.KDTree(len(points))
    for i, p in enumerate(points):
        tree.insert(Vector(p), i)
    tree.balance()
    return tree

def skew(v):
    return np.array([[    0, -v[2],  v[1]],
                     [ v[2],     0, -v[0]],
                     [-v[1],  v[0],    0]])

def point_to_plane_icp_subsample(free_obj, target_obj,
                                 max_iterations=30,
                                 tolerance=1e-6,
                                 sample_ratio_start=0.1,
                                 sample_ratio_end=1.0,
                                 sample_ratio_ramp_iters=6,
                                 alignment_mode = 'Whole meshes'):
   
    """
    Point-to-Plane ICP with:
      - Random subsampling ramping up
      - Once ramp is complete, continue at sample_ratio=1 until convergence
      - If stop condition is hit earlier, contiue at sample_ratio=1 until convergence
    inputs: 
    free_obj (blender object of type mesh, this object will be transformed) 
    target_obj (blender object of type mesh, this object is stationary) 
    tolerance (stop condition accuracy)
    sample_ratio_start (downsample ratio at the start of the optimization)
    sample_ratio_end (downsample after reaching sample_ratio_ramp_iters)
    sample_ratio_ramp_iters (number of iterations afer sample_ratio_end is reached)
    Alignment mode ("Whole meshes", or "Selected mesh portions"). "Selected mesh portions" requires both meshes to have selections set in Edit mode.
    """
    if alignment_mode == "Whole meshes":
        selection_only = False
    elif alignment_mode == "Selected mesh portions":
        selection_only = True

    source_verts = get_vertices_and_normals_world(free_obj, selection_only=selection_only)[0]
    tgt_verts, tgt_norms = get_vertices_and_normals_world(target_obj, selection_only=selection_only)

    tgt_tree = build_kdtree(tgt_verts)

    transform = np.eye(4)
    prev_error = None
    num_source = len(source_verts)

    ramp_done = False

    for it in range(max_iterations):
        t0 = time.time()

        # Determine current sample ratio
        if not ramp_done and it < sample_ratio_ramp_iters:
            sample_ratio = sample_ratio_start + (sample_ratio_end - sample_ratio_start) * (it / sample_ratio_ramp_iters)
        else:
            sample_ratio = sample_ratio_end
            ramp_done = True

        num_sample = max(1, int(sample_ratio * num_source))
        sampled_indices = np.random.choice(num_source, num_sample, replace=False)

        
        p = source_verts[sampled_indices] #Get all sampled source points in a single NumPy array

               
        nearest_indices = [tgt_tree.find(Vector(pt))[1] for pt in p] # Find nearest neighbors and collect their indices.

        q = tgt_verts[nearest_indices] #Use the collected indices to get all target points (q) and normals (n)  at once using NumPy.
        n = tgt_norms[nearest_indices]

        # Calculate all cross products
        diff = p - q
        cross_products = np.cross(p, n, axis=1)

        # Assemble the final A and b matrices.
        
        A = np.hstack((cross_products, n)) #    np.hstack joins the arrays horizontally.
        b = -np.einsum('ij,ij->i', n, diff).reshape(-1, 1) #    np.einsum performs all dot products between corresponding n and diff vectors.

        # Solve
        x, _, _, _ = np.linalg.lstsq(A, b, rcond=None)
        omega = x[:3].flatten()
        t = x[3:].flatten()

        # Full Rodrigues rotation
        theta = np.linalg.norm(omega)
        if theta < 1e-12:
            R = np.eye(3)
        else:
            k = omega / theta
            K = skew(k)
            R = np.eye(3) + np.sin(theta) * K + (1 - np.cos(theta)) * (K @ K)

        delta_T = np.eye(4)
        delta_T[:3, :3] = R
        delta_T[:3, 3] = t

        transform = delta_T @ transform
        free_obj.matrix_world = Matrix(delta_T) @ free_obj.matrix_world
        source_verts = (R @ source_verts.T).T + t

        mean_error = np.mean(np.abs(b))
        print(f"Iter {it+1}, mean error={mean_error:.6f}, time={time.time()-t0:.3f}s, "
              f"sample_ratio={sample_ratio:.2f}")

        # Convergence logic:
        if prev_error is not None and abs(prev_error - mean_error) < tolerance:
            # If we already at full sample ratio, stop
            if sample_ratio == sample_ratio_end:
                break
            # Otherwise, continue at full sample ratio
        prev_error = mean_error

    return Matrix(transform)

