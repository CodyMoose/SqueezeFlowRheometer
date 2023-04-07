import serial
from time import time
import json

with open("LoadCell\config.json","r") as read_file:
    config = json.load(read_file)

N = 1000 # number of samples to average
WAIT_TIME = 12 # wait some amount of time before starting to take measurements for taring

total = 0

ser = serial.Serial("COM5",115200)
START_TIME = time()

print("Taking first {:d} seconds to let load cell creep happen. This will lead to a more accurate tare value.".format(WAIT_TIME))
while time() - START_TIME <= WAIT_TIME:
    line = ser.readline().decode("utf-8")[:-2] # remove newline at end
    print(line)
ser.reset_input_buffer() # and clear any extra lines that may have been generated, we don't need them

print("Now recording values for taring")
for i in range(N):
    line = ser.readline().decode("utf-8")
    line = line[:-2] # strips it down to just the line content
    reading = int(line[:-1]) # trim the comma at the end
    print("{:5d}: {:8d}".format(i,reading))
    total += reading

tare = total / N
print("The tare value is {:.2f}".format(tare))

config['tare'] = tare
with open("LoadCell\config.json","w") as write_file:
    json.dump(config, write_file)