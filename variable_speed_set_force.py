import serial
from time import time
import json
import threading
import pytic

# import time
from time import sleep, time
import math
from datetime import datetime
import re

# - Initialization -------------------------------------------

date = datetime.now()
date_str = date.strftime("%Y-%m-%d_%H-%M-%S")
"""timestamp string for experiment start time in yyyy-mm-dd_HH:MM:SS format"""
csv_name = date_str + "_" + "fixed_speed_set_force" + "-data.csv"

with open("LoadCell\config.json", "r") as read_file:
    config = json.load(read_file)
    tare = config["tare"]
    calibration = config["calibration"]
    units = config["units"]


def ser_to_reading(serial_line):
    """Takes in raw serial readline line and returns the raw reading reported in that line"""
    numString = serial_line.decode("utf-8")[
        :-3
    ]  # strips it down to just the actual content
    reading = int(numString)
    return reading


def reading_to_units(reading):
    """Takes in raw reading and returns calibrated measurement"""
    return (reading - tare) / calibration


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


def set_vel_mms(vel_mms):
    """Sets actuator target velocity to vel_mms - the desired velocity in mm/s as a floating point number,
    returns vel - an integer velocity in steps/10,000s"""
    # sm = tic.variables.step_mode
    vel = math.floor(vel_mms * 1000000 * 2**tic.variables.step_mode)
    tic.set_target_velocity(vel)
    return vel


def get_pos_mm():
    """Moves to pos_mm - the desired position in mm as a floating point,
    returns pos - an integer position in steps"""
    # sm = tic.variables.step_mode
    pos = tic.variables.current_position / 100.0 * 2**-tic.variables.step_mode
    return pos


force = 0
"""Current force reading. Positive is a force pushing up on the load cell"""
target = 0
"""Target force. Positive is a force pushing up on the load cell"""

if __name__ == "__main__":
    target_line = input("Enter the target force in [{:}]: ".format(units))
    temp = re.compile("[0-9.]+")
    res = temp.search(target_line).group(0)
    target = float(res)
    print("Target force is {:.2f}{:}".format(target, units))

    ser = serial.Serial("COM5", 115200)

    tic = pytic.PyTic()

    # Connect to first available Tic Device serial number over USB
    serial_nums = tic.list_connected_device_serial_numbers()

    # print(serial_nums)
    tic.connect_to_serial_number(serial_nums[0])

    tic.set_current_limit(
        576
    )  # set limit to 576mA, right under the 600mA limit for the actuator
    tic.set_max_decel(200000)
    tic.set_max_accel(200000)
    tic.set_max_speed(5000000)  # 10mm/s

    # Zero current motor position
    tic.halt_and_set_position(0)

    # with open('data/'+csv_name,'a') as datafile:
    # # with open('data/test_file.csv','a') as datafile:
    # 	datafile.write('Current Time, Elapsed Time, Current Position, Target Position, Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV)\n')


def load_cell_thread():
    """Handles load cell measurement"""
    global force

    for i in range(10):  # get rid of first few lines that aren't readings
        ser.readline()
    ser.reset_input_buffer()  # and get rid of any others that were generated when we were busy setting up

    while True:
        reading = int(ser.readline().decode("utf-8")[:-3])
        force = (reading - tare) / calibration


def actuator_thread():
    """Drives actuator"""

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    # Energize Motor
    print("energizing")
    tic.energize()
    print("exiting safe start")
    tic.exit_safe_start()

    backoff_velocity = 1  # mm/s

    upper_limit = -100
    lower_limit = -4000

    error = 0
    """Positive error means force must increase, so actuator must extend down"""
    old_error = 0
    """Error from previous frame, used for derivative & integral calculation"""
    int_error = 0
    """Integrated error - TODO: implement error accumulation and also limiting"""
    der_error = 0
    """Time derivative of error - TODO: implement finite difference scheme to approximate derivative. Maybe just 1st order backward"""

    K_P = 0.1
    """Proportional control coefficient for error in grams to speed in mm/s"""
    K_I = 0
    K_D = 0.01

    prev_time = time()
    cur_time = time()

    while True:
        cur_time = time()
        dt = cur_time - prev_time
        prev_time = cur_time

        old_error = error
        error = target - force
        int_error = (
            (int_error + (old_error + error) / 2 * dt) if dt > 0 else int_error
        )  # trapezoidal integration
        der_error = 0.5 * der_error + (
            ((error - old_error) / dt) if dt > 0 else 0
        )  # first order backwards difference

        out_str = "{:6.2f}{:}, err = {:6.2f}, pos = {:6.2f}, ".format(
            force, units, error, get_pos_mm()
        )

        vel_P = -K_P * error
        """Proportional component of velocity response"""
        vel_I = -K_I * int_error
        """Integral component of velocity response"""
        vel_D = -K_D * der_error
        """Derivative component of velocity response"""
        vel = vel_P + vel_D + vel_I
        set_vel_mms(vel)

        out_str += "velP = {:6.2f}, velD = {:6.2f}, ".format(vel_P, vel_D)

        # print(force)
        if error < 0:
            out_str += "go up"
        elif error > 0:
            out_str += "go down"
        else:
            out_str += "stay here"
        if tic.variables.current_position < lower_limit:
            set_vel_mms(backoff_velocity)
            out_str += " - too low overriding ^^^^"
        if tic.variables.current_position >= upper_limit:
            set_vel_mms(-backoff_velocity)
            out_str += " - too high overriding vvvv"

        print(out_str)
        # print(force - target)
        # print(tic.variables.target_position)
        # print(tic.variables.error_status)
        tic.reset_command_timeout()


def background():
    """Records data to csv"""
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
            (not lc.is_alive()) and (not ac.is_alive()) and (time() - start_time) > 1
        ):
            print("end of print")
            break

    print("=" * 20 + " BACKGROUND IS DONE " + "=" * 20)


lc = threading.Thread(name="loadcell", target=load_cell_thread)
ac = threading.Thread(name="actuator", target=actuator_thread)
b = threading.Thread(name="background", target=background)

lc.start()
ac.start()
# b.start()
