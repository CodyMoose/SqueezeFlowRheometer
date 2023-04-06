import serial
from time import time
import json
import re

with open("LoadCell\config.json","r") as read_file:
    config = json.load(read_file)
    tare = config['tare']

N = 1000.0 # number of samples to average

total = 0

# Have the user place the calibration weight and ask what the weight is
print('Please place the calibration weight(s).')
cal_weight_str = input('Enter the total calibration weight with units (ex: 50g): ')

cal_weight_str = cal_weight_str.replace(' ','') # filter out spaces

# separate weight from units
temp = re.compile("([0-9.]+)([a-zA-Z]+)")
res = temp.match(cal_weight_str).groups()
cal_weight = abs(float(res[0]))
units = res[1]
config['units'] = units

ser = serial.Serial("COM5",115200)

for i in range(10): # ignore the first few lines, they're not data
    line = ser.readline()
ser.reset_input_buffer() # and clear any extra lines that may have been generated, we don't need them

for i in range(N):
    line = ser.readline()
    line = line.decode("utf-8")[:-2] # strips it down to just the line content
    reading = int(line[:-1]) # trim the comma at the end
    total += reading - tare

average = total / N
calibration = -average / cal_weight
print("The calibration value is {:.2f}".format(calibration))
input("You should now change the weights. For the next 10 seconds, I will print out the weight I am measuring. Press enter to begin.")

REPORT_DURATION = 10
START_TIME = time()
while time() - START_TIME <= REPORT_DURATION:
    reading = int(ser.readline().decode("utf-8")[:-3])
    weight = -(reading - tare)/calibration
    print('{:.2f}{:}'.format(weight,units))

config['calibration'] = calibration
with open("LoadCell\config.json","w") as write_file:
    json.dump(config, write_file)