import serial
import json
import threading
import pytic
from time import sleep, time
import math
from datetime import datetime
import re
from LoadCell import openscale

# - Initialization -------------------------------------------

date = datetime.now()
date_str = date.strftime("%Y-%m-%d_%H-%M-%S")
"""timestamp string for experiment start time in yyyy-mm-dd_HH:MM:SS format"""
csv_name = date_str + "_" + "newtonain_squeeze_flow_1" + "-data.csv"

HAMMER_RADIUS = 25e-3  # m
HAMMER_AREA = math.pi * HAMMER_RADIUS**2  # m^2


def move_to_pos(pos: int):
    """Moves actuator to desired position, finishes when the actuator reaches the target

    Args:
            pos (int): target position in steps from zero
    """
    tic.set_target_position(pos)
    while tic.variables.current_position != tic.variables.target_position:
        sleep(0.1)
        tic.reset_command_timeout()


def move_to_mm(pos_mm: float) -> int:
    """Moves actuator to desired position in mm

    Args:
            pos_mm (float): desired position in mm

    Returns:
            int: corresponding position in actuator's units, steps
    """
    pos = math.floor(pos_mm * 100 * 2**tic.variables.step_mode)
    move_to_pos(pos)
    return pos


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


def set_vel_mms(vel_mms: float) -> int:
    """Sets actuator target velocity in mm/s

    Args:
            vel_mms (float): the desired velocity in mm/s

    Returns:
            int: velocity in the actuator's units, steps/10,000s
    """
    vel = math.floor(vel_mms * 1000000 * 2**tic.variables.step_mode)
    tic.set_target_velocity(vel)
    return vel


def get_pos_mm() -> float:
    """Gets current actuator position in mm

    Returns:
            float: current actuator position in mm
    """
    pos = tic.variables.current_position / 100.0 * 2**-tic.variables.step_mode
    return pos


def get_vel_mms() -> float:
    """Gets current actuator velocity in mm/s

    Returns:
            float: current actuator velocity in mm/s
    """
    vel = tic.variables.current_velocity / 1000000 * 2**-tic.variables.step_mode
    return vel


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
target = 0
"""Target force. Positive is a force pushing up on the load cell"""
start_gap = 0
"""Initial distance away from hard stop."""
gap = 0
"""Current gap between hammer and hard stop"""
eta_guess = 0
"""Estimate of newtonian viscosity of sample"""

if __name__ == "__main__":
    target_line = input("Enter the target force in [{:}]: ".format(units))
    temp = re.compile("[0-9.]+")
    res = temp.search(target_line).group(0)
    target = float(res)
    print("Target force is {:.2f}{:}".format(target, units))

    gap_line = input("Enter the current gap in [m]: ")
    temp = re.compile("[0-9.]+")
    res = temp.search(target_line).group(0)
    start_gap = float(res)
    print("Starting gap is {:.2f}m".format(start_gap))

    scale = openscale.OpenScale()

    tic = pytic.PyTic()

    # Connect to first available Tic Device serial number over USB
    serial_nums = tic.list_connected_device_serial_numbers()

    # print(serial_nums)
    tic.connect_to_serial_number(serial_nums[0])

    tic.set_current_limit(576)  # mA, right under the 600mA limit for the actuator
    tic.set_max_decel(200000)
    tic.set_max_accel(200000)
    tic.set_max_speed(5000000)  # 5mm/s

    # Zero current motor position
    tic.halt_and_set_position(0)

    with open("data/" + csv_name, "a") as datafile:
        # with open('data/test_file.csv','a') as datafile:
        datafile.write(
            "Current Time, Elapsed Time, Current Position (mm), Current Position, Target Position, Current Velocity (mm/s), Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV), Current Force ({:}}), Target Force ({:}), Current Gap (m), Viscosity (Pa.s), Hammer Radius (m), Hammer Area (m^2)\n".format(
                scale.units, scale.units
            )
        )


def load_cell_thread():
    """Continuously reads load cell and reports the upward force on the load cell"""
    global force

    start_time = time()

    for i in range(10):  # get rid of first few lines that aren't readings
        scale.get_line()
    scale.flush_old_lines()  # and get rid of any others that were generated when we were busy setting up

    while True:
        force = scale.get_calibrated_measurement()

        if (time() - start_time) >= 2000 or (
            (not ac.is_alive()) and (not b.is_alive()) and (time() - start_time) > 1
        ):
            print("Stopping load cell reading")
            break


