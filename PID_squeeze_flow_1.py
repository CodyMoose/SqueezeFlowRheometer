import threading
from time import sleep, time
import math
from datetime import datetime
import re
from LoadCell.openscale import OpenScale
from Actuator.ticactuator import TicActuator
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

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
"""Current force reading. Negative is a force pushing up on the load cell"""
target = 0
"""Target force. Negative is a force pushing up on the load cell"""
FORCE_UP_SIGN = 1
"""Sign of a positive force. This should be 1 or -1, and is used to compute velocity based on force"""
dt_force = 0
"""Time between last two force measurements (s)"""
start_gap = 0
"""Initial distance (mm) away from hard stop."""
gap = 0
"""Current gap (m) between hammer and hard stop"""
sample_volume = 0
"""Amount of sample (m^3)"""
visc_volume = 0
"""Volume used for viscosity computations. Will be less than total sample if spread beyond hammer."""
eta_guess = 0
"""Estimate of newtonian viscosity of sample (Pa.s)"""
yield_stress_guess = 0
"""Estimate of yield stress of sample (Pa)"""
test_active = False
"""Whether or not the test is active. Should be true after force threshold is met but before test ends"""
spread_beyond_hammer = False
"""Whether or not the sample has spread beyond the hammer. This will happen if gap gets too thin."""
sample_str = ""
"""What the sample is made of. Used in filename."""

error = 0
"""Positive error means force must increase, so actuator must extend down"""
int_error = 0
"""Time-integrated error"""
der_error = 0
"""Time-derivative of error"""

K_P = 0.07
"""Proportional control coefficient for error in grams to speed in mm/s"""
K_I = 0.0005
"""Integral control coefficient for integrated error in grams*s to speed in mm/s"""
K_D = 0.0000167
"""Derivative control coefficient for error derivative in grams/s to speed in mm/s"""
decay_rate = 0.997
decay_rate_r = -0.1502

times = []
forces = []
gaps = []

if __name__ == "__main__":
    scale = OpenScale()

    # Get test details from user
    target_line = input("Enter the target force in [{:}]: ".format(scale.units))
    temp = re.compile("[0-9.]+")
    res = temp.search(target_line).group(0)
    target = float(res)
    print("Target force is {:.2f}{:}".format(target, scale.units))

    gap_line = input(
        "Enter the current gap in [mm]. If you want to use the gap in the config file, type 'config': "
    )
    if "config" in gap_line.lower():
        start_gap = float(scale.config["gap"])
    else:
        temp = re.compile("[0-9.]+")
        res = temp.search(gap_line).group(0)
        start_gap = abs(float(res))
    print("Starting gap is {:.2f}mm".format(start_gap))

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
        + "PID_squeeze_flow_1_{:}_{:d}mL_{:d}{:}".format(
            sample_str, round(sample_volume * 1e6), round(target), scale.units
        )
        + "-data.csv"
    )
    with open("data/" + csv_name, "a") as datafile:
        datafile.write(
            "Current Time,Elapsed Time,Current Position (mm),Current Position,Target Position,Current Velocity (mm/s),Current Velocity,Target Velocity,Max Speed,Max Decel,Max Accel,Step Mode,Voltage In (mV),Current Force ({:}),Target Force ({:}),Start Gap (m),Current Gap (m),Viscosity (Pa.s),Yield Stress (Pa),Sample Volume (m^3),Viscosity Volume (m^3), Test Active?, Spread beyond hammer?, Error, K_P, Integrated Error, K_I, Error Derivative, K_D\n".format(
                scale.units, scale.units
            )
        )


