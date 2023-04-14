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
csv_name = date_str + "_" + "accel_test_1" + "-data.csv"
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

    tic.set_current_limit(
        576
    )  # set limit to 576mA, right under the 600mA limit for the actuator
    tic.set_max_decel(500000)
    tic.set_max_accel(500000)
    tic.set_max_speed(10000000)  # 10mm/s

    # Zero current motor position
    tic.halt_and_set_position(0)

    with open("data/" + csv_name, "a") as datafile:
        # with open('data/test_file.csv','a') as datafile:
        datafile.write(
            "Current Time, Elapsed Time, Current Position, Target Position, Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV)\n"
        )


def move_to_pos(pos):
    tic.set_target_position(pos)
    while tic.variables.current_position != tic.variables.target_position:
        sleep(0.1)
        tic.reset_command_timeout()


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

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    # Energize Motor
    print("energizing")
    tic.energize()
    print("exiting safe start")
    tic.exit_safe_start()

    print("Going to center of stroke")
    center = -2000
    move_to_pos(center)

    print("Position oscillations")
    osc_mags = [250, 500, 750]  # steps
    osc_omegas = [1, 2, 3]  # rad/s
    osc_strengths = [
        1.5,
        1,
        0.75,
        0.5,
    ]  # set maximum acceleration to this times the necessary acceleration
    osc_length = 10  # seconds

    print(
        "This is gonna take a bit. At least {:d} minutes".format(
            math.ceil(
                osc_length
                * 2
                * len(osc_mags)
                * len(osc_omegas)
                * len(osc_strengths)
                / 60
            )
        )
    )

    osc_start = time()
    osc_time = time() - osc_start
    for A in osc_mags:
        for omega in osc_omegas:
            for strength in osc_strengths:
                print(
                    "Position oscillation for {:d} seconds: A = {:d}, omega = {:d}, strength = {:%}".format(
                        osc_length, A, omega, strength
                    )
                )
                tic.set_max_decel(500000)
                tic.set_max_accel(500000)
                move_to_pos(center + A)

                # Now restrict maximum acceleration
                a_max = (
                    A * omega**2 * 100
                )  # steps/s/100s, the units the controller uses for acceleration
                tic.set_max_decel(math.floor(a_max * strength))
                tic.set_max_accel(math.floor(a_max * strength))

                # Record the start time
                osc_start = time()
                osc_time = time() - osc_start
                while osc_time < osc_length:
                    osc_pos = A * math.cos(omega * osc_time) + center
                    tic.set_target_position(math.floor(osc_pos))
                    tic.reset_command_timeout()
                    osc_time = time() - osc_start

    print("Velocity oscillations")
    osc_mags = [2500000, 5000000, 7500000]  # steps/10,000s
    # osc_omegas = [1, 2, 3] # rad/s # just use rate, strengths, and length from above
    # osc_strengths = [1, 0.9, 0.8]
    # osc_length = 5
    osc_start = time()
    osc_time = time() - osc_start
    for A in osc_mags:
        for omega in osc_omegas:
            for strength in osc_strengths:
                print(
                    "Velocity oscillation for {:d} seconds: A = {:d}, omega = {:d}, strength = {:%}".format(
                        osc_length, A, omega, strength
                    )
                )
                start_pos = math.floor(center - A / 10000 / omega)
                tic.set_max_decel(500000)
                tic.set_max_accel(500000)
                move_to_pos(start_pos)
                osc_start = time()
                osc_time = time() - osc_start

                # Now restrict maximum acceleration
                a_max = (
                    A * omega / 100
                )  # steps/s/100s, the units the controller uses for acceleration
                print("Max Accel = {:d}".format(math.floor(a_max * strength)))
                tic.set_max_decel(math.floor(a_max * strength))
                tic.set_max_accel(math.floor(a_max * strength))
                while osc_time < osc_length:
                    osc_vel = A * math.sin(omega * osc_time)
                    tic.set_target_velocity(math.floor(osc_vel))
                    tic.reset_command_timeout()
                    osc_time = time() - osc_start

    go_home_quiet_down()
    # print("Going to zero")
    # move_to_pos(0)

    # # De-energize motor and get error status
    # print("entering safe start")
    # tic.enter_safe_start()
    # print("deenergizing")
    # tic.deenergize()
    # print(tic.variables.error_status)

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

        if (time() - start_time) >= 2000 or (
            (not f.is_alive()) and (time() - start_time) > 1
        ):
            print("end of print")
            break

    print("=" * 20 + " BACKGROUND IS DONE " + "=" * 20)


b = threading.Thread(name="background", target=background)
f = threading.Thread(name="foreground", target=foreground)

f.start()
b.start()

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
