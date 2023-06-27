import openscale
from time import time, sleep
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import math
import numpy as np
import threading

scale = openscale.OpenScale()

readings = []
differences = []

filtered_readings = []
filtered_diffs = []

# style.use("fivethirtyeight")
fig = plt.figure()
ax1 = fig.add_subplot(2, 2, 1)
ax2 = fig.add_subplot(2, 2, 2)
ax3 = fig.add_subplot(2, 2, 3)
ax4 = fig.add_subplot(2, 2, 4)

color1 = "C0"
color2 = "C1"
color3 = "C2"
color4 = "C3"


diffBins = np.logspace(np.log10(0.0001), np.log10(600), 100)
# diffBins = 100


def animate(i):
    global ax1, ax2, ax3, ax4
    ax1.clear()
    ax2.clear()
    ax3.clear()
    ax4.clear()

    # Store data & timestamps locally to prevent race conditions due to multithreading
    readingsTemp = readings[:]
    differencesTemp = differences[:]
    if len(differencesTemp) < 1:
        return

    ax1.set_xlabel("Force [g]")
    ax1.set_ylabel("Number of Readings")
    ax1.hist(readings, 100, color=color1)
    ax1.set_yscale("log")

    ax2.set_xlabel("Difference from last reading [g]")
    ax2.set_ylabel("Number of Readings")
    ax2.hist(differences, diffBins, color=color2)
    ax2.set_xscale("log")
    ax2.set_yscale("log")

    ax3.set_xlabel("Force [g]")
    ax3.set_ylabel("Number of Readings")
    ax3.hist(filtered_readings, 100, color=color3)
    ax3.set_yscale("log")

    ax4.set_xlabel("Difference from last reading [g]")
    ax4.set_ylabel("Number of Readings")
    ax4.hist(filtered_diffs, diffBins, color=color4)
    ax4.set_xscale("log")
    ax4.set_yscale("log")
    fig.suptitle("N = {:}".format(len(readings)))


outlier_threshold = 10


def get_data():
    global readings, differences  # , scale
    while True:
        weight = scale.reading_to_units(scale.wait_for_reading())
        if weight is None:  # if startup garbage not gone yet
            continue

        print("{:6.2f}{:}".format(weight, scale.units))

        # Grab new data & take difference
        readings.append(weight)
        if len(readings) >= 2:
            differences.append(abs(weight - readings[-2]))
            if len(readings) >= 3:
                if (
                    abs(weight - readings[-2]) <= outlier_threshold
                    or abs(weight - readings[-3]) <= outlier_threshold
                ):
                    filtered_readings.append(weight)
                    if len(filtered_readings) >= 2:
                        filtered_diffs.append(weight - filtered_readings[-2])


gd = threading.Thread(name="get_data", target=get_data)

gd.start()

ani = animation.FuncAnimation(fig, animate, interval=50)
plt.show()
