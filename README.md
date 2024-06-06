**MuSkeMo**

Build and visualize musculoskeletal models in Blender.

To download: Download the latest package on the right, under "Packages"

To install: In Blender, go to Edit > preferences > Add-ons and then click "Install...", and then select your downloaded zip file.

This README is currently very short and incomplete, more details will be added in due course. A video tutorial will be uploaded that demonstrates the functionality of the plugin.

**Inertial properties panel**

Compute inertial properties from 3D volumetric meshes, eg. from CT-segmentations or surface scans.
Inertial properties are **not dynamic**, if you move the 3D meshes or change their densities, you must recompute their inertial properties, otherwise COM, mass, and or inertia can be outdated.

**Body panel**

Define rigid bodies, assign precomputed inertial properties, or compute directly by selecting one or several volumetric meshes.
Inertial properties are **not dynamic**, if you move the source objects that the rigid bodies were based on, or change their densities, you must recompute all inertial properties of the body. Otherwise COM, mass, and or inertia can be outdated.

**Joint panel**

Define joints, and assign (and remove) parent and child bodies. If you want to change a joint location, remove the parent and child bodies first.

**Muscle panel**

Define path-point muscles. Muscle points are added to the 3D cursor location, and parented to the selected Body (so you have to define bodies first).
You can change the locations of the path points by selecting the muscle in edit mode (select the muscle and press "TAB"). If the parent bodies are repositioned, you must redefine the muscles.

**Export panel**

You can currently export Bodies, Joints, and Muscle paths. Under export options, it is possible to configure other text-based filetypes for export (e.g., txt, bat), and and configure custom delimiters.

**Import panel**

[in development]
