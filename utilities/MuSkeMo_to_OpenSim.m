clear;

% Load the Moco libraries
import org.opensim.modeling.*;

%% user switches

%model_directory = folderPath = uigetdir('', 'Select a folder');
model_dir = 'C:\Users\3827658\My Drive\MuSkeMo\Tutorial 1 files\v0.6.0 tryout model'; %directory that contains the model
geom_dir = 'Geometry'; %folder name that contains the geometry files


model_name = 'Emu_demo'; %name in opensim
filename = 'Emu_demo_model'; %filename when writing the model
version = '_v1';

global_or_local = 'local'; %'global' or 'local' coordinates

export_nomusc_version = 'yes'; %or yes, if you want to create a model without muscles as well to test contact geometry

%% Import model data

bodies_file = 'Bodies';
joints_file = 'Joint centers';
muscles_file = 'Muscles';
contacts_file = 'Contacts';
frame_file = 'Frames'; %only required if global_or_local == 'local' 

body_data = readtable([model_dir '/' bodies_file '.csv'],'VariableNamingRule','preserve');
joint_data = readtable([model_dir '/' joints_file '.csv'],'VariableNamingRule','preserve');
muscle_data = readtable([model_dir '/' muscles_file '.csv'],'VariableNamingRule','preserve');
contacts_data = readtable([model_dir '/' contacts_file '.csv'],'VariableNamingRule','preserve');

if strcmp(global_or_local,'local')
    
    frame_data = readtable([model_dir '/' frame_file '.csv'],'VariableNamingRule','preserve');
    
    %check if all bodies have a local frame assigned
    if any(strcmp(body_data.local_frame_name,'not_assigned'))
            
        ind_noframe_bodies = find(strcmp(body_data.local_frame_name,'not_assigned'));
        noframe_bodies = body_data.BODY_name(ind_noframe_bodies);
        
        errorMessage = sprintf(['Constructing a model with local frames requires ' ...
            'all bodies to have a local frame assigned. ' ...
            'The following bodies do not have a local frame assigned:\n%s'], strjoin(noframe_bodies, '\n'));

        % Throw the error with the formatted message
        error(errorMessage);
    end

    %check if all assigned local frames exist in the frames file
    if ~all(ismember(body_data.local_frame_name, frame_data.frame_name)) %if not all the local frames defined in bodies are actually available in frame data
        
        ind_missing_frames = ~ismember(body_data.local_frame_name, frame_data.frame_name);
        missing_frames = body_data.local_frame_name(ind_missing_frames);
        
        % Create a formatted string that includes the incorrect strings
        errorMessage = sprintf(['Constructing a model with local frames requires ' ...
            'all bodies to have a local frame assigned that corresponds to the frame file. ' ...
            'The following bodies have local_frames assigned that do not exist in the imported frames file:\n%s'], strjoin(missing_frames, '\n'));

        % Throw the error with the formatted message
        error(errorMessage);
        



    end
    
end



%% DO I LEAVE THIS?

joints_to_fix = {'none'};

%% post process muscle landmarks

muscle_point_names = muscle_data.muscle_point_name;

