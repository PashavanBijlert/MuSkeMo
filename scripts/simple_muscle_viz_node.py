import bpy

def create_simple_muscle_node_group():
    # Create a new node group for Geometry Nodes
    muscle_node_group = bpy.data.node_groups.new("SimpleMuscleNode", 'GeometryNodeTree')

    # Create Group Input and Group Output nodes
    group_input = muscle_node_group.nodes.new('NodeGroupInput')
    group_output = muscle_node_group.nodes.new('NodeGroupOutput')

    # Set locations for Group Input and Output nodes
    group_input.location = (-800, 0)
    group_output.location = (800, 0)

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
    curve_circle.location = (0, -200)
    curve_circle.mode = 'RADIUS'  # Set mode to radius
    curve_circle.inputs['Resolution'].default_value = 16  # Set resolution to 16

    # Create Merge by Distance node
    merge_by_distance = muscle_node_group.nodes.new('GeometryNodeMergeByDistance')
    merge_by_distance.location = (400, -200)  # Set location
    merge_by_distance.inputs['Distance'].default_value = bpy.context.scene.muskemo.muscle_visualization_radius * 0.13 # Set Merge Distance
    if bpy.app.version < (5, 0, 0): 
        merge_by_distance.mode = "ALL"
    else: 
        merge_by_distance.inputs["Mode"].default_value = "All" 
    
    
    # Create Set Shade Smooth node
    set_shade_smooth = muscle_node_group.nodes.new('GeometryNodeSetShadeSmooth')
    set_shade_smooth.location = (600, 0)
    set_shade_smooth.inputs['Shade Smooth'].default_value = True  # Enable shade smooth

    ### to be able to compute the length of the curve, we need a named attribute that stores the length.
    #If it already exists we pass it onto the store named attribute node. If it doesn't exist, we pass the newly computed length.
    #This if statement is handled by a switch node

    # Create store named attribute node
    named_attribute = muscle_node_group.nodes.new('GeometryNodeStoreNamedAttribute')
    named_attribute.location = (0,0)
    named_attribute.inputs['Name'].default_value = 'length'

    # Create curve length node
    curve_length = muscle_node_group.nodes.new('GeometryNodeCurveLength')
    curve_length.location = (-400, -400)

    # named attribute input node
    named_attribute_input = muscle_node_group.nodes.new('GeometryNodeInputNamedAttribute')
    named_attribute_input.location = (-500,-500)
    named_attribute_input.inputs['Name'].default_value = 'length'

    # Switch node  (set to float)
    switch_node_float = muscle_node_group.nodes.new('GeometryNodeSwitch')
    switch_node_float.location = (-300, -400)
    switch_node_float.input_type = 'FLOAT'
    


    # Domain size node (set to curve mode)
    domain_size = muscle_node_group.nodes.new('GeometryNodeAttributeDomainSize')
    domain_size.location = (-700, 150)
    domain_size.component = 'CURVE'

    # Compare node (set to integer, equal)
    compare_node = muscle_node_group.nodes.new('FunctionNodeCompare')
    compare_node.location = (-600, 150)
    compare_node.data_type = 'INT'
    compare_node.operation = 'EQUAL'
    compare_node.inputs[3].default_value = 1

    # Switch node (set to integer)
    switch_node = muscle_node_group.nodes.new('GeometryNodeSwitch')
    switch_node.location = (-400, 150)
    switch_node.input_type = 'INT'
    switch_node.inputs[2].default_value = 1

    # Endpoint selection node
    endpoint_selection = muscle_node_group.nodes.new('GeometryNodeCurveEndpointSelection')
    endpoint_selection.location = (-150, 450)

    # Integer node (set to 16)
    integer_node = muscle_node_group.nodes.new('FunctionNodeInputInt')
    integer_node.location = (-600, -200)
    integer_node.integer = 16

    # Math node (set to multiply, set second input to 2)
    math_node = muscle_node_group.nodes.new('ShaderNodeMath')
    math_node.location = (-250, 0)
    math_node.operation = 'MULTIPLY'
    math_node.inputs[1].default_value = 2

    # UV Sphere node
    uv_sphere = muscle_node_group.nodes.new('GeometryNodeMeshUVSphere')
    uv_sphere.location = (-100, 100)

    # Instances on points node
    instances_on_points = muscle_node_group.nodes.new('GeometryNodeInstanceOnPoints')
    instances_on_points.location = (0, 400)

    # Realize instances node
    realize_instances = muscle_node_group.nodes.new('GeometryNodeRealizeInstances')
    realize_instances.location = (200, 200)

    # Join geometry node
    join_geometry = muscle_node_group.nodes.new('GeometryNodeJoinGeometry')
    join_geometry.location = (400, 100)


   
    # Link the nodes: Group Input -> Curve to Mesh -> Merge by Distance -> Set Shade Smooth -> Group Output
    muscle_node_group.links.new(group_input.outputs['Curve'], named_attribute.inputs['Geometry']) 
    muscle_node_group.links.new(group_input.outputs['Curve'], instances_on_points.inputs['Points']) 

    muscle_node_group.links.new(group_input.outputs['Curve'], domain_size.inputs['Geometry']) 



    muscle_node_group.links.new(named_attribute.outputs['Geometry'],curve_to_mesh.inputs['Curve'])  # Curve link
    muscle_node_group.links.new(group_input.outputs['Curve'], curve_length.inputs['Curve'])
    
    #if length attribute exists already, reuse it. Otherwise compute it now
    muscle_node_group.links.new(curve_length.outputs['Length'], switch_node_float.inputs['False'])
    muscle_node_group.links.new(named_attribute_input.outputs['Attribute'], switch_node_float.inputs['True'])
    muscle_node_group.links.new(named_attribute_input.outputs['Exists'], switch_node_float.inputs['Switch'])
    muscle_node_group.links.new(switch_node_float.outputs['Output'],named_attribute.inputs['Value'])    #link the length into the named attribute so that we can call it outside the node
    
    muscle_node_group.links.new(group_input.outputs['Radius'], curve_circle.inputs['Radius'])  # Radius link
    muscle_node_group.links.new(group_input.outputs['Radius'], uv_sphere.inputs['Radius'])  # Radius link
    

    muscle_node_group.links.new(curve_circle.outputs['Curve'], curve_to_mesh.inputs['Profile Curve'])
    muscle_node_group.links.new(curve_to_mesh.outputs['Mesh'], join_geometry.inputs['Geometry'])
    muscle_node_group.links.new(realize_instances.outputs['Geometry'], join_geometry.inputs['Geometry'])
                                
    muscle_node_group.links.new(join_geometry.outputs['Geometry'], merge_by_distance.inputs['Geometry'])  # Connect join geometry to Merge by Distance
    muscle_node_group.links.new(merge_by_distance.outputs['Geometry'], set_shade_smooth.inputs['Geometry'])  # Connect Merge by Distance to Set Shade Smooth
    muscle_node_group.links.new(set_shade_smooth.outputs['Geometry'], group_output.inputs['Geometry'])  # Geometry link
    
    muscle_node_group.links.new(integer_node.outputs['Integer'], curve_circle.inputs['Resolution'])
    muscle_node_group.links.new(integer_node.outputs['Integer'], uv_sphere.inputs['Rings'])
    muscle_node_group.links.new(integer_node.outputs['Integer'], math_node.inputs[0])
    muscle_node_group.links.new(math_node.outputs[0], uv_sphere.inputs['Segments'])

    muscle_node_group.links.new(uv_sphere.outputs['Mesh'], instances_on_points.inputs['Instance'])
    muscle_node_group.links.new(instances_on_points.outputs['Instances'], realize_instances.inputs['Geometry'])
    muscle_node_group.links.new(uv_sphere.outputs['Mesh'], instances_on_points.inputs['Instance'])

    muscle_node_group.links.new(domain_size.outputs['Point Count'], compare_node.inputs[2])
    muscle_node_group.links.new(compare_node.outputs['Result'], switch_node.inputs['Switch'])
    muscle_node_group.links.new(switch_node.outputs['Output'], endpoint_selection.inputs['Start Size'])
    muscle_node_group.links.new(switch_node.outputs['Output'], endpoint_selection.inputs['End Size'])
    muscle_node_group.links.new(endpoint_selection.outputs['Selection'], instances_on_points.inputs['Selection'])

    return


def add_simple_muscle_node(muscle_name):
    # Get the object by name
    obj = bpy.data.objects.get(muscle_name)
    
    # Create a new node group for the geometry node
    node_group_name = f"{muscle_name}_SimpleMuscleViz"

    if node_group_name not in bpy.data.node_groups: #if the node group is new

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


    else: #if the node group already exists in the scene (multiple successive conversions between volumetric and tube)
        node_group = bpy.data.node_groups[node_group_name]

    # Create a new Geometry Nodes modifier on the object and assign the node group
    modifier = obj.modifiers.new(name=node_group_name, type='NODES')
    modifier.node_group = node_group
    
    radius =  bpy.context.scene.muskemo.muscle_visualization_radius
    modifier['Socket_1'] = radius

    return