import threading
from time import sleep, time
import math
from datetime import datetime
import re
from LoadCell.openscale import OpenScale
from Actuator.ticactuator import TicActuator

# - Initialization -------------------------------------------

date = datetime.now()
date_str = date.strftime("%Y-%m-%d_%H-%M-%S")
"""timestamp string for experiment start time in yyyy-mm-dd_HH:MM:SS format"""
csv_name = date_str + "_" + "fixed_speed_squeeze_flow" + "-data.csv"

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


def compute_gap() -> float:
    """Computes the gap in m

    Returns:
        float: Gap between parallel plates in squeeze flow
    """
    return (actuator.get_pos_mm() + loading_gap) / 1000.0  # m


force = 0
"""Current force reading. Negative is a force pushing up on the load cell"""
target = 0
"""Target Velocity."""
FORCE_UP_SIGN = 1
"""Sign of a positive force. This should be 1 or -1, and is used to compute velocity based on force"""
loading_gap = 0
"""Initial distance (mm) away from hard stop."""
gap = 0
"""Current gap (m) between hammer and hard stop"""
sample_volume = 0
"""Amount of sample (m^3)"""
visc_volume = 0
"""Volume used for viscosity computations. Will be less than total sample if spread beyond hammer."""
eta_guess = 0
"""Estimate of newtonian viscosity of sample (Pa.s)"""
test_active = False
"""Whether or not the test is active. Should be true after force threshold is met but before test ends"""
spread_beyond_hammer = False
"""Whether or not the sample has spread beyond the hammer. This will happen if gap gets too thin."""
sample_str = ""
"""What the sample is made of. Used in filename."""

