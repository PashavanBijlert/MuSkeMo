import bpy

from bpy.props import (StringProperty,
                        IntProperty,
                         PointerProperty,
                         FloatProperty,
                         BoolProperty,
                         EnumProperty,
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
        max = 100,
        precision = 5,
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
        max = 100,
        precision = 5,
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
    
    muscle_visualization_radius: FloatProperty(
        name = "Muscle visualization radius",
        description="Global visualization radius for newly created muscles",
        default = 0.015,
        min = 0,
        max = 100,
        precision = 5,
        step = 0.0025,
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


    model_export_directory: StringProperty(
        name = "Model export directory",
        description="Absolute filepath to the directory where you would like to export your model files",
        default = "",
        maxlen = 1024,
        )


    significant_digits: IntProperty(
        name = "Export significant digits",
        description="Significant digits in your data export",
        default = 4,
        min = 2,
        max = 8,
        )
    
        
    number_format: EnumProperty(
        name="Number format",
        description="Number format during export. Scientific notatation and general use significant digits, Fixed point always uses 8 decimals. See Python documentation",
        items=[ ('e', "Scientific notation", ""),
                ('g', "General format", ""),
                ('8f', "Fixed point 8 decimals", ""),
              ],
        default = "g",
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
    
    ARF_axes_size: FloatProperty(
        name = "Reference frame axes display size",
        description="Display size of the axes for newly created reference frames, in meters",
        default = 0.075,
        min = 1e-12,
        max = 100,
        precision = 5,
        )


#### landmark and marker panel

    landmark_name: StringProperty(
        name = "Landmark name",
        description="Desired name of the landmark or marker",
        default = "Landmark",
        maxlen = 1024,
        )
    
    landmark_collection: StringProperty(
        name = "Landmark collection",
        description="Name of the collection (ie. folder) that contains the landmarks and markers",
        default = "Landmarks",
        maxlen = 1024,
        )
    
    landmark_radius: FloatProperty(
        name = "Landmark radius",
        description="Landmark visualization radius, in meters",
        default = 0.001,
        min = 1e-12,
        max = 100,
        precision = 5,
        )
    

#### contact panel

    contact_name: StringProperty(
        name = "Contact sphere name",
        description="Desired name of the contact sphere",
        default = "contact",
        maxlen = 1024,
        )
    
    contact_collection: StringProperty(
        name = "Contact collection",
        description="Name of the collection (ie. folder) that contains the contacts",
        default = "Contacts",
        maxlen = 1024,
        )
    
    contact_radius: FloatProperty(
        name = "Contact sphere radius",
        description="Contact sphere radius, in meters",
        default = 0.015,
        min = 1e-12,
        max = 100,
        precision = 5,
        )