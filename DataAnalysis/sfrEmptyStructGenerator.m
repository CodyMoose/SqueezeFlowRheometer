function sfrStruct = sfrEmptyStructGenerator()
%SFRTRUCTGENERATOR Generates empty struct in the same form as sfrStructGenerator
%   Generates empty struct in the same form as sfrStructGenerator
% Outputs
%    sfrStruct  : a struct with the following properties, all of which are empty stand-ins
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
    
    % Get data straight from the file
    sfrStruct.t = [];
    sfrStruct.F = [];
    sfrStruct.F_tar = [];
    sfrStruct.h = [];
    sfrStruct.V = [];

    % Compute useful values based on data
    sfrStruct.R = [];
    sfrStruct.aspectRatio = [];
    sfrStruct.ScottYieldStress = [];
    sfrStruct.MeetenYieldStress = [];
    
    % Get unique target forces and identify when each step starts and stops
    sfrStruct.F_tars = [];
    sfrStruct.StepEndIndices = [];
end