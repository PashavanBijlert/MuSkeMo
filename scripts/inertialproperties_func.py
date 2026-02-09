import bpy
import numpy as np


def inertial_properties(obj):
    
    print('Source object = ' + obj.name)
    
    try:    #check if obj has a custom density assigned, if not assume it to be 1000 kg*m^-3
        rho = obj['density']
    except:
        obj['density'] = 1000   #density in kg*m^-3
        obj.id_properties_ui('density').update(description = 'density (in kg*m^-3)')
        rho = obj['density']
        
        print(obj.name + ' had no density assigned, automatically setting it to 1000 kg*m^-3')
        self.report({'WARNING'}, "Source object with the name '" + obj.name + "' has no precomputed density. Automatically setting it to 1000 kg*m^-3")
               
    else:    
        rho = obj['density'] 
    
    
    
    
    bpy.ops.object.select_all(action='DESELECT') #Deselect all, then select desired object 
    obj.select_set(True)
    bpy.ops.object.transform_apply()  
    bpy.ops.object.origin_set(type='ORIGIN_CENTER_OF_VOLUME')
    

    centroid_total = np.array(obj.location)           #volumetric centroid of the mesh

    polygons = obj.data.polygons #connectivity list, so each polygon has three number that correspond to a row in vertices
    
    if any(len(p.vertices) != 3 for p in obj.data.polygons):
        print("ERROR. Object with the name '" + obj.name + "' has non-triangular mesh faces. You must manually triangulate this mesh before computing inertial properties. Operation cancelled.")
        return{'FINISHED'}
        
    
    vertices = obj.data.vertices #points list. Each row in vertices gives you x y z coordinate of a vertex

   
           


    vol_tet = []                #volume of each tetrahedron
    centroid_tet = []           #centroid of each tetrahedron

    integrals = np.zeros(10)

    for n in range(len(polygons)):
        polygon = polygons[n]
        
        ver0 = obj.matrix_world @ vertices[polygon.vertices[0]].co; # vector to each vertex point from world origin, matrix_world accounts for location change due to parenting
        ver1 = obj.matrix_world @ vertices[polygon.vertices[1]].co;
        ver2 = obj.matrix_world @ vertices[polygon.vertices[2]].co;
           
        #centroid of each tetrahedron wrt to origin, which was set to volumetric centroid above
        centroid_tet.append((ver0 + ver1 + ver2)/4) 
        
        #volume of each tetrahedron
        vol_tet.append( ver0.dot(ver1.cross(ver2)) /  6 ) #scalar triple product
        
        #### Rest of this loop follows Eberly 2003 "Game Physics" Chapter 2.5.5
        
        ### Triangle vertices    
        x0= ver0.x
        y0= ver0.y
        z0= ver0.z
        
        x1= ver1.x
        y1= ver1.y
        z1= ver1.z
        
        x2= ver2.x
        y2= ver2.y
        z2= ver2.z
        
        #edges and cross product of edges
        a1 = x1 - x0
        b1 = y1 - y0
        c1 = z1 - z0
        a2 = x2 - x0
        b2 = y2 - y0
        c2 = z2 - z0
        d0 = b1 * c2 - b2 * c1
        d1 = a2 * c1 - a1 * c2
        d2 = a1 * b2 - a2 * b1
        
        
        #compute integral terms, use np.array to do all three at once
        
        w0 = np.array([x0, y0, z0])
        w1 = np.array([x1, y1, z1])
        w2 = np.array([x2, y2, z2])
        
        temp0 = w0 + w1
        f1 = temp0 + w2
        temp1 = w0 * w0
        temp2 = temp1 + w1 * temp0
        f2 = temp2 + w2 * f1
        f3 = w0 * temp1 + w1 * temp2 + w2 * f2
        
        g0 = f2 + w0 * (f1 + w0)
        g1 = f2 + w1 * (f1 + w1)
        g2 = f2 + w2 * (f1 + w2)
        
        f1x = f1[0]
        f1y = f1[1]
        f1z = f1[2]
        
        f2x = f2[0]
        f2y = f2[1]
        f2z = f2[2]
        
        f3x = f3[0]
        f3y = f3[1]
        f3z = f3[2]
        
        g0x = g0[0]
        g0y = g0[1]
        g0z = g0[2]
        
        g1x = g1[0]
        g1y = g1[1]
        g1z = g1[2]
        
        g2x = g2[0]
        g2y = g2[1]
        g2z = g2[2]
        
        integrals[0:7] += np.array([d0*f1x, d0*f2x, d1*f2y, d2*f2z, d0*f3x, d1*f3y, d2*f3z])
        
        integrals[7] += d0 * (y0 * g0x + y1 * g1x + y2 * g2x)
        integrals[8] += d1 * (z0 * g0y + z1 * g1y + z2 * g2y)
        integrals[9] += d2 * (x0 * g0z + x1 * g1z + x2 * g2z)
        

    volume = sum(vol_tet)

    centroid_tet = np.array(centroid_tet) #because object origin is set to volume centroid, this should be zero
    vol_tet = np.array(vol_tet)


    #print('vol computed manually = ' + str(volume) + ' m^3')
    #print(centroid_total)


    for n in range(len(polygons)):
        polygon = polygons[n]
        
        
        
    integrals[0]    *= 1/6 # volume
    integrals[1:4]  *= 1/24
    integrals[4:7]  *= 1/60
    integrals[7:10] *= 1/120

    vol_book = integrals[0]
    CoM_book = integrals[1:4]/vol_book

    #print('Volume using book method = ' + str(vol_book))
    #print('CoM using Book method = ' + str(CoM_book))

    Ixx = integrals[5] + integrals[6] - vol_book*(CoM_book[1]**2 + CoM_book[2]**2)
    Iyy = integrals[4] + integrals[6] - vol_book*(CoM_book[2]**2 + CoM_book[0]**2)
    Izz = integrals[4] + integrals[5] - vol_book*(CoM_book[0]**2 + CoM_book[1]**2)
   
    Ixy = (-integrals[7] + vol_book * CoM_book[0] * CoM_book[1])
    Iyz = (-integrals[8] + vol_book * CoM_book[1] * CoM_book[2])
    Ixz = (-integrals[9] + vol_book * CoM_book[0] * CoM_book[2])

    volumetric_I_com = np.array([Ixx, Iyy, Izz, Ixy, Ixz, Iyz])
    #print('Inertia using book method = ' + str(volumetric_I_com) )
    

    
    mass = vol_book*rho
    

    mass_I_com = volumetric_I_com*rho
    
    
    if vol_book < 0:
        raise Exception("Negative volume detected for source object'" + obj.name + "', check face normal orientation") 
        self.report({'ERROR'}, "Negative volume detected for source object'" + obj.name + "', check face normal orientation")
        return {'FINISHED'}       
        
        
    ##### add custom properties to the source objects (see blender documentation for properties)
    obj['mass'] = mass       #add mass property
    obj.id_properties_ui('mass').update(description = 'mass of the object in kg')
    
    obj['inertia_COM'] = mass_I_com    #add inertia property
    obj.id_properties_ui('inertia_COM').update(description = 'Ixx Iyy Izz Ixy Ixz Iyz (in kg*m^2) about object COM in global frame')
    
    
    obj['COM'] = CoM_book
    obj.id_properties_ui('COM').update(description = 'COM location (in global frame)')
    
    obj['default_pose'] = list(obj.matrix_world) #set a default pose to track in what pose the in props were computed

    return(mass, CoM_book, mass_I_com, vol_book, volumetric_I_com)



       
    
    
    
    