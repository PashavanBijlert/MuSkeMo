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

Author: Pasha van Bijlert
"""


import bpy
import numpy as np
from mathutils import Vector, kdtree, Matrix
import time

def get_vertices_and_normals_world(obj):
    mw = obj.matrix_world
    verts = np.array([mw @ v.co for v in obj.data.vertices])
    norms = np.array([mw.to_3x3() @ v.normal for v in obj.data.vertices])
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
                                 sample_ratio_ramp_iters=6):
   
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
    """
    source_verts = get_vertices_and_normals_world(free_obj)[0]
    tgt_verts, tgt_norms = get_vertices_and_normals_world(target_obj)
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

        # Build system
        A, b = [], []
        for idx in sampled_indices:
            p = source_verts[idx]
            nearest, index, _ = tgt_tree.find(Vector(p))
            q = tgt_verts[index]
            n = tgt_norms[index]
            diff = p - q
            A.append(np.concatenate((np.cross(p, n), n)))
            b.append(-np.dot(n, diff))

        A = np.array(A)
        b = np.array(b).reshape(-1, 1)

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

