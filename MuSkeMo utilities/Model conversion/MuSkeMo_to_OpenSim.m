function userInputsDialog()
    %% Create a figure for the dialog
    fig = uifigure('Position', [100 100 600 600], 'Name', 'Select your files for OpenSim model creation');
    
    % Create a grid layout for the entire figure
    mainGrid = uigridlayout(fig);
    mainGrid.RowHeight = {'1x'}; % Single row to stretch the tab group
    mainGrid.ColumnWidth = {'1x'}; % Single column to stretch the tab group

    % Create a tab group and attach it to the main grid
    tabGroup = uitabgroup(mainGrid);
    tabGroup.Layout.Row = 1;
    tabGroup.Layout.Column = 1;

    % Create tabs
    modelDataTab = uitab(tabGroup, 'Title', 'Model data');
    muscleParamsTab = uitab(tabGroup, 'Title', 'Muscle parameters');
    contactParamsTab = uitab(tabGroup, 'Title', 'Contact parameters');
    
    %% Add UI components to the "Model data" tab
    n_rows = 13;
    % Create a grid layout for the "Model data" tab
    grid = uigridlayout(modelDataTab, [n_rows, 3]);
    grid.RowHeight = repmat({'fit'}, 1, n_rows);
    grid.ColumnWidth = {'1x', '2x', 'fit'};

    %% Model Directory
    uilabel(grid, 'Text', 'Model Directory', 'HorizontalAlignment', 'right');
    modelDirField = uieditfield(grid, 'text');
    modelDirField.Tooltip = 'Directory where your MuSkeMo outputs are located, and where the OpenSim model will be created';
    uibutton(grid, 'Text', 'Browse', 'ButtonPushedFcn', @(btn, event) browseDirectory(modelDirField));

    %% Data File Selection
    DatafileLabels = {'Bodies', 'Joint Centers', 'Muscles (optional)', 'Wrap objects (optional)', 'Contacts (optional)', 'Frames (optional)'};
    datafileTooltips = {'Bodies file', 'Joint centers file (optional)', 'Muscles file (optional)', ...
        'Wrap objects file (optional)', 'Contacts file (optional)', ...
        'Frames file (optional. Required if you want a locally-defined model)'};
    datafileFields = cell(1, length(DatafileLabels));

    for i = 1:length(DatafileLabels)
        uilabel(grid, 'Text', DatafileLabels{i}, 'HorizontalAlignment', 'right');
        datafileFields{i} = uieditfield(grid, 'text');
        datafileFields{i}.Tooltip = datafileTooltips{i};
        uibutton(grid, 'Text', 'Browse', ...
            'ButtonPushedFcn', @(btn, event) browseFile(datafileFields{i}, modelDirField.Value));
    end

    %% Manual inputs
    ManualInputLabels = {'Model Name'; 'Filename'; 'Version'};
    ManualInputTooltips = {'Model name in OpenSim';...
        'File name of the .osim model file.';...
        'Designate the version number here'};

    ManualInputFields = cell(1, length(ManualInputLabels));

    for i = 1:length(ManualInputLabels)
        ui_label = uilabel(grid, 'Text', ManualInputLabels{i}, 'HorizontalAlignment', 'right');
        ui_label.Layout.Row = length(DatafileLabels) + i + 1;
        ui_label.Layout.Column = 1;
        if ~strcmp(ManualInputLabels{i}, 'Version')
            ui_editfield = uieditfield(grid, 'text');
        else
            ui_editfield = uieditfield(grid, 'text', 'Value', 'v1');
        end
        ui_editfield.Tooltip = ManualInputTooltips{i};
        ManualInputFields{i} = ui_editfield;
    end

    %% Dropdown fields
    DropDownLabels = {'Global or Local'; 'Export NoMusc Version'};
    DropDownOptions = {{'global', 'local'}; {'no', 'yes'}};
    DropDownTooltips = {{'Do you want the model defined in global or local coordinates?', ...
        'Local coordinates require local / anatomical reference frames to be defined'}; ...
        'Export a version without muscles. Can be useful for debugging'};
    
    DropDownFields = cell(1, length(DropDownLabels));

    for i = 1:length(DropDownLabels)
        ui_label = uilabel(grid, 'Text', DropDownLabels{i}, 'HorizontalAlignment', 'right');
        ui_label.Layout.Row = length(DatafileLabels) + length(ManualInputLabels) + i + 1;
        ui_label.Layout.Column = 1;
    
        ui_dropdown = uidropdown(grid, 'Items', DropDownOptions{i});
        ui_dropdown.Tooltip = DropDownTooltips{i};

        DropDownFields{i} = ui_dropdown;
    end

