InertialPropertiesPresets = {
    "Arithmetic": {
        "Macaulay 2023 Bird": 
        (["head", "neck", "torso", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "foot"],
         [1.008,  3.825,  1.436,  1.970,  1.736,  1.303,  4.538,  1.729,  0.792,  1.716]),
        "Macaulay 2023 Non-Avian Sauropsid": 
        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "foot"],
         [1.266,  8.646,  1.219,  3.369,  2.852,  2.866,  3.564,  5.102,  2.655,  3.494,  2.553]),
        "Macaulay 2023 Average": 
        (["head", "neck", "torso", "tail", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "foot"],
         [1.137,  6.235,  1.328,  3.369,  2.411,  2.301,  2.434,  4.820,  2.192,  2.143,  2.135]),
    },
    "Logarithmic": {
        "Macaulay 2023 Logarithmic Bird": 
        (["head", "neck", "torso", "humerus", "forearm", "hand", "thigh", "shank", "metatarsus", "foot"], #segment types
         [-0.085, 0.008, 0.213, 0.001, 0.017, 0.124, 0.487, 0.322, -0.402, 0.21], #log intercept
         [0.982, 0.892, 1.018, 0.95, 0.963, 1.012, 0.975, 1.021, 0.946, 1.002], #log slope
         [0.021, 0.037, 0.017, 0.044, 0.04, 0.057, 0.038, 0.022, 0.018, 0.034]), #log SEE (can leave 0)
        "Macaulay 2023 Logarithmic Non-Avian Sauropsid": 
        (["head", "neck", "tail"],
         [0.002, 0.004, 0.900],
         [0.4, 0.2, 0.6],
         [-0.4, -0.2, -0.6]),
    }
}