def actuator_thread():
    """Drives actuator"""
    global gap, eta_guess

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    # Energize Motor
    print("energizing")
    tic.energize()
    print("exiting safe start")
    tic.exit_safe_start()

    approach_velocity = -3  # mm/s, speed to approach bath of fluid at
    force_threshold = 0.5  # g, force must exceed this for control system to kick in.
    max_force = 80  # g, if force greater than this, stop test.

    backoff_velocity = 1  # mm/s

    upper_limit = -100
    lower_limit = -start_gap * 100

    error = 0
    """Positive error means force must increase, so actuator must extend down"""
    old_error = 0
    """Error from previous frame, used for derivative & integral calculation"""
    # int_error = 0
    # '''Integrated error - TODO: implement error accumulation and also limiting'''
    # der_error = 0
    # '''Time derivative of error - TODO: implement finite difference scheme to approximate derivative. Maybe just 1st order backward'''

    # K_P = 0.1
    # '''Proportional control coefficient for error in grams to speed in mm/s'''
    # K_I = 0
    # K_D = 0.01

    # Start by approaching and waiting until force is non-negligible
    set_vel_mms(approach_velocity)
    while True:
        # print("{:6.2f} <? {:6.2f}".format(force, force_threshold))
        tic.reset_command_timeout()
        if abs(force) > max_force:
            break
        if abs(force) > force_threshold:
            break
        # print("{:6.2f} >=? {:6.2f}".format(get_pos_mm() / 1000.0, start_gap))
        if abs(get_pos_mm() / 1000.0) >= start_gap:
            print("Hit the hard-stop without ever exceeding threshold force, stopping.")
            move_to_mm(0)
            break
    print("Force threshold met, switching over to force-velocity control.")

    gap = get_pos_mm() / 1000.0 + start_gap  # m

    prev_time = time()
    cur_time = time()
    while True:
        # Get timestep
        cur_time = time()
        dt = cur_time - prev_time
        prev_time = cur_time

        # Check if force beyond max amount
        if abs(force) > max_force:
            print("Force was too large, stopping.")
            move_to_mm(0)
            break

        # Check if went too far
        if abs(get_pos_mm()) / 1000.0 >= start_gap:
            print("Hit the hard-stop, stopping.")
            move_to_mm(0)
            break

        # Get gap
        gap = get_pos_mm() / 1000.0 + start_gap  # m

        # Guess viscosity
        eta_guess = (
            2
            * gap**3
            * scale.grams_to_N(force)
            / (3 * math.pi * HAMMER_RADIUS**4 * -(get_vel_mms() / 1000))
        )  # Pa.s

        # Set velocity based on force, gap, and viscosity guess
        v_new = (
            -2
            * gap**3
            * scale.grams_to_N(target)
            / (3 * math.pi * HAMMER_RADIUS**4 * eta_guess)
            * 1000
        )  # mm/s
        # v_new = target / force * get_vel_mms()
        # #   these two lines are equivalent, it works because force and velocity are linearly proportional
        set_vel_mms(v_new)

        old_error = error
        error = target - force
        # int_error = (int_error + (old_error + error)/2 * dt) if dt > 0 else int_error # trapezoidal integration
        # der_error = 0.5*der_error + (((error - old_error)/dt) if dt > 0 else 0) # first order backwards difference

        out_str = "{:6.2f}{:}, err = {:6.2f}, pos = {:6.2f}, ".format(
            force, scale.units, error, get_pos_mm()
        )

        # vel_P = -K_P * error
        # '''Proportional component of velocity response'''
        # vel_I = -K_I * int_error
        # '''Integral component of velocity response'''
        # vel_D = -K_D * der_error
        # '''Derivative component of velocity response'''
        # vel = vel_P + vel_D + vel_I
        # set_vel_mms(vel)

        # out_str += "velP = {:6.2f}, velD = {:6.2f}, ".format(vel_P,vel_D)

        # print(force)
        if error < 0:
            out_str += "go slower"
        elif error > 0:
            out_str += "go faster"
        else:
            out_str += "maintain speed"
        # if(tic.variables.current_position < lower_limit):
        # 	set_vel_mms(backoff_velocity)
        # 	out_str += " - too low overriding ^^^^"
        # if(tic.variables.current_position >= upper_limit):
        # 	set_vel_mms(-backoff_velocity)
        # 	out_str += " - too high overriding vvvv"

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
        cur_pos_mm = get_pos_mm()
        cur_pos = tic.variables.current_position
        tar_pos = tic.variables.target_position
        cur_vel_mms = get_vel_mms()
        cur_vel = tic.variables.current_velocity
        tar_vel = tic.variables.target_velocity
        max_speed = tic.variables.max_speed
        max_decel = tic.variables.max_decel
        max_accel = tic.variables.max_accel
        step_mode = tic.variables.step_mode
        vin_voltage = tic.variables.vin_voltage

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
                target,
                gap,
                eta_guess,
                HAMMER_RADIUS,
                HAMMER_AREA,
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
# b.start()
