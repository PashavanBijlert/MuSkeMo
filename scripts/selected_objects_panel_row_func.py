import bpy

def CreateSelectedObjRow(type, layout):
    """Dynamically creates a row for objects of a given (MuSkeMo) type"""
    
    # Mapping types to labels
    type_labels = {
        "BODY": "Bodies",
        "FRAME": "Frames",
        "JOINT": "Joints",
        "MUSCLE": "Muscles",
        "CONTACT": "Contacts",
        "LANDMARK": "Landmarks",
        "GEOMETRY": "Meshes",
        "MESH": "Meshes", #this is not a muskemo type
        "MESH_withdensity": "Meshes", #not a muskemo type. Mesh with inertial properties assigned
        "NOTJOINT": "Source",
        # Add more mappings as needed
    }
    
    label = type_labels.get(type, type)  # Default to type name if no mapping

    # Filter selected objects of the given type
    selected_items = [ob for ob in bpy.context.selected_objects if ob.get('MuSkeMo_type') == type]

   
    if type == 'MESH':
       selected_items = [ob for ob in bpy.context.selected_objects if (ob.type == 'MESH')]
    
    if type == 'MESH_withdensity': #
        selected_items = [ob for ob in bpy.context.selected_objects if (ob.type == 'MESH' and 'density' in ob)]
     
    if type == 'NOTJOINT':
        selected_items = [ob for ob in bpy.context.selected_objects if ob.get('MuSkeMo_type') != 'JOINT']
       

    # Define layout split factors
    fact_1 = 1/8  # Label width fraction
    fact_2 = 8/9   # Box width fraction

    # Create row
    row = layout.row()
    split = row.split(factor=fact_1)
    split.label(text=label)  # Label on the left
    split = split.split(factor=fact_2)

    # Object names box
    box = split.box()
    if selected_items:
        item_names = [ob.name for ob in selected_items]
        box.label(text=", ".join(item_names))  # Display names
    else:
        box.label(text="No " + label.lower() + " selected", icon='INFO')

    # Count box
    box = split.box()
    box.label(text=str(len(selected_items)))  # Display count