def load_cell_thread():
    """Continuously reads load cell and reports the upward force on the load cell"""
    global force, dt_force, error, der_error, int_error, decay_rate, decay_rate_r

    start_time = time()

    for i in range(10):  # get rid of first few lines that aren't readings
        scale.get_line()
    scale.flush_old_lines()  # and get rid of any others that were generated when we were busy setting up

    old_error = error
    """Error from previous frame, used for derivative & integral calculation"""

    cur_time = time()
    prev_time = cur_time

    while True:
        force = scale.wait_for_calibrated_measurement(True) * FORCE_UP_SIGN

        prev_time = cur_time
        cur_time = time()
        dt_force_old = dt_force
        dt_force = cur_time - prev_time

        older_error = old_error
        old_error = error
        error = target - force
        # int_error = int_error * decay_rate
        int_error = int_error * math.exp(decay_rate_r * dt_force)
        int_error += (
            ((old_error + error) / 2 * dt_force) if dt_force > 0 else 0
        )  # trapezoidal integration
        der_error = (
            ((error - old_error) / dt_force) if dt_force > 0 else 0
        )  # first order backwards difference
        # der_error = (
        #     (
        #         (2 * dt_force + dt_force_old)
        #         / (dt_force * (dt_force + dt_force_old))
        #         * error
        #         + -(dt_force + dt_force_old) / (dt_force * dt_force_old) * old_error
        #         + dt_force / (dt_force_old**2 * dt_force * dt_force_old) * older_error
        #     )
        #     if (dt_force > 0 and dt_force_old > 0)
        #     else 0
        # )  # second order backwards difference

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
    global gap, eta_guess, error, int_error, der_error, sample_volume, test_active, spread_beyond_hammer, visc_volume, yield_stress_guess, dt_force

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    # Energize Motor
    print("Energizing")
    actuator.energize()
    print("Exiting safe start")
    actuator.exit_safe_start()

    approach_velocity = -1  # mm/s, speed to approach bath of fluid at
    force_threshold = 0.6  # g, force must exceed this for control system to kick in.
    max_force = 80  # g, if force greater than this, stop test.

    backoff_velocity = 1  # mm/s

    # upper_limit = -100
    # lower_limit = -start_gap * 100

    # K_P = 0.04
    # """Proportional control coefficient for error in grams to speed in mm/s"""
    # K_I = 0.015
    # K_D = 0.0005

    # Start by approaching and waiting until force is non-negligible
    actuator.set_vel_mms(approach_velocity)
    while True:
        # print("{:6.2f} <? {:6.2f}".format(force, force_threshold))
        actuator.heartbeat()
        if abs(force) > max_force:
            test_active = False
            actuator.go_home_quiet_down()
            break
        if abs(force) > force_threshold:
            test_active = True
            break
        # print("{:6.2f} >=? {:6.2f}".format(get_pos_mm(), start_gap))
        if abs(actuator.get_pos_mm()) >= start_gap:
            print("Hit the hard-stop without ever exceeding threshold force, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

        # reset integrated error - prevent integral windup
        int_error = 0
    print("Force threshold met, switching over to force-velocity control.")

    gap = (actuator.get_pos_mm() + start_gap) / 1000.0  # m

    a = K_P
    b = 0.002
    c = 50
    d = 0.01
    # variable_K_P = lambda er: (b + a) / 2 - (b - a) / 2 * math.tanh(
    #     c * (abs(er / target) - d)
    # )
    a = 0.07
    b = 0.015
    c = 50
    d = 0.1**2
    variable_K_P = lambda er: (a + b) / 2 + (a - b) / 2 * math.tanh(
        c * ((er / target) ** 2 - d)
    )

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
        if abs(actuator.get_pos_mm()) >= start_gap:
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
        gap = (actuator.get_pos_mm() + start_gap) / 1000.0  # m

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
                force_N = OpenScale.grams_to_N(force)
                eta_guess = abs(
                    2
                    * math.pi
                    * gap**5
                    * force_N
                    / 3
                    / visc_volume**2
                    / (actuator.get_vel_mms() / 1000)
                )  # Pa.s
                yield_stress_guess = abs(
                    3
                    * math.sqrt(math.pi)
                    * gap**2.5
                    * force_N
                    / 2
                    / visc_volume**1.5
                )
        except:
            eta_guess = 0
            yield_stress_guess = 0

        # Prevent integral windup
        if abs(int_error) > 1000:
            int_error = 1000 * math.copysign(1000, int_error)

        # vel_P = -K_P * target * error
        vel_P = -variable_K_P(error) * 10 * error
        """Proportional component of velocity response"""
        vel_I = -K_I * 10 * int_error
        """Integral component of velocity response"""
        vel_D = -K_D * 10 * der_error
        """Derivative component of velocity response"""
        v_new = vel_P + vel_D + vel_I
        v_new = min(v_new, 0)  # Only go downward
        actuator.set_vel_mms(v_new)

        out_str = "{:6.2f}{:}, err = {:6.2f}, errI = {:6.2f}, errD = {:7.2f}, pos = {:6.2f}, v = {:11.5f} : vP = {:6.2f}, vI = {:6.2f}, vD = {:6.2f}, dt = {:6.2f}".format(
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
            dt_force,
        )

        if error < 0:
            out_str += " go slower"
        elif error > 0:
            out_str += " go faster"
        else:
            out_str += " maintain speed"

        print(out_str)
        actuator.heartbeat()


def background():
    """Records data to csv"""
    global actuator, start_gap, test_active, spread_beyond_hammer, visc_volume, error, int_error, der_error, yield_stress_guess

    start_time = time()
    while True:
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
        gap = (cur_pos_mm + start_gap) / 1000.0  # set gap whether or not test is active

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
                start_gap / 1000.0,
                gap,
                eta_guess,
                yield_stress_guess,
                sample_volume,
                visc_volume,
                test_active,
                spread_beyond_hammer,
                error,
                K_P,
                int_error,
                K_I,
                der_error,
                K_D,
            ]
            dataline = ",".join(map(str, output_params)) + "\n"
            datafile.write(dataline)
            # print(dataline)

        times.append(cur_duration)
        forces.append(force)
        gaps.append(gap)

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

max_time_window = 30
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
ax2 = ax1.twinx()

color1 = "C0"
color2 = "C1"


def animate(i):
    global ax1, ax2, times, forces, gaps
    ax1.clear()
    ax2.clear()

    # Throw away data & timestamps that are too old.
    # while times[-1] - times[0] > max_time_window:
    #     times.pop(0)
    #     forces.pop(0)
    #     gaps.pop(0)

    timesTemp = times[:]
    forcesTemp = forces[:]
    gapsTemp = gaps[:]

    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Force [g]", color=color1)
    ax2.set_ylabel("Gap [mm]", color=color2)

    ax1.plot(timesTemp, forcesTemp, color1, label="Force")
    ax2.plot(timesTemp, [1000 * g for g in gapsTemp], color2, label="Gap")
    plt.xlim(min(timesTemp), max(max(timesTemp), max_time_window))
    plt.title("Sample: {:}".format(sample_str))

    ax1.set_ylim((0, max(2 * target, max(forcesTemp))))
    ax2.set_ylim((0, 1000 * max(gapsTemp)))

    # Color y-ticks
    ax1.tick_params(axis="y", colors=color1)
    ax2.tick_params(axis="y", colors=color2)

    # Color y-axes
    ax1.spines["left"].set_color(color1)
    ax2.spines["left"].set_alpha(0)  # hide second left y axis to show first one
    ax2.spines["right"].set_color(color2)


ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
