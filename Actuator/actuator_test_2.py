from ticlib import TicUSB

# from src.ticlib import TicUSB
import time

# from time import sleep
import math


def move_to_pos(pos):
    tic.set_target_position(pos)
    tic.reset_command_timeout()
    while tic.get_current_position() != tic.get_target_position():
        time.sleep(0.1)
        tic.reset_command_timeout()


tic = TicUSB()

tic.halt_and_set_position(0)
tic.energize()
tic.exit_safe_start()

print("Now doing set positions the ugly way")
positions = [-500, -300, -800, 0]
for position in positions:
    print("Moving to: {:d}".format(position))
    tic.set_target_position(position)
    tic.reset_command_timeout()
    while tic.get_current_position() != tic.get_target_position():
        time.sleep(0.1)
        tic.reset_command_timeout()

print("Now doing set positions with my function")
for position in positions:
    print("Moving to: {:d}".format(position))
    move_to_pos(position)

print("Going to center of stroke")
center = -2000
move_to_pos(center)
# tic.set_target_position(center)
# while tic.get_current_position() != tic.get_target_position():
# 	time.sleep(0.1)

print("Oscillating for 20 seconds. Should be +/- 5mm in either direction")
osc_mag = -500
osc_start = time.time()
osc_length = 20
osc_omega = 1
cur_time = time.time()
while cur_time - osc_start < osc_length:
    cur_time = time.time()
    osc_pos = math.floor(osc_mag * math.sin(osc_omega * (cur_time - osc_start)))
    tic.set_target_position(osc_pos)
    tic.reset_command_timeout()

print("Going to zero point")
# tic.go_home(1) # move in the positive direction to go home
move_to_pos(0)

tic.deenergize()
tic.enter_safe_start()
