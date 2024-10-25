import bpy

from bpy.props import (StringProperty,
                        IntProperty,
                         PointerProperty,
                         FloatProperty,
                         BoolProperty,
                         EnumProperty,
                         FloatVectorProperty,
                         IntVectorProperty,
                         CollectionProperty,
                         )
from bpy.types import (PropertyGroup,
                        )
from .inertial_properties_panel import (SegmentParameterItem, #to fix the dependency for the scale factor list.
                                        update_expansion_type_arithmetic,
                                        update_expansion_type_logarithmic, InertialPropertiesPresets)
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
    
    wrap_geom_collection: StringProperty(
        name = "Wrap Geometry collection",
        description="Name of the collection (ie. folder) that contains the wrap geometry",
        default = "Wrapping geometry",
        maxlen = 1024,
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


    skeletal_mesh_collection: StringProperty(
        name = "Skeletal mesh collection",
        description="Name of the collection (ie. folder) that contains the skeletal meshes that you would like to generate convex hulls for",
        default = "Geometry",
        maxlen = 1024,
        ) 
    
    convex_hull_collection: StringProperty(
        name = "Convex hull collection",
        description="Name of the collection (ie. folder) that contains (or will contain) convex hulls based on the skeleton",
        default = "Convex hulls",
        maxlen = 1024,
        ) 
    
#### Dynamic scaling panel part of inertial properties panel
    segment_parameter_list_arithmetic: CollectionProperty(type=SegmentParameterItem)
    segment_parameter_list_logarithmic: CollectionProperty(type=SegmentParameterItem)

    expansion_type_arithmetic: EnumProperty(
        name="Expansion Type (Arithmetic)",
        items=[("Custom", "Custom", "")] + [(key, key, "") for key in InertialPropertiesPresets["Arithmetic"].keys()],
        default="Custom",  # Ensure Custom is default
        update=update_expansion_type_arithmetic
    )

    expansion_type_logarithmic: EnumProperty(
        name="Expansion Type (Logarithmic)",
        items=[("Custom", "Custom", "")] + [(key, key, "") for key in InertialPropertiesPresets["Logarithmic"].keys()],
        default="Custom",  # Ensure Custom is default
        update=update_expansion_type_logarithmic
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

#### import

    model_import_style: EnumProperty(
        name="Model import style",
        description="Import your model assuming global or local definitions",
        items=[ ('glob', "Global definitions", ""),
                ('loc', "Local definitions", ""),
                ],
        default = "loc",
        )
    
    import_visual_geometry: BoolProperty(
        name = 'Import visual geometry',
        description='Should visual geometry meshes attached to bodies be imported? Geometries are placed in a new collection with the name as specified in the bodies file',
        default = True,
    )

    enable_wrapping_on_import: BoolProperty(
        name = 'Enable wrapping during import (experimental)',
        description='Enable wrapping for imported muscles. Currently experimental, it is currently advised to manually add extra viapoints instead for visualization.',
        default = False,
    )

    gaitsym_geometry_folder: StringProperty(
        name = 'Gaitsym geometry folder',
        description="Name of the directory that contains the Gaitsym model's visual geometry. Must be a subdirectory of the model directory",
        default = '',
        maxlen = 256,
    )


    rotate_gaitsym_on_import: IntVectorProperty(
        name = 'Gaitsym import rotation',
        description='XYZ-Body fixed Euler angles (in degrees) for the import rotation of a Gaitsym model. Rotate -90 degrees about X to go from Z-up to Y-up',
        default = (0,0,0),
        min = -90,
        max = 90,
    )

    import_gaitsym_markers_as_frames: BoolProperty(
        name = 'Import Markers as Frames',
        description = 'Markers in Gaitsym models can function both as markers (that define positions) and reference frames (also specifying orientations)',
        default = False,
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
    
#### visualization panel

    number_of_repetitions: IntProperty(
        name = "Number of repetitions",
        description="The number of times you would like to repeat the trajectory (useful for looping strides in an animation)",
        default = 0,
        min = 0,
        max = 100
    )   

    fps :  IntProperty(
        name = "Frames per second",
        description="Target frames per second for the rendered animation. If you want slow-motion, input double the desired playback framerate",
        default = 60,
        min = 1,
        max = 300
    )   

    root_joint_name: StringProperty(
        name = "Root joint name",
        description="Name of the root joint (required if you want to ensure the model progresses with each looped stride)",
        default = "groundPelvis",
        maxlen = 1024,
        )
    
    forward_progression_coordinate: EnumProperty(
        name="Forward progression coordinate",
        description="Name of the coordinate that should progress forward with each stride (required if you want to loop several strides)",
        items=[ ('coordinate_Tx', "coordinate_Tx", ""),
                ('coordinate_Ty', "coordinate_Ty", ""),
                ('coordinate_Tz', "coordinate_Tz", ""),
                ('coordinate_Rx', "coordinate_Rx", ""),
                ('coordinate_Ry', "coordinate_Ry", ""),
                ('coordinate_Rz', "coordinate_Rz", ""),
              ],
        default = "coordinate_Tx",
        )
    
    in_degrees: BoolProperty(
        name="In degrees",
        description='Select this if angles are defined in degrees, but not hardcoded in the header of your .sto file',
        default = False,
    )

    
    muscle_color: FloatVectorProperty(
                 name = "Default muscle color",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (0.22, 0.00, 0.02, 1)
        )
    

    joint_color: FloatVectorProperty(
                 name = "Default joint color",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (0.00, 0.15, 1, 1)
        )
    
    bone_color: FloatVectorProperty(
                 name = "Default bone color",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (1, 0.85, 0.85, 1)
        )
    
    contact_color: FloatVectorProperty(
                 name = "Default contact color",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (0.2, 0.00, 1, 1)
        )
    
    marker_color: FloatVectorProperty(
                 name = "Default marker color",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (0.0, 0.1, 0.01, 1)
        )
    
    geom_primitive_color: FloatVectorProperty(
                 name = "Default geometric primitive color",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (0.55, 0.175, 0.0, 1)
        )
    
    wrap_geom_color: FloatVectorProperty(
                 name = "Wrapping geometry color",
                 subtype = "COLOR",
                 size = 4,
                 min = 0.0,
                 max = 1.0,
                 default = (0.0, 0.0, 0.1, 1)
        )
    
