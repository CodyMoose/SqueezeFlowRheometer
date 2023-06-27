import openscale
from time import time, sleep
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib import style
import math
import threading

scale = openscale.OpenScale()

readings = []
times = []
means = []
max_time_window = 7  # how many seconds of readings to store and plot.
start_time = time()

# style.use("fivethirtyeight")
fig = plt.figure()
ax1 = fig.add_subplot(1, 1, 1)
ax2 = ax1.twinx()

color1 = "C0"
color2 = "C1"


def animate(i):
    global ax1, ax2
    ax1.clear()
    ax2.clear()

    # Store data & timestamps locally to prevent race conditions due to multithreading
    timesTemp = times[:]
    readingsTemp = readings[:]
    meansTemp = means[:]
    if len(timesTemp) < 1:
        return

    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("data1 [-]", color=color1)
    ax1.plot(timesTemp, readingsTemp, color1, label="data1")
    ax1.plot(timesTemp, meansTemp, color2, label="Mean")
    plt.xlim(min(timesTemp), max(max(timesTemp), max_time_window))
    # ax2.set_ylabel("data2 [-]", color=color2)
    # ax2.plot(timesTemp, [-2 * r for r in readingsTemp], color2, label="data2")
    # ax1.set_ylim((-11, 11))
    # ax2.set_ylim((-22, 22))
    ax1.tick_params(axis="y", colors=color1)
    ax1.spines["left"].set_color(color1)
    # ax2.tick_params(axis="y", colors=color2)
    # ax2.spines["left"].set_alpha(0)
    # ax2.spines["right"].set_color(color2)


def get_data():
    global readings, times, max_time_window  # , scale
    while True:
        weight = scale.wait_for_calibrated_measurement()

        print("{:6.2f}{:}".format(weight, scale.units))

        # Grab new data & timestamp
        readings.append(weight)
        times.append(time() - start_time)
        means.append(sum(readings) / len(readings))

        # Throw away data & timestamps that are too old. There is definitely a smarter/faster way to do this.
        while times[-1] - times[0] > max_time_window:
            readings.pop(0)
            times.pop(0)
            means.pop(0)


gd = threading.Thread(name="get_data", target=get_data)

gd.start()

ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