%% Define Muscle Parameter Labels, Tooltips, and Defaults
muscleParamLabels = {'v_max', 'SEE_strain_at_Fmax', 'PEE_strain_at_Fmax'};
muscleParamTooltips = { ...
    'Maximal contractile velocity in L0/s', ...
    'Strain in the serial elastic element when the tendon force is equal to maximal isometric force',...
    'Strain in the parallel elastic element when PEE force reaches max isometric force'};
muscleParamDefaults = [10, 0.04, 0.6];


%% Add a grid layout to the "Muscle parameters" tab
nRows = length(muscleParamLabels); % Automatically adapts to the number of parameters
muscleParamsGrid = uigridlayout(muscleParamsTab, [nRows, 2]);
muscleParamsGrid.RowHeight = repmat({'fit'}, 1, nRows);
muscleParamsGrid.ColumnWidth = {'1x', '2x'};

%% Populate the "Muscle parameters" tab dynamically
muscleParamFields = cell(1, nRows);

for i = 1:nRows
    % Create label
    ui_label = uilabel(muscleParamsGrid, 'Text', muscleParamLabels{i}, 'HorizontalAlignment', 'right');
    ui_label.Layout.Row = i;
    ui_label.Layout.Column = 1;

    % Create input field
    ui_editfield = uieditfield(muscleParamsGrid, 'numeric', 'Value', muscleParamDefaults(i));
    ui_editfield.Tooltip = muscleParamTooltips{i};
    ui_editfield.Layout.Row = i;
    ui_editfield.Layout.Column = 2;

    % Store the input field
    muscleParamFields{i} = ui_editfield;
end

%% Define Contact Parameter Labels, Tooltips, and Defaults
contactParamLabels = {'Contact sphere radius','Plane strain modulus', 'Dissipation', 'Static friction',...
    'Dynamic friction', 'Transition velocity', 'Viscous friction', 'Hertz smoothing'};
contactParamTooltips = { 'Contact sphere radius in m',...
    'Contact plane strain modulus in N/m^2', ...
    'Dissipation coefficient in s/m', ...
    'Static friction coefficient',...
    'Dynamic friction coefficient', ...
    'Transition velocity between static and dynamic friction coefficient',...
    'Viscous friction coefficient',...
    'Hertz smoothing parameter for SmoothSphereHalfSpaceForce'};
contactParamDefaults = [0.015, 2500000, 1, 0.4, 0.4, 0.2, 0.1, 300];

%% Add a grid layout to the "Contact Parameters" tab
nRowsContact = length(contactParamLabels); % Automatically adapts to the number of parameters
contactParamsGrid = uigridlayout(contactParamsTab, [nRowsContact, 2]);
contactParamsGrid.RowHeight = repmat({'fit'}, 1, nRowsContact);
contactParamsGrid.ColumnWidth = {'1x', '2x'};

%% Populate the "Contact Parameters" tab dynamically
contactParamFields = cell(1, nRowsContact);

