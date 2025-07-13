import bpy
from math import nan

def create_wrapgeom(name, geomtype, collection_name,
                    parent_body='not_assigned', 
                    pos_in_global=[nan] * 3,
                    or_in_global_XYZeuler=[nan] * 3, 
                    or_in_global_quat=[nan] * 4,
                    pos_in_parent_frame=[nan] * 3,
                    or_in_parent_frame_XYZeuler=[nan] * 3, 
                    or_in_parent_frame_quat=[nan] * 4,
                    dimensions = {},
                    ):
    
    from .quaternions import matrix_from_quaternion
    from .euler_XYZ_body import matrix_from_euler_XYZbody

    #check if the collection name exists, and if not create it
    if collection_name not in bpy.data.collections:
        bpy.data.collections.new(collection_name)
        
    coll = bpy.data.collections[collection_name] #Collection which will recieve the scaled contacts

    if collection_name not in bpy.context.scene.collection.children:       #if the collection is not yet in the scene
        bpy.context.scene.collection.children.link(coll)     #add it to the scene
    
    #Make sure the correct collection is active
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection_name]

    ## check if material exists and if not, create it
    matname = 'wrap_geom_material'
    color = tuple(bpy.context.scene.muskemo.wrap_geom_color)
    transparency = 0.5

    ##### Assign a material
    
    if matname not in bpy.data.materials:   #if the material doesn't exist, get it
        from .create_transparent_material_func import create_transparent_material
        create_transparent_material(matname, color, transparency)

    mat = bpy.data.materials[matname]


    if geomtype == 'Cylinder':
        # Create a cylinder using bpy.ops

        if dimensions: #if the user specified dimensions
            radius = dimensions['radius']
            height = dimensions['height']

        else: #otherwise just set default values
            radius = 1.0
            height = 1.0

        bpy.ops.mesh.primitive_cylinder_add(
            radius=radius, 
            depth=height, 
            
        )


        bpy.context.object.name = name #set the name
        bpy.context.object.data.name = name #set the name of the object data
        obj = bpy.data.objects[name]

        ### create a geometry node mesh cylinder so that the object dimensions become parametric.

        ## first the node tree
        obj_type = 'WrapCylinderGeometry' #name of the cylinder node tree.
        if obj_type in bpy.data.node_groups: #check if the node tree exists, and if so, select it.
            node_tree= bpy.data.node_groups[obj_type]
            
            
        else: #if it doesn't exist, create it now.
                
            node_tree = bpy.data.node_groups.new('WrapCylinderGeometry','GeometryNodeTree')
            #output socket
            node_tree.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
            
            #input socket
            node_tree.interface.new_socket(name = "Radius", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
            node_tree.interface.new_socket(name = "Height", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
            
            
            group_output = node_tree.nodes.new(type='NodeGroupOutput')
            group_output.location = (400, 0)
            
        
        
            group_input = node_tree.nodes.new(type='NodeGroupInput')
            group_input.location = (-800, 0)

            primitive_cylinder = node_tree.nodes.new(type='GeometryNodeMeshCylinder')
            primitive_cylinder.location = (-600, 200)

            set_material = node_tree.nodes.new(type='GeometryNodeSetMaterial')
            set_material.location = (200, 0)
            
                
            # Addobject info nodes
            object_info = node_tree.nodes.new(type='GeometryNodeObjectInfo')
            object_info.location = (-600, -100)
            object_info.transform_space =  'RELATIVE'
            
            # Add a Self Object node
            self_object = node_tree.nodes.new(type='GeometryNodeSelfObject')
            self_object.location = (-800, -100)
            
            transform_geometry = node_tree.nodes.new(type='GeometryNodeTransform')
            transform_geometry.location = (0, 0)

            #Store named attribute for Radius
            NamedAttributeRadius = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeRadius.location = (-400, 300)
            NamedAttributeRadius.inputs["Name"].default_value = 'WrapCylRadius'

            #Store named attribute for Height
            NamedAttributeHeight = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeHeight.location = (-200, 250)
            NamedAttributeHeight.inputs["Name"].default_value = 'WrapCylHeight'

            # Link nodes
            links = node_tree.links
            
            #link self object node to object info node
            links.new(self_object.outputs['Self Object'], object_info.inputs['Object'])

            # Link object info outputs to transform geometry
            links.new(object_info.outputs['Location'], transform_geometry.inputs['Translation'])
            links.new(object_info.outputs['Rotation'], transform_geometry.inputs['Rotation'])

            # Link cylinder output to Named Attribute Radius
            links.new(primitive_cylinder.outputs['Mesh'], NamedAttributeRadius.inputs['Geometry'])

            # Link Named Attribute Radius to Named attribute height
            links.new(NamedAttributeRadius.outputs['Geometry'], NamedAttributeHeight.inputs['Geometry'])
                      
            # Link Named Attribute Height to transform geometry         
            links.new(NamedAttributeHeight.outputs['Geometry'], transform_geometry.inputs['Geometry'])

            # Update connection to set material
            links.new(transform_geometry.outputs['Geometry'], set_material.inputs['Geometry'])
            
            
            
            #set output
            links.new(set_material.outputs['Geometry'], group_output.inputs['Geometry'])

            ## set material 
            set_material.inputs['Material'].default_value = mat

            
        
            # Link group inputs to the primitive cylinder
            links.new(group_input.outputs['Radius'], primitive_cylinder.inputs['Radius'])
            links.new(group_input.outputs['Height'], primitive_cylinder.inputs['Depth'])

            # Link group inputs to named attribute
            links.new(group_input.outputs['Radius'], NamedAttributeRadius.inputs["Value"])
            links.new(group_input.outputs['Height'], NamedAttributeHeight.inputs["Value"])

        ## nNow Add a Geometry Nodes modifier
        modifier = obj.modifiers.new(name="WrapObjMesh", type='NODES')
    
        modifier.node_group = node_tree
        
        # Set the radius and depth in the modifier socket
        modifier['Socket_1'] = radius
        modifier['Socket_2'] = height

       

        ## custom properties for cylinder
        obj['wrap_type'] = geomtype   #to inform the user what type is created
        obj.id_properties_ui('wrap_type').update(description = "The type of wrapping object")


        add_drivers = False
        if add_drivers == True:


            # add drivers for radius and height custom property
            # radius
            driver = obj.driver_add('["cylinder_radius"]').driver

            var = driver.variables.new()        #make a new variable
            var.name = name + '_cyl_rad_var'            #give the variable a name

            #var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

            var.targets[0].id = obj #set the id to the active scene
            var.targets[0].data_path = 'modifiers["WrapObjMesh"]["Socket_1"]' #get the driving property

            driver.expression = var.name  #set the expression, in this case only the name of the variable and nothing else
            # height
            driver = obj.driver_add('["cylinder_height"]').driver

            var = driver.variables.new()        #make a new variable
            var.name = name + '_cyl_height_var'            #give the variable a name

            #var.targets[0].id_type = 'SCENE' #default is 'OBJECT', we want muskemo.muscle_visualization_radius to drive this, which lives under SCENE

            var.targets[0].id = obj #set the id to the active scene
            var.targets[0].data_path = 'modifiers["WrapObjMesh"]["Socket_2"]' #get the driving property

            driver.expression = var.name  #set the expression, in this case only the name of the variable and nothing else

    else: #if not a cylinder, skip for now.
        return
    

    ## operations that are not dependent on wrap type
    obj.rotation_mode = 'ZYX'    #change rotation sequence

    obj['MuSkeMo_type'] = 'WRAP'    #to inform the user what type is created
    obj.id_properties_ui('MuSkeMo_type').update(description = "The object type. Warning: don't modify this!")

    
    obj['parent_body'] = parent_body    #to inform the user what type is created
    obj.id_properties_ui('parent_body').update(description = "The parent body of this wrap geometry")

    obj['pos_in_parent_frame'] = pos_in_parent_frame
    obj.id_properties_ui('pos_in_parent_frame').update(description = 'Wrap geometry position in the parent body anatomical (local) reference frame (x, y, z, in meters). Optional.')

    obj['or_in_parent_frame_XYZeuler'] = or_in_parent_frame_XYZeuler
    obj.id_properties_ui('or_in_parent_frame_XYZeuler').update(description='Wrap geometry orientation XYZ-Euler angles in the parent body anatomical (local) reference frame (x, y, z, in rad). Optional.')

    obj['or_in_parent_frame_quat'] = or_in_parent_frame_quat
    obj.id_properties_ui('or_in_parent_frame_quat').update(description='Wrap geometry orientation quaternion decomposition in the parent body anatomical (local) reference frame (w, x, y, z). Optional.')


    obj['target_muscles'] = 'not_assigned'
    obj.id_properties_ui('target_muscles').update(description='Muscles that are affected by this wrapping object. Delimited by ";"')

    bpy.ops.object.select_all(action='DESELECT') 


    if or_in_global_quat !=[nan]*4:  #if a global orientation is supplied as a quaternion
        [gRb, bRg] = matrix_from_quaternion(or_in_global_quat)
        obj.matrix_world = gRb.to_4x4()

    
    if or_in_global_quat == [nan]*4 and or_in_global_XYZeuler != [nan]*3:

        [gRb, bRg] = matrix_from_euler_XYZbody(or_in_global_XYZeuler)
        obj.matrix_world = gRb.to_4x4()
    
    if pos_in_global != [nan]*3: #if the specified position is not [nan, nan, nan]
        obj.matrix_world.translation = pos_in_global

    #if the body exists, parent the contact to it
    if parent_body in bpy.data.objects: #if the parent body exists
        parent_body_obj = bpy.data.objects[parent_body]

        if 'BODY' in parent_body_obj['MuSkeMo_type']: #if it's a MuSkeMo body
            
            obj.parent = parent_body_obj
            obj.matrix_parent_inverse = parent_body_obj.matrix_world.inverted()     
    
    #####
    #     
    
    obj.data.materials.append(mat)

    ### viewport display color

    obj.active_material.diffuse_color = (color[0], color[1], color[2], transparency)    
        
        
        
        
