bl_info = {
    "name" : "MuSkeMo",
    "author" : "Pasha van Bijlert",
    "author_email" : "pasha.vanbijlert@naturalis.nl",
    "description" : "Build and visualize musculoskeletal models for use in 3rd party physics simulators",
    "blender" : (4, 0, 0),
    "version" : (0, 9, 75),
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
from .scripts.muskemo_properties import (SegmentParameterItem, #THIS MUST BE REGISTERED BEFORE MUSKEMOPROPERTIES, THERE IS A DEPENDENCY
                                            MuSkeMoProperties)          ## all properties that are assigned by the user as part of the addon

#### Global settings panel
from .scripts.global_settings_panel import (VIEW3D_PT_global_settings_panel,
                                            SetRecommendedNavigationSettingsOperator,
                                     SetChildVisibilityInOutlinerOperator,
                                     ResetToDefaultPoseOperator,
                                    )


#### body panel
from .scripts.body_panel import (VIEW3D_PT_MuSkeMo, VIEW3D_PT_body_panel,VIEW3D_PT_vizgeometry_subpanel,
                                VIEW3D_PT_body_manual_inprop_assignment_subpanel, 
                                CreateNewBodyOperator,
                                AssignInertialPropertiesOperator,
                                UpdateLocationFromCOMOperator,
                                AttachVizGeometryOperator, DetachVizGeometryOperator,
                                GeometryIntersectionCheckerOperator,      
                                )

#### joint panel
from .scripts.joint_panel import ( CreateNewJointOperator, 
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
from .scripts.muscle_panel import (CreateNewMuscleOperator,AddMusclepointOperator, 
                                      InsertMusclePointOperator, UpdateMuscleVizRadiusOperator,
                                      CreateWrappingGeometryOperator, 
                                      AssignWrapGeomParentOperator, ClearWrapGeomParentOperator,
                                        AssignWrappingOperator, ClearWrappingOperator,
                                        SingleDOFLengthMomentArmOperator,Regenerate2DMusclePlotOperator,
                                        AddLiveLengthViewerNodeOperator,
                                      VIEW3D_PT_muscle_panel,
                                      VIEW3D_PT_wrap_subpanel, VIEW3D_PT_moment_arm_subpanel,
                                      VIEW3D_PT_plotting_subpanel,)


#### inertial properties panel
from .scripts.inertial_properties_panel import(MUSKEMO_UL_InPropSegmentList,
                                               VIEW3D_PT_inertial_prop_panel, 
                                                  VIEW3D_PT_convex_hull_subpanel,
                                                  VIEW3D_PT_expand_convex_hulls_arith_subpanel,
                                                  VIEW3D_PT_expand_convex_hulls_logar_subpanel,
                                                  VIEW3D_PT_whole_body_mass_from_convex_hull_subpanel,
                                                  VIEW3D_PT_segment_inprops_from_convex_hull_subpanel,
                                                  SelMeshesInertialProperties, CollectionMeshInertialProperties,
                                                  CollectionConvexHull,
                                                  AddSegmentOperator, RemoveSegmentOperator,
                                                  ExpandConvexHullCollectionOperator,
                                                  WholeBodyMassFromConvexHullsOperator,
                                                  PerSegmentInpropsFromConvexHullsOperator,
                                                  
                                                  )

#### export panel
from .scripts.export_panel import (VIEW3D_PT_export_panel,  VIEW3D_PT_export_bodies_subpanel,
                                    VIEW3D_PT_export_joints_subpanel, VIEW3D_PT_export_muscles_subpanel,
                                    VIEW3D_PT_export_wrapping_subpanel,
                                    VIEW3D_PT_export_mesh_inprops_subpanel, VIEW3D_PT_export_frames_subpanel,
                                    VIEW3D_PT_export_landmarks_subpanel, VIEW3D_PT_export_contacts_subpanel,
                                    VIEW3D_PT_geometry_folder_subpanel,
                                    VIEW3D_PT_export_options_subpanel,
                                    ExportBodiesOperator, ExportJointsOperator,
                                    ExportMusclesOperator,ExportWrappingOperator,
                                    ExportMeshInPropsOperator,
                                    ExportFramesOperator, ExportLandmarksOperator,
                                    ExportContactsOperator, ExportGeometryFolderOperator,
                                    SelectModelExportDirectoryOperator,
                                    )

#### import panel

from .scripts.import_panel import (VIEW3D_PT_import_panel, VIEW3D_PT_import_modelcomponents_subpanel,
                                   VIEW3D_PT_import_OpenSim_model_subpanel, VIEW3D_PT_import_Gaitsym_model_subpanel,
                                   VIEW3D_PT_import_MuJoCo_model_subpanel, 
                                   ImportBodiesOperator,ImportJointsOperator,ImportMusclesOperator,
                                   ImportContactsOperator,ImportFramesOperator,
                                   ImportOpenSimModel, ImportGaitsymModel,
                                   ImportMuJoCoModel,
                                   )

#### visualization panel

from .scripts.visualization_panel import (VIEW3D_PT_visualization_panel, VIEW3D_PT_import_trajectory_subpanel,
                                          VIEW3D_PT_visualization_options_subpanel, VIEW3D_PT_default_colors_subpanel,
                                          CreateGroundPlaneOperator, SetCompositorBackgroundGradient,
                                           ConvertMusclesToVolumetricViz,ConvertMusclesToSimpleViz,
                                    ImportTrajectorySTO,#these are separate scripts)
                                    )
#### Anatomical (local) reference frame panel
from .scripts.frame_panel import (VIEW3D_PT_frame_panel,
                                AssignOrLandmarkOperator, 
                                AssignPrimaryAxisStartLandmarkOperator,
                                AssignPrimaryAxisEndLandmarkOperator,
                                AssignPlaneLandmarkOperator, 
                                ConstructFrameOperator, ConstructFrame3DCursorOperator,
                                AssignFrameParentBodyOperator,ClearFrameParentBodyOperator,)

#### Landmark & marker panel
from .scripts.landmark_marker_panel import (VIEW3D_PT_landmark_panel, CreateLandmarkOperator,
                                            )


#### Contact panel
from .scripts.contact_panel import (VIEW3D_PT_contact_panel, CreateContactOperator, 
                                    AssignContactParentOperator,ClearContactParentOperator,)


#### reflection panel

from .scripts.reflection_panel import (ReflectUnilateralBodiesOperator,
                                       ReflectUnilateralMusclesOperator,
                                       ReflectUnilateralWrapsOperator,
                                       ReflectUnilateralFramesOperator,
                                       ReflectUnilateralJointsOperator,
                                       ReflectUnilateralContactsOperator,
                                       VIEW3D_PT_reflection_panel, 
                                       )




#### body segment inertial properties function
from .scripts.inertialproperties_func import (inertial_properties)  ## This function computes inertial properties of a mesh





classes = (  #Global settings panel 
                                    VIEW3D_PT_global_settings_panel,
                                     SetRecommendedNavigationSettingsOperator,
                                     SetChildVisibilityInOutlinerOperator,
                                     ResetToDefaultPoseOperator,
    
    #Inertial properties panel 
                                    MUSKEMO_UL_InPropSegmentList,
                                    VIEW3D_PT_inertial_prop_panel, 
                                    VIEW3D_PT_convex_hull_subpanel, 
                                    VIEW3D_PT_expand_convex_hulls_arith_subpanel,
                                    VIEW3D_PT_expand_convex_hulls_logar_subpanel,
                                    VIEW3D_PT_whole_body_mass_from_convex_hull_subpanel,
                                    VIEW3D_PT_segment_inprops_from_convex_hull_subpanel,
                                    SelMeshesInertialProperties, 
                                    CollectionMeshInertialProperties,
                                    CollectionConvexHull,
                                    AddSegmentOperator, RemoveSegmentOperator,
                                    ExpandConvexHullCollectionOperator,
                                    WholeBodyMassFromConvexHullsOperator,
                                    PerSegmentInpropsFromConvexHullsOperator,

            #body_panel
                                    VIEW3D_PT_body_panel, VIEW3D_PT_vizgeometry_subpanel,
                                    VIEW3D_PT_body_manual_inprop_assignment_subpanel,
                                     CreateNewBodyOperator,
                                    AssignInertialPropertiesOperator,
                                      UpdateLocationFromCOMOperator,
                                      AttachVizGeometryOperator, DetachVizGeometryOperator,
                                      GeometryIntersectionCheckerOperator,
            #joint panel
                                      CreateNewJointOperator, 
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
                                    CreateNewMuscleOperator, AddMusclepointOperator, 
                                    InsertMusclePointOperator, UpdateMuscleVizRadiusOperator,
                                    CreateWrappingGeometryOperator,
                                    AssignWrapGeomParentOperator, ClearWrapGeomParentOperator,
                                    AssignWrappingOperator, ClearWrappingOperator,
                                    SingleDOFLengthMomentArmOperator,Regenerate2DMusclePlotOperator,
                                    AddLiveLengthViewerNodeOperator,
                                    VIEW3D_PT_muscle_panel,
                                    VIEW3D_PT_wrap_subpanel, VIEW3D_PT_moment_arm_subpanel,
                                    VIEW3D_PT_plotting_subpanel,
            #export panel
                                    VIEW3D_PT_export_panel, VIEW3D_PT_export_bodies_subpanel,
                                    VIEW3D_PT_export_joints_subpanel, VIEW3D_PT_export_muscles_subpanel,
                                    VIEW3D_PT_export_wrapping_subpanel,
                                    VIEW3D_PT_export_mesh_inprops_subpanel, VIEW3D_PT_export_frames_subpanel,
                                    VIEW3D_PT_export_landmarks_subpanel, VIEW3D_PT_export_contacts_subpanel,
                                    VIEW3D_PT_geometry_folder_subpanel,
                                    VIEW3D_PT_export_options_subpanel,
                                    ExportBodiesOperator, ExportJointsOperator,
                                    ExportMusclesOperator, ExportWrappingOperator,
                                    ExportMeshInPropsOperator,
                                    ExportFramesOperator, ExportLandmarksOperator,
                                    ExportContactsOperator, ExportGeometryFolderOperator,
                                    SelectModelExportDirectoryOperator,

            #import panel
                                  VIEW3D_PT_import_panel,  VIEW3D_PT_import_modelcomponents_subpanel,
                                  VIEW3D_PT_import_OpenSim_model_subpanel, VIEW3D_PT_import_Gaitsym_model_subpanel, 
                                  VIEW3D_PT_import_MuJoCo_model_subpanel, 
                                  ImportBodiesOperator, ImportJointsOperator, ImportMusclesOperator,
                                  ImportContactsOperator,ImportFramesOperator,

                                  ImportOpenSimModel, ImportGaitsymModel, #these are separate scripts
                                  ImportMuJoCoModel,

            # visualization panel
                                VIEW3D_PT_visualization_panel, VIEW3D_PT_import_trajectory_subpanel, 
                                VIEW3D_PT_visualization_options_subpanel, VIEW3D_PT_default_colors_subpanel,
                                CreateGroundPlaneOperator, SetCompositorBackgroundGradient,
                               ConvertMusclesToVolumetricViz,ConvertMusclesToSimpleViz,

                                ImportTrajectorySTO, # separate script

            #anatomical (local) reference frames panel
                                 VIEW3D_PT_frame_panel,
                                AssignOrLandmarkOperator,
                                AssignPrimaryAxisStartLandmarkOperator,
                                AssignPrimaryAxisEndLandmarkOperator,
                                AssignPlaneLandmarkOperator,
                                ConstructFrameOperator, ConstructFrame3DCursorOperator,
                                AssignFrameParentBodyOperator,ClearFrameParentBodyOperator,

            #landmark & marker panel
                                VIEW3D_PT_landmark_panel, CreateLandmarkOperator,

            
            #contact sphere panel
                                VIEW3D_PT_contact_panel, CreateContactOperator,                                       
                                AssignContactParentOperator, ClearContactParentOperator,

            
            #Reflection panel
                                ReflectUnilateralBodiesOperator,
                                ReflectUnilateralFramesOperator,
                                ReflectUnilateralMusclesOperator,
                                ReflectUnilateralWrapsOperator,
                                ReflectUnilateralJointsOperator,
                                ReflectUnilateralContactsOperator,
                                VIEW3D_PT_reflection_panel, 
                                       

            # properties
                                   SegmentParameterItem, #THIS MUST BE REGISTERED BEFORE MUSKEMOPROPERTIES, THERE IS A DEPENDENCY
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
