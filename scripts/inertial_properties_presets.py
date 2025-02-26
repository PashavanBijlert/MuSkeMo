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
         [0.021, 0.037, 0.017, 0.044, 0.04, 0.057, 0.038, 0.022, 0.018, 0.034]), #log mean squared errors, MSE (can leave 0)
        "Macaulay 2023 Logarithmic All Taxa (Bird and Non-Avian Sauropsid)": 
        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"],
         [-0.085,  0.008,	0.213,	0.387,	   0.001,	  0.017,  0.124,   0.487,	0.322,	     -0.402,   0.21], #log intercept
         [ 0.982,  0.892,	1.018,	0.984,	    0.95,	  0.963,  1.012,   0.975,	1.021,        0.946,  1.002], #log slope
         [ 0.027,  0.033,	0.016,	0.079,	    0.04,	  0.037,  0.051,   0.032,	0.021,	      0.022,  0.038]),#log mean squared errors, MSE (can leave 0)
        "Macaulay 2023 Logarithmic Non-Avian Sauropsid":
        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "pes"],
         [0.002,    0.73,	  0.2,	0.387,     0.888,	  0.677,  1.127,   0.951,	0.788,	      0.908,  0.745],#log intercept
         [0.978,   0.961,	1.039,	0.984,	    1.09,	  1.045,  1.106,   1.051,	1.075,	      1.074,  1.067],#log slope
         [0.034,   0.028,	0.017,	0.079,	   0.041,	  0.038,   0.04,   0.029,	0.029,	      0.046,  0.068]),#log mean squared errors, MSE (can leave 0)
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
        }
}