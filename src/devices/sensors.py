import math
import time

from devices import call_children
from hass.components import Sensor


def create_pid_sensor(manager):
    p = Generic(manager, 'p', ' ')
    i = Generic(manager, 'i', ' ')
    d = Generic(manager, 'd', ' ')
    percent_on = Generic(manager, 'percent_on', '%', 'mdi:power-socket-eu')
    return PidSensor(p, i, d, percent_on)


def create_estimator(manager):
    return EstimateTarget(manager, 'minutes_to_target')


class Generic(Sensor):
    def __init__(self, manager, name, unit_of_measurement, icon=None):
        super().__init__(manager, name, unit_of_measurement, icon=icon)
        self._state = 0.0

    def _format_state(self, state):
        return state

    def state_get(self):
        return self._state

    def state_set(self, state):
        self._state = state


class PidSensor:
    def __init__(self, p, i, d, percent_on):
        self._p = p
        self._i = i
        self._d = d
        self._percent_on = percent_on
        self._children = [self._p, self._i, self._d, self._percent_on]

    def __call__(self, p, i, d, percent_on):
        self._p.state_set(p)
        self._i.state_set(i)
        self._d.state_set(d)
        self._percent_on.state_set(percent_on)

    def on_connect(self):
        call_children(self._children, 'on_connect')

    def __enter__(self):
        call_children(self._children, '__enter__')
        return self

    def __exit__(self, *args):
        call_children(self._children, '__exit__', *args)


class EstimateTarget(Sensor):
    def __init__(self, manager, name):
        super().__init__(manager, name, 'minutes', 'mdi:clock')
        self._est_array = []
        self._est = 0
        self._reset()

    def _reset(self):
        self._est_array = []
        self._est = 999

    def _format_state(self, state):
        return int(state)

    def calculate_estimate(self, hvac):
        if hvac.mode_get() == 'off':
            self._reset()
            return

        if abs(hvac.target_get() - hvac.current_get()) < 1:
            self._est = 0
            return

        self._est_array.append((time.monotonic(), hvac.current_get()))

        if len(self._est_array) < 2:
            return

        if len(self._est_array) > 5:
            _, *tail = self._est_array
            self._est_array = tail

        res = 0
        for i in range(0, len(self._est_array) - 1):
            res += (self._est_array[i + 1][1] - self._est_array[i][1]) / (
                    self._est_array[i + 1][0] - self._est_array[i][0])
        res = res / (len(self._est_array) - 1) * 60
        if res != 0:
            res = (hvac.target_get() - hvac.current_get()) / res
        self._est = math.ceil(abs(res))

    def state_get(self):
        return self._est
