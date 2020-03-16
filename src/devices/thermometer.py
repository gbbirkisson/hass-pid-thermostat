from devices import call_children
from hass.components import Sensor, SettableSensor


def create_average_thermometer(mqtt, thermometers):
    return AverageThermometer(mqtt, thermometers)


def create_weighted_average_thermometer(mqtt, thermometers):
    return WeightedAverageThermometer(mqtt, thermometers)


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


class ThermometerWeight(SettableSensor):
    def __init__(self, mqtt, name):
        super().__init__(mqtt, name, 0, 50, 200)


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
    def __init__(self, mqtt, thermometers):
        super().__init__(mqtt, 'temp_average_weighted', '°C')
        self._thermometers = []
        for t in thermometers:
            weight = ThermometerWeight(mqtt, 'weight_{}'.format(t.get_name()))
            self._thermometers.append((t, weight))

    def state_get(self):
        values = [therm.state_get() for therm, weight in self._thermometers]
        weights = [weight.state_get() for therm, weight in self._thermometers]

        res = 0.0
        res_bak = 0.0

        for x, y in zip(values, weights):
            res_bak = x
            res += x * y

        # If all weights are 0, just return average
        sum_weights = sum(weights)
        if sum_weights == 0:
            return res_bak / len(weights)

        return res / sum_weights

    def available(self, new_available):
        call_children([w for _, w in self._thermometers], 'available', new_available)
        super().available(new_available)

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
