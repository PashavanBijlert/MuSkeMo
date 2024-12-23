% Run the dialog
userInputsDialog();

function userInputsDialog()
% Create a figure for the dialog
fig = uifigure('Position', [100 100 600 600], 'Name', 'Select your files for OpenSim model creation');

% Model Directory
uilabel(fig, 'Position', [30 540 100 22], 'Text', 'Model Directory');
modelDirField = uieditfield(fig, 'text', 'Position', [200 540 200 22]);
modelDirField.Tooltip = 'Directory where your MuSkeMo outputs are located, and where the OpenSim model will be created'
uibutton(fig, 'Position', [450 540 50 22], 'Text', 'Browse', 'ButtonPushedFcn', @(btn, event) browseDirectory(modelDirField));


% Data File Selection
DatafileLabels = {'Bodies', 'Joint Centers', 'Muscles (optional)', 'Wrap objects (optional)', 'Contacts (optional)', 'Frames (optional)'};

datafileTooltips = {'Bodies file';
    'Joint centers file (optional)';
    'Muscles file (optional)';
    'Wrap objects file (optional)';
    'Contacts file (optional)';
    'Frames file (optional. Required if you want a locally-defined model'};
datafileFields = cell(1, length(DatafileLabels));
for i = 1:length(DatafileLabels)
    uilabel(fig, 'Position', [30 500 - (i - 1) * 40 150 22], 'Text', DatafileLabels{i});
    datafileFields{i} = uieditfield(fig, 'text', 'Position', [200 500 - (i - 1) * 40 200 22]);
    datafileFields{i}.Tooltip = datafileTooltips{i};
    
    uibutton(fig, 'Position', [450 500 - (i - 1) * 40 50 22], 'Text', 'Browse', 'ButtonPushedFcn', @(btn, event) browseFile(datafileFields{i},modelDirField.Value));
end


% Model Name
uilabel(fig, 'Position', [30 260 100 22], 'Text', 'Model Name');
modelNameField = uieditfield(fig, 'text', 'Position', [200 260 200 22]);
modelNameField.Tooltip = 'Model name in OpenSim';

% Filename
uilabel(fig, 'Position', [30 220 100 22], 'Text', 'Filename');
filenameField = uieditfield(fig, 'text', 'Position', [200 220 200 22]);
filenameField.Tooltip = 'File name of the .osim model file.';

% Version
uilabel(fig, 'Position', [30 180 100 22], 'Text', 'Version');
versionField = uieditfield(fig, 'text', 'Position', [200 180 200 22],'Value','v1');
versionField.Tooltip = 'Designate the version number here';

% Global or Local
uilabel(fig, 'Position', [30 140 100 22], 'Text', 'Global or Local');
globalOrLocalDropdown = uidropdown(fig, 'Position', [200 140 200 22], 'Items', {'global', 'local'});
globalOrLocalDropdown.Tooltip = {'Do you want the model defined in global or local coordinates?';
    'Local coordinates require local / anatomical reference frames to be defined'};

% Export NoMusc Version
uilabel(fig, 'Position', [30 100 150 22], 'Text', 'Export NoMusc Version');
exportNoMuscDropdown = uidropdown(fig, 'Position', [200 100 200 22], 'Items', {'yes', 'no'},'Value','no');
exportNoMuscDropdown.Tooltip = 'Export a version without muscles. Can be useful for debugging';




% Create OpenSim model Button
uibutton(fig, 'Position', [140 60 200 22], 'Text', 'Create OpenSim Model', 'ButtonPushedFcn', @(btn, event) CreateOpenSimModelFunc(UnpackFields(modelDirField, datafileFields, modelNameField, filenameField, versionField, globalOrLocalDropdown, exportNoMuscDropdown)));



    function browseDirectory(modelDirField)
        
        folderPath = uigetdir('', 'Select a folder');
        if folderPath ~= 0
            modelDirField.Value = folderPath;
        end
        
        % Bring the User Inputs window back to focus
        fig.WindowState = 'normal';
        fig.Visible = 'on';
        figure(fig); % Bring the figure to the front
    end

    function browseFile(field,modeldir)
        
        
        [file, path] = uigetfile([modeldir '/*.*'], 'Select a file');
        if file ~= 0
            field.Value = file;
        end
        
        % Bring the User Inputs window back to focus
        fig.WindowState = 'normal';
        fig.Visible = 'on';
        figure(fig); % Bring the figure to the front
    end

end


function [ModelInfoStruct] = UnpackFields(modelDirField, datafileFields, modelNameField, filenameField, versionField, globalOrLocalDropdown, exportNoMuscDropdown)
%% This function unpacks the values from the UI button fields so that the Model creation script can be cleaner, having only a single struct which contains strings as an input.



ModelInfoStruct.model_dir = modelDirField.Value;
ModelInfoStruct.bodies_file = datafileFields{1}.Value;
ModelInfoStruct.joints_file = datafileFields{2}.Value;
ModelInfoStruct.muscles_file = datafileFields{3}.Value;
ModelInfoStruct.wrapping_file = datafileFields{4}.Value;
ModelInfoStruct.contacts_file = datafileFields{5}.Value;
ModelInfoStruct.frame_file = datafileFields{6}.Value;
ModelInfoStruct.model_name = modelNameField.Value;
ModelInfoStruct.filename = filenameField.Value;
ModelInfoStruct.version = versionField.Value;
ModelInfoStruct.global_or_local = globalOrLocalDropdown.Value;
ModelInfoStruct.export_nomusc_version = exportNoMuscDropdown.Value;

%% error checking
if isempty(ModelInfoStruct.model_dir)
    error(["You did not select the 'Model Directory'. You have to select the directory that contains all your MuSkeMo outputs."])
end

if isempty(ModelInfoStruct.bodies_file)
    error(["You did not select a 'Bodies' file. You have to specify one, and ensure it is in the model directory."])
end

if isempty(ModelInfoStruct.joints_file)
    error(["You did not select a 'Joints' file. You have to specify one, and ensure it is in the model directory."])
end


end