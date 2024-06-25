from mathutils import Matrix
import numpy as np

def quat_from_matrix(mat):
    #input: 3x3 rotation matrix (gRb, so from local to global) of type mathutils.Matrix
    #output: quaternion as a list, [w, x, y, z]


    #Algorithm from Eberly book, page 537
    trace = mat[0][0] + mat[1][1] + mat[2][2]

    ## assume the following quat matrix:

    #[1-2*(z**2 + y**2),   2*(x*y - w*z), 2*(z*x + w*y)  ]
    #[2*(x*y + w*z) , 1-2*(x**2 + z**2), 2*(y*z -w*x)]
    #[2*(z*x - w*y), 2*(y*z +w*x), 1-2*(x**2 + y**2)]


    if trace<0: #if trace is smaller than zero, we find out whether x, y, or z, is the biggest, and then compute the other parameters

        #assume x is biggest
        i = 0
        j = 1
        k = 2

        if mat[j][j]>mat[i][i]:  #if Ryy>Rxx
            i = 1
            j = 2
            k = 0

        if mat[j][j]>mat[i][i]: #if Rzz>Ryy
            i = 2
            j = 0
            k = 1    

        r = np.sqrt(mat[i][i] - mat[j][j] - mat[k][k] +1 )
        s = 0.5 / r

        quat_i = 0.5*r
        quat_j = (mat[i][j] + mat[j][i]) * s
        quat_k = (mat[k][i] + mat[i][k]) * s
        quat_w = (mat[k][j] - mat[j][k]) * s
        
        #map back from ijk to xyz

        if i == 0:  #i = x, j = y, k = z
            quat_x = quat_i
            quat_y = quat_j
            quat_z = quat_k

        elif i == 1: #i = y, j = z, k = x
            quat_y = quat_i
            quat_z = quat_j
            quat_x = quat_k
        else:        #i = z, j = x, k = y
            quat_z = quat_i
            quat_x = quat_j
            quat_y = quat_k    
        
        
    else: #if w is biggest, we compute that first (indirectly, by computing r)
        r = np.sqrt(trace + 1)
        s = 0.5/r
        
        quat_x = (mat[2][1] - mat[1][2]) * s
        quat_y = (mat[0][2] - mat[2][0]) * s
        quat_z = (mat[1][0] - mat[0][1]) * s
        quat_w = 0.5*r      
    
    quat = [quat_w, quat_x, quat_y, quat_z]
    return(quat)



def matrix_from_quaternion(quat):
    #input:  quaternion as a list, [w, x, y, z]
    #output:  3x3 rotation matrix gRb (from local to global) and bRg (from global to local) of type mathutils.Matrix
   
    
    w = quat[0]
    x = quat[1]
    y = quat[2]
    z = quat[3]

    gRb = Matrix([[1-2*(z**2 + y**2),   2*(x*y - w*z), 2*(z*x + w*y)  ],
                    [2*(x*y + w*z) , 1-2*(x**2 + z**2), 2*(y*z -w*x)],
                    [2*(z*x - w*y), 2*(y*z +w*x), 1-2*(x**2 + y**2)]])
                    
    bRg = gRb.copy()
    bRg.transpose()                
                    
    return(gRb, bRg)                