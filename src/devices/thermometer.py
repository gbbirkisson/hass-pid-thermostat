import logging
import sys

from ds18b20 import DS18B20

from hass.components import Sensor, Cover


def create_DS18B20_all_thermometers(mqtt, error_sensor=None):
    sensors_ids = DS18B20.get_available_sensors()

    if len(sensors_ids) == 0:
        raise Exception('No temp sensor detected')

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


def create_average_thermometers(mqtt, thermometers):
    average = AverageThermometer(mqtt, thermometers)
    w_average = WeightedAverageThermometer(mqtt,
                                           [(t, ThermometerWeight(mqtt, 'weight_{}'.format(t.get_name()))) for t in
                                            thermometers])
    return [average, w_average]


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


class ThermometerWeight(Cover):
    def __init__(self, mqtt, name, position=5):
        super().__init__(mqtt, name, 0, 10)
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
    def __init__(self, mqtt, thermometers_and_weights):
        super().__init__(mqtt, 'temp_average_weighted', '°C')
        self._thermometers = thermometers_and_weights

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
