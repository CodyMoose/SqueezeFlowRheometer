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
csv_name = date_str + "_" + "PID_squeeze_flow_1" + "-data.csv"

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
target = 0
"""Target force. Positive is a force pushing up on the load cell"""
dt_force = 0
"""Time between last two force measurements"""
start_gap = 0
"""Initial distance away from hard stop."""
gap = 0
"""Current gap between hammer and hard stop"""
sample_volume = 0
"""Amount of sample in m^3"""
eta_guess = 0
"""Estimate of newtonian viscosity of sample"""

error = 0
"""Positive error means force must increase, so actuator must extend down"""
int_error = 0
"""Time-integrated error"""
der_error = 0
"""Time-derivative of error"""

if __name__ == "__main__":
    scale = OpenScale()

    # Get test details from user
    target_line = input("Enter the target force in [{:}]: ".format(scale.units))
    temp = re.compile("[0-9.]+")
    res = temp.search(target_line).group(0)
    target = float(res)
    print("Target force is {:.2f}{:}".format(target, scale.units))

    gap_line = input("Enter the current gap in [mm]: ")
    temp = re.compile("[0-9.]+")
    res = temp.search(gap_line).group(0)
    start_gap = abs(float(res))
    print("Starting gap is {:.2f}mm".format(start_gap))

    vol_line = input("Enter the sample volume in [mL]: ")
    temp = re.compile("[0-9.]+")
    res = temp.search(gap_line).group(0)
    sample_volume = abs(float(res)) * 1e-6  # m^3
    print("Sample volume is {:.2f}mL".format(start_gap))

    weight = None
    while weight is None:
        weight = scale.wait_for_calibrated_measurement()
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

    with open("data/" + csv_name, "a") as datafile:
        datafile.write(
            "Current Time, Elapsed Time, Current Position (mm), Current Position, Target Position, Current Velocity (mm/s), Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV), Current Force ({:}), Target Force ({:}), Current Gap (m), Viscosity (Pa.s), Sample Volume (m^3)\n".format(
                scale.units, scale.units
            )
        )


def load_cell_thread():
    """Continuously reads load cell and reports the upward force on the load cell"""
    global force, dt_force, error, der_error, int_error

    start_time = time()

    for i in range(10):  # get rid of first few lines that aren't readings
        scale.get_line()
    scale.flush_old_lines()  # and get rid of any others that were generated when we were busy setting up

    old_error = error
    """Error from previous frame, used for derivative & integral calculation"""

    cur_time = time()
    prev_time = cur_time
    while True:
        force = scale.wait_for_calibrated_measurement()

        prev_time = cur_time
        cur_time = time()
        dt_force = cur_time - prev_time

        old_error = error
        error = target - force
        int_error += (
            ((old_error + error) / 2 * dt_force) if dt_force > 0 else 0
        )  # trapezoidal integration
        der_error = (
            ((error - old_error) / dt_force) if dt_force > 0 else 0
        )  # first order backwards difference

        # # Report error values
        # print("Error            = {:.2f}".format(error))
        # print("Integrated error = {:.2f}".format(int_error))
        # print("Derivative error = {:.2f}".format(der_error))

        if (time() - start_time) >= 2000 or (
            (not ac.is_alive()) and (not b.is_alive()) and (time() - start_time) > 1
        ):
            print("Stopping load cell reading")
            break


def actuator_thread():
    """Drives actuator"""
    global gap, eta_guess, error, int_error, der_error

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    # Energize Motor
    print("Energizing")
    actuator.energize()
    print("Exiting safe start")
    actuator.exit_safe_start()

    approach_velocity = -3  # mm/s, speed to approach bath of fluid at
    force_threshold = 1  # g, force must exceed this for control system to kick in.
    max_force = 80  # g, if force greater than this, stop test.

    backoff_velocity = 1  # mm/s

    # upper_limit = -100
    # lower_limit = -start_gap * 100

    K_P = 0.1
    """Proportional control coefficient for error in grams to speed in mm/s"""
    K_I = 0.001
    K_D = 0.01

    # Start by approaching and waiting until force is non-negligible
    actuator.set_vel_mms(approach_velocity)
    while True:
        # print("{:6.2f} <? {:6.2f}".format(force, force_threshold))
        actuator.heartbeat()
        if abs(force) > max_force:
            break
        if force > force_threshold:
            break
        # print("{:6.2f} >=? {:6.2f}".format(get_pos_mm(), start_gap))
        if abs(actuator.get_pos_mm()) >= start_gap:
            print("Hit the hard-stop without ever exceeding threshold force, stopping.")
            actuator.go_home_quiet_down()
            return

        # reset integrated error - prevent integral windup
        int_error = 0
    print("Force threshold met, switching over to force-velocity control.")

    gap = (actuator.get_pos_mm() + start_gap) / 1000.0  # m

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
            actuator.go_home_quiet_down()
            return

        # Check if went too far
        if abs(actuator.get_pos_mm()) >= start_gap:
            print("Hit the hard-stop, stopping.")
            actuator.go_home_quiet_down()
            return

        # Get gap
        gap = (actuator.get_pos_mm() + start_gap) / 1000.0  # m

        # Guess Newtonian viscosity
        eta_guess = abs(
            2
            * math.pi
            * gap**5
            * OpenScale.grams_to_N(force)
            / (3 * sample_volume * (actuator.get_vel_mms() / 1000))
        )  # Pa.s

        # prevent integral windup
        if abs(int_error) > 1000:
            int_error = 1000 * math.copysign(1000, int_error)

        vel_P = -K_P * error
        """Proportional component of velocity response"""
        vel_I = -K_I * int_error
        """Integral component of velocity response"""
        vel_D = -K_D * der_error
        """Derivative component of velocity response"""
        v_new = vel_P + vel_D + vel_I
        actuator.set_vel_mms(v_new)

        out_str = "{:6.2f}{:}, err = {:6.2f}, errI = {:6.2f}, errD = {:6.2f}, pos = {:6.2f}, v = {:6.2f} : vP = {:6.2f}, vI = {:6.2f}, vD = {:6.2f}".format(
            force,
            scale.units,
            error,
            int_error,
            der_error,
            actuator.get_pos_mm(),
            v_new,
            vel_P,
            vel_I,
            vel_D,
        )

        # print(force)
        if error < 0:
            out_str += " go slower"
        elif error > 0:
            out_str += " go faster"
        else:
            out_str += " maintain speed"
        # if(actuator.variables.current_position < lower_limit):
        # 	actuator.set_vel_mms(backoff_velocity)
        # 	out_str += " - too low overriding ^^^^"
        # if(actuator.variables.current_position >= upper_limit):
        # 	actuator.set_vel_mms(-backoff_velocity)
        # 	out_str += " - too high overriding vvvv"

        print(out_str)
        # print(force - target)
        # print(actuator.variables.target_position)
        # print(actuator.variables.error_status)
        actuator.heartbeat()


def background():
    """Records data to csv"""
    global actuator

    start_time = time()
    while True:
        # print(actuator)
        # print(actuator.variables)
        cur_pos_mm = actuator.get_pos_mm()
        cur_pos = actuator.variables.current_position
        tar_pos = actuator.variables.target_position
        cur_vel_mms = actuator.get_vel_mms()
        cur_vel = actuator.variables.current_velocity
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
                target,
                gap,
                eta_guess,
                sample_volume,
            ]
            dataline = ",".join(map(str, output_params)) + "\n"
            datafile.write(dataline)
            # print(dataline)

        sleep(0.1)

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
