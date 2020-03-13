import logging

from ds18b20 import DS18B20

from hass.components import Sensor, Cover


def create_average_thermometer(mqtt, manager, thermometers):
    t = AverageThermometer(mqtt, thermometers)
    manager.add(t, send_updates=True)
    return t


def create_weighted_average_thermometer(mqtt, manager, thermometers):
    pairs = []
    for thermometer in thermometers:
        weight = ThermometerWeight(mqtt, 'weight_{}'.format(thermometer.get_name()))
        manager.add(weight, send_updates=False)
        pairs.append((thermometer, weight))
    t = WeightedAverageThermometer(mqtt, pairs)
    manager.add(t, send_updates=True)
    return t


class Thermometer(Sensor):
    def __init__(self, mqtt, name, read_func):
        self._name = name.lower()
        self._therm = read_func
        super().__init__(mqtt, 'temp_' + self._name, '°C')

    # noinspection PyBroadException
    def state_get(self):
        return self._therm()

    def get_name(self):
        return self._name

    def __call__(self, *args, **kwargs):
        return self.state_get()


class ThermometerWeight(Cover):
    def __init__(self, mqtt, name, position=5):
        self._position = position
        super().__init__(mqtt, name, 0, 10)

    def position_set(self, value):
        self._position = value * 1.0

    def position_get(self):
        return self._position

    def multiplier(self):
        return self._position


class AverageThermometer(Sensor):
    def __init__(self, mqtt, thermometers):
        super().__init__(mqtt, 'temp_average', '°C')
        self._thermometers = thermometers

    def state_get(self):
        res = 0.0
        for t in self._thermometers:
            res = res + t.state_get()
        return res / len(self._thermometers)

    def __call__(self, *args, **kwargs):
        return self.state_get()


class WeightedAverageThermometer(Sensor):
    def __init__(self, mqtt, thermometers_and_weights):
        super().__init__(mqtt, 'temp_average_weighted', '°C')
        self._thermometers = thermometers_and_weights

    def state_get(self):
        values = [therm.state_get() for therm, weight in self._thermometers]
        weights = [weight.multiplier() for therm, weight in self._thermometers]

        res = 0.0
        for x, y in zip(values, weights):
            res += x * y

        return res / (sum(weights) * 1.0)

    def __call__(self, *args, **kwargs):
        return self.state_get()


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
