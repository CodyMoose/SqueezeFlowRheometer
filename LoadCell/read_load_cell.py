import serial
from time import time
import json
import re

with open("LoadCell\config.json", "r") as read_file:
    config = json.load(read_file)
    tare = config["tare"]
    calibration = config["calibration"]
    units = config["units"]

ser = serial.Serial("COM5", 115200)

for i in range(10):  # ignore the first few lines, they're not data
    line = ser.readline()
ser.reset_input_buffer()  # and clear any extra lines that may have been generated, we don't need them

while True:
    reading = int(ser.readline().decode("utf-8")[:-3])
    weight = (reading - tare) / calibration
    print("{:.2f}{:}".format(weight, units))
