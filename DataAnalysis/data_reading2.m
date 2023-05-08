% Prompt the user to select files
[filenames, filepath, filterindex] = uigetfile({'*.xlsx;*.csv', 'Excel or CSV files (*.xlsx, *.csv)'; '*.xlsx', 'Excel files (*.xlsx)'; '*.csv', 'CSV files (*.csv)'}, 'Select a file','MultiSelect','on');

% Determine the file type based on the extension
for i = 1:length(filenames)
    if(iscell(filenames))
        filename = filenames{i};
    else
        filename = filenames;
    end
	[~, ~, file_ext] = fileparts(filename);
	if strcmpi(file_ext, '.xlsx')
        % Read the data from an Excel file
        data{i} = readtable(fullfile(filepath, filename));
	elseif strcmpi(file_ext, '.csv')
        % Read the data from a CSV file
        data{i} = readtable(fullfile(filepath, filename), 'Delimiter', ',');
	else
        % Throw an error if the file type is not recognized
        error('File type not supported.');
    end
	if(~iscell(filenames))
        break; % only keep iterating if there's multiple files to read.
	end
end

data{1}.Properties.VariableNames

%%

figure(1)
tiledlayout(2,2)

nexttile
xV = 'ElapsedTime';
yV = 'CurrentGap_m_';
xF = @(arr) arr;
yF = @(arr) arr;
plotTables(data,xV,yV,xF,yF)

nexttile
xV = 'ElapsedTime';
yV = 'CurrentForce_g_';
xF = @(arr) arr;
yF = @(arr) arr;
plotTables(data,xV,yV,xF,yF)

nexttile
xV = 'ElapsedTime';
yV = 'Viscosity_Pa_s_';
xF = @(arr) arr;
yF = @(arr) arr;
plotTables(data,xV,yV,xF,yF)

nexttile
xV = 'ElapsedTime';
yV = 'ViscosityVolume_m_3_';
xF = @(arr) arr;
yF = @(arr) arr;
plotTables(data,xV,yV,xF,yF)

function plotTables(dat,xV,yV,xF,yF)
    for i = 1:length(dat)
        active_idx = and(reshape(strcmp(dat{i}.TestActive_,'True'),[],1), reshape(logical((1:length(dat{i}.TestActive_)) > 2800)',[],1));
%         active_idx = strcmp(dat{i}.TestActive_,'True');

        p = myplotfun(dat{i},xV,yV,xF,yF,active_idx);
        p.DisplayName = "File " + i;
        hold on
    end
    xlabel(xV);
    ylabel(yV);
    hold off
    if(length(dat) > 1)
        legend()
    end
end

function p = myplotfun(tab,xVar,yVar,xFun,yFun,active_idx)
    x = xFun(tab.(xVar)(active_idx));
    y = yFun(tab.(yVar)(active_idx));
    p = plot(x,y);
end