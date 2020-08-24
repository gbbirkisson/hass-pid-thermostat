def cpu_temp():
    with open('/sys/class/thermal/thermal_zone0/temp', 'r') as f:
        for line in f:
            return float(line.strip()) / 1000
    return None