% Use regular expression to remove the suffix (_or, _ins, _via#)
pattern = '_or|_ins|_via\d+';
muscle_names = regexprep(muscle_point_names, pattern, '');

% Get the unique muscle names
muscle_names = unique(muscle_names);


%% Instantiate an (empty) OpenSim Model
model = Model();
model.setName(model_name);


%% Set up some basic parameters

ground = model.getGround();

% Define the acceleration of gravity
model.setGravity(Vec3(0, -9.80665, 0));

orientation_zero = Vec3(0,0,0); %Joint axes orientations.

%% Set up a linear function for the SpatialTransform of each CustomJoint (see OpenSim docs)

%Create an opensim linear function with coefficients 1 & 0, eg. 1x + 0. This maps the coordinate to the joint.
fun = LinearFunction();
coefs = ArrayDouble();
coefs.append(1);
coefs.append(0);
fun.setCoefficients(coefs);


%% Body loop
for i = 1:height(body_data)

    body_name =body_data.BODY_name(i);

    body = Body();
    body.setName(body_name);
    body.setMass(body_data.("mass(kg)")(i));


    if strcmp(global_or_local,'global')
        ind_COM_glob = (find((contains(body_data.Properties.VariableNames, 'COM') & contains(body_data.Properties.VariableNames, 'global')) & ~contains(body_data.Properties.VariableNames, 'Ixx')));
        COM_glob(i,:) = body_data{i,ind_COM_glob};
        body.setMassCenter(ArrayDouble.createVec3(COM_glob(i,:)));

    elseif strcmp(global_or_local,'local')  %if local, assume COM is the body origin
        ind_COM_loc = (find((contains(body_data.Properties.VariableNames, 'COM') & contains(body_data.Properties.VariableNames, 'local')) & ~contains(body_data.Properties.VariableNames, 'Ixx')));
        COM_loc(i,:) = body_data{i,ind_COM_loc};
        body.setMassCenter(ArrayDouble.createVec3(COM_loc(i,:)));

        frame_name = body_data.local_frame_name{i}; %body_fixed frame

        frame_ind = find(strcmp(frame_name, frame_data.frame_name)); %index to the frame
        euler_ind = find(contains(frame_data.Properties.VariableNames, 'Euler')); % indices to the euler angles
        pos_ind = find(contains(frame_data.Properties.VariableNames, 'pos')); %indices to global position of the frame origin


        bodyframe_or_glob_eulerXYZ(i,:) = frame_data{frame_ind,euler_ind};%
        bodyframe_pos_glob(i,:) = frame_data{frame_ind,pos_ind};%


        [gRb, bRg] = matrix_from_euler_XYZbody(bodyframe_or_glob_eulerXYZ(i,:));

        %The geometry is aligned in the global reference frame. You can interpret this as
        % a frame that is global 0,0,0, aligned to the global axes. However, if we
        %use local reference frames for our bodies, the geometries need to
        %be defined with respect to those local reference frames. Thus, we
        %need to define a transformation fromt he global origin to the
        %body-fixed local frame. In essence, we are trying to find the
        %global origin position and global orientation, with respect to the
        %body-fixed frame - i.e. bRg*(or_g - body_or_g).
        % To go from body fixed to global, we rotate with gRb. But now, we want the
        %inverse rotation, we want to rotate from global to body fixed, so that the
        %geometry is aligned with the body-fixed local frame.
        % This is achieved with the matrix bRg. 
        % We'll implement this offset with an OpenSim offsetframe, and
        % decompose bRg. We'll call these decomposed angles the inverse
        % euler angles.

        % this is a body-fixed Euler XYZ decomposition

        phi_x_inv = atan2(-bRg(2,3), bRg(3,3));
        phi_y_inv = asin(bRg(1,3));
        phi_z_inv = atan2(-bRg(1,2), bRg(1,1));
        euler_angles_inv{i} = [phi_x_inv phi_y_inv phi_z_inv];

        % If the offset frame's origin is not shifted, the origin is
        % coincident with the local_frame origin. We want it to be placed
        % in the global origin, accounting for the local_frame's
        % orientation.
        % The offset in position is essentially the vector:
        % (global_origin - local_frame_origin). Both are initially reported
        % in the global frame, so we also rotate it to the body frame:
        %  bRg* ([0;0;0] - frame_or_g) = bRg* (-frame_or_g);
        
        position_offset(i,:) = bRg*(-bodyframe_pos_glob(i,:)');  %global origin position in the body_fixed frame
        
        
        %create an offset frame
        offsetframe = PhysicalOffsetFrame();
        offsetframe.setName([body.getName.char '_geom_frame']);
        offsetframe.set_orientation(ArrayDouble.createVec3( euler_angles_inv{i})); %rotate to global orientation wrt local_frame
        offsetframe.set_translation(ArrayDouble.createVec3(position_offset(i,:)));  %shift it from frame origin back to global origin
     
        offsetframe.connectSocket_parent(body);
        body.addComponent(offsetframe);
        
       
    end

    %moment of inertia about COM in global reference frame
    if strcmp(global_or_local,'global')

        ind_MOI_glob = (find((contains(body_data.Properties.VariableNames, 'I') & contains(body_data.Properties.VariableNames, 'global'))));
        MOI_glob(i,:) = body_data{i,ind_MOI_glob};

        body.setInertia(Inertia(ArrayDouble.createVec3(MOI_glob(i,1:3)),  ArrayDouble.createVec3(MOI_glob(i,4:6))));

        %moment of inertia about COM in local reference frame
    elseif strcmp(global_or_local,'local')
        ind_MOI_loc = (find((contains(body_data.Properties.VariableNames, 'I') & contains(body_data.Properties.VariableNames, 'local'))));
        MOI_loc(i,:) = body_data{i,ind_MOI_loc};

        body.setInertia(Inertia(ArrayDouble.createVec3(MOI_loc(i,1:3)),  ArrayDouble.createVec3(MOI_loc(i,4:6))));

    end


    if ~strcmp(body_data.Geometry{i},'no geometry') %if there is attached geometry
        
        %remove the trailing geometry delimiter, then split into separate geometries
        %(if there are more than one)
        geoms = strip(body_data.Geometry{i},'right',';');
        geoms = split(geoms,';');


        for g = 1:length(geoms)

            if strcmp(global_or_local,'global')
                body.attachGeometry(Mesh(geoms{g}));

            elseif strcmp(global_or_local,'local')


                offsetframe.attachGeometry(Mesh(geoms{g}));



            end
        end
    end

    model.addBody(body)
    %model.initSystem()
end


%% Joint loop
for j = 1:height(joint_data)

    joint_name = joint_data.joint_name{j};

    % orientation and position
    if strcmp(global_or_local,'global')
        % global position
        ind_pos_glob = (find(contains(joint_data.Properties.VariableNames, 'pos') & contains(joint_data.Properties.VariableNames, 'global')));
        pos_glob(j,:) = joint_data{j,ind_pos_glob};

        position_global = ArrayDouble.createVec3(pos_glob(j,:));  %global location


        % global orientation
        ind_or_glob = (find(contains(joint_data.Properties.VariableNames, 'or') & contains(joint_data.Properties.VariableNames, 'global') &  contains(joint_data.Properties.VariableNames, 'euler')));
        or_glob(j,:) = joint_data{j,ind_or_glob};

        orientation_global = ArrayDouble.createVec3(or_glob(j,:));  %global orientation

    elseif strcmp(global_or_local,'local')


        % pos in parent
        ind_pos_parent = (find(contains(joint_data.Properties.VariableNames, 'pos') & contains(joint_data.Properties.VariableNames, 'parent')));
        pos_parent(j,:) = joint_data{j,ind_pos_parent};

        position_in_parent = ArrayDouble.createVec3(pos_parent(j,:));

        % or in parent
        ind_or_parent = (find(contains(joint_data.Properties.VariableNames, 'or') & contains(joint_data.Properties.VariableNames, 'parent') &  contains(joint_data.Properties.VariableNames, 'euler')));
        or_parent(j,:) = joint_data{j,ind_or_parent};

        orientation_in_parent = ArrayDouble.createVec3(or_parent(j,:));

        % pos in child
        ind_pos_child = (find(contains(joint_data.Properties.VariableNames, 'pos') & contains(joint_data.Properties.VariableNames, 'child')));
        pos_child(j,:) = joint_data{j,ind_pos_child};

        position_in_child = ArrayDouble.createVec3(pos_child(j,:));

        % or in child
        ind_or_child = (find(contains(joint_data.Properties.VariableNames, 'or') & contains(joint_data.Properties.VariableNames, 'child') &  contains(joint_data.Properties.VariableNames, 'euler')));
        or_child(j,:) = joint_data{j,ind_or_child};

        orientation_in_child = ArrayDouble.createVec3(or_child(j,:));

    end



    %coordinates and spatialtransform

    S_T = SpatialTransform();

    ind_coords = (find(contains(joint_data.Properties.VariableNames, 'coordinate') ));


    n_coordinates = 0; %start with 0, add 1 per additional coordinate
    for co = 1:length(ind_coords) %loop through coordinates

        if iscell(joint_data{j,ind_coords(co)});%empty coordinate columns get filled in with NaN by readtable. If it's a cell, this should contain the coordinate name
            if ~isempty(joint_data{j,ind_coords(co)}{:}) %ensure the coordinate isn't empty

                coor_name = ArrayStr(joint_data{j,ind_coords(co)}{:},1); %to be added to the SpatialTransform

                n_coordinates = n_coordinates +1; %add one coordinate
                if co == 1
                    transform_axis = S_T.get_translation1;
                elseif co == 2
                    transform_axis = S_T.get_translation2;
                elseif co == 3
                    transform_axis = S_T.get_translation3;
                elseif co == 4
                    transform_axis = S_T.get_rotation1;
                elseif co == 5
                    transform_axis = S_T.get_rotation2;
                elseif co == 6
                    transform_axis = S_T.get_rotation3;
                end

                transform_axis.set_function(fun);
                transform_axis.setCoordinateNames(coor_name);
            end
        end

    end


    if strcmp(joint_data.parent_body{j},'ground') %if the joint parent is ground
        parentbody = model.getGround();

    else
        parentbody = model.getBodySet.get(joint_data.parent_body{j});

    end
    childbody = model.getBodySet.get(joint_data.child_body{j});


    if n_coordinates > 0 %if more than one coordinate

        if strcmp(global_or_local,'global')

            joint = CustomJoint(joint_name,parentbody, position_global,orientation_global,...
                childbody,position_global, orientation_global,S_T);

        elseif strcmp(global_or_local,'local')


            joint = CustomJoint(joint_name,parentbody, position_in_parent,orientation_in_parent,...
                childbody, position_in_child,orientation_in_child,S_T);

        end

        
    elseif n_coordinates == 0  %if n_coordinates is zero, the joint becomes a weldjoint

        if strcmp(global_or_local,'global')

            joint = WeldJoint(joint_name,parentbody, position_global,orientation_global,...
                childbody,position_global, orientation_global);

        elseif strcmp(global_or_local,'local')

            joint = WeldJoint(joint_name,parentbody, position_in_parent,orientation_in_parent,...
                childbody, position_in_child,orientation_in_child);

        end
        
    end

    model.addJoint(joint);

end

%% muscles


%% Define muscles in a loop

for i = 1:length(muscle_names)
    muscle_name = muscle_names{i};
    muscle = DeGrooteFregly2016Muscle();
    muscle.setName(muscle_name);
    
    muscle_ind = find(contains(muscle_data.muscle_point_name,muscle_name)); %all indices of muscle points of the current muscle
    
    %set the opensim muscle inputs from the muscle_data file
    muscle.setMaxIsometricForce(muscle_data.("F_max(N)")(muscle_ind(1))); %
    muscle.setOptimalFiberLength(muscle_data.("optimal_fiber_length(m)")(muscle_ind(1)));
    muscle.setTendonSlackLength(muscle_data.("tendon_slack_length(m)")(muscle_ind(1)));
    muscle.setPennationAngleAtOptimalFiberLength(deg2rad(muscle_data.("pennation_angle(deg)")(muscle_ind(1))));
    
    %muscle.set_tendon_strain_at_one_norm_force(0.04)

    n_mpts = length(muscle_ind); %number of muscle points
    n_vpts = n_mpts - 2; %number of viapoints is equal to total points - or and ins

    %%%% loop through muscle points

    for k =1:n_mpts %%% for the number of muscle points


        %%% if statement that forces muscles to be constructed in the order
        %%% origin, via1, ... vian, ins.
        if k == 1; %%% origin
            name = strjoin([muscle_names(i) '_or'],''); %joins together without a space

        elseif k>1 & k<n_mpts; %%% if the muscle origin is defined and we aren't at the last point yet
            name = strjoin([muscle_names(i) '_via' num2str(k-1)],''); %joins together without a space

        else k == n_mpts ; %%% last point is the insertion
            name = strjoin([muscle_names(i) '_ins'],''); %joins together without a space
        end
        ind =  startsWith(muscle_data.muscle_point_name,name); %index of the muscle origin
        body_name = [muscle_data.parent_body_name{ind}]; %this is the body that the viapoints get attached to

        if strcmp(global_or_local,'global')
                
            %get the column indices to muscle point global position
            pos_glob_indices = find(contains(muscle_data.Properties.VariableNames,'pos') & contains(muscle_data.Properties.VariableNames,'global'));
            point_pos_glob = muscle_data{ind,pos_glob_indices};

            point = ArrayDouble.createVec3(point_pos_glob); %vec3 of the point

        elseif strcmp(global_or_local,'local')
            
            %get the column indices to muscle point local position
            pos_loc_indices = find(contains(muscle_data.Properties.VariableNames,'pos') & contains(muscle_data.Properties.VariableNames,'local'));
            point_pos_loc = muscle_data{ind,pos_loc_indices};

            point = ArrayDouble.createVec3(point_pos_loc); %vec3 of the point


        end
        muscle.addNewPathPoint([name], model.getBodySet.get(body_name), point);

    end

    model.addForce(muscle)


end
% % % % %
% % % % % %% Define ligaments in a loop
% % % % %
% % % % % for i = 1:length(ligament_names)
% % % % %     ligament = Ligament();
% % % % %     ligament.setName([ligament_names{i}]);
% % % % %
% % % % %     geoPath = ligament.get_GeometryPath;
% % % % %
% % % % %
% % % % %     n_mpts = length(ligLMs.headers( startsWith(ligLMs.headers,[ligament_names{i} '_']))); %number of ligament points
% % % % %     n_vpts = n_mpts - 2; %number of viapoints is equal to total points - or and ins
% % % % %
% % % % %     %%%% loop through ligament points
% % % % %
% % % % %     for k =1:n_mpts %%% for the number of ligament points
% % % % %
% % % % %
% % % % %         %%% if statement that forces ligaments to be constructed in the order
% % % % %         %%% origin, via1, ... vian, ins.
% % % % %         if k == 1; %%% origin
% % % % %             name = strjoin([ligament_names(i) '_or'],''); %joins together without a space
% % % % %
% % % % %         elseif k>1 & k<n_mpts; %%% if the ligament origin is defined and we aren't at the last point yet
% % % % %             name = strjoin([ligament_names(i) '_via' num2str(k-1)],''); %joins together without a space
% % % % %
% % % % %         else k == n_mpts ; %%% last point is the insertion
% % % % %             name = strjoin([ligament_names(i) '_ins'],''); %joins together without a space
% % % % %         end
% % % % %         ind =  startsWith(ligLMs.headers,name); %index of the ligament origin
% % % % %         body = [ligLMs.VPBodies{ind}]; %this is the body that the viapoints get attached to
% % % % %
% % % % %         if strcmp(global_or_local,'global')
% % % % %             point = ArrayDouble.createVec3(ligLMs.points(ind,:)); %vec3 of the point
% % % % %
% % % % %         elseif strcmp(global_or_local,'local')
% % % % %
% % % % %
% % % % %             ind_PPbody = find(strcmp(BSPs.headers,body)); %find the index to the parent body
% % % % %              point = ArrayDouble.createVec3(bRg{ind_PPbody} *(ligLMs.points(ind,:) - BSPs.CoM(ind_PPbody,:))' ); %global point location - global body COM location
% % % % %
% % % % %
% % % % %         end
% % % % %         geoPath.appendNewPathPoint([name], model.getBodySet.get(body), point);
% % % % %
% % % % %     end
% % % % %
% % % % %     model.addForce(ligament)
% % % % %
% % % % %
% % % % % end
% % % % %
%% Make a Contact plane
groundContactLocation = Vec3(0,0.0,0);
groundContactOrientation = Vec3(0,0,-pi/2);
groundContactSpace = ContactHalfSpace(groundContactLocation, groundContactOrientation, ground);
groundContactSpace.setName('GroundContact');
model.addContactGeometry(groundContactSpace);

%% Add contacts & contact forces

r_contactsphere=0.015; %radius in meters

stiffness           = 11250000;  %version 2
dissipation         = 1;
staticFriction      = 0.4;
dynamicFriction     = 0.4;
viscousFriction     = 0.1;
transitionVelocity  = 0.2;

ConstantContactForce = 1e-5; % ConstantContactForce
HertzSmoothing = 300; % HertzSmoothing; version 2
HuntCrossleySmoothing = 50; % HuntCrossleySmoothing


for i= 1:height(contacts_data)


    %%%% Right side sphere
    contactSphere = ContactSphere();
    contactSphere.setRadius(r_contactsphere);
    name = contacts_data.CONTACT_name{i};
    contactSphere.setName(name);
    if strcmp(global_or_local,'global')
        pos_glob_indices = find(contains(contacts_data.Properties.VariableNames,'pos') & contains(contacts_data.Properties.VariableNames,'global'));
        contact_pos_glob = contacts_data{i,pos_glob_indices};

        contact_position = ArrayDouble.createVec3(contact_pos_glob); %vec3 of the contact
        
    elseif strcmp(global_or_local,'local')
        pos_loc_indices = find(contains(contacts_data.Properties.VariableNames,'pos') & contains(contacts_data.Properties.VariableNames,'local'));
        contact_pos_loc= contacts_data{i,pos_loc_indices};

        contact_position = ArrayDouble.createVec3(contact_pos_loc); %vec3 of the contact
        

    end


    contactSphere.setLocation(contact_position);
    contactSphere.setFrame(model.getBodySet.get(contacts_data.parent_body{i}));
    model.addContactGeometry(contactSphere);

   %%%% Right side force
    SSHSForce = SmoothSphereHalfSpaceForce();
    SSHSForce.setName(strrep(name,'Contact','Force')); %RFootContact becomes RFootForce, etc.
    SSHSForce.connectSocket_sphere(contactSphere);
    SSHSForce.connectSocket_half_space(groundContactSpace);

    SSHSForce.set_stiffness(stiffness);
    SSHSForce.set_dissipation(dissipation);
    SSHSForce.set_static_friction(staticFriction);
    SSHSForce.set_dynamic_friction(dynamicFriction);
    SSHSForce.set_viscous_friction(viscousFriction);


    SSHSForce.set_transition_velocity(transitionVelocity);
    SSHSForce.set_hertz_smoothing(HertzSmoothing);

    model.addForce(SSHSForce);


end


%% Print model file
model.finalizeConnections();
model.initSystem();




if strcmp(global_or_local,'local')
    version = [version '_local'];
end
model.print([model_dir '/' filename version '.osim']);


% % %%
% %
% % if strcmp(export_nomusc_version,'yes')
% %
% %
% %
% %     ModelFactory.removeMuscles(model)
% %     model.initSystem;
% %     model.finalizeConnections;
% %
% %
% %     model.print([filename version '_nomuscles.osim']);
% % end
% %
% %
