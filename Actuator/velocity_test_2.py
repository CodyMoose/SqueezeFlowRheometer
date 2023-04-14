import threading
import pytic

# import time
from time import sleep, time
import math
from datetime import datetime

# - Initialization -------------------------------------------


date = datetime.now()
date_str = date.strftime("%Y-%m-%d_%H-%M-%S")
"""timestamp string for experiment start time in yyyy-mm-dd_HH:MM:SS format"""
csv_name = date_str + "_" + "velocity_test_1" + "-data.csv"
# csv_name =  "actuator_test_1" + '-data.csv'
# csv_name = 'test_file.csv'
# print(csv_name)
"""csv file name - includes timestamp (yyyy-mm-dd_HH:MM:SS), material, dish, dutycycle, on/off time, and omega_shear in that order"""

if __name__ == "__main__":
    tic = pytic.PyTic()

    # Connect to first available Tic Device serial number over USB
    serial_nums = tic.list_connected_device_serial_numbers()

    # print(serial_nums)
    tic.connect_to_serial_number(serial_nums[0])

    tic.set_max_decel(500000)
    tic.set_max_accel(500000)

    with open("data/" + csv_name, "a") as datafile:
        # with open('data/test_file.csv','a') as datafile:
        datafile.write(
            "Current Time, Elapsed Time, Current Position, Target Position, Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV)\n"
        )


def move_to_pos(pos):
    print("current planning mode: {:d}".format(tic.variables.planning_mode))
    tic.set_target_position(pos)
    print("current planning mode: {:d}".format(tic.variables.planning_mode))
    while tic.variables.current_position != tic.variables.target_position:
        sleep(0.1)
        tic.reset_command_timeout()


def set_vel_to_pos(vel, pos):
    print("current planning mode: {:d}".format(tic.variables.planning_mode))
    s = math.copysign(1, vel)
    if s * (tic.variables.current_position - pos) < 0:
        tic.set_target_velocity(vel)
        print("current planning mode: {:d}".format(tic.variables.planning_mode))
        print("target velocity: {:d}".format(tic.variables.target_velocity))
        sleep(0.1)
        tic.reset_command_timeout()
        while s * (tic.variables.current_position - pos) < 0:
            sleep(0.1)
            tic.reset_command_timeout()
            print(
                "tv: {:d}, cv: {:d}, cp: {:d}, tp: {:d}".format(
                    tic.variables.target_velocity,
                    tic.variables.current_velocity,
                    tic.variables.current_position,
                    tic.variables.target_position,
                )
            )
        print(
            "reached target {:d}, current pos is {:d}".format(
                pos, tic.variables.current_position
            )
        )
    else:
        print("Velocity is wrong sign, not doing anything with it")
    tic.set_target_velocity(0)


def go_home_quiet_down():
    """Returns actuator to zero position, enters safe start, de-energizes, and reports any errors"""
    print("Going to zero")
    move_to_pos(0)

    # De-energize motor and get error status
    print("entering safe start")
    tic.enter_safe_start()
    print("deenergizing")
    tic.deenergize()
    print(tic.variables.error_status)


def foreground():
    """drives actuator"""
    # global tic

    # Load configuration file and apply settings
    # tic.settings.load_config('actuator_test_1_config.yml')
    # tic.settings.apply()

    # - Motion Command Sequence ----------------------------------

    # Zero current motor position
    tic.halt_and_set_position(0)

    # Energize Motor
    print("energizing")
    tic.energize()
    print("exiting safe start")
    tic.exit_safe_start()

    print("current planning mode: {:d}".format(tic.variables.planning_mode))

    # print("Going to center of stroke")
    # center = -2000
    # move_to_pos(center)
    # print("current planning mode: {:d}".format(tic.variables.planning_mode))

    # set_vel_to_pos(200,-1000)
    # print("current planning mode: {:d}".format(tic.variables.planning_mode))

    set_vel_to_pos(-200, -2000)
    print("current planning mode: {:d}".format(tic.variables.planning_mode))

    # set_vel_to_pos(-200,-1000) # should fail if actually at -2000
    # print("current planning mode: {:d}".format(tic.variables.planning_mode))

    set_vel_to_pos(200, -1000)
    print("current planning mode: {:d}".format(tic.variables.planning_mode))

    go_home_quiet_down()

    print("=" * 20 + " FOREGROUND IS DONE " + "=" * 20)


def background():
    """records data to csv"""
    global tic

    start_time = time()
    while True:
        # print(tic)
        # print(tic.variables)
        cur_pos = tic.variables.current_position
        tar_pos = tic.variables.target_position
        cur_vel = tic.variables.current_velocity
        tar_vel = tic.variables.target_velocity
        max_speed = tic.variables.max_speed
        max_decel = tic.variables.max_decel
        max_accel = tic.variables.max_accel
        step_mode = tic.variables.step_mode
        vin_voltage = tic.variables.vin_voltage

        # print("PSU Voltage:{:6.3f}V	Shunt Voltage:{:9.6f}V	Load Voltage:{:6.3f}V	Power:{:9.6f}W	Current:{:9.6f}A".format((bus_voltage2 + shunt_voltage2),(shunt_voltage2),(bus_voltage2),(power2),(current2)/1000))
        # print("")

        with open(
            "data/" + csv_name, "a"
        ) as datafile:  # write time & current details to csv
            # with open('data/test_file.csv','a') as datafile:
            cur_time = time()
            cur_duration = cur_time - start_time
            dataline = (
                str(cur_time)
                + ","
                + str(cur_duration)
                + ","
                + str(cur_pos)
                + ","
                + str(tar_pos)
                + ","
                + str(cur_vel)
                + ","
                + str(tar_vel)
                + ","
                + str(max_speed)
                + ","
                + str(max_decel)
                + ","
                + str(max_accel)
                + ","
                + str(step_mode)
                + ","
                + str(vin_voltage)
                + "\n"
            )
            datafile.write(dataline)
            # print(dataline)

        sleep(0.1)

        if (time() - start_time) >= 60 or (
            (not f.is_alive()) and (time() - start_time) > 1
        ):
            print("end of print")
            break

    print("=" * 20 + " BACKGROUND IS DONE " + "=" * 20)


b = threading.Thread(name="background", target=background)
f = threading.Thread(name="foreground", target=foreground)

b.start()
f.start()

# try:
# 	name  = input('Hit any key to interrupt...\n')
# except KeyboardInterrupt:
# 	print("going back to zero")
# 	move_to_pos(0)

# 	# De-energize motor and get error status
# 	print("entering safe start")
# 	tic.enter_safe_start()
# 	print("deenergizing")
# 	tic.deenergize()
# 	print(tic.variables.error_status)
