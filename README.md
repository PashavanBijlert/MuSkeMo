# **MuSkeMo**

Build and visualize musculoskeletal models in [Blender](https://www.blender.org/). The plugin has been tested in versions between 3.0-4.1.

To download: Click on the latest release on the right, and download "MuSkeMo.zip". The .zip file is used to install the plugin, but also contains a folder with utility functions (e.g., for OpenSim conversion).

To install: In Blender, go to Edit > preferences > Add-ons and then click "Install...", and then select your downloaded zip file. Then type in "MuSkeMo" in the search bar of the addon window, and enable the plugin by pressing the check mark. If using Blender 4.2+, you may need to use the legacy installer.

**Check out the [video tutorial on YouTube](https://www.youtube.com/watch?v=9eMm9YalXtg)**

This README gives an overview of the functionalities, but is not a full documentation. A complete documentation will be created in due course.

# **Inertial properties panel**

Compute inertial properties from 3D volumetric meshes, eg. from CT-segmentations or surface scans.
Inertial properties are **not dynamic**, if you move the 3D meshes or change their densities, you must recompute their inertial properties, otherwise COM, mass, and or inertia can be outdated.

# **Body panel**

Define rigid bodies, assign precomputed inertial properties, or compute directly by selecting one or several volumetric meshes.
Inertial properties are **not dynamic**, if you move the source objects that the rigid bodies were based on, or change their densities, you must recompute all inertial properties of the body. Otherwise COM, mass, and or inertia can be outdated.

In this panel, you can also attach visualization geometry (eg., bone meshes) to bodies. 

# **Joint panel**

Define joints, and assign (and remove) parent and child bodies. If you want to change a joint's position or orientation, detach the parent and child bodies first. If a parent or child body has an anatomical (local) reference frame assigned, MuSkeMo automatically computes the relative positions and orientations in these frames as well. Orientations are stored as body-fixed, XYZ-Euler angles and as quaternions. All data that are created are included during export (if local frames are not assigned, these values will be nan).

It is also possible to define coordinate names in the joint panel. After exporting from MuSkeMo, the model conversion scripts (e.g., MuSkeMo_to_OpenSim) will only add DOFs to model if they are named (e.g. hip_angle_r). If no coordinates are named for a joint, the joint is turne into an immobilized joint (e.g., WeldJoint in OpenSim). 

In the joint panel (under joint utilities), you can also mirror right side joints, fit geometric primitives (sphere, cylinder, ellipsoid, plane), and match the transformations of a joint to the fitted geometry. Warning: because inertial properties are not dynamic - if you change the location or rotation of a joint while it has bodies attached to it, their inertial properties will be incorrect. You will have to recompute them in that case. MuSkeMo provides a warning if this may have occured. 

# **Muscle panel**

Define path-point muscles. Muscle points are added to the 3D cursor location, and parented to the selected Body (so you have to define bodies first). 
To add a point, type in the muscle name, and select the target body. Press shift + right mouse button to position the 3D cursor. Muscle points are added to the 3D cursor location.
You can change the locations of the path points by selecting the muscle in edit mode (select the muscle and press "TAB"). If the parent bodies are repositioned, you must delete and redraw the muscles.

# **Anatomical & local reference frames panel**

Construct anatomical and local reference frames, by assigning landmarks or markers as the reference points to construct the axes directions. Local reference frames have a location and an orientation with respect to the global reference frame.
Internally, orientations are stored through rotation matrices, but are exported as rotation (unit) quaternions (w, x, y, z), and also as body-fixed (intrinsic, active) XYZ-Euler angles (phi_x, phi_y, phi_z, in rad). The latter is prone to gimbal lock. If anatomical / local frames are assigned to a body, MuSkeMo also computes inertial properties, joint positions and orientations, contact positions, and muscle path points with respect to these frames.


# **Landmark & marker panel**

Similar to muscle points, landmarks are added to the 3D cursor location.

# **Contact panel**

Similar to muscle points, contacts are added to the 3D cursor location. Contacts can also be assigned a parent body.

# **Export panel**

You can export all the user-created datatypes via this panel. The individual exporters export all the data types from the user-designated collections (folders) in Blender. It is possible to export all the visual geometry to a subfolder.

MuSkeMo exports all the data with respect to both the global reference frame (origin), and body-fixed local reference frames. Orientations are exported as XYZ-Euler angle decompositions, and as quaternion decompositions.

Under export options, it is possible to configure other text-based filetypes for export (e.g., txt, bat), configure custom delimiters, and choose the number formatting in the exported files.


# **Import panel**

You can currently import bodies, joints, muscles, frames, and contacts, if they are MuSkeMo-created CSV files.

MuSkeMo also provides an OpenSim importer. Currently, this only works with OpenSim models that were created using the MuSkeMo_to_OpenSim utility script (see below), using global-coordinates. A more generic OpenSim importer is planned for version 0.8.0.

As of version 0.7.1, development for a Gaitsym (2019) importer has been started. It is currently not fully-featured.

Future updates will also support Hyfydy model import.

# **Visualization panel**

MuSkeMo enables you to import simulated trajectories back into Blender to create high-quality animations with complex camera movements. This panel features a trajectory importer (currently OpenSim .sto format only) that has the optional feature to repeat the trajectory in a loop while progressing the forward translation coordinate (useful for simulations of a single stride). This panel also includes several convenience tools to aid users who are new to animations in Blender. 

Users are able to define their desired default colors in this panel (currently only muscle color has been exposed to the user).

# **MuSkeMo utilities**

The MuSkeMo.zip release contains a folder with MuSkeMo utlities. This includes a MuSkeMo_to_OpenSim.m Matlab script to convert your MuSkeMo outputs to an OpenSim model. You must have the [OpenSim Matlab API](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53089380/Scripting+with+Matlab) installed. 

It also contains an updater (Python) script to update older MuSkeMo scenes to v0.6.3 and up. To run this, open the python script in the Blender script editor and run it. Back up your work first.
