InertialPropertiesPresets = {
    "Arithmetic scale factor": { #each segment is directly scaled by the specified amount
        "Macaulay 2023 Bird": 
        (["head", "neck", "torso", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"],
         [1.008,  3.825,  1.436,  1.970,  1.736,  1.303,  4.538,  1.729,  0.792,  1.716]),
        "Macaulay 2023 Non-Avian Sauropsid": 
        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"],
         [1.266,  8.646,  1.219,  3.369,  2.852,  2.866,  3.564,  5.102,  2.655,  3.494,  2.553]),
        "Macaulay 2023 Average (Bird and Non-Avian Sauropsid)": 
        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"],
         [1.137,  6.235,  1.328,  3.369,  2.411,  2.301,  2.434,  4.820,  2.192,  2.143,  2.135]),
        "Sellers 2012 Large Mammals":
        (["whole_body"],
         [1.206]),
        },
    "Logarithmic scale factor": { #each segment is scaled according to a power curve
        "Macaulay 2023 Logarithmic Bird": 
        (["head", "neck", "torso", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"], #segment types
         [-0.085, 0.008, 0.213, 0.001, 0.017, 0.124, 0.487, 0.322, -0.402, 0.21], #log intercept
         [0.982, 0.892, 1.018, 0.95, 0.963, 1.012, 0.975, 1.021, 0.946, 1.002], #log slope
#         [0.021, 0.037, 0.017, 0.044, 0.04, 0.057, 0.038, 0.022, 0.018, 0.034]), #log mean squared errors, MSE (can leave 0)
         [0.0,    0.0,  0.0,  0.0,  0.0,  0.0,  0.0,   0.0,   0.0,   0.0]), #log mean squared errors, set to 0 because Macaulay et al reported a different error estimate
#        "Macaulay 2023 Logarithmic All Taxa (Bird and Non-Avian Sauropsid)": 
#        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"],
#         [-0.085,  0.008,	0.213,	0.387,	   0.001,	  0.017,  0.124,   0.487,	0.322,	     -0.402,   0.21], #log intercept
#         [ 0.982,  0.892,	1.018,	0.984,	    0.95,	  0.963,  1.012,   0.975,	1.021,        0.946,  1.002], #log slope
#         [ 0.027,  0.033,	0.016,	0.079,	    0.04,	  0.037,  0.051,   0.032,	0.021,	      0.022,  0.038]),#log mean squared errors, MSE (can leave 0)
        "Macaulay 2023 Logarithmic Non-Avian Sauropsid":
        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"],
         [0.002,    0.73,	  0.2,	0.387,     0.888,	  0.677,  1.127,   0.951,	0.788,	      0.908,  0.745],#log intercept
         [0.978,   0.961,	1.039,	0.984,	    1.09,	  1.045,  1.106,   1.051,	1.075,	      1.074,  1.067],#log slope
#         [0.034,   0.028,	0.017,	0.079,	   0.041,	  0.038,   0.04,   0.029,	0.029,	      0.046,  0.068]),#log mean squared errors, MSE (can leave 0)
         [0.0,    0.0,  0.0,  0.0,  0.0,  0.0,  0.0,   0.0,   0.0,   0.0]), #log mean squared errors, set to 0 because Macaulay et al reported a different error estimate
        "Coatham 2021 Logarithmic Mammal (rewritten volumetric)":
        (["upperarm", "forearm",  "hand",	"thigh",	"shank",	"foot",	"head",	"neck",	"torso", "tail1", "tail2", "tail3",	"tail4"],
         [-0.0576,   -0.02998,      -0.237,  0.378,   -0.0631,    -0.0368, -0.0908, 0.0898,-0.0338,-0.0375,  -0.287,  -0.361,   -0.411],#log intercept
         [8.79E-01, 9.09E-01,  9.51E-01,   9.43E-01,  9.21E-01,  9.90E-01,9.35E-01, 8.71E-01,9.35E-01,8.90E-01,8.70E-01,8.84E-01,8.74E-01],#log slope
         [5.72E-02, 4.96E-02, 4.11E-04, 1.10E-01,  2.56E-03,   7.80E-04, 2.22E-02, 2.06E-01, 0, 2.37E-04, 1.15E-03, 1.98E-04, 8.93E-05]),#log mean squared errors, MSE (can leave 0)
       
        },




    "Logarithmic whole body mass": { #estimate whole body mass using a power curve of convex hulls of the whole body
        "Wright 2024 Logarithmic Tetrapods":
        (["whole_body"],
         [0.215],#log intercept. They have density as a separate parameter, which would add 3*0.968 to this number
         [0.968],#log slope
         [0.0]),#log mean squared errors, MSE (can leave 0)
        "Brassey 2018 Logarithmic Primates":
        (["whole_body"],
         [3.17],#log intercept
         [1.02],#log slope
         [0.0]),#log mean squared errors, MSE (can leave 0)
         "Brassey 2016 Logarithmic Pigeons, Eviscerated": #
        (["whole_body"],
         [2.7],#log intercept (converted from -2.31, because the original study uses mm3 as input and g as output)
         [0.89],#log slope
         [0.0]),#log mean squared errors, MSE (can leave 0)
         "Brassey 2016 Logarithmic Pigeons, Combined": #
        (["whole_body"],
         [2.57],#log intercept (converted from -2.08, because the original study uses mm3 as input and g as output)
         [0.85],#log slope
         [0.0]),#log mean squared errors, MSE (can leave 0)
         "Brassey 2014 Logarithmic Primates":
        (["whole_body"],
         [3.24],#log intercept
         [1.07],#log slope
         [0.004]),#log mean squared errors, MSE (can leave 0)
        "Brassey 2014 Logarithmic Mammals": ##these should be split off for a "compute properties directly from hull" panel
        (["whole_body"],
         [3.09],#log intercept
         [0.92],#log slope
         [0.005]),#log mean squared errors, MSE (can leave 0)
        },

    "Logarithmic segment inertial properties": {
        "Coatham 2021 Logarithmic Mammals":
        (['arm_l_mass', 'arm_l_cmx', 'arm_l_cmy', 'arm_l_cmz', 'arm_l_Ixx', 'arm_l_Iyy', 'arm_l_Izz', 'arm_l_Ixy', 'arm_l_Ixz', 'arm_l_Iyz', 'forearm_l_mass', 'forearm_l_cmx', 'forearm_l_cmy', 'forearm_l_cmz', 'forearm_l_Ixx', 'forearm_l_Iyy', 'forearm_l_Izz', 'forearm_l_Ixy', 'forearm_l_Ixz', 'forearm_l_Iyz', 'hand_l_mass', 'hand_l_cmx', 'hand_l_cmy', 'hand_l_cmz', 'hand_l_Ixx', 'hand_l_Iyy', 'hand_l_Izz', 'hand_l_Ixy', 'hand_l_Ixz', 'hand_l_Iyz', 'thigh_l_mass', 'thigh_l_cmx', 'thigh_l_cmy', 'thigh_l_cmz', 'thigh_l_Ixx', 'thigh_l_Iyy', 'thigh_l_Izz', 'thigh_l_Ixy', 'thigh_l_Ixz', 'thigh_l_Iyz', 'shank_l_mass', 'shank_l_cmx', 'shank_l_cmy', 'shank_l_cmz', 'shank_l_Ixx', 'shank_l_Iyy', 'shank_l_Izz', 'shank_l_Ixy', 'shank_l_Ixz', 'shank_l_Iyz', 'foot_l_mass', 'foot_l_cmx', 'foot_l_cmy', 'foot_l_cmz', 'foot_l_Ixx', 'foot_l_Iyy', 'foot_l_Izz', 'foot_l_Ixy', 'foot_l_Ixz', 'foot_l_Iyz', 'head_mass', 'head_cmx', 'head_cmy', 'head_cmz', 'head_Ixx', 'head_Iyy', 'head_Izz', 'head_Ixy', 'head_Ixz', 'head_Iyz', 'neck_mass', 'neck_cmx', 'neck_cmy', 'neck_cmz', 'neck_Ixx', 'neck_Iyy', 'neck_Izz', 'neck_Ixy', 'neck_Ixz', 'neck_Iyz', 'torso_mass', 'torso_cmx', 'torso_cmy', 'torso_cmz', 'torso_Ixx', 'torso_Iyy', 'torso_Izz', 'torso_Ixy', 'torso_Ixz', 'torso_Iyz', 'tail1_mass', 'tail1_cmx', 'tail1_cmy', 'tail1_cmz', 'tail1_Ixx', 'tail1_Iyy', 'tail1_Izz', 'tail1_Ixy', 'tail1_Ixz', 'tail1_Iyz', 'tail2_mass', 'tail2_cmx', 'tail2_cmy', 'tail2_cmz', 'tail2_Ixx', 'tail2_Iyy', 'tail2_Izz', 'tail2_Ixy', 'tail2_Ixz', 'tail2_Iyz', 'tail3_mass', 'tail3_cmx', 'tail3_cmy', 'tail3_cmz', 'tail3_Ixx', 'tail3_Iyy', 'tail3_Izz', 'tail3_Ixy', 'tail3_Ixz', 'tail3_Iyz', 'tail4_mass', 'tail4_cmx', 'tail4_cmy', 'tail4_cmz', 'tail4_Ixx', 'tail4_Iyy', 'tail4_Izz', 'tail4_Ixy', 'tail4_Ixz', 'tail4_Iyz'],
         [3.05E-01, 4.45E-04, 1.01E-03, -5.82E-04, 2.60E-01, 3.04E-01, 2.91E-01, -2.55E-03, -1.43E-02, -1.23E-03, 2.44E-01, -3.96E-07, -1.33E-03, -7.07E-04, 2.43E-01, 2.69E-01, 2.62E-01, 8.19E-04, 8.08E-04, -3.05E-06, -9.11E-02, -1.25E-04, 6.57E-04, 9.64E-04, -1.40E-01, -9.20E-02, -9.14E-02, -1.30E-04, -8.20E-05, -7.49E-06, 5.49E-01, -1.86E-03, 2.74E-04, -1.95E-03, 5.72E-01, 5.76E-01, 4.82E-01, 2.33E-05, 7.82E-04, -1.29E-03, 1.74E-01, -1.47E-03, 7.55E-04, -1.75E-03, 1.32E-01, 1.19E-01, 8.12E-02, 1.52E-05, 2.21E-05, -6.29E-05, -6.52E-03, -2.90E-03, -5.62E-05, 1.24E-03, -1.52E-03, -2.83E-02, -1.74E-02, -1.76E-05, 1.26E-06, 6.71E-06, 1.06E-01, 8.99E-05, -2.12E-04, 3.96E-03, 6.40E-02, 9.28E-02, 8.89E-02, -5.84E-05, 4.08E-03, -2.62E-05, 4.77E-01, 4.51E-04, -1.96E-03, -1.66E-03, 5.25E-01, 5.14E-01, 4.96E-01, 3.83E-04, -2.78E-02, 2.32E-04, 1.61E-01, 2.09E-03, 4.66E-04, 4.21E-04, 9.29E-02, 1.00E-01, 8.80E-02, -2.28E-03, -7.49E-02, -3.12E-03, 2.94E-01, 1.16E-04, 7.10E-04, -1.19E-03, 3.57E-01, 3.51E-01, 1.42E-01, 1.66E-06, 3.23E-05, -3.10E-06, 1.03E-01, 9.40E-04, 3.98E-04, -2.59E-04, 2.09E-01, 1.95E-01, 1.03E-02, 1.05E-06, 1.17E-04, -6.46E-06, -1.39E-02, -2.71E-03, 8.55E-05, -6.91E-04, 1.35E-01, 9.76E-02, -6.26E-02, 4.52E-07, 1.09E-04, -3.60E-07, -3.40E-02, -5.52E-03, -1.11E-04, 1.29E-04, 1.05E-01, 7.00E-02, -2.14E-02, 1.25E-07, 1.09E-04, -2.40E-07], #log intercept
         [8.79E-01, 9.91E-01, 9.82E-01, 1.01E+00, 9.25E-01, 9.26E-01, 9.25E-01, 1.83E+00, 1.85E+00, 1.84E+00, 9.09E-01, 1.00E+00, 1.01E+00, 1.08E+00, 9.52E-01, 9.50E-01, 9.50E-01, 2.24E+00, 2.34E+00, 2.07E+00, 9.51E-01, 9.90E-01, 9.91E-01, 9.84E-01, 9.68E-01, 9.72E-01, 9.72E-01, 7.74E-01, 8.42E-01, 8.67E-01, 9.43E-01, 8.73E-01, 1.04E+00, 1.05E+00, 9.70E-01, 9.72E-01, 9.49E-01, 3.84E+00, 4.52E+00, 3.77E+00, 9.21E-01, 9.04E-01, 1.02E+00, 1.04E+00, 9.52E-01, 9.54E-01, 9.45E-01, 1.54E+00, 1.50E+00, 1.51E+00, 9.90E-01, 9.90E-01, 1.01E+00, 9.65E-01, 9.95E-01, 1.00E+00, 9.98E-01, 8.70E-01, 1.68E+00, 1.85E+00, 9.35E-01, 9.98E-01, 1.25E+00, 9.95E-01, 9.52E-01, 9.60E-01, 9.61E-01, 2.45E+00, 1.43E+00, 2.52E+00, 8.71E-01, 9.98E-01, 1.01E+00, 1.01E+00, 9.46E-01, 9.31E-01, 9.27E-01, 8.13E+00, 3.44E+00, 7.96E+00, 9.35E-01, 9.28E-01, 5.76E-01, 9.85E-01, 9.61E-01, 9.65E-01, 9.66E-01, 6.74E-01, 1.18E+00, 3.54E-01, 8.90E-01, 9.76E-01, 8.39E-01, 1.01E+00, 9.45E-01, 9.43E-01, 9.17E-01, 7.68E+00, 2.06E+00, 6.58E+00, 8.70E-01, 9.98E-01, 9.10E-01, 1.00E+00, 9.39E-01, 9.35E-01, 9.16E-01, 1.85E+00, 1.76E+00, 1.89E+00, 8.84E-01, 9.77E-01, 1.27E+00, 1.01E+00, 9.55E-01, 9.45E-01, 9.18E-01, 1.82E+00, 1.08E+00, 1.85E+00, 8.74E-01, 9.78E-01, 1.16E+00, 1.00E+00, 9.42E-01, 9.30E-01, 9.16E-01, 1.19E+00, 1.00E+00, 1.17E+00], #log slope
         [5.72E-02, 2.50E-05, 6.50E-06, 4.65E-05, 1.07E-03, 2.00E-01, 1.84E-01, 2.59E-04, 2.00E-02, 1.90E-05, 4.96E-02, 2.89E-06, 7.52E-06, 2.60E-05, 2.40E-04, 1.13E-02, 1.03E-02, 3.98E-04, 7.16E-04, 3.51E-05, 4.11E-04, 2.15E-05, 5.26E-07, 5.01E-06, 3.51E-08, 4.55E-05, 4.64E-05, 1.79E-06, 2.00E-07, 1.20E-09, 1.10E-01, 3.05E-05, 1.17E-05, 4.47E-05, 6.97E-03, 6.17E-03, 4.30E-05, 1.33E-06, 2.93E-05, 3.12E-04, 2.56E-03, 9.09E-06, 3.16E-06, 2.54E-05, 4.33E-06, 1.49E-06, 1.11E-06, 4.69E-08, 4.88E-08, 1.14E-06, 7.80E-04, 1.34E-05, 4.22E-07, 2.92E-06, 1.62E-07, 1.74E-07, 5.47E-07, 7.92E-08, 9.13E-10, 1.40E-09, 2.22E-02, 1.58E-05, 1.99E-06, 3.54E-05, 3.62E-03, 4.83E-02, 2.69E-02, 1.76E-05, 1.05E-02, 3.31E-06, 2.06E-01, 5.45E-05, 1.68E-05, 1.59E-05, 4.34E-02, 5.96E-01, 3.24E-01, 7.61E-06, 1.15E-01, 2.38E-06, 1.17E+01, 7.28E-05, 7.16E-06, 5.79E-05, 1.36E+00, 5.05E+00, 1.29E+00, 2.02E-03, 9.07E-01, 6.79E-03, 2.37E-04, 7.25E-06, 9.11E-07, 5.24E-06, 1.34E-05, 1.36E-05, 1.42E-09, 1.92E-11, 7.67E-09, 6.66E-10, 1.15E-03, 7.36E-06, 2.58E-07, 8.89E-07, 2.14E-03, 2.59E-03, 8.13E-07, 6.82E-10, 1.13E-04, 1.39E-08, 1.98E-04, 2.09E-05, 1.06E-06, 4.16E-06, 5.65E-04, 7.50E-04, 8.40E-07, 5.12E-10, 7.21E-05, 1.58E-09, 8.93E-05, 5.04E-05, 3.86E-07, 3.56E-07, 1.94E-04, 4.58E-04, 8.82E-06, 8.66E-10, 1.05E-04, 2.96E-09]) #log mean squared errors
        }    
}

