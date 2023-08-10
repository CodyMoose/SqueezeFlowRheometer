xd = linspace(-10,0,10000);

f = @(x) 5./(1 + x.^2);

yd = f(xd) + (2*rand(size(xd)) - 1);

w = 0.5;
window = @(x) w^-4 * (x - w).^2 .* (x + w).^2;
% window = @(x) x - x + 1;

N = 100;
xq = linspace(-10,0,N);
yq = zeros(1,N);
for i = 1:N
    x = xq(i);
    nearby = xd(abs(xd - x) <= w);
    weights = window(nearby - x);
    weights = weights ./ sum(weights);
    yq(i) = sum(weights .* yd(abs(xd - x) <= w));
end

figure(1)
plot(xd, f(xd),'k-','DisplayName','Actual')
hold on
plot(xd,yd,'b:','DisplayName','Noisy Signal')
plot(xq,yq,'g.','DisplayName','Smoothed')
hold off
legend
ylim([-1,6])

%% Load rigidity data file

% filePath = "C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-08-07_10-28-04_rigidity_test-data.csv";
filePath = "C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-08-07_11-50-25_rigidity_test-data.csv";
% filePath = "C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-08-07_15-48-06_rigidity_test-data.csv";

rigidity_data = sfrStructGenerator(filePath)
%%
threshold = 0.002;
idxs = rigidity_data.F > threshold;
% plot(rigidity_data.h,rigidity_data.F)
% hold on
% plot(rigidity_data.h(idxs),rigidity_data.F(idxs))
% hold off

rigidity_h = rigidity_data.h(idxs);
rigidity_F = rigidity_data.F(idxs);


N = 100;
xq = linspace(min(rigidity_h),max(rigidity_h),N);

% w = 1e-5;
w = xq(2) - xq(1)
window = @(x) w^-4 * (x - w).^2 .* (x + w).^2;

yq = zeros(1,N);
for i = 1:N
    x = xq(i);
    nearby = rigidity_h(abs(rigidity_h - x) <= w);
    weights = window(nearby - x);
    weights = weights ./ sum(weights);
    yq(i) = sum(weights .* rigidity_F(abs(rigidity_h - x) <= w));

    % nearby = rigidity_data.h(abs(rigidity_data.h - x) <= w);
    % weights = window(nearby - x);
    % weights = weights ./ sum(weights);
    % yq(i) = sum(weights .* rigidity_data.F(abs(rigidity_data.h - x) <= w));
end

figure(1)
plot(rigidity_h,rigidity_F,'r-','DisplayName','Noisy Signal')
hold on
plot(xq,yq,'b.','DisplayName','Smoothed')
hold off
legend