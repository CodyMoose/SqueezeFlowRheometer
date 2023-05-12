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
max_time_window = 30  # how many seconds of readings to store and plot.
start_time = time()

# style.use("fivethirtyeight")
fig = plt.figure()
ax = fig.add_subplot(1, 1, 1)


def animate(i):
    global ax
    ax.clear()
    ax.plot(times, readings)


def get_data():
    global readings, times, max_time_window, scale
    while True:
        weight = scale.wait_for_calibrated_measurement()
        if weight is None:  # if startup garbage not gone yet
            continue

        print("{:6.2f}{:}".format(weight, scale.units))
        # weight = 10 * math.sin(time())

        # Grab new data & timestamp
        readings.append(weight)
        times.append(time() - start_time)

        # Throw away data & timestamps that are too old. There is definitely a smarter/faster way to do this.
        while times[-1] - times[0] > max_time_window:
            readings.pop(0)
            times.pop(0)


gd = threading.Thread(name="get_data", target=get_data)

gd.start()

ani = animation.FuncAnimation(fig, animate, interval=10)
plt.show()
