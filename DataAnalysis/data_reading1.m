% dir_path = "C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data"
% opts = detectImportOptions("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-25_16-56-01_PID_squeeze_flow_1_PEG_4mL_10g-data.csv");
% preview("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-25_16-56-01_PID_squeeze_flow_1_PEG_4mL_10g-data.csv",opts)
% table = readmatrix("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-25_16-56-01_PID_squeeze_flow_1_PEG_4mL_10g-data.csv");
% sqTable = readtable("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-25_16-56-01_PID_squeeze_flow_1_PEG_4mL_10g-data.csv");

sqTable1 = readtable("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-28_14-55-14_PID_squeeze_flow_1_PEG_4mL_10g-data.csv");
sqTable2 = readtable("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-28_15-13-49_PID_squeeze_flow_1_PEG_4mL_10g-data.csv");
sqTable3 = readtable("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-28_15-29-58_PID_squeeze_flow_1_PEG_4mL_10g-data.csv");
sqTable4 = readtable("C:\Users\rcmoo\Documents\GitHub\SqueezeFlowRheometer\data\2023-04-28_15-50-23_PID_squeeze_flow_1_PEG_4mL_10g-data.csv");

% sqTable.Properties.VariableNames'
%%
clf

F_factor = 0.00980665; % N/gram force

test_active1 = strcmp(sqTable1.TestActive_,'True');
vel1 = sqTable1.CurrentVelocity_mm_s_(test_active1) / 1000;
gap1 = sqTable1.CurrentGap_m_(test_active1);
F1 = sqTable1.CurrentForce_g_(test_active1) * F_factor;
t1 = sqTable1.ElapsedTime(test_active1);
t1 = t1 - t1(1);

test_active2 = strcmp(sqTable2.TestActive_,'True');
vel2 = sqTable2.CurrentVelocity_mm_s_(test_active2) / 1000;
gap2 = sqTable2.CurrentGap_m_(test_active2);
F2 = sqTable2.CurrentForce_g_(test_active2) * F_factor;
t2 = sqTable2.ElapsedTime(test_active2);
t2 = t2 - t2(1);

test_active3 = strcmp(sqTable3.TestActive_,'True');
vel3 = sqTable3.CurrentVelocity_mm_s_(test_active3) / 1000;
gap3 = sqTable3.CurrentGap_m_(test_active3);
F3 = sqTable3.CurrentForce_g_(test_active3) * F_factor;
t3 = sqTable3.ElapsedTime(test_active3);
t3 = t3 - t3(1);

test_active4 = strcmp(sqTable4.TestActive_,'True');
vel4 = sqTable4.CurrentVelocity_mm_s_(test_active4) / 1000;
gap4 = sqTable4.CurrentGap_m_(test_active4);
F4 = sqTable4.CurrentForce_g_(test_active4) * F_factor;
t4 = sqTable4.ElapsedTime(test_active4);
t4 = t4 - t4(1);

% figure(1)
% plot(t,vel)
% 
% figure(2)
% plot(t,gap)
% 
% figure(3)
% plot(t,F)


N = 301;
hammer_area = pi * 0.025^2;

vel_mean1 = movmean(vel1,N);
gap_mean1 = movmean(gap1,N);
F_mean1 = movmean(F1,N);
visc_volume1 = min(hammer_area * gap_mean1, sqTable1.SampleVolume_m_3_(test_active1));
eta_guess1 = abs((2 * pi * gap_mean1.^5 .* F_mean1) ./ (3 * visc_volume1.^2 .* vel_mean1));

vel_mean2 = movmean(vel2,N);
gap_mean2 = movmean(gap2,N);
F_mean2 = movmean(F2,N);
visc_volume2 = min(hammer_area * gap_mean2, sqTable2.SampleVolume_m_3_(test_active2));
eta_guess2 = abs((2 * pi * gap_mean2.^5 .* F_mean2) ./ (3 * visc_volume2.^2 .* vel_mean2));

vel_mean3 = movmean(vel3,N);
gap_mean3 = movmean(gap3,N);
F_mean3 = movmean(F3,N);
visc_volume3 = min(hammer_area * gap_mean3, sqTable3.SampleVolume_m_3_(test_active3));
eta_guess3 = abs((2 * pi * gap_mean3.^5 .* F_mean3) ./ (3 * visc_volume3.^2 .* vel_mean3));

vel_mean4 = movmean(vel4,N);
gap_mean4 = movmean(gap4,N);
F_mean4 = movmean(F4,N);
visc_volume4 = min(hammer_area * gap_mean4, sqTable4.SampleVolume_m_3_(test_active4));
eta_guess4 = abs((2 * pi * gap_mean4.^5 .* F_mean4) ./ (3 * visc_volume4.^2 .* vel_mean4));

% figure(1)
% plot(t,vel)
% hold on
% plot(t,vel_mean)
% hold off

figure(2)
plot(t1,eta_guess1)
hold on
plot(t2,eta_guess2)
plot(t3,eta_guess3)
plot(t4,eta_guess4)
hold off
xlabel('time')
ylabel('viscosity')


figure(3)
plot(gap_mean1,eta_guess1,'.')
hold on
plot(gap_mean2,eta_guess2,'.')
plot(gap_mean3,eta_guess3,'.')
plot(gap_mean4,eta_guess4,'.')
hold off
xlabel('gap')
ylabel('viscosity')