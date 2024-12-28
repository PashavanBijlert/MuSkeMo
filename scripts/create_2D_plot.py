import bpy
import bmesh
import numpy as np

def create_2D_plot(
    plot_params,
    x_ticks=5,
    y_ticks=5,
    plot_lower_left=(0, 0),  # The lower-left corner of the plot visualization. Input should be a tuple.
    plot_dimensions=(10, 10),  # Dimensions of the entire plot Input should be a tuple.
    font_scale=0.05,
    tick_size=0.2,
    xlim = (0,0), #Input should be a tuple.
    ylim = (0,0), #Input should be a tuple.
    curve_thickness = 0.01,
):
    """
    Create a 2D plot in Blender with axes, ticks, labels, and units.
    Scales the data to fit the user-defined plot dimensions.
    """
    # Extract parameters from the dictionary
    plotname = plot_params["plotname"]
    x_data = plot_params["x_data"]
    y_data = plot_params["y_data"]
    x_label = plot_params["x_label"]
    y_label = plot_params["y_label"]
    x_unit = plot_params["x_unit"]
    y_unit = plot_params["y_unit"]

    # Ensure the plot collection exists
    if plotname not in bpy.data.collections:
        coll = bpy.data.collections.new(plotname)
        bpy.context.scene.collection.children.link(coll)
    else:
        coll = bpy.data.collections[plotname]
        for obj in coll.objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[plotname]

    # Determine data ranges
    if xlim == (0,0):
        
        x_min, x_max = min(x_data), max(x_data)
        
    else:
        
        x_min = xlim[0]
        x_max = xlim[1]
        
    if ylim == (0,0):
        
        y_min, y_max = min(y_data), max(y_data)
        
    else:
        
        y_min = ylim[0]
        y_max = ylim[1]
    
    x_range = x_max - x_min
    y_range = y_max - y_min

    # Calculate scaling factors
    scale_x = plot_dimensions[0] / x_range
    scale_y = plot_dimensions[1] / y_range

    origin_x = plot_lower_left[0] - x_min * scale_x
    origin_y = plot_lower_left[1] - y_min * scale_y

    scaled_x_data = [origin_x + x * scale_x for x in x_data]
    scaled_y_data = [origin_y + y * scale_y for y in y_data]

    font_size = font_scale * min(plot_dimensions)

    def create_text(text, location, rotation=(0, 0, 0), align="CENTER"):
        location = (*location, 0) if len(location) == 2 else location
        bpy.ops.object.text_add(location=location, rotation=rotation)
        text_obj = bpy.context.object
        text_obj.data.body = text
        text_obj.scale = (font_size, font_size, font_size)
        text_obj.data.align_x = align
        text_obj.data.align_y = "CENTER"
        return text_obj

    def create_plot_line(x_data, y_data, curve_thickness):
        """
        Creates a 3D polycurve to represent the plot line using Blender's curve objects.
        """
        # Create a new curve data block
        curve_data = bpy.data.curves.new("PlotCurve", type='CURVE')
        curve_data.dimensions = '3D'
        
        # Create a new object for the curve and link it to the collection
        curve_obj = bpy.data.objects.new("PlotCurveObj", curve_data)
        coll.objects.link(curve_obj)
        
        # Add a new spline to the curve
        spline = curve_data.splines.new(type='POLY')
        spline.points.add(len(x_data) - 1)  # Add the appropriate number of points
        
        # Set the coordinates for the spline points
        for i, (x, y) in enumerate(zip(x_data, y_data)):
            spline.points[i].co = (x, y, 0, 1)  # (x, y, z, w), w=1 for homogeneous coordinate
        
        # Optional: Set the thickness of the curve
        curve_data.bevel_depth = curve_thickness  # Adjust for desired thickness

    def determine_precision(limit, ticks):
        range_per_tick = limit / ticks
        if range_per_tick >= 1:
            return 1
        elif range_per_tick >= 0.1:
            return 2
        elif range_per_tick >= 0.01:
            return 3
        elif range_per_tick >= 0.001:
            return 4
        elif range_per_tick >= 0.0001:
            return 5
        else:
            return 6

    def create_axes_with_ticks():
        mesh = bpy.data.meshes.new("AxesMesh")
        axes_obj = bpy.data.objects.new("Axes", mesh)
        coll.objects.link(axes_obj)

        bm = bmesh.new()

        end_x = plot_lower_left[0] + plot_dimensions[0]
        end_y = plot_lower_left[1] + plot_dimensions[1]

        bm.verts.new((plot_lower_left[0], origin_y, 0))
        bm.verts.new((end_x, origin_y, 0))
        bm.edges.new(bm.verts[-2:])

        bm.verts.new((origin_x, plot_lower_left[1], 0))
        bm.verts.new((origin_x, end_y, 0))
        bm.edges.new(bm.verts[-2:])

        x_precision = determine_precision(x_range, x_ticks)
        y_precision = determine_precision(y_range, y_ticks)

        for i in range(x_ticks + 1):
            x_pos = plot_lower_left[0] + i * (plot_dimensions[0] / x_ticks)
            bm.verts.new((x_pos, plot_lower_left[1] - tick_size / 2, 0))
            bm.verts.new((x_pos, plot_lower_left[1] + tick_size / 2, 0))
            bm.edges.new(bm.verts[-2:])
            create_text(
                f"{x_min + i * (x_range / x_ticks):.{x_precision}f}",
                location=(x_pos, plot_lower_left[1] - tick_size * 2),
                align="CENTER",
            )

        for i in range(y_ticks + 1):
            y_pos = plot_lower_left[1] + i * (plot_dimensions[1] / y_ticks)
            bm.verts.new((plot_lower_left[0] - tick_size / 2, y_pos, 0))
            bm.verts.new((plot_lower_left[0] + tick_size / 2, y_pos, 0))
            bm.edges.new(bm.verts[-2:])
            create_text(
                f"{y_min + i * (y_range / y_ticks):.{y_precision}f}",
                location=(plot_lower_left[0] - tick_size * 4, y_pos),
                align="CENTER",
            )

        corners = [
            (plot_lower_left[0], plot_lower_left[1], 0),
            (end_x, plot_lower_left[1], 0),
            (end_x, end_y, 0),
            (plot_lower_left[0], end_y, 0),
        ]
        for corner in corners:
            bm.verts.new(corner)
        bm.verts.ensure_lookup_table()
        bm.edges.new((bm.verts[-4], bm.verts[-3]))
        bm.edges.new((bm.verts[-3], bm.verts[-2]))
        bm.edges.new((bm.verts[-2], bm.verts[-1]))
        bm.edges.new((bm.verts[-1], bm.verts[-4]))

        bm.to_mesh(mesh)
        bm.free()

    create_plot_line(scaled_x_data, scaled_y_data, curve_thickness)
    create_axes_with_ticks()

    create_text(
        f"{x_label} ({x_unit})",
        location=(plot_lower_left[0] + plot_dimensions[0] / 2, plot_lower_left[1] - tick_size * 4),
        align="CENTER",
    )
    create_text(
        f"{y_label} ({y_unit})",
        location=(plot_lower_left[0] - tick_size * 6, plot_lower_left[1] + plot_dimensions[1] / 2),
        rotation=(0, 0, 1.5708),
        align="CENTER",
    )