for i = 1:nRowsContact
    % Create label
    ui_label = uilabel(contactParamsGrid, 'Text', contactParamLabels{i}, 'HorizontalAlignment', 'right');
    ui_label.Layout.Row = i;
    ui_label.Layout.Column = 1;

    % Create input field
    ui_editfield = uieditfield(contactParamsGrid, 'numeric', 'Value', contactParamDefaults(i));
    ui_editfield.Tooltip = contactParamTooltips{i};
    ui_editfield.Layout.Row = i;
    ui_editfield.Layout.Column = 2;

    % Store the input field
    contactParamFields{i} = ui_editfield;
end

    %% Create OpenSim Model Button
    create_model_button = uibutton(grid, 'Text', 'Create OpenSim Model', ...
        'ButtonPushedFcn', @(btn, event) CreateOpenSimModelFunc(UnpackFields(modelDirField, datafileFields, ...
        ManualInputFields, DropDownFields, muscleParamFields, contactParamFields)));
    create_model_button.Layout.Row = n_rows;
    create_model_button.Layout.Column = 2;

    %% Nested functions for file browsing
    function browseDirectory(field)
        folderPath = uigetdir('', 'Select a folder');
        if folderPath ~= 0
            field.Value = folderPath;
        end
        figure(fig); % Bring figure to front
    end

    function browseFile(field, modeldir)
        [file, path] = uigetfile([modeldir '/*.*'], 'Select a file');
        if file ~= 0
            field.Value = file;
        end
        figure(fig); % Bring figure to front
    end
end


%%
function [ModelInfoStruct] = UnpackFields(modelDirField, datafileFields, ManualInputFields, DropDownFields, muscleParamFields, contactParamFields)
    % This function unpacks the values from the UI fields into a struct
    % the UI fields are saved as cells.
    ModelInfoStruct.model_dir = modelDirField.Value;
    
    ModelInfoStruct.bodies_file = datafileFields{1}.Value;
    ModelInfoStruct.joints_file = datafileFields{2}.Value;
    ModelInfoStruct.muscles_file = datafileFields{3}.Value;
    ModelInfoStruct.wrapping_file = datafileFields{4}.Value;
    ModelInfoStruct.contacts_file = datafileFields{5}.Value;
    ModelInfoStruct.frame_file = datafileFields{6}.Value;
    
    ModelInfoStruct.model_name = ManualInputFields{1}.Value;
    ModelInfoStruct.filename = ManualInputFields{2}.Value;
    ModelInfoStruct.version = ManualInputFields{3}.Value;
    
    ModelInfoStruct.global_or_local = DropDownFields{1}.Value;
    ModelInfoStruct.export_nomusc_version = DropDownFields{2}.Value;
    
    ModelInfoStruct.v_max = muscleParamFields{1}.Value;
    ModelInfoStruct.SEE_strain_at_Fmax = muscleParamFields{2}.Value;
    ModelInfoStruct.PEE_strain_at_Fmax = muscleParamFields{3}.Value;
    
    ModelInfoStruct.contact_sphere_radius = contactParamFields{1}.Value;
    ModelInfoStruct.plane_strain_modulus= contactParamFields{2}.Value;
    ModelInfoStruct.dissipation= contactParamFields{3}.Value;
    ModelInfoStruct.static_friction_coef= contactParamFields{4}.Value;
    ModelInfoStruct.dynamic_friction_coef= contactParamFields{5}.Value;
    ModelInfoStruct.transition_velocity = contactParamFields{6}.Value;
    ModelInfoStruct.viscous_friction_coef= contactParamFields{7}.Value;    
    ModelInfoStruct.hertz_smoothing = contactParamFields{8}.Value;

    
          


    %% Error checking
    if isempty(ModelInfoStruct.model_dir)
        error("You must select the 'Model Directory'.");
    end
    if isempty(ModelInfoStruct.bodies_file)
        error("You must select a 'Bodies' file.");
    end
    if isempty(ModelInfoStruct.joints_file)
        error("You must select a 'Joints' file.");
    end
    if (strcmp(ModelInfoStruct.global_or_local,'local') & isempty(ModelInfoStruct.frame_file))
        error("You must select a 'Frames' file if you want to construct a model using local definitions.");
    end
end


