%% Load Data

sfrDataFolder = "C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\";

sfrFiles = ["2023-07-13_11-38-52_PID_squeeze_flow_1_Test1a-Carbopol_1mL_5g-data.csv";
    "2023-07-13_12-34-44_PID_squeeze_flow_1_Test2a-Carbopol_1mL_5g-data.csv";
    "2023-07-13_12-56-20_PID_squeeze_flow_1_Test3a-Carbopol_1mL_30g-data.csv";
    "2023-07-13_14-33-28_PID_squeeze_flow_1_Test4a-Carbopol_5mL_10g-data.csv";
    "2023-07-18_10-21-01_PID_squeeze_flow_1_Test1a-Carbopol_1mL_5g-data.csv"];

s = sfrEmptyStructGenerator();
sfrStructs = repmat(s,length(sfrFiles),1);
for i = 1:length(sfrFiles)
    filePath = sfrDataFolder + sfrFiles(i);
    sfrStructs(i) = sfrStructGenerator(filePath);
end

%% Plot Data
colors = ["#0072BD","#D95319","#EDB120","#7E2F8E","#77AC30","#4DBEEE","#A2142F",...
    "#0072BD","#D95319","#EDB120","#7E2F8E","#77AC30","#4DBEEE","#A2142F"];

colorList = parula()

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
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_");
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = testNum + " " + volStr + "mL";

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



figure(3)
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_");
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = "SFR: " + testNum + " " + volStr + "mL";
    
    plotColor = colors(i);
    semilogx(sfrStructs(i).aspectRatio(sfrStructs(i).StepEndIndices(:,2)),...
        sfrStructs(i).MeetenYieldStress(sfrStructs(i).StepEndIndices(:,2)),'o',...
        'DisplayName',DisplayName,'MarkerEdgeColor',plotColor,...
        'MarkerFaceColor',plotColor);
    hold on
end
hold off
xlabel('h/R [-]')
ylabel('Yield Stress [Pa]')

% Add legend for the first/main plot handle
hLegend = legend('location','southwest');
hLegend.NumColumns = 2;
title("Perfect Slip, Meeten (2000)")


figure(4)
% plot sfr data
for i = 1:length(sfrFiles)
    testNum = split(sfrFiles(i),"PID_squeeze_flow_1_");
    testNum = split(testNum(2), "-");
    testNum = testNum(1);
    volStr = num2str(sfrStructs(i).V(1)*10^6,3);
    DisplayName = "SFR: " + testNum + " " + volStr + "mL";

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

%% Save out figures for each test

saveFig = figure(5);

mkdir(sfrDataFolder + "Figures\");
for i = 1:length(sfrStructs)
    sfrDateStr = extractBefore(sfrFiles(i),"_");
    mkdir(sfrDataFolder + "Figures\" + sfrDateStr + "\");

    clf
    yyaxis left
    plot(sfrStructs(i).t,sfrStructs(i).F)
    ylabel('Force (N)')
    hold on
    yyaxis right
    plot(sfrStructs(i).t,1000*sfrStructs(i).h)
    ylabel('Gap (mm)')
    hold off
    xlabel('Time (s)')
    xlim([min(sfrStructs(i).t), max(sfrStructs(i).t)])
    
    figTitle = replace(replace("Test" + extractAfter(sfrFiles(i),"Test"),"_"," "),"-data.csv","");
    figTitle = "SFR: " + sfrDateStr + " " + figTitle(1);
    title(figTitle)
    
    figFileName = extractBefore(sfrDataFolder + "Figures\" + sfrDateStr + "\" + sfrFiles(i),".") + ".png";
    saveas(saveFig,figFileName)
end