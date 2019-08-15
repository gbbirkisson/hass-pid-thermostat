from ds18b20 import DS18B20


def get_thermometer():
    sensors_ids = DS18B20.get_available_sensors()

    if len(sensors_ids) != 1:
        raise Exception('One and only one sensor should be detected, found {}'.format(sensors_ids))
    sensor = DS18B20(sensors_ids[0])

    return sensor.get_temperature
