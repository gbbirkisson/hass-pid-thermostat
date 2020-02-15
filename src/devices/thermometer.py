import logging

from ds18b20 import DS18B20


def get_thermometers():
    return _Thermometers()


class _Thermometers:
    def __init__(self):
        logging.debug('Getting the temperature sensor')

        sensors_ids = DS18B20.get_available_sensors()

        if len(sensors_ids) == 0:
            raise Exception('No temp sensor detected')

        self._sensors = []
        for id in sensors_ids:
            logging.debug('Adding sensor {}'.format(id))
            self._sensors.append(DS18B20(id))

    def __call__(self):
        res = 0.0
        for t in self._sensors:
            res = res + t.get_temperature()
        return res / len(self._sensors)

    def sensors(self):
        return self._sensors