if __name__ == "__main__":
    scale = OpenScale()

    # Get test details from user
    target_line = input("Enter the target velocity in [mm/s]: ")
    temp = re.compile("[0-9.]+")
    res = temp.search(target_line).group(0)
    target = float(res)
    print("Target velocity is {:.2f}mm/s".format(target))

    loading_gap_line = input(
        "Enter the current gap in [mm]. If you want to use the gap in the config file, type 'config': "
    )
    if "config" in loading_gap_line.lower():
        loading_gap = float(scale.config["gap"])
    else:
        temp = re.compile("[0-9.]+")
        res = temp.search(loading_gap_line).group(0)
        loading_gap = abs(float(res))
    print("Initial gap is {:.2f}mm".format(loading_gap))

    start_gap_line = input(
        "Enter the gap to start the test at in [mm]. Rheometer will move from current loading gap to the start gap and then start the test: "
    )
    temp = re.compile("[0-9.]+")
    res = temp.search(start_gap_line).group(0)
    start_gap = abs(float(res))
    print("Test start gap is {:.2f}mm".format(start_gap))

    vol_line = input("Enter the sample volume in [mL]: ")
    temp = re.compile("[0-9.]+")
    res = temp.search(vol_line).group(0)
    sample_volume = abs(float(res)) * 1e-6  # m^3
    print("Sample volume is {:.2f}mL".format(sample_volume * 1e6))

    sample_str = input("What's the sample made of? This will be used for file naming. ")

    weight = None
    while weight is None:
        weight = scale.wait_for_calibrated_measurement(True)
    if abs(weight) > 0.5:
        ans = input(
            "The load cell is out of tare! Current reading is {:.2f}{:}. Do you want to tare it now? (y/n) ".format(
                weight, scale.units
            )
        )
        if ans == "y":
            scale.tare()

    actuator = TicActuator(step_mode=4)
    actuator.set_max_accel_mmss(20, True)
    actuator.set_max_speed_mms(5)

    # Zero current motor position
    actuator.halt_and_set_position(0)
    actuator.heartbeat()

    csv_name = (
        date_str
        + "_"
        + "fixed_speed_squeeze_flow_{:}_{:d}mL_{:d}{:}".format(
            sample_str, round(sample_volume * 1e6), round(target), scale.units
        )
        + "-data.csv"
    )
    with open("data/" + csv_name, "a") as datafile:
        datafile.write(
            "Current Time, Elapsed Time, Current Position (mm), Current Position, Target Position, Current Velocity (mm/s), Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV), Current Force ({:}), Target Speed (mm/s), Start Gap (m), Current Gap (m), Viscosity (Pa.s), Sample Volume (m^3), Viscosity Volume (m^3), Test Active?, Spread beyond hammer?\n".format(
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

    cur_time = time()
    prev_time = cur_time

    while True:
        force = scale.wait_for_calibrated_measurement(True) * FORCE_UP_SIGN

        # prev_time = cur_time
        # cur_time = time()

        if (time() - start_time) >= 2000 or (
            (not ac.is_alive()) and (not b.is_alive()) and (time() - start_time) > 1
        ):
            print("Stopping load cell reading")
            break


def actuator_thread():
    """Drives actuator"""
    global gap, eta_guess, sample_volume, test_active, spread_beyond_hammer, visc_volume

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    # Energize Motor
    print("Energizing")
    actuator.energize()
    print("Exiting safe start")
    actuator.exit_safe_start()

    approach_velocity = -1  # mm/s, speed to approach bath of fluid at
    force_threshold = 2  # g, force must exceed this for control system to kick in.
    max_force = 80  # g, if force greater than this, stop test.

    backoff_velocity = 1  # mm/s

    # upper_limit = -100
    # lower_limit = -start_gap * 100

    # Start by approaching to the start gap
    gap = compute_gap()
    actuator.set_vel_mms(approach_velocity)
    while abs(gap) > abs(start_gap) / 1000.0:
        # print("{:6.2f} <? {:6.2f}".format(force, force_threshold))
        actuator.heartbeat()
        if abs(force) > max_force:
            test_active = False
            actuator.go_home_quiet_down()
            return
        # print("{:6.2f} >=? {:6.2f}".format(get_pos_mm(), start_gap))
        if abs(actuator.get_pos_mm()) >= loading_gap:
            print("Hit the hard-stop without ever exceeding threshold force, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

    test_active = True
    print("Reached start gap, test now active.")
    actuator.set_vel_mms(-abs(target))

    gap = compute_gap()

    prev_time = time()
    cur_time = time()
    while True:
        # print("another step")
        # Get timestep
        cur_time = time()
        dt = cur_time - prev_time
        prev_time = cur_time

        # Check if force beyond max amount
        # print("Force = {:}".format(force))
        if abs(force) > max_force:
            print("Force was too large, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

        # Check if went too far
        if abs(actuator.get_pos_mm()) >= loading_gap:
            print("Hit the hard-stop, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

        # Check if returned towards zero too far
        if abs(actuator.get_pos_mm()) <= 1:
            print("Returned too close to home, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

        # Get gap
        gap = compute_gap()

        # Check if sample spread beyond hammer, but only perform the check if it hasn't already
        hammer_volume = gap * HAMMER_AREA  # volume under hammer
        if not spread_beyond_hammer:
            spread_beyond_hammer = sample_volume > hammer_volume

        # Guess Newtonian viscosity
        visc_volume = min(sample_volume, hammer_volume)
        try:
            if (
                visc_volume > 0 and abs(actuator.get_vel_mms()) > 0
            ):  # viscosity estimates only valid if sample volume is positive
                eta_guess = abs(
                    2
                    * math.pi
                    * gap**5
                    * OpenScale.grams_to_N(force)
                    / 3
                    / visc_volume**2
                    / (actuator.get_vel_mms() / 1000)
                )  # Pa.s
        except:
            eta_guess = 0

        out_str = "{:6.2f}{:}, v = {:11.5f}, pos = {:6.2f}, gap = {:6.2f}".format(
            force,
            scale.units,
            actuator.get_vel_mms(),
            actuator.get_pos_mm(),
            gap * 1000.0,
        )

        print(out_str)
        # print(actuator.variables.target_position)
        # print(actuator.variables.error_status)
        actuator.heartbeat()


def background():
    """Records data to csv"""
    global actuator, loading_gap, test_active, spread_beyond_hammer, visc_volume

    start_time = time()
    while True:
        # print(actuator)
        # print(actuator.variables)
        cur_pos = actuator.get_pos()
        cur_pos_mm = actuator.steps_to_mm(cur_pos)
        tar_pos = actuator.get_variable_by_name("target_position")
        cur_vel = actuator.get_vel()
        cur_vel_mms = actuator.vel_to_mms(cur_vel)
        tar_vel = actuator.get_variable_by_name("target_velocity")
        max_speed = actuator.get_variable_by_name("max_speed")
        max_decel = actuator.get_variable_by_name("max_decel")
        max_accel = actuator.get_variable_by_name("max_accel")
        step_mode = actuator.get_variable_by_name("step_mode")
        vin_voltage = actuator.get_variable_by_name("vin_voltage")
        gap = compute_gap()

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
                loading_gap / 1000.0,
                gap,
                eta_guess,
                sample_volume,
                visc_volume,
                test_active,
                spread_beyond_hammer,
            ]
            dataline = ",".join(map(str, output_params)) + "\n"
            datafile.write(dataline)
            # print(dataline)

        sleep(0.02)

        if (time() - start_time) >= 2000 or (
            (not ac.is_alive()) and (time() - start_time) > 1
        ):
            print("Time since started: {:.0f}".format(time() - start_time))
            print("Actuator thread dead? {:}".format(not ac.is_alive()))
            print("end of background")
            break

    print("=" * 20 + " BACKGROUND IS DONE " + "=" * 20)


lc = threading.Thread(name="loadcell", target=load_cell_thread)
ac = threading.Thread(name="actuator", target=actuator_thread)
b = threading.Thread(name="background", target=background)

lc.start()
ac.start()
b.start()
