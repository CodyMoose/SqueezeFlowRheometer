function [] = sfrPrettyPlot(latex)
    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
    % Plot parameters
    % MATLAB treats mac and PC displays differently which can create
    % weird looking graphs. Here we handle system differences
    if(nargin<1 || isempty(latex))
        latex = false;
    end

    if ismac
        plot_width_in_px = 800;
        plot_height_in_px = 600;
        marker_size=15;
        marker_line_width=2.5;
        box_thickness = 1.5;
        axis_tick_font_size = 24;
        axis_label_font_size = 24;
        legend_font_size = 20;
        error_bar_cap_size = 15;
    else % (ispc || isunix)
        plot_width_in_px = 600;
        plot_height_in_px = 450;
%         marker_size=10;
        marker_size=6;
        marker_line_width=2.0;
        box_thickness = 1;
        axis_tick_font_size = 12;
        axis_label_font_size = 14;
        legend_font_size = 10;
        error_bar_cap_size = 10;
    end
    
    marker_outline = 'matching'; % could be 'black' or 'matching'

    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

    % Use h as handle for current figure
    hFig = gcf;                    
    % Change figure background colour to white
    set(hFig, 'Color', 'white');

    % Make the figure bigger
    % set(hFig, 'rend', 'painters', 'Units', 'pixels', 'pos', ...
    %     [100 100 plot_width_in_px plot_height_in_px]);

    % Grab the axes handle(s)
    axis_handles=findobj(hFig,'type','axe');

    % Iterate over all axes handle(s), this is useful if there are subplots
    for i = 1:length(axis_handles)
        ax = axis_handles(i);

        % Change default font size (tick labels, legend, etc.)
        set(ax, 'FontSize', axis_tick_font_size, 'FontName', 'Arial', 'LineWidth', box_thickness);
        
        set(ax, 'Box', 'on');

        % Change font size for axis text labels
        set(get(ax, 'XLabel'),'FontSize', axis_label_font_size, 'FontWeight', 'Bold');
        set(get(ax, 'YLabel'),'FontSize', axis_label_font_size, 'FontWeight', 'Bold');
        if(latex)
            set(get(ax, 'XLabel'), 'Interpreter', 'latex');
            set(get(ax, 'YLabel'), 'Interpreter', 'latex');
            set(get(ax, 'Title'), 'Interpreter', 'latex');
            set(ax, 'TickLabelInterpreter', 'latex');
            set(get(ax, 'Legend'), 'Interpreter', 'latex');
%             ax.XLabel.Interpreter = 'latex';
%             ax.YLabel.Interpreter = 'latex';
%             ax.Title.Interpreter = 'latex';
%             ax.TickLabelInterpreter = 'latex';
%             % ax.Legend.Interpreter = 'latex';
%             % ax.XLabel.FontSize = 14;
%             % ax.YLabel.FontSize = 14;
%             % ax.Legend.FontSize = 12;
%             for i = 1:length(ax.Children)
%                 ax.Children(i).LineWidth = 1;
%             end
        end
        
        try % try statement to avoid error with categorical axes
%         ax.XRuler.Exponent = 0; % Remove exponential notation from the X axis
        ax.YRuler.Exponent = 0; % Remove exponential notation from the Y axis
        catch
        end
        
    end

    % Also adjust tiled layout format if that's used
    t = get(gcf,'children');
    if isa(t, 'matlab.graphics.layout.TiledChartLayout')
        % set(t, 'FontSize', axis_tick_font_size, 'FontName', 'Arial', 'LineWidth', box_thickness);
        set(get(t, 'XLabel'),'FontSize', axis_label_font_size, 'FontWeight', 'Bold');
        set(get(t, 'YLabel'),'FontSize', axis_label_font_size, 'FontWeight', 'Bold');
        set(get(t, 'Title'),'FontSize', axis_label_font_size + 2, 'FontWeight', 'Bold');
        if(latex)
            set(get(t, 'XLabel'), 'Interpreter', 'latex');
            set(get(t, 'YLabel'), 'Interpreter', 'latex');
            set(get(t, 'Title'), 'Interpreter', 'latex');
        end
    end
    
    % Find all the lines, and markers
    LineH = findobj(hFig, 'type', 'line', '-or', 'type', 'errorbar');

    if(~isempty(LineH) && false)
        for i=1:length(LineH) % Iterate over all lines in the plot
            % Decide what color for the marker edges
            this_line_color = get(LineH(i),'color');
            if strcmp(marker_outline, 'black')
                marker_outline_color = 'black';
            elseif strcmp(marker_outline, 'matching')
                marker_outline_color = this_line_color;
            else
                marker_outline_color = 'black';
            end

            % If the LineWidth has not been customized, then change it
            if (get(LineH(i), 'LineWidth') <= 1.0)
                set(LineH(i), 'LineWidth', marker_line_width)
            end
            % Change lines and markers if they exist on the plot
%             set(LineH(i),   'MarkerSize', marker_size, ...
%                 'MarkerEdgeColor', marker_outline_color, ...
%                 'MarkerFaceColor', this_line_color);
            set(LineH(i),   'MarkerSize', marker_size, ...
                'MarkerEdgeColor', marker_outline_color, ...
                'MarkerFaceColor', 'none');
        end
    end

    % Find and change the error bars
    LineH = findobj(hFig, 'type', 'errorbar');
    if(~isempty(LineH))
        for i=1:length(LineH) % Iterate over all lines in the plot
            LineH(i).CapSize=error_bar_cap_size;
%             LineH(i).Color = [0 0 0]; % Set all error bars to black

        end
    end

    % Find the legend, and if there is one, change it  
    h = get(hFig,'children');
    if isa(h, 'matlab.graphics.layout.TiledChartLayout')
        h = get(h,'Children');
    end

    for k = 1:length(h)
        if strcmpi(get(h(k),'Tag'),'legend')
            set(h(k), 'FontSize', legend_font_size, 'location', 'northeast');
        end
    end

end