import serial
from time import time
import json
import threading
import pytic
# import time
from time import sleep, time
import math
from datetime import datetime

# - Initialization -------------------------------------------

date = datetime.now()
date_str = date.strftime("%Y-%m-%d_%H-%M-%S")
'''timestamp string for experiment start time in yyyy-mm-dd_HH:MM:SS format'''
csv_name =  date_str + "_" + "actuator_load_cell_test_1" + '-data.csv'

weight = 0

with open("LoadCell\config.json","r") as read_file:
	config = json.load(read_file)
	tare = config['tare']
	calibration = config['calibration']
	units = config['units']

def ser_to_reading(serial_line):
	'''Takes in raw serial readline line and returns the raw reading reported in that line'''
	numString = serial_line.decode("utf-8")[:-3] # strips it down to just the actual content
	reading = int(numString)
	return reading

def reading_to_units(reading):
	'''Takes in raw reading and returns calibrated measurement'''
	return (reading - tare)/calibration

def move_to_pos(pos):
	tic.set_target_position(pos)
	while tic.variables.current_position != tic.variables.target_position:
		sleep(0.1)
		tic.reset_command_timeout()

def go_home_quiet_down():
	'''Returns actuator to zero position, enters safe start, de-energizes, and reports any errors'''
	print("Going to zero")
	move_to_pos(0)

	# De-energize motor and get error status
	print("entering safe start")
	tic.enter_safe_start()
	print("deenergizing")
	tic.deenergize()
	print(tic.variables.error_status)

if __name__=='__main__':
	ser = serial.Serial("COM5",115200)

	tic = pytic.PyTic()

	# Connect to first available Tic Device serial number over USB
	serial_nums = tic.list_connected_device_serial_numbers()

	# print(serial_nums)
	tic.connect_to_serial_number(serial_nums[0])

	tic.set_current_limit(576) # set limit to 576mA, right under the 600mA limit for the actuator
	tic.set_max_decel(200000)
	tic.set_max_accel(200000)
	tic.set_max_speed(5000000) # 10mm/s

	# Zero current motor position
	tic.halt_and_set_position(0)
	
	# with open('data/'+csv_name,'a') as datafile:
	# # with open('data/test_file.csv','a') as datafile:
	# 	datafile.write('Current Time, Elapsed Time, Current Position, Target Position, Current Velocity, Target Velocity, Max Speed, Max Decel, Max Accel, Step Mode, Voltage In (mV)\n')

def load_cell_thread():
	'''Handles load cell measurement'''
	global weight

	for i in range(10): # get rid of first few lines that aren't readings
		ser.readline()
	ser.reset_input_buffer() # and get rid of any others that were generated when we were busy setting up

	
	while True:
		reading = int(ser.readline().decode("utf-8")[:-3])
		weight = (reading - tare)/calibration

def actuator_thread():
	'''Drives actuator'''
	
	print("Waiting 2 seconds before starting")
	sleep(2)

	# - Motion Command Sequence ----------------------------------

	# Energize Motor
	print("energizing")
	tic.energize()
	print("exiting safe start")
	tic.exit_safe_start()
	
	move_to_pos(-2000)
		
	down_thresh = -20
	up_thresh = 10
	while True:
		direction = "up" if weight >= up_thresh else ("down" if weight <= down_thresh else "stop")
		print('{:7.2f}{:}: {:}'.format(weight,units,direction))
		sleep(0.05)
		match direction:
			case "up":
				tic.set_target_position(-500)
			case "stop":
				tic.set_target_position(-2000)
			case "down":
				tic.set_target_position(-3500)
		print(tic.variables.target_position)
		print(tic.variables.error_status)
		tic.reset_command_timeout()


def background():
	'''Records data to csv'''
	global tic
	
	start_time = time()
	while True:
		# print(tic)
		# print(tic.variables)
		cur_pos = tic.variables.current_position
		tar_pos = tic.variables.target_position
		cur_vel = tic.variables.current_velocity
		tar_vel = tic.variables.target_velocity
		max_speed = tic.variables.max_speed
		max_decel = tic.variables.max_decel
		max_accel = tic.variables.max_accel
		step_mode = tic.variables.step_mode
		vin_voltage = tic.variables.vin_voltage


		# print("PSU Voltage:{:6.3f}V	Shunt Voltage:{:9.6f}V	Load Voltage:{:6.3f}V	Power:{:9.6f}W	Current:{:9.6f}A".format((bus_voltage2 + shunt_voltage2),(shunt_voltage2),(bus_voltage2),(power2),(current2)/1000))
		#print("")

		with open('data/'+csv_name,'a') as datafile: # write time & current details to csv
		# with open('data/test_file.csv','a') as datafile:
			cur_time = time()
			cur_duration = cur_time - start_time
			dataline = str(cur_time)+","+str(cur_duration)+","+str(cur_pos)+","+str(tar_pos)+","+str(cur_vel)+","+str(tar_vel)+","+str(max_speed)+","+str(max_decel)+","+str(max_accel)+","+str(step_mode)+","+str(vin_voltage)+'\n'
			datafile.write(dataline)
			# print(dataline)
		
		sleep(0.1)

		if (time() - start_time) >= 2000 or ((not lc.is_alive()) and (not ac.is_alive()) and (time() - start_time) > 1):
			print("end of print")
			break
	
	print("="*20 + " BACKGROUND IS DONE " + "="*20)

lc = threading.Thread(name = 'loadcell', target = load_cell_thread)
ac = threading.Thread(name = 'actuator', target = actuator_thread)
b = threading.Thread(name = 'background', target = background)

lc.start()
ac.start()
# b.start()