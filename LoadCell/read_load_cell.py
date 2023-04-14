import openscale

scale = openscale.OpenScale()

while True:
    weight = scale.get_calibrated_measurement()
    print("{:.2f}{:}".format(weight, scale.units))
