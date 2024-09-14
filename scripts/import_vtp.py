import bpy
import os
import xml.etree.ElementTree as ET
import numpy as np

def load_vtp_as_mesh(filepath):
    # Get the filename from the path
    filename = os.path.basename(filepath)

    # Parse the .vtp XML file
    tree = ET.parse(filepath)
    root = tree.getroot()

    # Debugging: Print XML structure to check the paths
    #print("XML Structure:")
    #for elem in root.iter():
    #    print(elem.tag, elem.attrib)

    # Find the point data in the .vtp file
    points_elem = root.find(".//Points/DataArray")
    #if points_elem is None:
    #    raise ValueError("Points element not found in the VTP file")

    # Extract the DataArray elements for connectivity and offsets
    polys_elem = root.find(".//Polys")
    #if polys_elem is None:
    #   raise ValueError("Polys element not found in the VTP file")

    connectivity_elem = polys_elem.find("./DataArray[@Name='connectivity']")
    offsets_elem = polys_elem.find("./DataArray[@Name='offsets']")

    # Debugging: Check if elements were found
    #if connectivity_elem is None:
    #    raise ValueError("Connectivity element not found in the VTP file")
    #if offsets_elem is None:
    #    raise ValueError("Offsets element not found in the VTP file")

    # Extract points (coordinates) from the Points element
    num_components = int(points_elem.get("NumberOfComponents", "3"))
    points_raw = points_elem.text.strip().split()

    # Ensure the points are reshaped into the correct form (triples for 3D points)
    points = np.array(points_raw, dtype=float).reshape((-1, num_components))
    #print("Points Array Shape:", points.shape)

    # Parse the connectivity and offsets values as lists of integers
    connectivity = list(map(int, connectivity_elem.text.strip().split()))
    offsets = list(map(int, offsets_elem.text.strip().split()))

    # List to store the final polygons
    polys = []

    # Iterate over the offsets to extract the individual polygons from the connectivity array
    start = 0
    for end in offsets:
        polygon = connectivity[start:end]
        polys.append(polygon)
        start = end

    #print("Polygons:", polys)

    # Create a new mesh and object in Blender
    mesh = bpy.data.meshes.new(filename)

    

    obj = bpy.data.objects.new(filename, mesh)

    # Link object to the current scene
    bpy.context.collection.objects.link(obj)

    # Set the mesh data with n-gons support
    mesh.from_pydata(points.tolist(), [], polys)
    for poly in mesh.polygons:
        poly.use_smooth = True
    mesh.update()

    return obj
