import logging

from ds18b20 import DS18B20
from gpiozero import LED
from ha_mqtt.util import env

from devices.spi import SpiTempSensor


def create_temp_sensors():
    sensors = [SpiTempSensor(0, 0)]
    for s in DS18B20.get_available_sensors():
        sensors.append(DS18B20(s))
    return sensors


def create_ssr(error_sensor):
    led = LED(env('SSR_PIN', 'GPIO18'))

    def _set_state(s):
        try:
            led.value = s
        except:
            error_sensor.count()
            logging.error("Error in setting SSR", exc_info=True)

    return _set_state
