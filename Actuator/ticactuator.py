from pytic import PyTic
from time import sleep
import math


class TicActuator(PyTic):
    """Wrapper for existing pytic package, but with useful helper functions to allow operations in coherent units"""

    def __init__(
        self, step_size: float = 0.01, step_mode: int = 0, current_limit: int = 576
    ):
        """Handler for actuator operations, includes helper fucntions to enable using coherent units

        Args:
            step_size (float, optional): Size of actuator's full step in mm. Defaults to 0.01.
            step_mode (int, optional): Microstepping mode. Defaults to 0 (full steps).
            current_limit (int, optional): Current limit in mA. Defaults to 576.
        """
        super().__init__()

        # Connect to first available Tic Device serial number over USB
        serial_nums = self.list_connected_device_serial_numbers()
        self.connect_to_serial_number(serial_nums[0])

        if self.get_variable_by_name("vin_voltage") < 7000:
            input("Wait! You didn't turn the power on for the actuator! Do that now.")

        self.step_size = step_size  ## mm/step
        self.microstep_ratio = 1

        self.my_set_step_mode(
            step_mode
        )  # have to use own method because the superclass sets its own attributes on super().__init__()
        self.set_current_limit(current_limit)

    def steps_to_mm(self, val: float) -> float:
        """Converts microsteps to mm

        Args:
            val (float): value in microsteps

        Returns:
            float: corresponding value in mm
        """
        val_mm = val / self.microstep_ratio * self.step_size
        return val_mm

    def mm_to_steps(self, val_mm: float) -> float:
        """Converts mm to microsteps

        Args:
            val_mm (float): value in mm

        Returns:
            float: value in microsteps
        """
        val = val_mm * self.microstep_ratio / self.step_size
        return val

    def get_pos(self) -> int:
        """Gets current actuator position in microsteps

        Returns:
                float: current actuator position in microsteps
        """
        pos = None
        while pos is None:
            try:
                pos = self.get_variable_by_name("current_position")
            except:
                pos = None
            else:
                break
        return pos

    def get_pos_mm(self) -> float:
        """Gets current actuator position in mm

        Returns:
                float: current actuator position in mm
        """
        pos = self.steps_to_mm(self.get_pos())
        return pos

    def move_to_pos(self, pos: int):
        """Moves actuator to desired position, finishes when the actuator reaches the target

        Args:
                pos (int): target position in steps from zero
        """
        self.set_target_position(pos)
        while self.get_pos() != self.get_variable_by_name("target_position"):
            sleep(0.05)
            self.reset_command_timeout()

    def move_to_mm(self, pos_mm: float) -> int:
        """Moves actuator to desired position in mm

        Args:
                pos_mm (float): desired position in mm

        Returns:
                int: corresponding position in actuator's units, steps
        """
        pos = math.floor(self.mm_to_steps(pos_mm))
        self.move_to_pos(pos)
        return pos

    def mms_to_vel(self, vel_mms: float) -> int:
        """Converts velocity in mm/s to actuator units of steps/10,000s

        Args:
            vel_mms (float): velocity in mm/s

        Returns:
            int: velocity in actuator units of steps/10,000s
        """
        vel = math.floor(self.mm_to_steps(vel_mms) * 10000)
        return vel

    def vel_to_mms(self, vel: int) -> float:
        """Converts velocity in actuator units of steps/10,000s to mm/s

        Args:
            vel (int): velocity in actuator units of steps/10,000s

        Returns:
            float: velocity in mm/s
        """
        vel_mms = self.steps_to_mm(vel) / 10000
        return vel_mms

    def get_vel(self) -> int:
        """Gets current actuator velocity in microsteps/10,000s

        Returns:
                float: current actuator velocity in microsteps/10,000s
        """

        vel = None
        while vel is None:
            try:
                vel = self.get_variable_by_name("current_velocity")
            except:
                vel = None
            else:
                break
        return vel

    def get_vel_mms(self) -> float:
        """Gets current actuator velocity in mm/s

        Returns:
                float: current actuator velocity in mm/s
        """

        vel_mms = self.vel_to_mms(self.get_vel())
        return vel_mms

    def set_vel_mms(self, vel_mms: float) -> int:
        """Sets actuator target velocity in mm/s

        Args:
                vel_mms (float): the desired velocity in mm/s

        Returns:
                int: velocity in the actuator's units, steps/10,000s
        """
        vel = self.mms_to_vel(vel_mms)
        self.set_target_velocity(vel)
        return vel

    def set_max_speed_mms(self, max_speed_mms: float) -> int:
        """Sets actuator maximum speed in mm/s

        Args:
            max_speed_mms (float): the desired max speed in mm/s

        Returns:
            int: max speed in the actuator's units, steps/10,000s
        """
        max_speed = self.mms_to_vel(max_speed_mms)
        self.set_max_speed(max_speed)
        return max_speed

    def mmss_to_accel(self, accel_mmss: float) -> int:
        """Converts acceleration in mm/s^2 to actuator units of steps/100s/s

        Args:
            accel_mmss (float): acceleration in mm/s^2

        Returns:
            int: acceleration in actuator units of steps/100s/s
        """
        accel = math.floor(self.mm_to_steps(accel_mmss) * 100)
        return accel

    def set_max_accel_mmss(
        self, max_accel_mmss: float, also_set_decel: bool = False
    ) -> int:
        """Sets actuator maximum acceleration in mm/s^2. Also sets decel if desired

        Args:
            max_accel_mmss (float): the desired max accelerartion in mm/s^2
            also_set_decel (bool, optional): whether or not to also set deceleration. Defaults to False.

        Returns:
            int: max acceleration in the actuator's units, steps/100s/s
        """
        max_accel = self.mmss_to_accel(max_accel_mmss)
        self.set_max_accel(max_accel)
        if also_set_decel:
            self.set_max_decel(max_accel)
        return max_accel

    def set_max_decel_mmss(self, max_decel_mmss: float) -> int:
        """Sets actuator maximum deceleration in mm/s^2

        Args:
            max_accel_mmss (float): the desired max decelerartion in mm/s^2

        Returns:
            int: max deceleration in the actuator's units, steps/100s/s
        """
        max_decel = self.mmss_to_accel(max_decel_mmss)
        self.set_max_accel(max_decel)
        return max_decel

    def my_set_step_mode(self, step_mode: int = 0) -> int:
        """Sets actuator's fractional stepping mode

        Args:
            step_mode (int, optional): Microstepping mode. Defaults to 0 (full steps).

        Returns:
            int: Number of microsteps per full step
        """
        if step_mode < 0:
            return self.microstep_ratio
        self.set_step_mode(step_mode)
        self.microstep_ratio = 2 ** self.get_variable_by_name("step_mode")
        return self.microstep_ratio

    def heartbeat(self):
        """Resets command timeout back to 1 second. Call this at least every second to prevent actuator stopping.
        Alias for reset_command_timeout() because heartbeat is easier to remember.
        """
        self.reset_command_timeout()

    def go_home_quiet_down(self):
        """Returns actuator to zero position, enters safe start, de-energizes, and reports any errors"""
        print("Going to zero")
        self.move_to_pos(0)

        # De-energize motor and get error status
        print("Entering safe start")
        self.enter_safe_start()
        print("Deenergizing")
        self.deenergize()
        print(self.get_variable_by_name("error_status"))

    def get_variable_by_name(self, name: str):
        """Gets actuator variables and keeps trying until success

        Args:
            name (str): name of variable to retrieve

        Returns:
            _type_: the value of the variable that was requested, type may vary
        """
        var = None
        while var is None:
            try:
                var = getattr(self.variables, name)
            except:
                var = None
            else:
                break
        return var

    def startup(self):
        """Energizes actuator and exits safe start"""
        print("Energizing actuator")
        self.energize()
        print("Exiting safe start")
        self.exit_safe_start()
