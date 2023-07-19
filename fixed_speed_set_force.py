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

from Actuator.ticactuator import TicActuator

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

    actuator = TicActuator(step_mode=4)
    actuator.set_max_accel_mmss(20, True)
    actuator.set_max_speed_mms(5)

    # Zero current motor position
    actuator.halt_and_set_position(0)
    actuator.heartbeat()

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

    actuator.startup()

    threshold = 0.5
    vel_mag = 1  # mm/s

    upper_limit = -100
    lower_limit = -4000
    while True:
        out_str = "{:6.2f}{:}, {:6.2f}, ".format(force, units, actuator.get_pos_mm())
        # print(force)
        if force - target > threshold:
            out_str = out_str + "go up"
            actuator.set_vel_mms(vel_mag)
        elif force - target < -threshold:
            out_str = out_str + "go down"
            actuator.set_vel_mms(-vel_mag)
        else:
            out_str = out_str + "stay here"
            actuator.set_vel_mms(0)
        if actuator.variables.current_position < lower_limit:
            actuator.set_vel_mms(vel_mag)
            out_str = out_str + " - too low overriding ^^^^"
        if actuator.variables.current_position >= upper_limit:
            actuator.set_vel_mms(-vel_mag)
            out_str = out_str + " - too high overriding vvvv"

        print(out_str)
        # print(force - target)
        # print(actuator.variables.target_position)
        # print(actuator.variables.error_status)
        actuator.heartbeat()


def background():
    """Records data to csv"""
    global tic

    start_time = time()
    while True:
        # print(actuator)
        # print(actuator.variables)
        cur_pos = actuator.variables.current_position
        tar_pos = actuator.variables.target_position
        cur_vel = actuator.variables.current_velocity
        tar_vel = actuator.variables.target_velocity
        max_speed = actuator.variables.max_speed
        max_decel = actuator.variables.max_decel
        max_accel = actuator.variables.max_accel
        step_mode = actuator.variables.step_mode
        vin_voltage = actuator.variables.vin_voltage

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
