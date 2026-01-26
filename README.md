# **MuSkeMo**

![Horse multipanel figure](./MuSkeMo%20manual/figures/Multipanel%20figure%20cropped.png?raw=true)

Build and visualize musculoskeletal models in [Blender](https://www.blender.org/). The plugin has been tested in Blender versions between 4.1-4.5, and the 5.0 Beta (for which support is currently experimental).

To download: Navigate to the [releases page](https://github.com/PashavanBijlert/MuSkeMo/releases) and download the most recent version of "MuSkeMo.zip". The .zip file is used to install the plugin, but also contains a folder with utility functions (e.g., for OpenSim conversion).

To install: In Blender, go to Edit > preferences > Add-ons and then click "Install...", and then select your downloaded zip file. Then type in "MuSkeMo" in the search bar of the addon window, and enable the plugin by pressing the check mark. If using Blender 4.2+, you may need to use the legacy installer. Installation (including without administrator privileges) is covered in the first video tutorial.

# **How to use**

**Check out the [video tutorial series on YouTube](https://youtube.com/playlist?list=PLfgxaucAWlEp5-cavvXmdrTIWYT_tgZYK&si=PxcQh2DkdoQNeOAC)**. 

**Download the [MuSkeMo user manual](https://github.com/PashavanBijlert/MuSkeMo/blob/main/MuSkeMo%20manual/MuSkeMo%20manual.pdf)**. The user manual gives detailed instructions on how to use the plugin, and is also included with MuSkeMo.zip. 

# **Preprint**

I am preparing a publication to submit for peer-review describing MuSkeMo. Until that is available, please cite the [preprint on bioRxiv](https://www.biorxiv.org/content/10.1101/2024.12.10.627828v1) if you used MuSkeMo for your work.

PA van Bijlert. MuSkeMo: Open-source software to construct, analyze, and visualize human and animal musculoskeletal models and movements in Blender. bioRxiv (preprint) 2024.12.10.627828; doi: https://doi.org/10.1101/2024.12.10.627828 

# **Using MuSkeMo**

After installation, all of MuSkeMo's features can be accessed via its panels. The user manual gives detailed instructions on how to use them, but they are summarized below in this README. In general, MuSkeMo's panels work by selection and button pressing, and MuSkeMo gives informative error messages if you did something incorrectly.


# **Inertial properties panel**

Compute inertial properties from 3D volumetric meshes, eg. from CT-segmentations or surface scans. Inertial properties are not dynamic, if you move the 3D meshes or change their densities, you must recompute their inertial properties, otherwise COM, mass, and or inertia can be outdated. This panel also allows you to generate convex hulls, and expand them on a per-segment basis using empirical equations.

![convex_hull_gif](https://github.com/user-attachments/assets/72c2b4c0-ace9-44c6-9789-4a5650504f40)


# **Body panel**

Define rigid bodies, assign precomputed inertial properties, or compute directly by selecting one or several volumetric meshes. In this panel, you can also attach visualization geometry (eg., bone meshes) to bodies. 

# **Joint panel**

Define joints, and assign (and remove) parent and child bodies. If you want to change a joint's position or orientation, detach the parent and child bodies first. If a parent or child body has an anatomical (local) reference frame assigned, MuSkeMo automatically computes the relative positions and orientations in these frames as well. Orientations are stored as body-fixed, XYZ-Euler angles and as quaternions. All data that are created are included during export (if local frames are not assigned, these values will be nan).

It is also possible to define coordinate names in the joint panel. After exporting from MuSkeMo, the model conversion scripts (e.g., MuSkeMo_to_OpenSim) will only add DOFs to model if they are named (e.g. hip_angle_r). If no coordinates are named for a joint, the joint is turne into an immobilized joint (e.g., WeldJoint in OpenSim). 

In the joint panel (under joint utilities), you can also fit geometric primitives (sphere, cylinder, ellipsoid, plane), and match the transformations of a joint to the fitted geometry. By default, MuSkeMo ensures that child objects and parent objects are not transformed with the joint. Instead, only the joint's position or orientation is changed, and related data (e.g., pos_in_child) are recomputed automatically.

![object_fit](https://github.com/user-attachments/assets/18241aab-5354-4967-89fb-4f4a11bf57e4)


# **Muscle panel**

Define path-point muscles. Muscle points are added to the 3D cursor location, and parented to the selected Body (so you have to define bodies first). 
To add a point, select the muscle and the target body. Press shift + right mouse button to position the 3D cursor. Muscle points are added to the 3D cursor location.
You can change the locations of the path points by selecting the muscle in edit mode (select the muscle and press "TAB").

Muscles can be visualized using a volume-accurate visualizer, and these visualizations can be customized in a parametric manner using the modifier inputs, and by changing the shape curve.
![muscle_settings](https://github.com/user-attachments/assets/b6a37b56-b9e7-466a-931a-0f4f2dfa603c)

![muscle_belly_shape](https://github.com/user-attachments/assets/30f2d5ba-8799-425b-adc5-0d5375637b69)

Within the muscle panel, it is also possible to create wrapping geometry (currently, only cylinders are supported), and assign these to muscles.

It is possible to compute moment arms and muscle lengths in the Muscle Panel, and these can be recomputed on the fly when changing muscle paths. A live length viewer can help tune musculotendon parameters, especially when combined with imported kinematics.

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

MuSkeMo also provides an OpenSim importer. The default behavior is to import using local frame definitions - as is common with OpenSim models. This involves reconstructing all the local frames defined in the parent and child frame data of each joint, and reconstructing all the 3D transformations with respect to these data. The MuSkeMo importer also saves the global positions and orientations of the model components, and reconstructs the Moment of Inertia about the COM in the global frame using gRb * MOI_b * bRg, where gRb is the matrix that expresses the body-fixed local frame in the global reference frame.

If your OpenSim model was constructed using global definitions using the MuSkeMo_to_OpenSim script, you can also select a global import. This option does not reconstruct any local frames.

OpenSim model geometry should either be placed in a subdirectory of the model directory, or in the same directory as the model file (.osim file) itself. If placed in a subdirectory to the model directory, the subdirectory should either be named "Geometry", or can have a custom name defined in the "mesh_file" field in the body (e.g., 'customsubdirectory/skull.obj'). 

MuSkeMo includes a Gaitsym (2019) importer. It imports bodies, joints, muscles, and contact spheres (DampedSpring elements are treated as muscles). Muscles wrapping is currently not supported. Visual geometry can be imported, but requires the user to type the name of the containing folder in "Gaitsym geometry folder". The geometries must be in a subdirectory of the model directory. It is possible to rotate a Gaitsym model upon import.

A MuJoCo importer is currently being developed, and future updates will also support Hyfydy model import.

# **Visualization panel**

MuSkeMo enables you to import simulated trajectories back into Blender to create high-quality animations with complex camera movements. This panel features a trajectory importer (including OpenSim .sto, .mot, and custom filetypes such as .csv) that has the optional feature to repeat the trajectory in a loop while progressing the forward translation coordinate (useful for simulations of a single stride). This panel also includes several convenience tools to aid users who are new to animations in Blender. 

Users are able to define their desired default colors in this panel.

# **Reflection panel**

This panel allows you to create symmetric models, by only defining components on a single side and then reflecting them to the other side. The panel searches for objects that have a 'side string' (e.g. '_l' or '_r') at the end of their name. You can choose your own side string.

# **MuSkeMo utilities**

The MuSkeMo.zip release contains a folder with MuSkeMo utlities. This includes a MuSkeMo_to_OpenSim.m Matlab script to convert your MuSkeMo outputs to an OpenSim model. You must have the [OpenSim Matlab API](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53089380/Scripting+with+Matlab) installed. This folder also includes python scripts that can be run in Blender's script editor, including pose sampling scripts, a muscle line of action fitter,  moment arms analyses, and some demo scripts that show you how to access MuSkeMo functionality via the Python API.
