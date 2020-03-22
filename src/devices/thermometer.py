from devices import call_children
from hass.components import Sensor, SettableSensor
from utils import env, env_int, func_wrapper


def _get_name(name):
    return env('OVERRIDE_NAME_' + name.upper(), name)


def _get_weight(name, default):
    return env_int(name.upper(), default)


def create_average_thermometer(manager, thermometers):
    return AverageThermometer(manager, thermometers)


def create_weighted_average_thermometer(manager, thermometers):
    return WeightedAverageThermometer(manager, thermometers)


class Thermometer(Sensor):
    def __init__(self, manager, name, read_func):
        self._name = _get_name(name).lower()
        self._therm = read_func
        super().__init__(manager, 'temp_' + self._name, '°C')

    # noinspection PyBroadException
    def state_get(self):
        return self._therm()

    def get_name(self):
        return self._name

    def __call__(self, *args, **kwargs):
        return self.state_get()


class ThermometerWeight(SettableSensor):
    def __init__(self, manager, name):
        super().__init__(manager, name, 0, _get_weight(name, 100), 200)


class AverageThermometer(Sensor):
    def __init__(self, manager, thermometers):
        super().__init__(manager, 'temp_average', '°C', icon='mdi:thermometer-lines')
        self._thermometers = thermometers

        self.state_get = func_wrapper.wrap(self.state_get)

    def state_get(self):
        res = 0.0
        for t in self._thermometers:
            res = res + t.state_get()
        return res / len(self._thermometers)

    def __call__(self, *args, **kwargs):
        return self.state_get()


class WeightedAverageThermometer(Sensor):
    def __init__(self, manager, thermometers):
        super().__init__(manager, 'temp_average_weighted', '°C', icon='mdi:thermometer-lines')
        self._thermometers = []
        for t in thermometers:
            weight = ThermometerWeight(manager, 'weight_{}'.format(t.get_name()))
            self._thermometers.append((t, weight))

        self.state_get = func_wrapper.wrap(self.state_get)

    def state_get(self):
        values = [therm.state_get() for therm, weight in self._thermometers]
        weights = [weight.state_get() for therm, weight in self._thermometers]

        res = 0.0

        for x, y in zip(values, weights):
            res += x * y

        # If all weights are 0, just return average
        sum_weights = sum(weights)
        if sum_weights == 0:
            return sum(values) / len(values)

        return res / sum_weights

    def on_connect(self):
        call_children([w for _, w in self._thermometers], 'on_connect')
        super().on_connect()

    def __enter__(self):
        call_children([w for _, w in self._thermometers], '__enter__')
        return super().__enter__()

    def __exit__(self, *args):
        call_children([w for _, w in self._thermometers], '__exit__', *args)
        super().__exit__(*args)

    def __call__(self, *args, **kwargs):
        return self.state_get()
