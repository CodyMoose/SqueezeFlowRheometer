function sfrStruct = sfrStructGenerator(filePath)
%SFRTRUCTGENERATOR Gets useful values from SFR data files
%   Takes in Squeeze Flow Rheometer data and generates a struct with
%   information about the test.
% Inputs
%    filePath              : location of the SFR data file
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

    % Get the file
    sfrDataTable = readtable(filePath);

    % Discard pre- and post- test data
    %   (before it reaches the sample and after the last step is done)
    activeIndices = strcmp(sfrDataTable.TestActive_,'True');
    sfrDataTable = sfrDataTable(activeIndices,:);
    
    % Get data straight from the file
    sfrStruct.t = sfrDataTable.ElapsedTime;
    sfrStruct.F = gramsToN(sfrDataTable.CurrentForce_g_);
    sfrStruct.F_tar = gramsToN(sfrDataTable.TargetForce_g_);
    sfrStruct.h = sfrDataTable.CurrentGap_m_;
    sfrStruct.V = sfrDataTable.ViscosityVolume_m_3_;

    % Compute useful values based on data
    sfrStruct.R = sqrt(sfrStruct.V./(sfrStruct.h * pi));
    sfrStruct.aspectRatio = sfrStruct.h ./ sfrStruct.R;
    sfrStruct.ScottYieldStress = 1.5*sqrt(pi) * (sfrStruct.F .* sfrStruct.h.^(2.5) ./ (sfrStruct.V.^(1.5)));
    sfrStruct.MeetenYieldStress = (sfrStruct.F .* sfrStruct.h ./ sfrStruct.V(1)) / sqrt(3);
    
    % Get unique target forces and identify when each step starts and stops
    sfrStruct.F_tars = unique(sfrStruct.F_tar);
    sfrStruct.StepEndIndices = zeros(length(sfrStruct.F_tars),2);
    for i = 1:length(sfrStruct.F_tars)
        sfrStruct.StepEndIndices(i,1) = find(sfrStruct.F_tar == sfrStruct.F_tars(i),1,"first");
        sfrStruct.StepEndIndices(i,2) = find(sfrStruct.F_tar == sfrStruct.F_tars(i),1,"last");
    end


    % Get test date, test number, and sample volume as strings
    fileName = extractAfter(filePath, "\");

    temp = split(fileName,"PID_squeeze_flow_1_Test");
    dateStr = extractAfter(extractBefore(temp(1),"_"),"-"); % get just month and day
    temp = replace(temp(2), "-","_");
    temp = split(temp(1), "_");
    testNum = temp(1);
    sampleSubstance = lower(temp(2));
    testNum = extractBefore(testNum(1),2);
    % volStr = num2str(sfrStruct.V(1)*10^6,3) + "mL";
    volStr = num2str(sfrStruct.V(1)*10^6,"%.2f") + "mL";

    sfrStruct.dateStr = dateStr;
    sfrStruct.testNum = testNum;
    sfrStruct.sampleSubstance = sampleSubstance;
    sfrStruct.volStr = volStr;
end

function F = gramsToN(f)
    F = 0.00980665 * f;
end