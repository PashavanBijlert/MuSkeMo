Unless stated otherwise, all the python scripts in this folder (and subfolders) are intended to be opened and run in Blender's [text editor](https://docs.blender.org/manual/en/latest/editors/text_editor.html).

The Matlab scripts will require installing the [OpenSim API](https://opensimconfluence.atlassian.net/wiki/spaces/OpenSim/pages/53089380/Scripting+with+Matlab)

## Create a frame with Python

Install and enable the MuSkeMo add-on. Open [`FrameCreationScriptExample.py`](FrameCreationScriptExample.py) in Blender's Text Editor and click **Run Script**. The example creates a frame named `myframename` in the `Frames` collection. The frame is one meter along the global X axis, with its axes aligned to the global axes.

To use your own frame, choose a unique object `name` and set the display size in meters (`size`) and rigid transform (`worldMat`). The script passes the last column's first three entries to `create_frame()` as the origin in global coordinates, in meters. It passes the upper-left 3 × 3 block as `gRb`, which rotates vectors from the local frame into global coordinates. Set `collection_name` in the call to choose a different destination. To parent the frame while preserving its global pose, set `parent_body` to the name of an existing MuSkeMo body. The example leaves the frame unparented by default.
