bl_info = {
    "name" : "MuSkeMo",
    "author" : "Pasha van Bijlert",
    "author_email" : "pasha.vanbijlert@naturalis.nl",
    "description" : "Build and visualize musculoskeletal models for use in 3rd party physics simulators",
    "blender" : (3, 0, 0),
    "version" : (0, 7, 0),
    "location" : "",
    "warning" : "",
    "category" : "Physics",
    "doc_url" : "https://github.com/PashavanBijlert/MuSkeMo",
    "tracker_url" : "https://github.com/PashavanBijlert/MuSkeMo/issues",
    }


import bpy
from mathutils import Vector

from bpy.props import (PointerProperty,
                                        )
from bpy.types import (Panel,
                        PropertyGroup,
                        )

from math import nan

import numpy as np

### Parent class, all the panels will fall under the "MuSkeMo" class
class VIEW3D_PT_MuSkeMo: # class naming convention ‘CATEGORY_PT_name’
    bl_idname = 'VIEW3D_PT_MuSkeMo'
    # where to add the panel in the UI
    bl_space_type = "VIEW_3D"  # 3D Viewport area (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/space_type_items.html#rna-enum-space-type-items)
    bl_region_type = "UI"  # Sidebar region (find list of values here https://docs.blender.org/api/current/bpy_types_enum_items/region_type_items.html#rna-enum-region-type-items)

    bl_category = "MuSkeMo" # found in the Sidebar


#### properties
from .scripts.muskemo_properties import (MuSkeMoProperties)          ## all properties that are assigned by the user as part of the addon


#### body panel
from .scripts.body_panel import (VIEW3D_PT_MuSkeMo, VIEW3D_PT_body_panel,VIEW3D_PT_vizgeometry_subpanel,
                                 VIEW3D_PT_body_utilities_subpanel, 
                                    CreateNewBodyOperator,
                                      ReflectBilateralBodiesOperator, AssignInertialPropertiesOperator,
                                      ComputeInertialPropertiesOperator,UpdateLocationFromCOMOperator,
                                      AttachVizGeometryOperator, DetachVizGeometryOperator,
                                      
                                      )

#### joint panel
from .scripts.joint_panel import ( CreateNewJointOperator, ReflectRightsideJointsOperator, 
                                      AssignParentBodyOperator, AssignChildBodyOperator,
                                      ClearParentBodyOperator,ClearChildBodyOperator,
                                      UpdateCoordinateNamesOperator,
                                      FitSphereGeomOperator,FitSphereLSOperator,
                                      FitCylinderOperator, FitEllipsoidOperator,
                                      FitPlaneOperator, 
                                      MatchOrientationOperator, MatchPositionOperator,
                                      VIEW3D_PT_joint_panel,VIEW3D_PT_joint_coordinate_subpanel,
                                      VIEW3D_PT_joint_utilities_subpanel,
                                      )

#### muscle panel
from .scripts.muscle_panel import (AddMusclepointOperator, ReflectRightsideMusclesOperator,
                                      InsertMusclePointOperator, UpdateMuscleVizRadius,
                                      VIEW3D_PT_muscle_panel,)


#### inertial properties panel
from .scripts.inertial_properties_panel import(VIEW3D_PT_inertial_prop_panel, VIEW3D_PT_inertial_prop_subpanel,
                                                  VIEW3D_PT_convex_hull_subpanel,
                                                  SelMeshesInertialProperties, CollectionMeshInertialProperties,
                                                  )

#### export panel
from .scripts.export_panel import (VIEW3D_PT_export_panel,  VIEW3D_PT_export_bodies_subpanel,
                                   VIEW3D_PT_export_joints_subpanel, VIEW3D_PT_export_muscles_subpanel,
                                     VIEW3D_PT_export_mesh_inprops_subpanel, VIEW3D_PT_export_frames_subpanel,
                                    VIEW3D_PT_export_landmarks_subpanel, VIEW3D_PT_export_contacts_subpanel,
                                    VIEW3D_PT_geometry_folder_subpanel,
                                    VIEW3D_PT_export_options_subpanel,
                                    ExportBodiesOperator, ExportJointsOperator,
                                    ExportMusclesOperator,ExportMeshInPropsOperator,
                                   ExportFramesOperator, ExportLandmarksOperator,
                                   ExportContactsOperator, ExportGeometryFolderOperator,
                                    SelectModelExportDirectoryOperator,
                                    )

#### import panel

from .scripts.import_panel import (VIEW3D_PT_import_panel, VIEW3D_PT_import_modelcomponents_subpanel,
                                   VIEW3D_PT_import_full_model_subpanel, 
                                   ImportBodiesOperator,ImportJointsOperator,ImportMusclesOperator,
                                   ImportContactsOperator,ImportFramesOperator,
                                   ImportOpenSimModel, ImportGaitsymModel,
                                   )

#### visualization panel

from .scripts.visualization_panel import (VIEW3D_PT_visualization_panel, VIEW3D_PT_import_trajectory_subpanel,
                                          VIEW3D_PT_visualization_options_subpanel,
                                          CreateGroundPlaneOperator, SetCompositorBackgroundGradient,
                                    ImportTrajectorySTO,#these are separate scripts)
                                    )
