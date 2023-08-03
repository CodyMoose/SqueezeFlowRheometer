%% Load Data

sfrDataFolder = "C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\";

sfrFiles = ["2023-07-13_11-38-52_PID_squeeze_flow_1_Test1a-Carbopol_1mL_5g-data.csv";
    "2023-07-13_12-34-44_PID_squeeze_flow_1_Test2a-Carbopol_1mL_5g-data.csv";
    "2023-07-13_12-56-20_PID_squeeze_flow_1_Test3a-Carbopol_1mL_30g-data.csv";
    "2023-07-13_14-33-28_PID_squeeze_flow_1_Test4a-Carbopol_5mL_10g-data.csv";
    "2023-07-18_10-21-01_PID_squeeze_flow_1_Test1a-Carbopol_1mL_5g-data.csv";
    % "2023-07-18_13-36-55_PID_squeeze_flow_1_Test3a-Carbopol_1mL_5g-data.csv"; % force signal was very noisy due to control system issues
    "2023-07-18_14-28-17_PID_squeeze_flow_1_Test4a-Carbopol_2mL_5g-data.csv";
    "2023-07-18_15-18-45_PID_squeeze_flow_1_Test5a-Carbopol_4mL_5g-data.csv";
    % "2023-07-19_14-03-21_PID_squeeze_flow_1_Test1a_Carbopol_1mL_5g-data.csv"; % 07-19 data was not good
    % "2023-07-19_15-03-59_PID_squeeze_flow_1_Test2c-Carbopol_1mL_5g-data.csv";
    % "2023-07-19_15-50-08_PID_squeeze_flow_1_Test3a_Carbopol_1mL_5g-data.csv";
    % "2023-07-19_16-17-19_PID_squeeze_flow_1_Test4a_Carbopol_1mL_5g-data.csv";
    % "2023-07-20_10-30-09_PID_squeeze_flow_1_Test1a_KI=0.7_KP=0.005_decay_rate=-0.1507_carbopol_1mL_5g-data.csv";
    "2023-07-20_10-51-52_PID_squeeze_flow_1_Test2a_carbopol_KI=0.01_power=2.5_1mL_5g-data.csv";
    "2023-07-20_11-22-20_PID_squeeze_flow_1_Test3a_carbopol_KP=3_KI=0.03_power=1_1mL_5g-data.csv";
    "2023-07-20_11-51-48_PID_squeeze_flow_1_Test4a_carbopol_limited_interr_influence_1mL_5g-data.csv";
    "2023-07-20_13-28-05_PID_squeeze_flow_1_Test5a_carbopol_controlled_KP_error_1mL_5g-data.csv";
    "2023-07-20_13-51-13_PID_squeeze_flow_1_Test6a_carbopol_smaller_limitation_carbopol_1mL_5g-data.csv";
    "2023-07-20_14-13-09_PID_squeeze_flow_1_Test7a_carbopol_big_v_test_for_changed_limitations_6mL_5g-data.csv";
    "2023-07-27_13-50-25_PID_squeeze_flow_1_Test1a-CarbopolA_1mL_5g-data.csv";
    "2023-07-27_14-37-43_PID_squeeze_flow_1_Test2a-CarbopolA_1mL_5g-data.csv";
    "2023-07-28_12-32-43_PID_squeeze_flow_1_Test1a-CarbopolB_1mL_5g-data.csv";
    "2023-07-28_13-30-08_PID_squeeze_flow_1_Test2a-CarbopolB_1mL_5g-data.csv";
    "2023-07-28_14-18-07_PID_squeeze_flow_1_Test3a-CarbopolB_1mL_5g-data.csv";
    "2023-07-31_11-35-36_PID_squeeze_flow_1_Test1a-CarbopolB_0mL_5g-data.csv";
    "2023-07-31_15-20-49_PID_squeeze_flow_1_Test2a-CarbopolB_2mL_5g-data.csv";
    "2023-07-31_16-40-45_PID_squeeze_flow_1_Test3a-CarbopolB_2mL_5g-data.csv";
    % "2023-07-31_16-54-45_PID_squeeze_flow_1_Test4b-CarbopolB_2mL_20g-data.csv"; % it was not allowed to reach equilibrium and is not valid
    "2023-08-01_12-01-47_PID_squeeze_flow_1_Test1a-CarbopolA_2mL_5g-data.csv";
    "2023-08-01_12-46-21_PID_squeeze_flow_1_Test2a-CarbopolA_3mL_5g-data.csv";
    "2023-08-01_13-47-01_PID_squeeze_flow_1_Test3a-CarbopolA_4mL_5g-data.csv";
    "2023-08-01_14-48-46_PID_squeeze_flow_1_Test4a-CarbopolA_5mL_5g-data.csv";
    "2023-08-01_15-58-22_PID_squeeze_flow_1_Test5a-CarbopolB_1mL_5g-data.csv";
    "2023-08-02_13-12-39_PID_squeeze_flow_1_Test1a-CarbopolB_2mL_5g-data.csv";
    "2023-08-02_14-19-49_PID_squeeze_flow_1_Test2b-CarbopolB_3mL_5g-data.csv";
    "2023-08-02_15-26-10_PID_squeeze_flow_1_Test3a-CarbopolB_4mL_5g-data.csv";
    "2023-08-02_16-28-59_PID_squeeze_flow_1_Test4a-CarbopolB_5mL_5g-data.csv";
    ];

