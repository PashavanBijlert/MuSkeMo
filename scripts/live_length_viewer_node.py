import bpy

def add_live_length_viewer_node(obj):
    if not obj.modifiers.get("LiveLengthViewer"):
        mod = obj.modifiers.new(name="LiveLengthViewer", type='NODES')
        
        
        if not bpy.data.node_groups.get("LiveLengthViewerNodeGroup"): #if the node group doesn't already exist, create it.
        
        
            node_group = bpy.data.node_groups.new("LiveLengthViewerNodeGroup", 'GeometryNodeTree')
            

            # Add input and output nodes
            input_node = node_group.nodes.new(type='NodeGroupInput')
            output_node = node_group.nodes.new(type='NodeGroupOutput')

            node_group.interface.new_socket(name='Geometry', description="", in_out='INPUT', socket_type='NodeSocketGeometry', parent=None)  # Create Geometry input socket
            node_group.interface.new_socket(name='Position', description="", in_out='INPUT', socket_type='NodeSocketVector', parent=None)  # Create Radius input socket\
            node_group.interface.new_socket(name='Size', description="", in_out='INPUT', socket_type='NodeSocketFloat', parent=None)  # Create Radius input socket\

            # Create output socket for Geometry
            node_group.interface.new_socket(name='Geometry', description="", in_out='OUTPUT', socket_type='NodeSocketGeometry', parent=None)  # Create Geometry output socket

            input_node.location = (-800, 0)
            output_node.location = (800, 0)

            # Add the nodes in between
            # 1. Named Attribute
            named_attribute_node = node_group.nodes.new(type='GeometryNodeInputNamedAttribute')
            named_attribute_node.data_type = 'FLOAT'
            named_attribute_node.location = (-600, -200)
            named_attribute_node.inputs[0].default_value = 'length'

            # 2. Attribute Statistic
            attribute_statistic_node = node_group.nodes.new(type='GeometryNodeAttributeStatistic')
            attribute_statistic_node.location = (-400, -200)
            
            # 3. Value to String
            value_to_string_node = node_group.nodes.new(type='FunctionNodeValueToString')
            value_to_string_node.location = (-200, -200)
            value_to_string_node.inputs[1].default_value = 3  # Decimals

            # 4. String to Curves
            string_to_curves_node = node_group.nodes.new(type='GeometryNodeStringToCurves')
            string_to_curves_node.location = (-0, -200)

            # 5. Transform Geometry
            transform_geometry_node = node_group.nodes.new(type='GeometryNodeTransform')
            transform_geometry_node.location = (400, -200)

            # 6. Join Geometry
            join_geometry_node = node_group.nodes.new(type='GeometryNodeJoinGeometry')
            join_geometry_node.location = (600, 0)
            
            
             # 7. Fill curve node
            fill_curve_node = node_group.nodes.new(type='GeometryNodeFillCurve')
            fill_curve_node.location = (200, -200)
            
            # 8. String node
            string_node = node_group.nodes.new(type='FunctionNodeInputString')
            string_node.location = (-200, -600)
            string_node.string = 'm' # Decimals
            
            # 9 Join string node
            
            join_string_node =  node_group.nodes.new(type='GeometryNodeStringJoin')
            join_string_node.location = (-100, -400)
    

            # Link nodes
            links = node_group.links 
            #connect input sockets
            links.new(input_node.outputs['Geometry'], join_geometry_node.inputs['Geometry'])
            links.new(input_node.outputs['Position'], transform_geometry_node.inputs['Translation'])
            links.new(input_node.outputs['Size'], string_to_curves_node.inputs['Size'])
            
            links.new(named_attribute_node.outputs['Attribute'], attribute_statistic_node.inputs['Attribute'])  # Float attribute
            links.new(input_node.outputs['Geometry'], attribute_statistic_node.inputs['Geometry']) #geometry to att stat
            links.new(attribute_statistic_node.outputs['Mean'], value_to_string_node.inputs['Value'])  # Mean
            
            links.new(string_node.outputs['String'], join_string_node.inputs['Strings']) #second input string #(reverse order)
            links.new(value_to_string_node.outputs['String'], join_string_node.inputs['Strings']) #first input string
            
            
            
            links.new(join_string_node.outputs['String'], string_to_curves_node.inputs['String'])  # String
            links.new(string_to_curves_node.outputs['Curve Instances'], fill_curve_node.inputs['Curve'])  # Geometry
            
            links.new(fill_curve_node.outputs['Mesh'], transform_geometry_node.inputs['Geometry'])  # Geometry
            links.new(transform_geometry_node.outputs['Geometry'], join_geometry_node.inputs['Geometry'])  # Geometry
            links.new(join_geometry_node.outputs['Geometry'], output_node.inputs['Geometry'])  # Final output
            
        else:
            node_group = bpy.data.node_groups.get("LiveLengthViewerNodeGroup")
        
        mod.node_group = node_group
        mod["Socket_2"] = 1.0