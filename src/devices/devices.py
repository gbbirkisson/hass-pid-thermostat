import logging
import sys

from ds18b20 import DS18B20
from gpiozero import LED

from devices.switch import SSR
from devices.thermometer import Thermometer


def create_DS18B20_all_thermometers(mqtt, error_sensor=None):
    sensors_ids = DS18B20.get_available_sensors()

    if len(sensors_ids) == 0:
        raise Exception('No temp sensor detected')

    logging.info('Found sensors %s' % sensors_ids)

    return [create_DS18B20_thermometer(mqtt, i, error_sensor) for i in sensors_ids]


def create_DS18B20_thermometer(mqtt, DS18B20_id, error_sensor=None):
    sensor = DS18B20(DS18B20_id)
    last_value = [sensor.get_temperature()]

    def _read_temp():
        try:
            last_value[0] = sensor.get_temperature()
        except:
            if error_sensor is not None:
                error_sensor.register_error(
                    "Could not read temperature on sensor '{}': {}".format(sensor.get_id(), sys.exc_info()[0]))
        return last_value[0]

    return Thermometer(mqtt, sensor.get_id(), _read_temp, error_sensor)


def create_ssr(mqtt, pin, error_sensor=None):
    led = LED(pin)

    def _set_state(s):
        try:
            led.value = s
        except:
            if error_sensor is not None:
                error_sensor.register_error(
                    "Could not set pin value '{}': {}".format(s, led, sys.exc_info()[0]))

    return SSR(mqtt, _set_state)
