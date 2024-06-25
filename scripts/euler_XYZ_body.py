from mathutils import Matrix
import numpy as np


def euler_XYZbody_from_matrix(mat):
    #input: 3x3 rotation matrix gRb of type mathutils.Matrix
    #output: list of euler angles (phi_x, phi_y, phi_z)
    
    #This script assumes: body-fixed (intrinsic) successive rotations about body-X, body-Y, then body-Z axes.
    #This script assumes active rotations (so the object rotates, not the frame). We assume matrix premultiplication of standing vectors.
    #In other words: gRb = Rx * Ry * Rz * v_b, where v_b is a vector v expressed in body-fixed frame b, and gRb rotates from body-fixed to global coordinates
    
    phi_y = np.arcsin(mat[0][2]) #alternative: phi_y = np.arctan2(gRl[0,2], math.sqrt(1 - (gRl[0,2])**2)) 
    phi_x = np.arctan2(-mat[1][2],mat[2][2])    #angle alpha in wiki
    phi_z = np.arctan2(-mat[0][1],mat[0][0])    #angle gamma in wiki

    euler_xyz = [phi_x, phi_y, phi_z]
    return(euler_xyz)


def matrix_from_euler_XYZbody(angles_xyz):
    #inputs: list of euler angles (phi_x, phi_y, phi_z)
    #outputs: 3x3 rotation matrix of type mathutils.Matrix, outputs both gRb (from body to global) and bRg (from global to body)
    
    #This script assumes: body-fixed (intrinsic) successive rotations about body-X, body-Y, then body-Z axes.
    #This script assumes active rotations (so the object rotates, not the frame). We assume matrix premultiplication of standing vectors.
    #In other words: gRb = Rx * Ry * Rz * v_b, where v_b is a vector v expressed in body-fixed frame b, and gRb rotates from body-fixed to global coordinates
    
    phi_x = angles_xyz[0]
    phi_y = angles_xyz[1]
    phi_z = angles_xyz[2]
    
    cos = np.cos
    sin = np.sin
    
    
    Rx =  Matrix([[1,          0,           0],
                  [0, cos(phi_x), -sin(phi_x)],
                  [0, sin(phi_x), cos(phi_x)]])
                  
    Ry =  Matrix([[ cos(phi_y), 0, sin(phi_y)],
                  [          0, 1,          0],
                  [-sin(phi_y), 0, cos(phi_y)]])
                  
    Rz =  Matrix([[cos(phi_z), -sin(phi_z), 0],
                  [sin(phi_z),  cos(phi_z), 0],
                  [         0,           0, 1]])
                  
    gRb = Rx @ Ry @ Rz
    
    bRg = gRb.copy()
    bRg.transpose() 
    
    return(gRb, bRg)