#### Anatomical (local) reference frame panel
from .scripts.ARF_panel import (VIEW3D_PT_arf_panel,
                                AssignOrLandmarkOperator, AssignYDirLandmarkOperator,
                                AssignYZPlaneLandmarkOperator, ReflectSelectedRSideFrames,
                                ConstructARFOperator, 
                                AssignARFParentBodyOperator,ClearARFParentBodyOperator,)

#### Landmark & marker panel
from .scripts.landmark_marker_panel import (VIEW3D_PT_landmark_panel, CreateLandmarkOperator,
                                            )


#### Contact panel
from .scripts.contact_panel import (VIEW3D_PT_contact_panel, CreateContactOperator, 
                                    AssignContactParentOperator,ClearContactParentOperator,)

#### body segment inertial properties function
from .scripts.inertialproperties_func import (inertial_properties)  ## This function computes inertial properties of a mesh




classes = (  #Inertial properties panel 
                                    VIEW3D_PT_inertial_prop_panel, VIEW3D_PT_inertial_prop_subpanel,
                                    VIEW3D_PT_convex_hull_subpanel, 
                                    SelMeshesInertialProperties, CollectionMeshInertialProperties,
            #body_panel
                                    VIEW3D_PT_body_panel, VIEW3D_PT_vizgeometry_subpanel,
                                    VIEW3D_PT_body_utilities_subpanel,
                                     CreateNewBodyOperator,
                                    ReflectBilateralBodiesOperator, AssignInertialPropertiesOperator,
                                      ComputeInertialPropertiesOperator,UpdateLocationFromCOMOperator,
                                      AttachVizGeometryOperator, DetachVizGeometryOperator,
            #joint panel
                                      CreateNewJointOperator, ReflectRightsideJointsOperator, 
                                      AssignParentBodyOperator, AssignChildBodyOperator,
                                       ClearParentBodyOperator,ClearChildBodyOperator,
                                      UpdateCoordinateNamesOperator,
                                      FitSphereGeomOperator,FitSphereLSOperator,
                                      FitCylinderOperator, FitEllipsoidOperator,
                                      FitPlaneOperator, 
                                      MatchOrientationOperator, MatchPositionOperator,
                                      VIEW3D_PT_joint_panel,VIEW3D_PT_joint_coordinate_subpanel,
                                      VIEW3D_PT_joint_utilities_subpanel,
            #Muscle panel 
                                    AddMusclepointOperator, ReflectRightsideMusclesOperator,
                                      InsertMusclePointOperator, UpdateMuscleVizRadius,
                                      VIEW3D_PT_muscle_panel,
            #export panel
                                    VIEW3D_PT_export_panel, VIEW3D_PT_export_bodies_subpanel,
                                    VIEW3D_PT_export_joints_subpanel, VIEW3D_PT_export_muscles_subpanel,
                                    VIEW3D_PT_export_mesh_inprops_subpanel, VIEW3D_PT_export_frames_subpanel,
                                    VIEW3D_PT_export_landmarks_subpanel, VIEW3D_PT_export_contacts_subpanel,
                                    VIEW3D_PT_geometry_folder_subpanel,
                                    VIEW3D_PT_export_options_subpanel,
                                    ExportBodiesOperator, ExportJointsOperator,
                                    ExportMusclesOperator, ExportMeshInPropsOperator,
                                    ExportFramesOperator, ExportLandmarksOperator,
                                    ExportContactsOperator, ExportGeometryFolderOperator,
                                    SelectModelExportDirectoryOperator,

            #import panel
                                  VIEW3D_PT_import_panel,  VIEW3D_PT_import_modelcomponents_subpanel,
                                  VIEW3D_PT_import_full_model_subpanel, 
                                  ImportBodiesOperator, ImportJointsOperator, ImportMusclesOperator,
                                  ImportContactsOperator,ImportFramesOperator,

                                  ImportOpenSimModel, ImportGaitsymModel, #these are separate scripts

            # visualization panel
                                VIEW3D_PT_visualization_panel, VIEW3D_PT_import_trajectory_subpanel, 
                                VIEW3D_PT_visualization_options_subpanel,
                                CreateGroundPlaneOperator, SetCompositorBackgroundGradient,

                                ImportTrajectorySTO, # separate script

            #anatomical (local) reference frames panel
                                 VIEW3D_PT_arf_panel,
                                AssignOrLandmarkOperator, AssignYDirLandmarkOperator,
                                AssignYZPlaneLandmarkOperator, ReflectSelectedRSideFrames,
                                ConstructARFOperator,
                                AssignARFParentBodyOperator,ClearARFParentBodyOperator,

            #landmark & marker panel
                                VIEW3D_PT_landmark_panel, CreateLandmarkOperator,

            
            #contact sphere panel
                                VIEW3D_PT_contact_panel, CreateContactOperator,                                       
                                AssignContactParentOperator, ClearContactParentOperator,

            # properties
                                   MuSkeMoProperties,
         
)



def register():
    for c in classes:
        bpy.utils.register_class(c)
    
    bpy.types.Scene.muskemo = PointerProperty(type=MuSkeMoProperties)  ### this call stores all the custom properties under the property Scene.muskemo
    

def unregister():
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

    del bpy.types.Scene.muskemo    
    
if __name__ == "__main__":
    register()