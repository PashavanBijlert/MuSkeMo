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


    elif geomtype == 'Sphere':
        
        if dimensions: #if the user specified dimensions
            radius = dimensions['radius']

        else: #otherwise just set default values
            radius = 1.0

        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=radius,   
        )   

    elif geomtype == 'Ellipsoid':
        if dimensions: #if the user specified dimensions
            radius_x = dimensions['radius_x']
            radius_y = dimensions['radius_y']
            radius_z = dimensions['radius_z']

        else: #otherwise just set default values
            radius_x = 0.05
            radius_y = 0.075
            radius_z = 0.1


        bpy.ops.mesh.primitive_ico_sphere_add(
            radius=1, scale = (radius_x, radius_y, radius_z)
        )  



    bpy.context.object.name = name #set the name
    bpy.context.object.data.name = name #set the name of the object data
    obj = bpy.data.objects[name]

    if geomtype == 'Ellipsoid': #this bakes the underlying object as an ellipsoid, but we're going to overwrite it with a geometry nodes parametric object anyway
        
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        bpy.ops.object.transform_apply(location=False, rotation=False,scale=True)
        obj.select_set(False )

    #Node tree name, if it exists get it, otherwise create it anew.

    if geomtype == 'Cylinder':
        node_tree_name = 'WrapCylinderGeometry' #name of the cylinder node tree.
    
    elif geomtype == 'Sphere':
        node_tree_name = 'WrapSphereGeometry' #name of the cylinder node tree.
        

    elif geomtype == 'Ellipsoid':
        node_tree_name = 'WrapEllipsoidGeometry' #name of the cylinder node tree.


    
    if node_tree_name in bpy.data.node_groups: #check if the node tree exists, and if so, select it.
        node_tree= bpy.data.node_groups[node_tree_name]
            
        
    else: #if it doesn't exist, create it now.

       
        node_tree = bpy.data.node_groups.new(node_tree_name,'GeometryNodeTree')
        #output socket
        node_tree.interface.new_socket(name='Geometry', in_out='OUTPUT', socket_type='NodeSocketGeometry')
        
        if geomtype == 'Cylinder':
            #input socket
            node_tree.interface.new_socket(name = "Radius", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
            node_tree.interface.new_socket(name = "Height", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
        
        elif geomtype == 'Sphere':
            #input socket
            node_tree.interface.new_socket(name = "Radius", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
            
        elif geomtype == 'Ellipsoid':
            #input socket
            node_tree.interface.new_socket(name = "Radius x", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
            node_tree.interface.new_socket(name = "Radius y", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
            node_tree.interface.new_socket(name = "Radius z", in_out = 'INPUT', socket_type = 'NodeSocketFloat')
            node_tree.interface.new_socket(name = "Ellipsoid resolution", in_out = 'INPUT', socket_type = 'NodeSocketInt')


            combine_xyz = node_tree.nodes.new(type='ShaderNodeCombineXYZ')
            combine_xyz.location = (-600, 0)

        group_output = node_tree.nodes.new(type='NodeGroupOutput')
        group_output.location = (400, 0)
        
    
    
        group_input = node_tree.nodes.new(type='NodeGroupInput')
        group_input.location = (-800, 0)

        if geomtype == 'Cylinder':
            primitive_object = node_tree.nodes.new(type='GeometryNodeMeshCylinder')
            primitive_object.location = (-600, 200)

        elif geomtype == 'Sphere':
            primitive_object = node_tree.nodes.new(type='GeometryNodeMeshIcoSphere')
            primitive_object.location = (-600, 200)
            primitive_object.inputs["Subdivisions"].default_value = 3

        elif geomtype == 'Ellipsoid':
            primitive_object = node_tree.nodes.new(type='GeometryNodeMeshIcoSphere')
            primitive_object.location = (-600, 200)
            
             

            
            
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
        
        if geomtype == 'Cylinder':
            #Store named attribute for Radius
            NamedAttributeRadius = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeRadius.location = (-400, 300)
            NamedAttributeRadius.inputs["Name"].default_value = 'WrapCylRadius'

            #Store named attribute for Height
            NamedAttributeHeight = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeHeight.location = (-200, 250)
            NamedAttributeHeight.inputs["Name"].default_value = 'WrapCylHeight'

        elif geomtype == 'Sphere':
            #Store named attribute for Radius
            NamedAttributeRadius = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeRadius.location = (-400, 300)
            NamedAttributeRadius.inputs["Name"].default_value = 'WrapSphereRadius'


        elif geomtype == 'Ellipsoid':

            #Store named attribute for Radii
            NamedAttributeRadiusX = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeRadiusX.location = (-400, 300)
            NamedAttributeRadiusX.inputs["Name"].default_value = 'WrapEllipsoidRadiusX'     

            #Store named attribute for Radii
            NamedAttributeRadiusY = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeRadiusY.location = (-300, 250)
            NamedAttributeRadiusY.inputs["Name"].default_value = 'WrapEllipsoidRadiusY'  

            #Store named attribute for Radii
            NamedAttributeRadiusZ = node_tree.nodes.new(type='GeometryNodeStoreNamedAttribute')
            NamedAttributeRadiusZ.location = (-200, 200)
            NamedAttributeRadiusZ.inputs["Name"].default_value = 'WrapEllipsoidRadiusZ'    

        # Link nodes
        links = node_tree.links
        
        #link self object node to object info node
        links.new(self_object.outputs['Self Object'], object_info.inputs['Object'])

        # Link object info outputs to transform geometry
        links.new(object_info.outputs['Location'], transform_geometry.inputs['Translation'])
        links.new(object_info.outputs['Rotation'], transform_geometry.inputs['Rotation'])

        if geomtype == 'Cylinder':
            # Link cylinder output to Named Attribute Radius
            links.new(primitive_object.outputs['Mesh'], NamedAttributeRadius.inputs['Geometry'])

            # Link Named Attribute Radius to Named attribute height
            links.new(NamedAttributeRadius.outputs['Geometry'], NamedAttributeHeight.inputs['Geometry'])
                        
            # Link Named Attribute Height to transform geometry         
            links.new(NamedAttributeHeight.outputs['Geometry'], transform_geometry.inputs['Geometry'])


        elif geomtype == 'Sphere':
            # Link sphere output to Named Attribute Radius
            links.new(primitive_object.outputs['Mesh'], NamedAttributeRadius.inputs['Geometry'])
            
            # Link Named Attribute Radius to Named attribute height to transform geometry
            links.new(NamedAttributeRadius.outputs['Geometry'], transform_geometry.inputs['Geometry'])
                        
        elif geomtype == 'Ellipsoid':
            #link ellipsoid output to Named Attribute Radius x
            links.new(primitive_object.outputs['Mesh'], NamedAttributeRadiusX.inputs['Geometry'])

            #link  Named Attribute Radius x to Named Attribute Radius y
            links.new(NamedAttributeRadiusX.outputs['Geometry'], NamedAttributeRadiusY.inputs['Geometry'])

            #link  Named Attribute Radius y to Named Attribute Radius z
            links.new(NamedAttributeRadiusY.outputs['Geometry'], NamedAttributeRadiusZ.inputs['Geometry'])

            #link  Named Attribute Radius z to transform geometry
            links.new(NamedAttributeRadiusZ.outputs['Geometry'], transform_geometry.inputs['Geometry'])

            #link combine xyz output to transform geometry
            links.new(combine_xyz.outputs['Vector'], transform_geometry.inputs['Scale'])



        # Update connection to set material
        links.new(transform_geometry.outputs['Geometry'], set_material.inputs['Geometry'])
        
        
        #set output
        links.new(set_material.outputs['Geometry'], group_output.inputs['Geometry'])

        ## set material 
        set_material.inputs['Material'].default_value = mat

        if geomtype == 'Cylinder':
    
            # Link group inputs to the primitive cylinder
            links.new(group_input.outputs['Radius'], primitive_object.inputs['Radius'])
            links.new(group_input.outputs['Height'], primitive_object.inputs['Depth'])

            # Link group inputs to named attribute
            links.new(group_input.outputs['Radius'], NamedAttributeRadius.inputs["Value"])
            links.new(group_input.outputs['Height'], NamedAttributeHeight.inputs["Value"])

        elif geomtype == 'Sphere':
    
            # Link group inputs to the primitive cylinder
            links.new(group_input.outputs['Radius'], primitive_object.inputs['Radius'])

            # Link group inputs to named attribute
            links.new(group_input.outputs['Radius'], NamedAttributeRadius.inputs["Value"]) 

        elif geomtype == 'Ellipsoid':
    
            # Link group inputs to the primitive cylinder
            links.new(group_input.outputs['Radius x'], combine_xyz.inputs['X'])

            # Link group inputs to named attribute
            links.new(group_input.outputs['Radius x'], NamedAttributeRadiusX.inputs["Value"])   

            # Link group inputs to the primitive cylinder
            links.new(group_input.outputs['Radius y'], combine_xyz.inputs['Y'])

            # Link group inputs to named attribute
            links.new(group_input.outputs['Radius y'], NamedAttributeRadiusY.inputs["Value"])  

            # Link group inputs to the primitive cylinder
            links.new(group_input.outputs['Radius z'], combine_xyz.inputs['Z'])

            # Link group inputs to named attribute
            links.new(group_input.outputs['Radius z'], NamedAttributeRadiusZ.inputs["Value"])
            
            # link group input to ellipsoid (sphere) subdivision
            links.new(group_input.outputs['Ellipsoid resolution'], primitive_object.inputs["Subdivisions"])    

    ## nNow Add a Geometry Nodes modifier
    modifier = obj.modifiers.new(name="WrapObjMesh", type='NODES')

    modifier.node_group = node_tree
    
    if geomtype == 'Cylinder':
        # Set the radius and depth in the modifier socket
        modifier['Socket_1'] = radius
        modifier['Socket_2'] = height

    if geomtype == 'Sphere':
        # Set the radius and depth in the modifier socket
        modifier['Socket_1'] = radius

    if geomtype == 'Ellipsoid':    
        # Set the radii in the modifier socket
        modifier['Socket_1'] = radius_x
        modifier['Socket_2'] = radius_y
        modifier['Socket_3'] = radius_z
        modifier['Socket_4'] = 4 #default ellipsoid resolution

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
        
        
        
        
