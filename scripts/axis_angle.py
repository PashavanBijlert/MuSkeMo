from mathutils import (Matrix, Vector)
import numpy as np


def matrix_from_axis_angle(axis, angle): #Equation from Vallery & Schwab 2018, Advanced Dynamics, pg. 373
    #input:  desired axis as a list [x, y, z], angle in rad.
    #output:  3x3 rotation matrix gRb (from local to global) of type mathutils.Matrix
    
    axis_norm = Vector(axis).normalized() #ensure unit vector
    
    axis_cross_product_matrix = Matrix([[0, -axis_norm[2], axis_norm[1]],
    [axis_norm[2], 0, -axis_norm[0]],
    [-axis_norm[1], axis_norm[0], 0]])
    
    id_matrix = Matrix([[1, 0,0],[0,1,0],[0,0,1]]) #identity matrix
    

    gRb = id_matrix + Matrix((1-np.cos(angle)) * axis_cross_product_matrix@axis_cross_product_matrix) + Matrix(np.sin(angle)*axis_cross_product_matrix)
    
    
    return gRb


