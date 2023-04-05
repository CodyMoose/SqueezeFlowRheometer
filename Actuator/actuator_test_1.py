import pytic
# import time
from time import sleep, time
import math

# - Initialization -------------------------------------------

tic = pytic.PyTic()

def move_to_pos(pos):
	tic.set_target_position(pos)
	while tic.variables.current_position != tic.variables.target_position:
		sleep(0.1)
		tic.reset_command_timeout()

# Connect to first available Tic Device serial number over USB
serial_nums = tic.list_connected_device_serial_numbers()

# print(serial_nums)
tic.connect_to_serial_number(serial_nums[0])

# Load configuration file and apply settings
# tic.settings.load_config('actuator_test_1_config.yml')
# tic.settings.apply()

# - Motion Command Sequence ----------------------------------

# Zero current motor position
tic.halt_and_set_position(0)

# Energize Motor
print("energizing")
tic.energize()
print("exiting safe start")
tic.exit_safe_start()

print("going to zero")
move_to_pos(0)

# tic.go_home(1)
# sleep(10)

# Move to listed positions
positions = [-1000, -2000, -3000, 0]
# for p in positions:
# 	print("moving to: " + str(p))
# 	tic.set_target_position(p)
# 	while tic.variables.current_position != tic.variables.target_position:
# 		# print("Position: current = {:d}, target = {:d}".format(tic.variables.current_position, tic.variables.target_position))
# 		# print("Velocity: current = {:d}".format(tic.variables.current_velocity))
# 		print("Position: current = {:d}, target = {:d},    Velocity: current = {:d}".format(tic.variables.current_position, tic.variables.target_position, tic.variables.current_velocity))
# 		if tic.variables.error_status != 0:
# 			print(tic.variables.error_status)
# 		tic.reset_command_timeout() # you have to give it a heartbeat at least every second
# 		# tic.clear_driver_error()
# 		sleep(0.1)

for p in positions:
	print("moving to: " + str(p))
	move_to_pos(p)

print("Going to center of stroke")
center = -2000
move_to_pos(center)

print("Oscillating for 20 seconds. Should be +/- 5mm in either direction")
osc_mag = -500
osc_start = time()
osc_length = 20
osc_omega = 1
osc_time = time() - osc_start
while osc_time < osc_length: 
	osc_time = time() - osc_start
	osc_pos = osc_mag * math.sin(osc_omega * osc_time) + center
	tic.set_target_position(math.floor(osc_pos))
	tic.reset_command_timeout() # you have to give it a heartbeat at least every second

print("going back to zero")
move_to_pos(0)

# De-energize motor and get error status
print("entering safe start")
tic.enter_safe_start()
print("deenergizing")
tic.deenergize()
print(tic.variables.error_status)