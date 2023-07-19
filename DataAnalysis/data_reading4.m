%% Load Data

sfrDataFolder = "C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\";

sfrFiles = ["2023-07-13_11-38-52_PID_squeeze_flow_1_Test1a-Carbopol_1mL_5g-data.csv";
    "2023-07-13_12-34-44_PID_squeeze_flow_1_Test2a-Carbopol_1mL_5g-data.csv";
    "2023-07-13_12-56-20_PID_squeeze_flow_1_Test3a-Carbopol_1mL_30g-data.csv";
    "2023-07-13_14-33-28_PID_squeeze_flow_1_Test4a-Carbopol_5mL_10g-data.csv";
    "2023-07-18_10-21-01_PID_squeeze_flow_1_Test1a-Carbopol_1mL_5g-data.csv";
    "2023-07-18_13-36-55_PID_squeeze_flow_1_Test3a-Carbopol_1mL_5g-data.csv";
    "2023-07-18_14-28-17_PID_squeeze_flow_1_Test4a-Carpobol_2mL_5g-data.csv";
    "2023-07-18_15-18-45_PID_squeeze_flow_1_Test5a-Carbopol_4mL_5g-data.csv"];

s = sfrEmptyStructGenerator();
sfrStructs = repmat(s,length(sfrFiles),1);
for i = 1:length(sfrFiles)
    filePath = sfrDataFolder + sfrFiles(i);
    sfrStructs(i) = sfrStructGenerator(filePath);
end

%% Plot Data
colors = ["#0072BD","#D95319","#EDB120","#7E2F8E","#77AC30","#4DBEEE","#A2142F",...
    "#0072BD","#D95319","#EDB120","#7E2F8E","#77AC30","#4DBEEE","#A2142F"];

colorList = parula();
minVol = sfrStructs(1).V(1);
maxVol = sfrStructs(1).V(1);
for i = 2:length(sfrStructs)
    minVol = min(minVol, sfrStructs(i).V(1));
    maxVol = max(maxVol, sfrStructs(i).V(1));
end

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

figure(3)
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_");
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = testNum + " " + volStr + "mL";

    % colorIndex = max(ceil(length(colorList) * (sfrStructs(i).V(1) - minVol)/(maxVol - minVol)),1);
    % plotColor = colorList(colorIndex,:);
    plotColor = colors(i);
    
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



figure(4)
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_Test");
    dateStr = extractAfter(extractBefore(testNum(1),"_"),"-"); % get just month and day
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = dateStr + " " + testNum + " " + volStr + "mL";
    
    % colorIndex = max(ceil(length(colorList) * (sfrStructs(i).V(1) - minVol)/(maxVol - minVol)),1);
    % plotColor = colorList(colorIndex,:);
    plotColor = colors(i);
    fillColor = plotColor;
    if i > 4
        fillColor = 'auto';
    end

    plot(sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2)),...
        sfrStructs(i).MeetenYieldStress(sfrStructs(i).StepEndIndices(:,2)),'o',...
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


figure(5)
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_");
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = "SFR: " + testNum + " " + volStr + "mL";

    % colorIndex = max(ceil(length(colorList) * (sfrStructs(i).V(1) - minVol)/(maxVol - minVol)),1);
    % plotColor = colorList(colorIndex,:);
    plotColor = colors(i);
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
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = dateStr + " " + testNum + " " + volStr + "mL";
    
    % colorIndex = max(ceil(length(colorList) * (sfrStructs(i).V(1) - minVol)/(maxVol - minVol)),1);
    % plotColor = colorList(colorIndex,:);
    plotColor = colors(i);
    fillColor = plotColor;
    if i > 4
        fillColor = 'auto';
    end

    semilogx(sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2)),...
        sfrStructs(i).MeetenYieldStress(sfrStructs(i).StepEndIndices(:,2)),'o',...
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
hLegend = legend('location','southwest');
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
    for j = 1:length(sfrStructs(i).F_tars)
        idxs = sfrStructs(i).StepEndIndices(j,:);
        var_indices = floor(idxs(2) - portion_of_step*(idxs(2) - idxs(1))):idxs(2);
        F_var = var(sfrStructs(i).F(var_indices));
        F_vars = [F_vars; F_var];
        F_stds = [F_stds; sqrt(F_var)];
        h_infinitys = [h_infinitys; sfrStructs(i).h(idxs(2))];
    end
end


y = F_stds;
X = 1./h_infinitys;
c = X \ y

mean_F_std = mean(F_stds);
SST = sum((F_stds - mean_F_std).^2);
SSR = sum((F_stds - (c./h_infinitys)).^2);
R_squared = 1 - SSR / SST

figure(8)
% loglog(h_infinitys, F_vars,'o')
% xlabel('h [m]')
% ylabel('Force Variance [N^2]')
scatter(h_infinitys, F_stds,'o','filled')
set(gca, 'xscale', 'log', 'yscale', 'log')
hold on
xl = xlim;
xq = linspace(xl(1),xl(2));
yl = ylim;
plot(xq, c./xq, 'k-');
hold off

xlabel('h [m]')
ylabel('Force Standard Deviation \sigma [N]')
title('Force Variation with Gap')


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