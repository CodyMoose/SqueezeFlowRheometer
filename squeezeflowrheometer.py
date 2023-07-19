import re
import math


class SqueezeFlowRheometer:
    def input_targets(scale_unit: str) -> list[float]:
        """Takes in a list of strictly increasing force targets from the user

        Args:
            inp (str): units of the scale calibration to get appropriate user input

        Returns:
            list[float]: list of force targets to run squeeze flow to
        """
        target_list_acceptable = False

        while not target_list_acceptable:
            # Take in values
            targets_string = input(
                "Please give the set of force targets in [{:}] you want to test, separated by commas and/or spaces: ".format(
                    scale_unit
                )
            )
            targets_string = targets_string.replace(
                " ", ","
            )  # convert spaces to commas to ensure succesful separation of values
            targets_str_list = targets_string.split(",")  # split list at commas
            targets_str_list = list(
                filter(None, targets_str_list)
            )  # throw out any empty strings created by a ", " becoming ",," being split into an empty string
            targets_list = [
                float(tar) for tar in targets_str_list
            ]  # parse string to float
            target_list_acceptable = True  # default to assuming the values are fine

            # Catch if it's not strictly increasing
            increasing_bools = [
                targets_list[i] < targets_list[i + 1]
                for i in range(len(targets_str_list) - 1)
            ]
            strictly_increasing = all(increasing_bools)
            if not strictly_increasing:
                print(
                    "The set of forces must be strictly increasing. Every force target must be higher than the previous value."
                )
                target_list_acceptable = False
            print()

        targets_list_printable = ", ".join([str(tar) for tar in targets_list])
        print(
            "The list of target forces in [{:}] is {:}".format(
                scale_unit, targets_list_printable
            )
        )
        return targets_list

    def find_num_in_str(inp: str) -> float:
        """Finds a number in a string potentially containing additional exraneous text

        Args:
            inp (str): input string that contains a number and could have extra whitespace, punctuation, or other

        Returns:
            float: the number contained therein, now parsed as a positive float
        """
        temp = re.compile("[0-9.]+")
        res = temp.search(inp).group(0)
        return abs(float(res))

    def input_start_gap(scale) -> float:
        """Gets start gap in mm from user.

        Returns:
            float: the start gap in mm
        """
        gap_line = input(
            "Enter the current gap in [mm]. If you want to use the gap in the config file, just hit Enter: "
        )
        if "config" in gap_line.lower() or len(gap_line) <= 0:
            gap = float(scale.config["gap"])
        else:
            gap = SqueezeFlowRheometer.find_num_in_str(gap_line)
        print("Starting gap is {:.2f}mm".format(gap))
        return gap

    def input_sample_volume() -> float:
        """Gets sample volume in mL from user

        Returns:
            float: sample volume in mL
        """
        vol_line = input("Enter the sample volume in [mL]: ")
        sample_vol = SqueezeFlowRheometer.find_num_in_str(vol_line) * 1e-6  # m^3
        print("Sample volume is {:.2f}mL".format(sample_vol * 1e6))
        return sample_vol

    def input_step_duration(default_duration) -> float:
        """Gets duration of each step in seconds from user

        Returns:
            float: duration of each step in seconds
        """
        dur_line = input(
            "Enter the duration of each step in seconds. Simply press Enter for the default of {:}s: ".format(
                default_duration
            )
        )
        if "config" in dur_line.lower() or len(dur_line) <= 0:
            step_dur = default_duration
        else:
            step_dur = SqueezeFlowRheometer.find_num_in_str(dur_line)
        print("Test duration is {:.2f}s".format(step_dur))
        return step_dur

    def input_retract_start_gap(sample_volume, settings) -> float:
        """Gets gap to approach to and retract from from the user for a retraction test.

        Returns:
            float: the target gap in mm
        """
        plateDiameter = 0.050  # m
        min_gap = (
            1000 * 4 * sample_volume / (math.pi * plateDiameter**2)
        )  # mm, minimum gap before sample is squeeze beyond the plate
        while True:
            target_gap_line = input(
                "Enter the target gap to retract from in [mm]. If you want to use the gap in the settings file, just hit Enter: "
            )
            if "settings" in target_gap_line.lower() or len(target_gap_line) <= 0:
                target_gap = float(settings["retract_gap_mm"])
            else:
                target_gap = SqueezeFlowRheometer.find_num_in_str(target_gap_line)

            if target_gap < min_gap:
                print(
                    "That gap is too small! The sample will squeeze out past the edge of the plate. Try a gap larger than {:.2f}".format(
                        min_gap
                    )
                )
            else:
                break
        print("Target gap is {:.2f}mm".format(target_gap))
        return target_gap

    def input_retract_speed(settings) -> float:
        """Gets retraction speed from the user for a retraction experiment.

        Returns:
            float: the target retraction speed in mm/s
        """
        target_speed_line = input(
            "Enter the retraction speed in [mm/s]. If you want to use the speed in the settings file, just hit Enter: "
        )
        if "settings" in target_speed_line.lower() or len(target_speed_line) <= 0:
            target_speed = abs(float(settings["retract_speed_mms"]))
        else:
            target_speed = abs(SqueezeFlowRheometer.find_num_in_str(target_speed_line))
        print("Retraction speed is {:.1f}mm/s".format(target_speed))
        return target_speed
