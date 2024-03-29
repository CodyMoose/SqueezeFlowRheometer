import serial
from time import time
import json
import re
import numpy as np
import matplotlib.pyplot as plt
import math


class OpenScale:
    OLD_READING_KEEP_AMOUNT = 2
    """How many old readings to keep"""
    OUTLIER_JUMP_THRESHOLD = 10
    """The maximum acceptable jump in grams between two force readings"""

    def __init__(self):
        self.ser = serial.Serial("COM5", 115200)
        self.config_path = "LoadCell\config.json"
        self.outlier_threshold = (
            100  # g, if a measurement is beyond this limit, throw it out
        )

        self.old_readings = [None] * (
            OpenScale.OLD_READING_KEEP_AMOUNT + 1
        )  # also have to store current value

        try:
            with open(self.config_path, "r") as read_file:
                self.config = json.load(read_file)
                self.tare_value = self.config["tare"]
                self.calibration = self.config["calibration"]
                self.units = self.config["units"]
        except:
            self.config = {}

    def flush_old_lines(self):
        """Clears existing serial buffer"""
        self.ser.reset_input_buffer()

    def get_line(self) -> bytes:
        """Grabs the next line of serial input from the OpenScale

        Returns:
            bytes: next line from OpenScale
        """
        return self.ser.readline()

    def ser_to_reading(serial_line: bytes) -> int:
        """Takes in serial line and returns raw reading reported therein

        Args:
                serial_line (bytes): a line of load cell serial input

        Returns:
                int: the load cell reading in that line
        """
        try:
            numString = serial_line.decode("utf-8")[:-3]  # just get the actual content
            reading = int(numString)
            return reading
        except:
            print(serial_line)
            return None

    def reading_to_units(self, reading: int) -> float:
        """Takes in raw load cell reading and returns calibrated measurement

        Args:
                reading (int): raw value from load cell input

        Raises:
            Exception: If load cell has not been calibrated, cannot give a calibrated measurement.

        Returns:
                float: calibrated measurement in units the load cell is calibrated to
        """

        if (
            ("tare" not in self.config)
            or ("calibration" not in self.config)
            or ("units" not in self.config)
        ):
            raise Exception(
                "Load cell has not been calibrated, cannot report a calibrated measurement."
            )
        if reading == None:
            return None
        return (reading - self.tare_value) / self.calibration

    def get_reading(self) -> int:
        """Grabs the next serial line and returns the reading

        Returns:
            int: raw reading from OpenScale
        """
        return OpenScale.ser_to_reading(self.get_line())

    def wait_for_reading(self) -> int:
        reading = None
        while reading is None:
            reading = self.get_reading()

        self.old_readings.pop(0)
        self.old_readings.append(self.reading_to_units(reading))
        return reading

    def get_calibrated_measurement(self) -> float:
        """Grabs the next serial line and returns the calibrated measurement

        Returns:
            float: force measurement in units chosen during calibration
        """
        meas = self.reading_to_units(self.get_reading())
        self.old_readings.pop(0)
        self.old_readings.append(meas)
        return meas

    def wait_for_calibrated_measurement(self, non_outlier: bool = True) -> float:
        """Waits for the next valid reading and returns the calibrated measurement

        Args:
            non_outlier (bool, optional): Whether to wait for a force within a reasonable margin. Defaults to True.

        Returns:
            float: force measurement in units chosen during calibration
        """
        meas = None
        while meas is None:
            meas = self.reading_to_units(self.wait_for_reading())
            if self.check_if_outlier(
                meas
            ):  # if it's too far from all of the previous readings
                meas = None
        return meas

    def check_if_outlier(self, measurement: float) -> bool:
        """Checks if a measurement is too far from any of the previous stored values.

        Args:
            measurement (float): _description_

        Returns:
            bool: True if it's an outlier (too far from prior measurements), False if it's a real measurement
        """
        return not any(
            [
                (
                    (old is not None)  # make sure we're comparing to an actual value
                    and (
                        abs(measurement - (old if old is not None else 0))
                        <= OpenScale.OUTLIER_JUMP_THRESHOLD
                    )
                )
                for old in self.old_readings[
                    0:-1
                ]  # don't include current reading, which is the last one in the list
            ]
        )  # if it's too far from any of the previous readings

    def grams_to_N(f: float) -> float:
        """Takes in force in grams and converts to Newtons

        Args:
                f (float): force in grams

        Returns:
                float: force in Newtons
        """
        return 0.00980665 * f

    def tare(self, wait_time: int = 120, N: int = 1000) -> float:
        """Performs taring of the load cell. Saves tare value

        Args:
            wait_time (int, optional): Time to wait for load cell creep to occur. Defaults to 120.
            N (int, optional): Number of samples to average over. Defaults to 1000.

        Returns:
            float: tare value - the average reading when the load cell has no force applied
        """

        total = 0

        print(
            "Taking first {:d} seconds to let load cell creep happen. This will lead to a more accurate tare value.".format(
                wait_time
            )
        )
        START_TIME = time()
        while time() - START_TIME <= wait_time:
            remaining = wait_time - (time() - START_TIME)
            line = self.get_line()
            print("{:5.1f}: {:}".format(remaining, line))
        self.flush_old_lines()  # and clear any extra lines that may have been generated, we don't need them

        readings = [0] * N
        print("Now recording values for taring")
        for i in range(N):
            try:
                reading = self.wait_for_reading()
            except:
                pass  # I don't care if the load cell hasn't yet been calibrated when I'm taring
            readings[i] = reading
            print("{:5d}: {:8d}".format(i, reading))

        # Throw out top 1% and bottom 1%
        remove_rate = 0.01
        readings_sorted = sorted(readings)
        readings = readings_sorted[
            math.floor(remove_rate * N) : math.floor((1 - remove_rate) * N)
        ]
        print(
            "Keeping the middle {:.0%} of samples to remove outliers due to noise".format(
                1 - 2 * remove_rate
            )
        )

        # tare_value = total / N
        tare_value = sum(readings) / len(readings)
        print("The tare value is {:.2f}".format(tare_value))

        reading_std = np.std(readings)
        max_reading = max(readings)
        min_reading = min(readings)
        print(
            "min: {:}, max: {:}, standard dev: {:}".format(
                min_reading, max_reading, reading_std
            )
        )
        readings_over = sorted(i for i in readings if i >= tare_value + reading_std)
        readings_under = sorted(
            (i for i in readings if i <= tare_value - reading_std), reverse=True
        )
        print(
            "Number over 1std: {:}, Number under 1std: {:}, total outside 1std: {:}".format(
                len(readings_over),
                len(readings_under),
                len(readings_over) + len(readings_under),
            )
        )
        print(
            "Number within 1std: {:}".format(
                len(readings) - len(readings_over) - len(readings_under)
            )
        )
        # print(readings_over)
        # print(readings_under)
        plt.hist(sorted(np.array(readings) - tare_value), 50)
        plt.xlabel("Deviation from the mean")
        plt.ylabel("Number of samples")
        plt.title("Middle {:.0%} of readings".format(1 - 2 * remove_rate))
        plt.show()

        self.config["tare"] = tare_value
        with open(self.config_path, "w") as write_file:
            json.dump(self.config, write_file)

        self.tare_value = tare_value
        return tare_value

    def calibrate(
        self, tare_first: bool = False, N: int = 1000, report_duration: int = 10
    ) -> float:
        """Performs calibration of load cell

        Args:
            N (int, optional): Number of samples to average over. Defaults to 1000.
            report_duration (int, optional): Amount of time to report values after calibration is complete. Defaults to 10.

        Returns:
            float: _description_
        """
        if (
            ("tare" not in self.config)
            or ("calibration" not in self.config)
            or ("units" not in self.config)
        ):
            print("Load cell has not been tared, will now perform taring.")
            tare_first = True
        if tare_first:
            input(
                "Please remove any weights you had placed. Press enter to being taring process."
            )
            self.tare(N=N)
            print("Taring complete. Now to calibrate.")

        total = 0

        # Have the user place the calibration weight and ask what the weight is
        print("Please place the calibration weight(s).")
        cal_weight_str = input(
            "Enter the total calibration weight with units (ex: 50g): "
        )

        cal_weight_str = cal_weight_str.replace(" ", "")  # filter out spaces

        # separate weight from units
        temp = re.compile("([0-9.]+)([a-zA-Z]+)")
        res = temp.match(cal_weight_str).groups()
        cal_weight = abs(float(res[0]))
        units = res[1]
        self.config["units"] = units

        for i in range(10):  # ignore the first few lines, they're not data
            self.get_line()
        self.flush_old_lines()  # and clear any extra lines that may have been generated, we don't need them

        readings = [0] * N
        for i in range(N):
            # reading = self.get_reading()
            reading = self.wait_for_reading() - self.tare_value
            readings[i] = reading
            print("{:5d}: {:10.1f}".format(i, reading))
            total += reading - self.tare_value

        # Throw out top 1% and bottom 1%
        remove_rate = 0.01
        readings_sorted = sorted(readings)
        readings = readings_sorted[
            math.floor(remove_rate * N) : math.floor((1 - remove_rate) * N)
        ]
        print(
            "Keeping the middle {:.0%} of samples to remove outliers due to noise".format(
                1 - 2 * remove_rate
            )
        )

        # average = total / N
        average = sum(readings) / len(readings)
        print("The calibration average is {:.2f}".format(average))

        reading_std = np.std(readings)
        max_reading = max(readings)
        min_reading = min(readings)
        print(
            "min: {:}, max: {:}, standard dev: {:}".format(
                min_reading, max_reading, reading_std
            )
        )
        readings_over = sorted(i for i in readings if i >= average + reading_std)
        readings_under = sorted(
            (i for i in readings if i <= average - reading_std), reverse=True
        )
        print(
            "Number over 1std: {:}, Number under 1std: {:}, total outside 1std: {:}".format(
                len(readings_over),
                len(readings_under),
                len(readings_over) + len(readings_under),
            )
        )
        print(
            "Number within 1std: {:}".format(
                len(readings) - len(readings_over) - len(readings_under)
            )
        )
        # print(readings_over)
        # print(readings_under)
        plt.hist(sorted(np.array(readings) - average), 50)
        plt.xlabel("Deviation from the mean")
        plt.ylabel("Number of samples")
        plt.title("Middle {:.0%} of readings".format(1 - 2 * remove_rate))
        plt.show()

        calibration = -average / cal_weight
        self.config["calibration"] = calibration
        with open(self.config_path, "w") as write_file:
            json.dump(self.config, write_file)

        print("The calibration value is {:.2f}".format(calibration))
        input(
            "You should now change the weights. For the next 10 seconds, I will print out the weight I am measuring. Press enter to begin."
        )
        self.flush_old_lines()

        START_TIME = time()
        while time() - START_TIME <= report_duration:
            # reading = int(ser.readline().decode("utf-8")[:-3])
            # weight = -(reading - self.tare_value) / calibration
            weight = -self.get_calibrated_measurement()
            weight = -self.wait_for_calibrated_measurement()
            if weight is None:  # if startup garbage not gone yet
                continue
            print("{:6.2f}{:}".format(weight, units))

        return calibration

    def check_tare(self):
        """Check if load cell is within tare, otherwise tare it."""
        weight = self.wait_for_calibrated_measurement(True)
        if abs(weight) > 0.5:
            ans = input(
                "The load cell is out of tare! Current reading is {:.2f}{:}. Do you want to tare it now? (y/n) ".format(
                    weight, self.units
                )
            )
            if ans == "y":
                self.tare()
