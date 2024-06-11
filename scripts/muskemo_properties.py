import bpy

from bpy.props import (StringProperty,
                        IntProperty,
                         PointerProperty,
                         FloatProperty,
                         )
from bpy.types import (PropertyGroup,
                        )


class MuSkeMoProperties(PropertyGroup):

##### bodies
    body_collection: StringProperty(
        name = "Body collection",
        description="Name of the collection (ie. folder) that contains the bodies",
        default = "Bodies",
        maxlen = 1024,
        )

    bodyname: StringProperty(
        name="Body name",
        description="Body name (including optional side, eg. 'head' or 'thigh_r')",
        default="",
        maxlen=1024,
        )
        
    side_suffix: StringProperty(
        name="Side suffix",
        description="Side suffix, e.g. '_r' for the body 'thigh_r'. Search for bodies with this suffix to mirror.",
        default="_r",
        maxlen=1024,
        )
        
    otherside_suffix: StringProperty(
        name="Other side suffix",
        description="Other side suffix, e.g. '_l' for the body 'thigh_r'. Mirrored bodies get this suffix.",
        default="_l",
        maxlen=1024,
        )    
    
    reflection_plane: StringProperty(
        name="Reflection plane",
        description="Desired reflection plane. Options are 'XY', 'YZ', and 'XZ'",
        default="XY",
        maxlen=1024,
        )    
    
    axes_size: FloatProperty(
        name = "Body axes display size",
        description="Size of the axes for newly created bodies, in meters",
        default = 0.1,
        min = 1e-12,
        max = 100
        )
    
    geometry_collection: StringProperty(
        name="Geometry collection",
        description="Blender collection name in which the visual (bone) geometry will be placed. This will also be the geometry folder name during export.",
        default="Geometry",
        maxlen=1024,
        )
    


#### joints

    jointname: StringProperty(
        name="Joint name",
        description="Joint name (including optional side, eg. 'neck' or 'hip_r')",
        default="",
        maxlen=1024,
        )
        
           
    coor_Rx: StringProperty(
        name="Rx",
        description="name of the Rotational x coordinate",
        default="",
        maxlen=1024,
        )
        
    coor_Ry: StringProperty(
        name="Ry",
        description="name of the Rotational y coordinate",
        default="",
        maxlen=1024,
        )
        
    coor_Rz: StringProperty(
        name="Rz",
        description="name of the Rotational z coordinate",
        default="",
        maxlen=1024,
        )    
            
        
    coor_Tx: StringProperty(
        name="Tx",
        description="name of the Translational x coordinate",
        default="",
        maxlen=1024,
        )
        
    coor_Ty: StringProperty(
        name="Ty",
        description="name of the Translational y coordinate",
        default="",
        maxlen=1024,
        )
        
    coor_Tz: StringProperty(
        name="Tz",
        description="name of the Translational z coordinate",
        default="",
        maxlen=1024,
        )    
        
        
    jointsphere_size: FloatProperty(
        name = "Joint sphere radius",
        description="Joint sphere visualization radius, in meters",
        default = 0.05,
        min = 1e-12,
        max = 100
        )

    joint_collection: StringProperty(
        name = "Joint collection",
        description="Name of the collection (ie. folder) that contains the joints",
        default = "Joint centers",
        maxlen = 1024,
        ) 


#### Muscles
    muscle_collection: StringProperty(
        name = "Muscle collection",
        description="Name of the collection (ie. folder) that contains the muscles",
        default = "Muscles",
        maxlen = 1024,
        ) 

    musclename: StringProperty(
        name="Muscle name",
        description="The muscle name (including side, eg. gastrocnemius_r)",
        default="",
        maxlen=1024,
        )
    
    insert_point_after: IntProperty(
        name = "Insert after",
        description="The muscle point number after which a new point will be inserted, starting at 1 for the origin",
        default = 1,
        min = 1,
        max = 100
        )
    

#### Inertial properties panel

    segment_density: FloatProperty(
        name = "Segment density (in kg m^-3)",
        description="Density in kg m^-3 that you would like to assign to the mesh when computing inertial parameters",
        default = 1000,
        min = 1e-12,
        max = 100000000
        )    


    source_object_collection: StringProperty(
        name = "Collection",
        description="Name of the collection (ie. folder) that contains the soft tissue geometry (meshes)",
        default = "",
        maxlen = 1024,
        ) 
    

#### Export panel

    export_filetype: StringProperty(
        name = "Export filetype",
        description="The filetype you would like to export your data in, e.g., csv or txt. Input in lower case, no period or quotations",
        default = "csv",
        maxlen = 8,
        )
    
    delimiter: StringProperty(
        name = "Delimiter",
        description="The delimiter for your data file (with what character do you want to separate each data entry?). Input without quotations, spaces count as delimiter characters",
        default = ",",
        maxlen = 8,
        )


#### anatomical (local) reference frame panel

    framename: StringProperty(
        name="Frame name",
        description="Name of the new anatomical (local) reference frame",
        default="",
        maxlen=1024,
        )


    or_landmark_name: StringProperty(
        name="Origin",
        description="Name of the landmark that defines the frame origin",
        default="",
        maxlen=1024,
        )

    ydir_landmark_name: StringProperty(
        name="Y direction",
        description="Name of the landmark that defines the y (long-axis) direction",
        default="",
        maxlen=1024,
        )
        
    yz_plane_landmark_name: StringProperty(
        name="YZ plane (temp z)",
        description="Name of the landmark that defines the YZ plane (by defining a temporary z axis)",
        default="",
        maxlen=1024,
        )

    frame_collection: StringProperty(
        name = "Frame collection",
        description="Name of the collection (ie. folder) that contains the anatomical (local) frames",
        default = "Frames",
        maxlen = 1024,
        )
