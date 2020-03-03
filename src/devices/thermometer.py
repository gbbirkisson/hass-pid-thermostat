import logging

from ds18b20 import DS18B20

from hass.components import Sensor, Cover


class Thermometer(Sensor):
    def __init__(self, mqtt, id):
        super().__init__(mqtt, 'temp_' + id.lower(), '°C')
        self._therm = DS18B20(id)

    def id_get(self):
        return self._therm.get_id()

    def state_get(self):
        return self._therm.get_temperature()


class ThermometerWeight(Cover):
    def __init__(self, mqtt, id, position=100):
        super().__init__(mqtt, id, 0, 200)
        self._position = position

    def position_set(self, value):
        self._position = value

    def position_get(self):
        return self._position

    def multiplier(self):
        return self._position / 100


class AverageThermometer(Sensor):
    def __init__(self, mqtt, thermometers):
        super().__init__(mqtt, 'temp_average', '°C')
        self._thermometers = thermometers

    def state_get(self):
        res = 0.0
        for t in self._thermometers:
            res = res + t.state_get()
        return res / len(self._thermometers)


class WeightedAverageThermometer(Sensor):
    def __init__(self, mqtt, thermometers_weights):
        super().__init__(mqtt, 'temp_average_weighted', '°C')
        self._thermometers = thermometers_weights

    def state_get(self):
        values = [therm.state_get() for therm, weight in self._thermometers]
        weights = [weight.multiplier() for therm, weight in self._thermometers]

        res = 0.0
        for x, y in zip(values, weights):
            res += x * y

        return res / sum(self._thermometers)


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
