# **MuSkeMo**

Build and visualize musculoskeletal models in Blender.

To download: Click on the latest release on the right, and download "MuSkeMo.zip".

To install: In Blender, go to Edit > preferences > Add-ons and then click "Install...", and then select your downloaded zip file. Then type in "MuSkeMo" in the search bar of the addon window, and enable the plugin by pressing the check mark.

**Check out the [video tutorial on YouTube](https://www.youtube.com/watch?v=9eMm9YalXtg)**

This README is currently very short and incomplete, more details will be added in due course.

# **Inertial properties panel**

Compute inertial properties from 3D volumetric meshes, eg. from CT-segmentations or surface scans.
Inertial properties are **not dynamic**, if you move the 3D meshes or change their densities, you must recompute their inertial properties, otherwise COM, mass, and or inertia can be outdated.

# **Body panel**

Define rigid bodies, assign precomputed inertial properties, or compute directly by selecting one or several volumetric meshes.
Inertial properties are **not dynamic**, if you move the source objects that the rigid bodies were based on, or change their densities, you must recompute all inertial properties of the body. Otherwise COM, mass, and or inertia can be outdated.

In this panel, you can also attach visualization geometry (eg., bone meshes) to bodies. 

# **Joint panel**

Define joints, and assign (and remove) parent and child bodies. If you want to change a joint location, remove the parent and child bodies first.

You can define the coordinate names for the joints here. Planned behaviour for this is that the conversion scripts will only add DOFs to model if they are named (e.g. hip_angle_r) 

In the joint panel (under joint utilities), you can also mirror right side joints, fit geometric primitives (sphere, cylinder, ellipsoid, plane), and match the transformations of a joint to the fitted geometry. Warning: because inertial properties are not dynamic - if you change the location or rotation of a joint while it has bodies attached to it, their inertial properties will be incorrect. You will have to recompute them in that case. MuSkeMo provides a warning if this may have occured. 

# **Muscle panel**

Define path-point muscles. Muscle points are added to the 3D cursor location, and parented to the selected Body (so you have to define bodies first). 
To add a point, type in the muscle name, and select the target body. Press shift + right mouse button to position the 3D cursor. Muscle points are added to the 3D cursor location.
You can change the locations of the path points by selecting the muscle in edit mode (select the muscle and press "TAB"). If the parent bodies are repositioned, you must delete and redraw the muscles.

# **Anatomical & local reference frames panel**

Construct anatomical and local reference frames, by assigning landmarks or markers as the reference points to construct the axes directions. Local reference frames have a location and an orientation with respect to the global reference frame.
Internally, orientations are stored through rotation matrices, but they can be exported as rotation (unit) quaternions (w, x, y, z), and also as body-fixed XYZ-Euler angles (phi_x, phi_y, phi_z, in rad). The latter is prone to gimbal lock.
As of v0.5.0, you can only export the local frames themselves. All other data types are exported in global coordinates. v0.6.0 will allow you to export data with respect to the locally defined reference frames.

# **Landmark & marker panel**

Similar to muscle points, landmarks are added to the 3D cursor location.

# **Contact panel**

Similar to muscle points, contacts are added to the 3D cursor location. Contacts can also be assigned a parent body.

# **Export panel**

You can export all the user-created datatypes via this panel. The individual exporters export all the data types from the user-designated collections (folders) in Blender. It is possible to export all the visual geometry to a subfolder.

Under export options, it is possible to configure other text-based filetypes for export (e.g., txt, bat), and and configure custom delimiters.

As of v0.5.0, all the exports are only in the global reference frame. v0.6.0 will include both global and local frame export.



# **Import panel**

[in development]
