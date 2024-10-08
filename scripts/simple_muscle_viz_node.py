import bpy

def create_simple_muscle_node_group():
    # Create a new node group for Geometry Nodes
    muscle_node_group = bpy.data.node_groups.new("SimpleMuscleNode", 'GeometryNodeTree')

    # Create Group Input and Group Output nodes
    group_input = muscle_node_group.nodes.new('NodeGroupInput')
    group_output = muscle_node_group.nodes.new('NodeGroupOutput')

    # Set locations for Group Input and Output nodes
    group_input.location = (-400, 0)
    group_output.location = (600, 0)

    # Create input sockets for the Curve and Radius directly in the node group
    muscle_node_group.interface.new_socket(name='Curve', description="", in_out='INPUT', socket_type='NodeSocketGeometry', parent=None)  # Create a Curve input socket
    muscle_node_group.interface.new_socket(name='Radius', description="", in_out='INPUT', socket_type='NodeSocketFloat', parent=None)  # Create a Radius input socket

    # Create output socket
    muscle_node_group.interface.new_socket(name='Geometry', description="", in_out='OUTPUT', socket_type='NodeSocketGeometry', parent=None)  # Create a Geometry output socket

    # Create Curve to Mesh node
    curve_to_mesh = muscle_node_group.nodes.new('GeometryNodeCurveToMesh')
    curve_to_mesh.location = (200, 0)
    curve_to_mesh.inputs['Fill Caps'].default_value = True  # Enable fill caps

    # Create Curve Circle node
    curve_circle = muscle_node_group.nodes.new('GeometryNodeCurvePrimitiveCircle')
    curve_circle.location = (200, -200)
    curve_circle.mode = 'RADIUS'  # Set mode to radius
    curve_circle.inputs['Resolution'].default_value = 16  # Set resolution to 16

    # Create Merge by Distance node
    merge_by_distance = muscle_node_group.nodes.new('GeometryNodeMergeByDistance')
    merge_by_distance.location = (400, -200)  # Set location
    merge_by_distance.inputs['Distance'].default_value = bpy.context.scene.muskemo.muscle_visualization_radius * 0.13 # Set Merge Distance
    merge_by_distance.mode = 'ALL'  # Set mode to All

    # Create Set Shade Smooth node
    set_shade_smooth = muscle_node_group.nodes.new('GeometryNodeSetShadeSmooth')
    set_shade_smooth.location = (600, 0)
    set_shade_smooth.inputs['Shade Smooth'].default_value = True  # Enable shade smooth

    # Link the nodes: Group Input -> Curve to Mesh -> Merge by Distance -> Set Shade Smooth -> Group Output
    muscle_node_group.links.new(group_input.outputs['Curve'], curve_to_mesh.inputs['Curve'])  # Curve link
    muscle_node_group.links.new(group_input.outputs['Radius'], curve_circle.inputs['Radius'])  # Radius link
    muscle_node_group.links.new(curve_circle.outputs['Curve'], curve_to_mesh.inputs['Profile Curve'])
    muscle_node_group.links.new(curve_to_mesh.outputs['Mesh'], merge_by_distance.inputs['Geometry'])  # Connect Curve to Mesh to Merge by Distance
    muscle_node_group.links.new(merge_by_distance.outputs['Geometry'], set_shade_smooth.inputs['Geometry'])  # Connect Merge by Distance to Set Shade Smooth
    muscle_node_group.links.new(set_shade_smooth.outputs['Geometry'], group_output.inputs['Geometry'])  # Geometry link

    return


def add_simple_muscle_node(muscle_name):
    # Get the object by name
    obj = bpy.data.objects.get(muscle_name)
    
    # Create a new node group for the geometry node
    node_group_name = f"{muscle_name}_SimpleMuscleViz"
    node_group = bpy.data.node_groups.new(node_group_name, 'GeometryNodeTree')

    # Create Group Input and Group Output nodes
    group_input = node_group.nodes.new('NodeGroupInput')
    group_output = node_group.nodes.new('NodeGroupOutput')

    # Set locations for Group Input and Output nodes
    group_input.location = (-400, 0)
    group_output.location = (400, 0)

    # Create input sockets using the provided code snippet
    node_group.interface.new_socket(name='Geometry', description="", in_out='INPUT', socket_type='NodeSocketGeometry', parent=None)  # Create Geometry input socket
    node_group.interface.new_socket(name='Radius', description="", in_out='INPUT', socket_type='NodeSocketFloat', parent=None)  # Create Radius input socket

    # Create output socket for Geometry
    node_group.interface.new_socket(name='Geometry', description="", in_out='OUTPUT', socket_type='NodeSocketGeometry', parent=None)  # Create Geometry output socket

    # Add the existing SimpleMuscleNode
    simple_muscle_node = node_group.nodes.new('GeometryNodeGroup')
    simple_muscle_node.node_tree = bpy.data.node_groups.get('SimpleMuscleNode')
    simple_muscle_node.location = (0, 0)

    # Create Set Material node
    set_material_node = node_group.nodes.new('GeometryNodeSetMaterial')
    set_material_node.location = (200, 0)
    set_material_node.inputs['Material'].default_value = bpy.data.materials.get(muscle_name)  # Set material to muscle_name

    # Link the nodes: Input -> SimpleMuscleNode -> Set Material -> Output
    node_group.links.new(group_input.outputs['Geometry'], simple_muscle_node.inputs['Curve'])  # Geometry link
    node_group.links.new(group_input.outputs['Radius'], simple_muscle_node.inputs['Radius'])      # Radius link
    node_group.links.new(simple_muscle_node.outputs['Geometry'], set_material_node.inputs['Geometry'])  # SimpleMuscleNode to Set Material link
    node_group.links.new(set_material_node.outputs['Geometry'], group_output.inputs['Geometry'])  # Set Material to Group Output link

    # Create a new Geometry Nodes modifier on the object and assign the node group
    modifier = obj.modifiers.new(name=node_group_name, type='NODES')
    modifier.node_group = node_group
    
    radius =  bpy.context.scene.muskemo.muscle_visualization_radius
    modifier['Socket_1'] = radius

    return