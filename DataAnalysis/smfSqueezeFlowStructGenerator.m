function smfStruct = smfSqueezeFlowStructGenerator(filePath)
%SMFSQUEEZEFLOWSTRUCTGENERATOR Gets useful values from SMF squeeze flow
%data
%   Takes in SMF rheometer data for squeeze flow tests and generates a
%   struct with information about the test.
% Inputs
%    filePath              : location of the SMF data file
% Outputs
%    sfrStruct  : a struct with the following properties
%      t                  : current time since test became active, s
%      F                  : current force, N
%      F_tar              : current target force, N
%      F_tars             : list of unique target forces that were tested, N
%      stepEndIndices     : matrix of indices at which each step starts and ends
%      h                  : gap between the two parallel plates, m
%      V                  : operating volume of sample under the plate, m^3
%      R                  : radius of the sample, assuming perfectly cylindrical, m
%      aspectRatio        : h/R, unitless
%      ScottYieldStress   : yield stress computed according to the Scott (1935) model, Pa
%      MeetenYieldStress  : yield stress computed according to the Meeten (2000) model, Pa

    % Get the name of each sheet, and from there the name of each test
    sheets = sheetnames(filePath);
    tests = sheets(2:end);

    smfStruct = sfrEmptyStructGenerator(); % get the same form

    % Get data straight from the file
    for i = 1:length(tests)
        T = loadTriosExcel(filePath,tests(i));

        % Identify when each step starts and ends
        smfStruct.StepEndIndices = [smfStruct.StepEndIndices; length(smfStruct.t) + 1, length(smfStruct.t) + length(T.StepTime)];

        if(i == 1)
            t_start = 0;
        else
            t_start = smfStruct.t(end);
        end
        smfStruct.t = [smfStruct.t; t_start + T.StepTime];

        smfStruct.F = [smfStruct.F; T.NormalForce];
        % no target force saved here, so can't put it in the struct
        smfStruct.h = [smfStruct.h; T.Gap / 1000];
    end
    
    % Extract the sample volume from file title
    volString = split(filePath,'-');
    volString = split(volString(end),'mL');
    volString = replace(volString(1),'_','.');
    vol = str2double(volString) * 10^-6;
    smfStruct.V = vol;

    % Compute useful values based on data
    smfStruct.R = sqrt(smfStruct.V./(smfStruct.h * pi));
    smfStruct.aspectRatio = smfStruct.h ./ smfStruct.R;
    smfStruct.ScottYieldStress = 1.5*sqrt(pi) * (smfStruct.F .* smfStruct.h.^(2.5) ./ (smfStruct.V.^(1.5)));
    smfStruct.MeetenYieldStress = (smfStruct.F .* smfStruct.h ./ smfStruct.V) / sqrt(3);
end

function T = loadTriosExcel(path, sheet)
    [num, txt] = xlsread(path, string(sheet));
    varnames = txt(2,:);
    varnames = regexprep(varnames, '[^a-zA-Z\d\s]', '');
    expression = '(^|[\. ])\s*.';
    replace = '${upper($0)}';
    varnames = regexprep(varnames,expression,replace);
    varnames = regexprep(varnames, '\s', '');
    varunits = txt(3,:);
    T = array2table(num, 'VariableNames', varnames);
    T.Properties.VariableUnits = varunits;
end