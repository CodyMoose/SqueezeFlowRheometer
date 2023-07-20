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
csv_name = date_str + "_" + "retraction" + "-data.csv"

HAMMER_RADIUS = 25e-3  # m
HAMMER_AREA = math.pi * HAMMER_RADIUS**2  # m^2

force = 0
"""Current force reading. Negative is a force pushing up on the load cell"""
FORCE_UP_SIGN = 1
"""Sign of an upward force. This should be 1 or -1"""
start_gap = 0
"""Initial distance (mm) away from hard stop."""
approach_gap = 0
"""The gap to start retraction from."""
gap = 0
"""Current gap (m) between hammer and hard stop"""
sample_volume = 0
"""Amount of sample (m^3)"""
visc_volume = 0
"""Volume used for viscosity computations. Will be less than total sample if spread beyond hammer."""
test_active = False
"""Whether or not the test is active. Should be true after force threshold is met but before test ends"""
spread_beyond_hammer = False
"""Whether or not the sample has spread beyond the hammer. This will happen if gap gets too thin."""
sample_str = ""
"""What the sample is made of. Used in filename."""

times = []
forces = []
gaps = []

settings = {}


if __name__ == "__main__":
    scale = OpenScale()

    # Input test values from external settings file
    settings_path = "Retraction/retraction_settings.json"
    with open(settings_path, "r") as read_file:
        settings = json.load(read_file)

    # Get test details from user
    start_gap = sfr.input_start_gap(scale)
    sample_volume = sfr.input_sample_volume()
    approach_gap = sfr.input_retract_start_gap(sample_volume, settings)
    retract_speed = sfr.input_retract_speed(settings)
    sample_str = input("What's the sample made of? This will be used for file naming. ")

    # # Get test details from settings file & config file
    # start_gap = float(scale.config["gap"])
    # approach_gap = float(settings["retract_gap_mm"])
    # retract_speed = float(settings["retract_speed_mms"])
    # sample_str = float(settings["sample_str"])

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
        + "retraction_{:}_{:d}mL_{:d}mm_{:d}mms".format(
            sample_str,
            round(sample_volume * 1e6),
            round(approach_gap),
            round(retract_speed),
        )
        + "-data.csv"
    )

    # Make sure the data folder as well as the figures folder exists before trying to save anything there
    Path("data/Figures/{:}".format(date.strftime("%Y-%m-%d"))).mkdir(
        parents=True, exist_ok=True
    )

    with open("Retraction/data/" + csv_name, "a") as datafile:
        datafile.write(
            "Current Time,Elapsed Time,Current Position (mm),Current Position,Target Position,Current Velocity (mm/s),Current Velocity,Target Velocity,Max Speed,Max Decel,Max Accel,Step Mode,Voltage In (mV),Current Force ({:}),Start Gap (m),Current Gap (m),Sample Volume (m^3),Viscosity Volume (m^3), Test Active?, Spread beyond hammer?\n".format(
                scale.units
            )
        )


def load_cell_thread():
    """Continuously reads load cell and reports the upward force on the load cell"""
    global force

    start_time = time()

    for _ in range(10):  # get rid of first few lines that aren't readings
        scale.get_line()
    scale.flush_old_lines()  # and get rid of any others that were generated when we were busy setting up

    while True:
        force = scale.wait_for_calibrated_measurement(True) * FORCE_UP_SIGN

        if (time() - start_time) >= 7200 or (
            (not ac.is_alive()) and (not bkg.is_alive()) and (time() - start_time) > 1
        ):
            print("Stopping load cell reading")
            break


def actuator_thread():
    """Drives actuator"""
    global test_active, times, gaps, forces

    print("Waiting 2 seconds before starting")
    sleep(2)

    # - Motion Command Sequence ----------------------------------

    actuator.startup()

    approach_velocity = settings["approach_max_speed_mms"]
    max_force = 80  # g, if force greater than this, stop test.

    # Start by approaching and waiting until force is non-negligible
    actuator.set_max_speed_mms(approach_velocity)

    retract_start_pos = -start_gap + approach_gap
    print("Moving to start position of {:.1f}mm".format(retract_start_pos))
    actuator.move_to_mm(retract_start_pos)

    actuator.heartbeat()

    pause_time = settings["pause_time_at_gap"]
    print("Reached start position. Pausing for {:d} second(s).".format(pause_time))

    actuator.set_max_speed_mms(retract_speed)
    for i in range(0, int(pause_time / 0.1)):
        actuator.heartbeat()
        sleep(0.1)
        actuator.heartbeat()

    # Now that test is about to start, throw away most of the pre-test data.
    data_keep_time = 2  # how many seconds to keep
    data_rate = 10  # roughly how many datapoints I record per second
    keep_datapoints = data_keep_time * data_rate  # how many datapoints to keep
    if len(times) > keep_datapoints:
        # only throw away points if they're older than data_keep_time
        times = times[-keep_datapoints:]
        forces = forces[-keep_datapoints:]
        gaps = gaps[-keep_datapoints:]

    actuator.heartbeat()

    # Start the test
    print("Starting retraction.")
    test_active = True
    print(actuator.get_pos_mm())
    actuator.move_to_mm(0)
    print(actuator.get_pos_mm())
    test_active = False
    print("Retraction complete.")


def background():
    """Records data to csv"""
    global actuator, start_gap, test_active, spread_beyond_hammer, visc_volume

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
                start_gap / 1000.0,
                gap,
                sample_volume,
                visc_volume,
                test_active,
                spread_beyond_hammer,
            ]
            dataline = ",".join(map(str, output_params)) + "\n"
            datafile.write(dataline)
            # print(dataline)

        times.append(cur_duration)
        forces.append(force)
        gaps.append(gap)

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
fig = plt.figure(figsize=(7.2, 4.8))
ax1 = fig.add_subplot(1, 1, 1)
ax2 = ax1.twinx()

color1 = "C0"
color2 = "C1"
color3 = "C2"


def animate(i):
    global ax1, ax2, times, forces, gaps

    if len(times) <= 0:
        return

    ax1.clear()
    ax2.clear()

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

    ax1.set_ylim((min(forcesTemp), max(forcesTemp)))
    ax2.set_ylim((0, 1000 * max(gapsTemp)))

    # Color y-ticks
    ax1.tick_params(axis="y", colors=color1)
    ax2.tick_params(axis="y", colors=color2)

    # Color y-axes
    ax1.spines["left"].set_color(color1)
    ax2.spines["left"].set_alpha(0)  # hide second left y axis to show first one
    ax2.spines["right"].set_color(color2)

    ax1.grid(True)
    ax2.grid(False)

    # plt.axis("tight")


ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
