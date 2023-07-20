import threading
from time import sleep, time
import json
import math
from datetime import datetime
import re
from LoadCell.openscale import OpenScale
from Actuator.ticactuator import TicActuator
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from pathlib import Path
from squeezeflowrheometer import SqueezeFlowRheometer as sfr

# - Initialization -------------------------------------------

date = datetime.now()
date_str = date.strftime("%Y-%m-%d_%H-%M-%S")
"""timestamp string for experiment start time in yyyy-mm-dd_HH:MM:SS format"""
csv_name = date_str + "_" + "PID_squeeze_flow_multistep" + "-data.csv"

HAMMER_RADIUS = 25e-3  # m
HAMMER_AREA = math.pi * HAMMER_RADIUS**2  # m^2


force = 0
"""Current force reading. Negative is a force pushing up on the load cell"""
target = 0
"""Target force. Negative is a force pushing up on the load cell"""
targets = []
"""Monotonically increasing list of target forces. Will run a test on each force, one after the other."""
step_id = 0
"""Which target step the test is currently on. 0 is the first step"""
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

K_P = 0.7
"""Proportional control coefficient for error in grams to speed in mm/s"""
K_I = 0.005
"""Integral control coefficient for integrated error in grams*s to speed in mm/s"""
K_D = 0.000167
"""Derivative control coefficient for error derivative in grams/s to speed in mm/s"""
decay_rate_r = -0.1502
ref_gap = 0

a = 0.7
b = 0.15
c = 50
d = 0.01

default_duration = 250
"""Default length of a test in seconds"""
test_duration = 0
"""User-chosen test length in seconds. Selected during input sequence."""

times = []
forces = []
gaps = []
yieldStressGuesses = []

fig = plt.figure(figsize=(7.2, 4.8))

if __name__ == "__main__":
    scale = OpenScale()

    # Input test values from external settings file
    settings_path = "test_settings.json"
    with open(settings_path, "r") as read_file:
        settings = json.load(read_file)
        K_P = settings["K_P"]
        K_I = settings["K_I"]
        K_D = settings["K_D"]
        decay_rate_r = settings["decay_rate_r"]
        a = settings["a"]
        b = settings["b"]
        c = settings["c"]
        d = settings["d"]
        ref_gap = settings["ref_gap"]
        default_duration = settings["test_duration"]

    # Update variable control parameter based on settings values
    variable_K_P = lambda er, tar: (a + b) / 2 + (a - b) / 2 * math.tanh(
        c * ((er / tar) ** 2 - d)
    )

    # Get test details from user
    targets = sfr.input_targets(scale.units)
    target = targets[step_id]
    start_gap = sfr.input_start_gap(scale)
    test_duration = sfr.input_step_duration(default_duration)
    sample_volume = sfr.input_sample_volume()
    sample_str = input("What's the sample made of? This will be used for file naming. ")

    # # Get test details from settings file & config file
    # targets = settings["targets"]
    # test_duration = settings["test_duration"]
    # sample_str = settings["sample_str"]
    # start_gap = float(scale.config["gap"])

    scale.check_tare()

    actuator = TicActuator(step_mode=settings["actuator_step_mode"])
    actuator.set_max_accel_mmss(settings["actuator_max_accel_mmss"], True)
    actuator.set_max_speed_mms(settings["actuator_max_speed_mms"])

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

    # Make sure the data folder as well as the figures folder exists before trying to save anything there
    Path("data/Figures/{:}".format(date.strftime("%Y-%m-%d"))).mkdir(
        parents=True, exist_ok=True
    )

    with open("data/" + csv_name, "a") as datafile:
        datafile.write(
            "Current Time,Elapsed Time,Current Position (mm),Current Position,Target Position,Current Velocity (mm/s),Current Velocity,Target Velocity,Max Speed,Max Decel,Max Accel,Step Mode,Voltage In (mV),Current Force ({:}),Target Force ({:}),Start Gap (m),Current Gap (m),Viscosity (Pa.s),Yield Stress (Pa),Sample Volume (m^3),Viscosity Volume (m^3), Test Active?, Spread beyond hammer?, Error, K_P, Integrated Error, K_I, Error Derivative, K_D\n".format(
                scale.units, scale.units
            )
        )


