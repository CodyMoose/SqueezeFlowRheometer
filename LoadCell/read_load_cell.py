import openscale

scale = openscale.OpenScale()

while True:
    weight = scale.wait_for_calibrated_measurement()
    if weight is None:  # if startup garbage not gone yet
        continue
    print("{:6.2f}{:}".format(weight, scale.units))
