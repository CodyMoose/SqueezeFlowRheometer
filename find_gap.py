import json
import threading
import pytic
from time import sleep, time
import math
from datetime import datetime
import re
from Actuator.ticactuator import TicActuator
from LoadCell.openscale import OpenScale

# - Initialization -------------------------------------------

date = datetime.now()
date_str = date.strftime("%Y-%m-%d_%H-%M-%S")
"""timestamp string for experiment start time in yyyy-mm-dd_HH:MM:SS format"""
csv_name = date_str + "_" + "find_gap" + "-data.csv"
config_path = "LoadCell\config.json"

HAMMER_RADIUS = 25e-3  # m
HAMMER_AREA = math.pi * HAMMER_RADIUS**2  # m^2


def grams_to_N(f: float) -> float:
    """Takes in force in grams and converts to Newtons

    Args:
            f (float): force in grams

    Returns:
            float: force in Newtons
    """
    return 0.00980665 * f


force = 0
"""Current force reading. Positive is a force pushing up on the load cell"""
FORCE_UP_SIGN = -1
"""Sign of a positive force. This should be 1 or -1, and is used to compute velocity based on force"""
start_gap = 0
"""Initial distance away from hard stop."""
gap = 0
"""Current gap between hammer and hard stop"""

if __name__ == "__main__":
    scale = OpenScale()

    # target_line = input("Enter the target force in [{:}]: ".format(scale.units))
    # temp = re.compile("[0-9.]+")
    # res = temp.search(target_line).group(0)
    # target = float(res)
    # print("Target force is {:.2f}{:}".format(target, scale.units))

    gap_line = input("How far should I go out to start, in mm? ")
    temp = re.compile("[0-9.]+")
    res = temp.search(gap_line).group(0)
    start_gap = float(res)
    print("Starting gap is {:.2f}mm".format(start_gap))

    actuator = TicActuator(step_mode=5)
    actuator.set_max_accel_mmss(20, True)
    actuator.set_max_speed_mms(5)

    # Zero current motor position
    actuator.halt_and_set_position(0)
    actuator.heartbeat()

    with open("data/" + csv_name, "a") as datafile:
        datafile.write(
            "Current Time, Elapsed Time, Current Position (mm), Current Position, Target Position, Current Velocity (mm/s), Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV), Current Force ({:}) Current Gap (m)\n".format(
                scale.units
            )
        )


def load_cell_thread():
    """Continuously reads load cell and reports the upward force on the load cell"""
    global force

    start_time = time()

    for i in range(10):  # get rid of first few lines that aren't readings
        scale.get_line()
    scale.flush_old_lines()  # and get rid of any others that were generated when we were busy setting up

    cur_time = time()
    prev_time = cur_time
    outlier_threshold = 100
    while True:
        force = scale.wait_for_calibrated_measurement(True) * FORCE_UP_SIGN

        if (time() - start_time) >= 2000 or (
            (not ac.is_alive()) and (not b.is_alive()) and (time() - start_time) > 1
        ):
            print("Stopping load cell reading")
            return


