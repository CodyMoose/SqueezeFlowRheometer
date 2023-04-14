import openscale

scale = openscale.OpenScale()

while True:
    weight = scale.get_calibrated_measurement()
    if weight is None:  # if startup garbage not gone yet
        continue
    print("{:.2f}{:}".format(weight, scale.units))