s = sfrEmptyStructGenerator();
sfrStructs = repmat(s,length(sfrFiles),1);
for i = 1:length(sfrFiles)
    filePath = sfrDataFolder + sfrFiles(i);
    sfrStructs(i) = sfrStructGenerator(filePath);
    % sfrFiles(i)
    % sfrStructs(i)
end

%%% Exclude bad data

% 2023-07-20 Test3a had very bad noise from control system in last 2 steps.
    % Exclude last 2 steps
idx = find(strcmp(sfrFiles,"2023-07-20_11-22-20_PID_squeeze_flow_1_Test3a_carbopol_KP=3_KI=0.03_power=1_1mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices(1:2,:);
end

% 2023-07-20 Test4a was abruptly ended before the last step could finish.
    % Exclude last step
idx = find(strcmp(sfrFiles,"2023-07-20_11-51-48_PID_squeeze_flow_1_Test4a_carbopol_limited_interr_influence_1mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices(1:3,:);
end

% 2023-07-20 Test7a had very bad noise from control system in last 2 steps,
    % unclear why. Exclude last 2 steps
idx = find(strcmp(sfrFiles,"2023-07-20_14-13-09_PID_squeeze_flow_1_Test7a_carbopol_big_v_test_for_changed_limitations_6mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices(1:3,:);
end

% 2023-07-27 Test1a weird behavior in step 5 unclear why.
    % Exclude step 5
idx = find(strcmp(sfrFiles,"2023-07-27_13-50-25_PID_squeeze_flow_1_Test1a-CarbopolA_1mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices([1:4,6:10],:);
end

% 2023-07-27 Test2a weird behavior in steps 8 and 10 unclear why.
    % Exclude steps 8 and 10
idx = find(strcmp(sfrFiles,"2023-07-27_14-37-43_PID_squeeze_flow_1_Test2a-CarbopolA_1mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices([1:7,9],:);
end

% 2023-07-31 Test1a film became too thin to appropriately reach target
    % force after step 6. Exclude steps 7-10
idx = find(strcmp(sfrFiles,"2023-07-31_11-35-36_PID_squeeze_flow_1_Test1a-CarbopolB_0mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices(1:6,:);
end

% 2023-07-31 Test2a had something weird in step 10. Exclude it.
idx = find(strcmp(sfrFiles,"2023-07-31_15-20-49_PID_squeeze_flow_1_Test2a-CarbopolB_2mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices(1:9,:);
end

% 2023-08-01 Test2a had weird plateau in gap for step 14
idx = find(strcmp(sfrFiles,"2023-08-01_12-46-21_PID_squeeze_flow_1_Test2a-CarbopolA_3mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices([1:13,15],:);
end

% 2023-08-01 Test5a had weird plateaus in gap for steps 6, 8, 9, and 11 on
idx = find(strcmp(sfrFiles,"2023-08-01_15-58-22_PID_squeeze_flow_1_Test5a-CarbopolB_1mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices([1:5,7,10],:);
end

% 2023-08-02 Test1a had weird plateau in gap for step 9
idx = find(strcmp(sfrFiles,"2023-08-02_13-12-39_PID_squeeze_flow_1_Test1a-CarbopolB_2mL_5g-data.csv"));
if ~isempty(idx)
    sfrStructs(idx).StepEndIndices = sfrStructs(idx).StepEndIndices([1:5,7,10],:);
end

%%% Get list of unique dates
date_strs = strings(length(sfrFiles),1);
for i = 1:length(sfrFiles)
    % date_strs(i) = extractAfter(extractBefore(extractBefore(sfrFiles(i),"PID"),"_"),"-");
    date_strs(i) = sfrStructs(i).dateStr;
end
date_strs = unique(date_strs);

%%% Get list of unique samples
sample_strs = strings(length(sfrFiles),1);
for i = 1:length(sfrFiles)
    sample_strs(i) = sfrStructs(i).sampleSubstance;
end
sample_strs = unique(sample_strs);

%% Plot Data
colors = ["#0072BD","#D95319","#EDB120","#7E2F8E","#77AC30","#4DBEEE","#A2142F"];
markers = ['o','s','d','^','p','h','<','>'];

colorList = parula();

minVol = sfrStructs(1).V(1);
maxVol = sfrStructs(1).V(1);
for i = 2:length(sfrStructs)
    minVol = min(minVol, sfrStructs(i).V(1));
    maxVol = max(maxVol, sfrStructs(i).V(1));
end

if false
figure(1)
for i = 1:length(sfrFiles)
    DisplayName = split(sfrFiles(i),"PID_squeeze_flow_1_");
    DisplayName = replace(DisplayName(2), "-data.csv","");
    loglog(sfrStructs(i).h, sfrStructs(i).F,'DisplayName',DisplayName);
    hold on
end
hold off
xlabel('Gap [m]')
ylabel('Force [N]')
legend('Location','southwest')
end

if false
figure(2)
for i = 1:length(sfrFiles)
    DisplayName = split(sfrFiles(i),"PID_squeeze_flow_1_");
    DisplayName = replace(DisplayName(2), "-data.csv","");
    loglog(pi * sfrStructs(i).R.^2, sfrStructs(i).F,'DisplayName',DisplayName);
    hold on
end
hold off
xlabel('Cylinder Cross-Section [m^2]')
ylabel('Force [N]')
legend('Location','southwest')
end

% plot sfr data
if false
figure(3)
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_");
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = testNum + " " + volStr + "mL";

    % colorIndex = max(ceil(length(colorList) * (sfrStructs(i).V(1) - minVol)/(maxVol - minVol)),1);
    % plotColor = colorList(colorIndex,:);
    % plotColor = colors(i);
    plotColor = colors(mod(i - 1, length(colors)) + 1);
    
    hLine = semilogx(sfrStructs(i).aspectRatio, sfrStructs(i).MeetenYieldStress,'+-',...
        'DisplayName',DisplayName,'Color',plotColor,'MarkerSize',0.00001);


    hold on
    plot(sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2)),...
        sfrStructs(i).MeetenYieldStress(sfrStructs(i).StepEndIndices(:,2)),'o',...
        'HandleVisibility','off','MarkerEdgeColor',plotColor,...
        'MarkerFaceColor',plotColor);
end

hold off
xlabel('h/R [-]')
ylabel('Yield Stress [Pa]')
title('Perfect Slip, Meeten (2000)')

% Add legend for the first/main plot handle
hLegend = legend('location','northeast');
% hLegend.NumColumns = 2;
drawnow(); % have to render the internal nodes before accessing them

%%% Do weird stuff to get the legend to have both the dots and the curves
%%% in one entry
%%% https://www.mathworks.com/matlabcentral/answers/509606-how-to-merge-two-legend-in-one#answer_811453
for i = 1:length(sfrFiles)
    % Extract legend nodes/primitives
    hLegendEntry = hLegend.EntryContainer.NodeChildren(end - i + 1); % top row of legend
    iconSet = hLegendEntry.Icon.Transform.Children.Children; % array of first/bottom row's icons (marker+line)
    
    % Create a new icon marker to add to the icon set
    newLegendIcon = copy(iconSet(1)); % copy the object (or look into making a matlab.graphics.primitive.world.Marker)
    newLegendIcon.Parent = iconSet(1).Parent;
    newLegendIcon.Style = 'circle';
    newLegendIcon.Size = 6;
    newLegendIcon.FaceColorData = newLegendIcon.EdgeColorData;
end
end


% plot data, changing symbol by day and color by test
if true
figure(4)
for i = 1:length(sfrFiles)
    s = sfrStructs(i);
    DisplayName = s.dateStr + " " + s.testNum + " " + s.volStr;

    plotColor = colors(mod(i - 1, length(colors)) + 1);
    fillColor = plotColor;
    % if i > 7 % make symbols hollow after some point
    %     fillColor = 'auto';
    % end

    markerIdx = find(strcmp(date_strs,s.dateStr));
    markerStr = markers(markerIdx);

    plot(s.aspectRatio(s.StepEndIndices(:,2)),...
        s.MeetenYieldStress(s.StepEndIndices(:,2)),markerStr,...
        'DisplayName',DisplayName,'MarkerEdgeColor',plotColor,...
        'MarkerFaceColor',fillColor);

    hold on
end
hold off
xlabel('h/R [-]')
ylabel('Yield Stress [Pa]')

% Add legend for the first/main plot handle
hLegend = legend('location','northeast');
hLegend.NumColumns = 2;
title("Perfect Slip, Meeten (2000)")
end

% plot data, changing symbol by day and color by sample
if true
figure(5)
for i = 1:length(sfrFiles)
    s = sfrStructs(i);
    % DisplayName = s.dateStr + " " + s.testNum + " " + s.volStr;
    sampleStr = upper(extractAfter(s.sampleSubstance,"carbopol"));
    DisplayName = s.dateStr + " " + s.testNum + " " + s.volStr + " " + sampleStr;


    colorIdx = find(strcmp(sample_strs,s.sampleSubstance));
    plotColor = colors(colorIdx);
    fillColor = plotColor;
    % if i > 7 % make symbols hollow after some point
    %     fillColor = 'auto';
    % end

    markerIdx = find(strcmp(date_strs,s.dateStr));
    markerStr = markers(markerIdx);

    plot(s.aspectRatio(s.StepEndIndices(:,2)),...
        s.MeetenYieldStress(s.StepEndIndices(:,2)),markerStr,...
        'DisplayName',DisplayName,'MarkerEdgeColor',plotColor,...
        'MarkerFaceColor',fillColor);

    hold on
end
hold off
xlabel('h/R [-]')
ylabel('Yield Stress [Pa]')

% Add legend for the first/main plot handle
hLegend = legend('location','northeast');
hLegend.NumColumns = 2;
title("Perfect Slip, Meeten (2000)")
end

% plot sfr data
if false
figure(5)
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_");
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = "SFR: " + testNum + " " + volStr + "mL";

    plotColor = colors(mod(i - 1, length(colors)) + 1);
    semilogx(sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2)),...
        sfrStructs(i).ScottYieldStress(sfrStructs(i).StepEndIndices(:,2)),'o',...
        'DisplayName',DisplayName,'MarkerEdgeColor',plotColor,...
        'MarkerFaceColor',plotColor);
    hold on
end
hold off
xlabel('h/R [-]')
ylabel('Yield Stress [Pa]')

% Add legend for the first/main plot handle
hLegend = legend('location','northwest');
hLegend.NumColumns = 2;
title("No-Slip, Scott (1935)")
end



%% Do linear fit of Meeten Stress vs. h/R

h_R = [];
yieldStress = [];

for i = 1:length(sfrFiles)
    h_R = [h_R; sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2))];
    yieldStress = [yieldStress; sfrStructs(i).MeetenYieldStress(sfrStructs(i).StepEndIndices(:,2))];
end

X = [ones(length(yieldStress),1), h_R];
y = yieldStress;

b = X \ y;

yieldStressIntercept = b(1);

figure(4)
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_Test");
    dateStr = extractAfter(extractBefore(testNum(1),"_"),"-"); % get just month and day
    testNum = split(testNum(2), "-");
    testNum = split(testNum(1), "_");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = dateStr + " " + testNum + " " + volStr + "mL";

    plotColor = colors(mod(i - 1, length(colors)) + 1);
    fillColor = plotColor;
    % if i > 7 % make symbols hollow after some point
    %     fillColor = 'auto';
    % end

    markerIdx = find(strcmp(date_strs,dateStr));
    markerStr = markers(markerIdx);

    plot(sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2)),...
        sfrStructs(i).MeetenYieldStress(sfrStructs(i).StepEndIndices(:,2)),markerStr,...
        'DisplayName',DisplayName,'MarkerEdgeColor',plotColor,...
        'MarkerFaceColor',fillColor);

    hold on
end
xlabel('h/R [-]')
ylabel('Yield Stress [Pa]')
xl = xlim;
yl = ylim;
xq = linspace(min(xl), max(xl));
trendlineStr = "y = " + num2str(b(2),'%.1f') + "x + " + num2str(b(1),'%.1f');
plot(xq, xq*b(2) + b(1), 'k-', 'DisplayName', trendlineStr)
hold off

% Add legend for the first/main plot handle
hLegend = legend('location','northeast');
hLegend.NumColumns = 2;
title("Perfect Slip, Meeten (2000)")

meanYieldStress = mean(yieldStress);
SST = sum((yieldStress - meanYieldStress).^2);
SSR = sum((yieldStress - (h_R*b(2) + b(1))).^2);
R_squared = 1 - SSR / SST

%% Look at variance of force signal versus gap

portion_of_step = 0.5; % look at the last __ fraction of the force signal in that step (don't look at the start because it needs a chance to try and equilibrate)

F_vars = [];
F_stds = [];
h_infinitys = [];
for i = 1:length(sfrFiles)
    for j = 1:size(sfrStructs(i).StepEndIndices,1)
        idxs = sfrStructs(i).StepEndIndices(j,:);
        var_indices = floor(idxs(2) - portion_of_step*(idxs(2) - idxs(1))):idxs(2);
        F_var = var(sfrStructs(i).F(var_indices));
        F_vars = [F_vars; F_var];
        F_stds = [F_stds; sqrt(F_var)];
        h_infinitys = [h_infinitys; sfrStructs(i).h(idxs(2))];
    end
end

y = log(F_stds);
X = [ones(length(h_infinitys),1), log(h_infinitys)];
q = X \ y;
c = exp(q(1))
n = q(2)

mean_F_std = mean(F_stds);
SST = sum((F_stds - mean_F_std).^2);
SSR = sum((F_stds - (c * h_infinitys.^n)).^2);
R_squared = 1 - SSR / SST

figure(8)
scatter(h_infinitys, F_stds,'o','filled')
set(gca, 'xscale', 'log', 'yscale', 'log')
hold on
xl = xlim;
xq = linspace(xl(1),xl(2));
yl = ylim;
% plot(xq, c./xq, 'k-');
plot(xq, c * xq.^n, 'k-');
hold off

xlabel('h [m]')
ylabel('Force Standard Deviation \sigma [N]')
title('Force Variation with Gap')


%% Plot normalized Yield stress

figure(8)
% plot sfr data
for i = 1:length(sfrFiles)
    s = sfrStructs(i);
    DisplayName = s.dateStr + " " + s.testNum + " " + s.volStr;

    plotColor = colors(mod(i - 1, length(colors)) + 1);
    fillColor = plotColor;

    markerIdx = find(strcmp(date_strs,s.dateStr));
    markerStr = markers(markerIdx);

    x = s.aspectRatio(s.StepEndIndices(:,2));
    y = s.MeetenYieldStress(s.StepEndIndices(:,2));
    y = y / max(y);

    semilogx(x,y,...
        markerStr,'DisplayName',DisplayName,'MarkerEdgeColor',plotColor,...
        'MarkerFaceColor',fillColor);

    hold on
end
hold off
xlabel('h/R [-]')
ylabel('Normalized Yield Stress \tau / \tau_{max} [-]')
ylim([0,1])

% Add legend for the first/main plot handle
% hLegend = legend('location','southwest','FontSize',6);
% hLegend.NumColumns = 2;
title("Yield Stress Falloff at Small Gap")

%% Investigate surface tension impact

sigma = 0.066; % From Boujlel & Coussot (2013)
theta = 1.8; % bows outward, which is what we observe in experiments

figure(8)
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_Test");
    dateStr = extractAfter(extractBefore(testNum(1),"_"),"-"); % get just month and day
    testNum = split(testNum(2), "-");
    testNum = split(testNum(1), "_");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = dateStr + " " + testNum + " " + volStr + "mL";
    plotColor = colors(mod(i - 1, length(colors)) + 1);
    fillColor = plotColor;

    % if i > 7 % make symbols hollow after some point
    %     fillColor = 'auto';
    % end

    markerIdx = find(strcmp(date_strs,dateStr));
    markerStr = markers(markerIdx);

    x = sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2));
    % y = sfrStructs(i).MeetenYieldStress(sfrStructs(i).StepEndIndices(:,2));
    y = (sfrStructs(i).F(sfrStructs(i).StepEndIndices(:,2)) .* sfrStructs(i).h(sfrStructs(i).StepEndIndices(:,2)) ./ sfrStructs(i).V(1)) / sqrt(3);
    % y = y / max(y);

    yyaxis left
    % semilogx(x,y,...
    %     markerStr,'DisplayName',DisplayName,'MarkerEdgeColor',plotColor,...
    %     'MarkerFaceColor',fillColor);
    semilogx(x,y,...
        markerStr,'DisplayName',DisplayName,'MarkerEdgeColor',colors(1),...
        'MarkerFaceColor',colors(1));
    % semilogx(x,y,...
        % markerStr);
    yyaxis right
    y = sfrStructs(i).V(1) ./ sfrStructs(i).h(sfrStructs(i).StepEndIndices(:,2));
    F_sigma = sigma * (-2*cos(theta)*y./ sfrStructs(i).h(sfrStructs(i).StepEndIndices(:,2)) + sqrt(pi * y));
    F_yield_stress = sfrStructs(i).F(sfrStructs(i).StepEndIndices(:,2)) - F_sigma;
    y = (F_yield_stress .* sfrStructs(i).h(sfrStructs(i).StepEndIndices(:,2)) ./ sfrStructs(i).V(1)) / sqrt(3);
    % y = y / max(y);
    % semilogx(x,y,...
    %     markerStr);
    semilogx(x,y,...
        markerStr,'DisplayName',DisplayName,'MarkerEdgeColor',colors(2),...
        'MarkerFaceColor',colors(2));

    hold on
end
hold off
xlabel('h/R [-]')
yyaxis left
ylabel('Yield Stress, Meeten (2000) [Pa]')
ylim([0,250])
yyaxis right
ylabel('Yield Stress with Surface Tension Correction [Pa]')
ylim([0,250])

% Add legend for the first/main plot handle
% hLegend = legend('location','northeast');
% hLegend.NumColumns = 2;
title("Comparison of Surface Tension Importance")

%% Save out figures for each test

saveFig = figure(6);

mkdir(sfrDataFolder + "Figures\");
for i = 1:length(sfrStructs)
    sfrDateStr = extractBefore(sfrFiles(i),"_");
    mkdir(sfrDataFolder + "Figures\" + sfrDateStr + "\");

    clf
    yyaxis left
    plot(sfrStructs(i).t,sfrStructs(i).F)
    ylabel('Force (N)')

    yl = ylim;
    ylim([0, max(yl)]);

    hold on
    yyaxis right
    plot(sfrStructs(i).t,1000*sfrStructs(i).h)
    ylabel('Gap (mm)')

    yl = ylim;
    ylim([0, max(yl)]);

    hold off
    xlabel('Time (s)')
    xlim([min(sfrStructs(i).t), max(sfrStructs(i).t)])
    
    figTitle = replace(replace("Test" + extractAfter(sfrFiles(i),"Test"),"_"," "),"-data.csv","");
    figTitle = "SFR: " + sfrDateStr + " " + figTitle(1);
    title(figTitle)
    
    % figFileName = extractBefore(sfrDataFolder + "Figures\" + sfrDateStr + "\" + sfrFiles(i),".") + ".png";
    figFileName = extractBefore(sfrDataFolder + "Figures\" + "\" + sfrFiles(i),".") + ".png";
    saveas(saveFig,figFileName)
end