def load_cell_thread():
    """Continuously reads load cell and reports the upward force on the load cell"""
    global force, dt_force, error, der_error, int_error, decay_rate_r

    start_time = time()

    for _ in range(10):  # get rid of first few lines that aren't readings
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
        dt_force = cur_time - prev_time

        old_error = error
        error = target - force
        int_error = int_error * math.exp(decay_rate_r * dt_force)
        int_error += (
            ((old_error + error) / 2 * dt_force) if dt_force > 0 else 0
        )  # trapezoidal integration
        der_error = (
            ((error - old_error) / dt_force) if dt_force > 0 else 0
        )  # first order backwards difference

        if (time() - start_time) >= 7200 or (
            (not ac.is_alive()) and (not bkg.is_alive()) and (time() - start_time) > 1
        ):
            print("Stopping load cell reading")
            break


def actuator_thread():
    """Drives actuator"""
    # global gap, eta_guess, error, int_error, der_error, sample_volume, test_active, spread_beyond_hammer, visc_volume, yield_stress_guess, times, gaps, forces
    global error, int_error, der_error, test_active, times, gaps, forces, yieldStressGuesses, target, step_id, ref_gap, fig

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    actuator.startup()

    approach_velocity = -1  # mm/s, speed to approach bath of fluid at
    force_threshold = 0.6  # g, force must exceed this for control system to kick in.
    max_force = 80  # g, if force greater than this, stop test.

    backoff_velocity = 1  # mm/s

    # Start by approaching and waiting until force is non-negligible
    actuator.set_vel_mms(approach_velocity)
    while True:
        actuator.heartbeat()
        if abs(force) > max_force:
            test_active = False
            actuator.go_home_quiet_down()
            break
        if force > force_threshold:
            test_active = True
            break
        if abs(actuator.get_pos_mm()) >= start_gap:
            print("Hit the hard-stop without ever exceeding threshold force, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

        # reset integrated error - prevent integral windup
        int_error = 0

    print("Force threshold met, switching over to force-velocity control.")

    # Now that test is active, throw away most of the pre-test data.
    data_keep_time = 2  # how many seconds to keep
    data_rate = 10  # roughly how many datapoints I record per second
    keep_datapoints = data_keep_time * data_rate  # how many datapoints to keep
    if len(times) > keep_datapoints:
        # only throw away points if they're older than data_keep_time
        times = times[-keep_datapoints:]
        forces = forces[-keep_datapoints:]
        gaps = gaps[-keep_datapoints:]
        yieldStressGuesses = yieldStressGuesses[-keep_datapoints:]

    start_time = time()
    end_test_procedure = False
    step_id = 0
    target = targets[step_id]

    gap_m = (actuator.get_pos_mm() + start_gap) / 1000.0  # current gap in m
    ref_gap = max(
        ref_gap, gap_m
    )  # if sample volume is large, might need to increase the ref gap

    mute_derivative_term_steps = 0
    mute_derivative_term_steps_max = 100
    while True:
        # Check if force beyond max amount
        if abs(force) > max_force:
            print(
                "Force was too large, stopping - {:3.2f}{:}".format(force, scale.units)
            )
            test_active = False
            actuator.go_home_quiet_down()
            return

        # Check if went too far
        cur_pos_mm = actuator.get_pos_mm()
        gap_m = (cur_pos_mm + start_gap) / 1000.0  # current gap in m
        if cur_pos_mm >= start_gap:
            print("Hit the hard-stop, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

        # Check if returned towards zero too far
        if abs(cur_pos_mm) <= 1:
            print("Returned too close to home, stopping.")
            test_active = False
            actuator.go_home_quiet_down()
            return

        if time() - start_time >= test_duration:
            step_id = step_id + 1
            if step_id < len(targets):
                print("Step time limit reached, next step.")
                target = targets[step_id]
                start_time = time()
                mute_derivative_term_steps = mute_derivative_term_steps_max
            else:
                print("Last step complete. Test is done.")
                test_active = False

                # Save fig out before it retracts at end of test
                fig_name = csv_name.replace("-data.csv", "-livePlottedFigure.png")
                fig_path = (
                    "data/Figures/{:}/".format(date.strftime("%Y-%m-%d")) + fig_name
                )
                plt.show()
                plt.draw()
                fig.savefig(fig_path,transparent=True)

                actuator.go_home_quiet_down()
                return

        # Prevent integral windup
        if abs(int_error) > 5:
            #int_error = 1000 * math.copysign(1000, int_error)
            int_error = 0

        # vel_P = -K_P * error
        vel_P = -variable_K_P(error, target) * error
        if abs(error) > 1:
            l_error = 1*error/abs(error)
            vel_P = -variable_K_P(l_error, target) * l_error
        """Proportional component of velocity response"""
        vel_I = -K_I * int_error
        """Integral component of velocity response"""
        vel_D = -K_D * der_error
        """Derivative component of velocity response"""

        if mute_derivative_term_steps > 0:
            mute_derivative_term_steps = mute_derivative_term_steps - 1
            der_error = 0
            vel_D = 0

        # v_new = vel_P + vel_D + vel_I
        v_new = vel_P + vel_I
        # v_new = vel_P
        # v_new = v_new * (gap_m / ref_gap) ** 2.5  # go slower when gap is small
        v_new = v_new * (gap_m / ref_gap) ** 1
        # v_new = min(v_new, 0)  # Only go downward
        actuator.set_vel_mms(v_new)

        out_str = "{:6.2f}{:}, err = {:6.2f}, errI = {:6.2f}, errD = {:7.2f}, gap = {:6.2f}, v = {:11.5f} : vP = {:6.2f}, vI = {:6.2f}, vD = {:6.2f}".format(
            force,
            scale.units,
            error,
            int_error,
            der_error,
            gap_m * 1000,
            v_new,
            vel_P,
            vel_I,
            vel_D,
        )
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

        visc_volume = min(sample_volume, HAMMER_AREA * gap)
        yield_stress_guess = (
            1.5
            * math.sqrt(math.pi)
            * OpenScale.grams_to_N(force)
            * (gap) ** 2.5
            / ((visc_volume) ** 1.5)
        )  # Scott (1935)
        yield_stress_guess = (
            OpenScale.grams_to_N(force) * gap / visc_volume / math.sqrt(3)
        )  # Meeten (2000)

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
                variable_K_P(error, target),
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
        yieldStressGuesses.append(yield_stress_guess)

        sleep(0.02)

        if (time() - start_time) >= 7200 or (
            (not ac.is_alive()) and (time() - start_time) > 1
        ):
            print("Time since started: {:.0f}".format(time() - start_time))
            print("Actuator thread dead? {:}".format(not ac.is_alive()))
            print("end of background")
            break

    print("=" * 20 + " BACKGROUND IS DONE " + "=" * 20)


lc = threading.Thread(name="loadcell", target=load_cell_thread)
ac = threading.Thread(name="actuator", target=actuator_thread)
bkg = threading.Thread(name="background", target=background)

lc.start()
ac.start()
bkg.start()

max_time_window = 30
ax1 = fig.add_subplot(1, 1, 1)
ax2 = ax1.twinx()
ax3 = ax1.twinx()

color1 = "C0"
color2 = "C1"
color3 = "C2"


def animate(i):
    global ax1, ax2, times, forces, gaps, yieldStressGuesses

    if len(times) <= 0:
        return

    ax1.clear()
    ax2.clear()
    ax3.clear()

    # Throw away data & timestamps that are too old.
    # while times[-1] - times[0] > max_time_window:
    #     times.pop(0)
    #     forces.pop(0)
    #     gaps.pop(0)

    timesTemp = times[:]
    forcesTemp = forces[:]
    gapsTemp = gaps[:]
    yieldStressGuessesTemp = yieldStressGuesses[:]

    # print("{:7d}: {:}".format(len(timesTemp), timesTemp[-1] - timesTemp[0]))

    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Force [g]", color=color1)
    ax2.set_ylabel("Gap [mm]", color=color2)
    ax3.set_ylabel("Yield Stress [Pa]", color=color3)

    ax1.plot(timesTemp, forcesTemp, color1, label="Force")
    ax2.plot(timesTemp, [1000 * g for g in gapsTemp], color2, label="Gap")
    ax3.plot(timesTemp, yieldStressGuessesTemp, color3, label="Yield Stress")

    plt.xlim(min(timesTemp), max(max(timesTemp), max_time_window))
    plt.title("Sample: {:}".format(sample_str))

    ax1.set_ylim((-0.5, max(2 * target, max(forcesTemp))))
    ax2.set_ylim((0, 1000 * max(gapsTemp)))

    # Color y-ticks
    ax1.tick_params(axis="y", colors=color1)
    ax2.tick_params(axis="y", colors=color2)
    ax3.tick_params(axis="y", colors=color3)

    # Color y-axes
    ax1.spines["left"].set_color(color1)
    ax2.spines["left"].set_alpha(0)  # hide second left y axis to show first one
    ax2.spines["right"].set_color(color2)
    ax3.spines["left"].set_alpha(0)  # hide third left y axis to show first one
    ax3.spines["right"].set_color(color3)

    # ax3.spines["right"].set_position(
    #     ("axes", 1.1)
    # )  # move it further right to prevent overlap
    ax3.spines["right"].set_position(
        ("outward", 10)
    )  # move it further right to prevent overlap

    ax1.grid(True)
    ax2.grid(False)
    ax3.grid(False)

    # plt.axis("tight")


ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