def actuator_thread():
    """Drives actuator"""
    global gap

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    actuator.startup()

    approach_velocity = -0.5  # mm/s, speed to approach bath of fluid at
    force_threshold = 0.8  # g, the force to look for when you hit something
    max_force = 80  # g, if force greater than this, stop test.
    backoff_dist = 0.1  # mm, distance to back away when you hit

    hit_pos = 0

    # Go to starting gap
    actuator.move_to_mm(-abs(start_gap))
    print("Reached start point. Now approaching to find the hard stop slowly.")

    # Start by approaching and waiting until force is non-negligible
    actuator.set_vel_mms(approach_velocity)
    while True:
        # print("{:6.2f} <? {:6.2f}".format(force, force_threshold))
        actuator.heartbeat()
        if abs(force) > max_force:
            print("Force was too large, stopping.")
            actuator.go_home_quiet_down()
            return
        if abs(force) > force_threshold:
            hit_pos = actuator.get_pos_mm()
            print("Hit something at {:.2f}mm".format(hit_pos))
            actuator.move_to_mm(hit_pos + backoff_dist)
            break
        # print("{:6.2f} >=? {:6.2f}".format(get_pos_mm() / 1000.0, start_gap))
    print("Force threshold met, switching over to fine approach.")

    N_find = 25
    gap_list = [0] * N_find
    slowdown_factor = 0.05  # what factor to slow down by on fine approach

    for i in range(N_find):
        actuator.set_vel_mms(approach_velocity * slowdown_factor)
        while True:
            # Check if force beyond max amount
            if abs(force) > max_force:
                print("Force was too large, stopping.")
                actuator.go_home_quiet_down()
                return

            # Check if we reached something with a lighter force
            if abs(force) > force_threshold:
                hit_pos = actuator.get_pos_mm()
                gap_list[i] = hit_pos
                if i < N_find - 1:
                    print(
                        "Hit something at {:.4f}mm, backing up to check again".format(
                            hit_pos
                        )
                    )
                else:
                    print("Hit something at {:.4f}mm, done checking".format(hit_pos))
                actuator.move_to_mm(hit_pos + backoff_dist)
                break

            out_str = "{:2d}: {:7.3f}{:}, pos = {:8.3f}mm".format(
                i + 1, force, scale.units, actuator.get_pos_mm()
            )

            # print(force)
            # if(actuator.variables.current_position < lower_limit):
            # 	set_vel_mms(backoff_velocity)
            # 	out_str += " - too low overriding ^^^^"
            # if(actuator.variables.current_position >= upper_limit):
            # 	set_vel_mms(-backoff_velocity)
            # 	out_str += " - too high overriding vvvv"

            print(out_str)
            # print(actuator.variables.error_status)
            actuator.heartbeat()

    mean_gap = abs(sum(gap_list) / N_find)
    print("The mean gap is {:f}mm".format(mean_gap))

    # Save gap in config file
    try:
        with open(config_path, "r") as read_file:
            config = json.load(read_file)
    except:
        config = {}
    config["gap"] = mean_gap
    with open(config_path, "w") as write_file:
        json.dump(config, write_file)

    actuator.go_home_quiet_down()
    print("Done with actuator")


def background():
    """Records data to csv"""
    global actuator

    start_time = time()
    while True:
        cur_pos_mm = actuator.get_pos_mm()
        cur_pos = actuator.get_pos()
        tar_pos = actuator.variables.target_position
        cur_vel_mms = actuator.get_vel_mms()
        cur_vel = actuator.get_vel()
        tar_vel = actuator.variables.target_velocity
        max_speed = actuator.variables.max_speed
        max_decel = actuator.variables.max_decel
        max_accel = actuator.variables.max_accel
        step_mode = actuator.variables.step_mode
        vin_voltage = actuator.variables.vin_voltage

        with open(
            "data/" + csv_name, "a"
        ) as datafile:  # write time & current details to csv
            cur_time = time()
            cur_duration = cur_time - start_time

            output_params = [
                cur_time,
                cur_duration,
                cur_pos_mm,
                cur_pos,
                tar_pos,
                cur_vel_mms,
                cur_vel,
                tar_vel,
                max_speed,
                max_decel,
                max_accel,
                step_mode,
                vin_voltage,
                force,
                gap,
            ]
            dataline = ",".join(map(str, output_params)) + "\n"
            datafile.write(dataline)
            # print(dataline)

        sleep(0.1)

        if (time() - start_time) >= 2000 or (
            (not ac.is_alive()) and (time() - start_time) > 1
        ):
            print("end of print")
            break

    print("=" * 20 + " BACKGROUND IS DONE " + "=" * 20)


lc = threading.Thread(name="loadcell", target=load_cell_thread)
ac = threading.Thread(name="actuator", target=actuator_thread)
b = threading.Thread(name="background", target=background)

lc.start()
ac.start()
b.start()
