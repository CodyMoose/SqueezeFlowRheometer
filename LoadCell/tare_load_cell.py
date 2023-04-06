import serial
from time import time
import json

with open("LoadCell\config.json","r") as read_file:
    config = json.load(read_file)

N = 1000.0 # number of samples to average
WAIT_TIME = 120 # wait some amount of time before starting to take measurements for taring

total = 0

ser = serial.Serial("COM5",115200)
START_TIME = time()

while time() - START_TIME <= WAIT_TIME:
    line = ser.readline()
for i in range(N):
    line = line.decode("utf-8")[:-2] # strips it down to just the line content
    reading = int(line[:-1]) # trim the comma at the end
    total += reading

tare = total / N
print("The tare value is {:.2f}".format(tare))

config['tare'] = tare
with open("LoadCell\config.json","w") as write_file:
    json.dump(config, write_file)