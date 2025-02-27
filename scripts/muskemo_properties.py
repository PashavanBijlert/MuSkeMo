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


from .inertial_properties_presets import InertialPropertiesPresets  #import the presets, that can be extended by the user

#### for the dynamic panel that allows the user to input different scale factor templates for inertial properties / convex hull scaling
####  This group is used multiple times within MuSkeMoProperties, so it needs to be registered first! 
#  Define the properties for segment parameters
class SegmentParameterItem(PropertyGroup):
    body_segment: StringProperty(name="Body Segment Name", 
                                 description = "Body segment name, all objects in the convex hull collection that contain this string in their name will be expanded",
                                 default="Segment")
    scale_factor: FloatProperty(name="Scale Factor",
                                description = 'Arithmetic scale factor. Convex hull volume will be scaled by this number',
                                  default=1.0, precision=3, step=0.1)
    log_intercept: FloatProperty(name="Log Intercept", 
                                 description = "Y-intercept of the regression for the expansion factor in log mode",
                                 default=0.0, precision=3, step=0.1)
    log_slope: FloatProperty(name="Log Slope",
                             description = "Slope of the regression for the expansion in log mode",
                               default=1.0, precision=3, step=0.1)
    log_MSE: FloatProperty(name="Log MSE", 
                           description = "Mean Squared Error of the log regression, used to correct the expansion when transforming from log back to arithmetic scale factors. Optional",
                           default=0.0, precision=3, step=0.1)
####




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

    wrap_geom_type: EnumProperty(
        name="Wrapping geometry type",
        description="What type of geometry would you like to create?",
        items=[ ('Cylinder', "Cylinder", ""),
                  ],
        default = "Cylinder",
        )
    
    wrap_geom_name: StringProperty(
        name = "Wrap Geometry Name",
        description="Desired name of the wrapping geometry that you would like to create.",
        default = "",
        maxlen = 1024,
        )


    parametric_wraps: BoolProperty(
        name = 'Parametric Wraps',
        description='If selected, newly created wraps will remain parametric using Blender drivers. This can reduce performance if importing a model with a lot of wrapping.',
        default = False,
    )

### muscle panel extra tooltips


    show_muscle_tooltips: BoolProperty(
        name = 'Show Muscle Tooltips',
        description = 'Press this button to display extra tooltips related to muscle creation',
        default=True,
    )

# moment arms subpanel

    # active_joint_1: StringProperty(
    #     name="Active Joint 1",
    #     description="The name of the joint that will be rotated for moment arm computations",
    #     default="",
    #     maxlen=1024,
    #     )
    

    joint_1_dof: EnumProperty(
        name="Joint 1 DOF",
        description="Which (local) rotational degree of freedom of Active Joint 1 are you interested in for the moment arm computation?",
        items=[ ('Rx', "Rx", ""),
                ('Ry', "Ry", ""),
                ('Rz', "Rz", ""),
              ],
        default = "Rz",
        )
    
    joint_1_ranges: IntVectorProperty(
          name="Joint 1 ranges (deg)",
        size=2,  #
        default=(0,0),
        description="Min and max joint angles (in degrees) for Active Joint 1, between which you would like to compute the moment arm."
        )
    
    angle_step_size: FloatProperty(
        name = "Angle step size",
        description="Step size (in degrees) of the joint angle for the moment arm computations. Lower is slower.",
        default = 1,
        min = 0.0000001,
        max = 1
        )    
    

    export_length_and_moment_arm: BoolProperty(
        name="Export length and moment arm",
        description='Export a .CSV of both length and moment arm data. See export panel for file export options',
        default = False,
    )


