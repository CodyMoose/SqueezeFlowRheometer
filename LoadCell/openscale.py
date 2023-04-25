import serial
from time import time
import json
import re


class OpenScale:
    def __init__(self):
        self.ser = serial.Serial("COM5", 115200)
        self.config_path = "LoadCell\config.json"
        self.outlier_threshold = (
            100  # g, if a measurement is beyond this limit, throw it out
        )

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
        numString = serial_line.decode("utf-8")[:-3]  # just get the actual content
        try:
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
        return reading

    def get_calibrated_measurement(self) -> float:
        """Grabs the next serial line and returns the calibrated measurement

        Returns:
            float: force measurement in units chosen during calibration
        """
        return self.reading_to_units(self.get_reading())

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
            if abs(meas) > self.outlier_threshold:
                meas = None
        return meas

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

        print("Now recording values for taring")
        for i in range(N):
            # reading = self.get_reading()
            reading = self.wait_for_reading()
            print("{:5d}: {:8d}".format(i, reading))
            total += reading

        tare_value = total / N
        print("The tare value is {:.2f}".format(tare_value))

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

        for i in range(N):
            # reading = self.get_reading()
            reading = self.wait_for_reading()
            print("{:5d}: {:8d}".format(i, reading))
            total += reading - self.tare_value

        average = total / N
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
            print("{:.2f}{:}".format(weight, units))

        return calibration
