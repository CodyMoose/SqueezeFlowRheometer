import serial
import serial.tools.list_ports as port_list

ports = list(port_list.comports())

for p in ports:
    print(p)
tareReading = 185570
calibrationFactor = -12047.76734

ser = serial.Serial("COM5", 115200)
count = 0
while True:
    line = ser.readline()
    line = line.decode("utf-8")[:-2]  # strips it down to just the line content
    # print(line)
    count += 1
    if count >= 8:
        reading = int(line[:-1])  # trim the comma at the end
        grams = float(reading - tareReading) / float(calibrationFactor)
        # print(reading)
        print(grams)