#### Muscle plotting parameters 



    generate_plot_bool: BoolProperty(
        name="Generate plot",
        description='Generate plot after computation of moment arms and lengths.',
        default = True,
    )
    
    plot_type: EnumProperty(
        name="Plot type",
        description="Do you want to generate a plot of muscle lengths or moment arms?",
        items=[ ('length', "length", ""),
                ('moment arm', "moment arm", ""),
              ],
        default = "moment arm",
        )


    convert_to_degrees: BoolProperty(
        name="x-axis in degrees",
        description='Plot the data against degrees instead of radians',
        default = True,
    )
        

    xlim: FloatVectorProperty(
          name="x-axis limits",
        size=2,  #
        default=(0,0),
        description="Plotting limits for the x-axis. Scaled according to the data if the input is (0,0)"
        )

    ylim: FloatVectorProperty(
          name="y-axis limits",
        size=2,  #
        default=(0,0),
        description="Plotting limits for the y-axis. Scaled according to the data if the input is (0,0)"
        )    

    plot_lower_left: FloatVectorProperty(
          name="Origin position",
        size=2,  #
        default=(1,1),
        description="Lower left corner position for the plot."
        )
    
    plot_dimensions: FloatVectorProperty(
          name="Plot dimensions",
        size=2,  #
        default=(1,1),
        description="Size of the plot (x and y dimensions)"
        )
    
    plot_font_scale: FloatProperty(
        name = "Font scale",
        description="Scale factor of the plot fonts",
        default = 0.05,
        min = 0.0001,
        max = 1,
        precision = 2,
        step = 0.05,
        )
    
    plot_tick_size: FloatProperty(
        name = "Tick size",
        description="Relative scale of the  axes ticks" ,
        default = 0.2,
        min = 0.0001,
        max = 1,
        precision = 2,
        step = 0.05,
        )
    
    plot_curve_thickness: FloatProperty(
        name = "Plot curve thickness",
        description="How thick would you like the plotted data durve to be." ,
        default = 0.01,
        min = 0.0001,
        max = 1,
        precision = 2,
        step = 0.005,
        )

    plot_ticknumber: IntVectorProperty(
          name= "Axes ticks",
        size=2,  #
        default=(3,3),
        description="Number of ticks for the x and y axes (respectively)"
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
    #the collection property of type segmentparameteritem is defined at the top of this script, and has to be registered first so that MuSkeMoProperties can make use of it
    #the presets contain the actual parameters
    segment_parameter_list_arithmetic: CollectionProperty(type=SegmentParameterItem) #imported class from the inprop panel script
    segment_parameter_list_logarithmic: CollectionProperty(type=SegmentParameterItem) # for logarithmic per segment expansion
    whole_body_mass_logarithmic_parameters: CollectionProperty(type=SegmentParameterItem) #for logarithmic summed ch volume to estimate total body mass
    segment_inertial_logarithmic_parameters: CollectionProperty(type=SegmentParameterItem) #for per segment log ch parameters to directly estimate inertial properties of the segment


    ###these update functions update the collectionproperties, which store the empirical equations in the Blender panel.
    ### update functions for the template enumproperties (extensible panel inputs) below
    # Update function for Arithmetic expansion template
    def update_expansion_template_arithmetic(self, context):
        muskemo = context.scene.muskemo
        segment_parameter_list = muskemo.segment_parameter_list_arithmetic
        segment_parameter_list.clear()

        preset_key = muskemo.expansion_template_arithmetic

        if preset_key == "Custom":
            # Custom case: no prefilling, just set default values
            for i in range(10):
                new_item = segment_parameter_list.add()
                new_item.body_segment = f"Segment {i+1}"
                new_item.scale_factor = 1.0
        else:
            # Use preset data
            preset_data = InertialPropertiesPresets["Arithmetic scale factor"].get(preset_key, ([], []))
            body_segments, factors = preset_data
            for i, segment in enumerate(body_segments):
                new_item = segment_parameter_list.add()
                new_item.body_segment = segment
                new_item.scale_factor = factors[i]

    # Update function for Logarithmic expansion template
    def update_expansion_template_logarithmic(self, context):
        muskemo = context.scene.muskemo
        segment_parameter_list = muskemo.segment_parameter_list_logarithmic
        segment_parameter_list.clear()

        preset_key = muskemo.expansion_template_logarithmic

        if preset_key == "Custom":
            # Custom case: no prefilling, just set default values
            for i in range(3):  # Assuming 3 segments for custom
                new_item = segment_parameter_list.add()
                new_item.body_segment = f"Segment {i+1}"
                new_item.log_intercept = 0.0
                new_item.log_slope = 1.0
                new_item.log_MSE = 0.0
        else:
            # Use preset data
            preset_data = InertialPropertiesPresets["Logarithmic scale factor"].get(preset_key, ([], [], []))
            body_segments, factors1, factors2, factors3 = preset_data
            for i, segment in enumerate(body_segments):
                new_item = segment_parameter_list.add()
                new_item.body_segment = segment
                new_item.log_intercept = factors1[i]
                new_item.log_slope = factors2[i]
                new_item.log_MSE = factors3[i]


    # Update function for Logarithmic whole body mass template #whole body mass estimate from CH
    def update_mass_from_CH_template_logarithmic(self, context):
        muskemo = context.scene.muskemo
        segment_parameter_list = muskemo.whole_body_mass_logarithmic_parameters
        segment_parameter_list.clear()

        preset_key = muskemo.mass_from_CH_template_logarithmic

        if preset_key == "Custom":
            # Custom case: no prefilling, just set default values
            for i in range(3):  # Assuming 3 segments for custom
                new_item = segment_parameter_list.add()
                new_item.body_segment = f"Segment {i+1}"
                new_item.log_intercept = 0.0
                new_item.log_slope = 1.0
                new_item.log_MSE = 0.0
        else:
            # Use preset data
            preset_data = InertialPropertiesPresets["Logarithmic whole body mass"].get(preset_key, ([], [], []))
            body_segments, factors1, factors2, factors3 = preset_data
            for i, segment in enumerate(body_segments):
                new_item = segment_parameter_list.add()
                new_item.body_segment = segment
                new_item.log_intercept = factors1[i]
                new_item.log_slope = factors2[i]
                new_item.log_MSE = factors3[i]  


    # Update function for Logarithmic segment in props template #per segment inertial properties estimate from CH
    def update_segment_inprops_from_CH_template_logarithmic(self, context):
        muskemo = context.scene.muskemo
        segment_parameter_list = muskemo.segment_inertial_logarithmic_parameters
        segment_parameter_list.clear()

        preset_key = muskemo.segment_inprops_from_CH_template_logarithmic

        if preset_key == "Custom":
            # Custom case: no prefilling, just set default values
            for i in range(3):  # Assuming 3 segments for custom
                new_item = segment_parameter_list.add()
                new_item.body_segment = f"Segment {i+1}"
                new_item.log_intercept = 0.0
                new_item.log_slope = 1.0
                new_item.log_MSE = 0.0
        else:
            # Use preset data
            preset_data = InertialPropertiesPresets["Logarithmic segment inertial properties"].get(preset_key, ([], [], []))
            body_segments, factors1, factors2, factors3 = preset_data
            for i, segment in enumerate(body_segments):
                new_item = segment_parameter_list.add()
                new_item.body_segment = segment
                new_item.log_intercept = factors1[i]
                new_item.log_slope = factors2[i]
                new_item.log_MSE = factors3[i]            



    #the templates are for extensible panel inputs
    expansion_template_arithmetic: EnumProperty(
        name="Expansion Template (Arithmetic)",
        items=[("Custom", "Custom", "")] + [(key, key, "") for key in InertialPropertiesPresets["Arithmetic scale factor"].keys()],
        default="Custom",  # Ensure Custom is default
        update=update_expansion_template_arithmetic
    )

    expansion_template_logarithmic: EnumProperty(
        name="Expansion Template (Logarithmic)",
        items=[("Custom", "Custom", "")] + [(key, key, "") for key in InertialPropertiesPresets["Logarithmic scale factor"].keys()],
        default="Custom",  # Ensure Custom is default
        update=update_expansion_template_logarithmic
    )   


    mass_from_CH_template_logarithmic: EnumProperty(
        name="Mass from CH template (Logarithmic)",
        items=[("Custom", "Custom", "")] + [(key, key, "") for key in InertialPropertiesPresets["Logarithmic whole body mass"].keys()],
        default="Custom",  # Ensure Custom is default
        update=update_mass_from_CH_template_logarithmic
    )  

    segment_inprops_from_CH_template_logarithmic: EnumProperty(
        name="Segment inertial properties from CH template (Logarithmic)",
        items=[("Custom", "Custom", "")] + [(key, key, "") for key in InertialPropertiesPresets["Logarithmic segment inertial properties"].keys()],
        default="Custom",  # Ensure Custom is default
        update=update_segment_inprops_from_CH_template_logarithmic
    ) 

    segment_index: IntProperty(name="Active Segment Index",  #this is used internally by the seg inprops from CH panel. THat is such a long list that it should be in a scrollable box in the panel, and that requires a UIList which needs to be passed the index as a property
                               default=-1)

    expanded_hull_collection: StringProperty(
        name = "Expanded hull collection",
        description="Name of the collection (ie. folder) that contains (or will contain) scaled convex hulls, representing tissue outlines",
        default = "Expanded hulls",
        maxlen = 1024,
        )
    

    
####

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


    muscle_current_position_export: BoolProperty(
        name="Export muscles in current position",
        description='This allows you to export the muscles in a different position than the one they were created in. Useful if your model neutral pose is not a biologically realistic posture.',
        default = True,
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
        name = 'Enable wrapping during import (Cylinders)',
        description='Enable cylinder wrapping for imported muscles. It may be required to manually tune the parameters after import.',
        default = True,
    )

    gaitsym_geometry_folder: StringProperty(
        name = 'Gaitsym geometry folder',
        description="Name of the directory that contains the Gaitsym model's visual geometry. Must be a subdirectory of the model directory",
        default = '',
        maxlen = 256,
    )


    rotate_on_import: IntVectorProperty(
        name = 'Model import rotation',
        description='XYZ-Body fixed Euler angles (in degrees) for the import rotation of a Gaitsym or MuJoCo model. Rotate -90 degrees about X to go from Z-up to Y-up',
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
    
    frame_axes_size: FloatProperty(
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
        default = "",
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

    specific_tension: FloatProperty(
        name = "Specific tension",
        description="Specific tension of the muscles, in N/m^2. Used for determining muscle volume for visualizations.",
        default = 300000,
        min = 0,
        max = 2000000,
        precision = 0,
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


    ############### Global properties panel

    left_side_string: StringProperty(
                name = "Left side string",
                description="What do you use in the name to designate the left side? Default is '_l', like in 'thigh_l'",
                default = "_l",
                maxlen = 1024,
        )
    
    right_side_string: StringProperty(
                name = "Right side string",
                description="What do you use in the name to designate the right side? Default is '_r', like in 'thigh_r'",
                default = "_r",
                maxlen = 1024,
        )

    reflection_plane: EnumProperty(
        name="Reflection Plane",
        description="Desired reflection plane.",
        items=[
            ('XY', "XY", "Reflect across the XY plane"),
            ('YZ', "YZ", "Reflect across the YZ plane"),
            ('XZ', "XZ", "Reflect across the XZ plane"),
        ],
        default='XY',
    )

    ######## default colors
    
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
    
