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
        self._update_period = 60  # Every 60 sec
        self._last_update_time = 0
        self._last_update_temp = 0
        self._est = 'NaN'

    def _reset(self):
        self._last_update_time = 0
        self._last_update_temp = 0
        self._est = 'NaN'

    def calculate_estimate(self, hvac):
        if hvac.mode_get() == 'off':
            self._reset()
            return

        new_temp = hvac.current_get()
        target = hvac.target_get()

        if abs(target - new_temp) < 1:
            self._est = 0
            return

        new_time = time.monotonic()

        if self._last_update_time == 0:
            self._last_update_time = new_time
            self._last_update_temp = new_temp
            return

        if (new_time - self._last_update_time) < self._update_period:
            return

        temp_diff_left = target - new_temp
        temp_diff_interval = new_temp - self._last_update_temp
        temp_diff_time = new_time - self._last_update_time

        res = temp_diff_time / temp_diff_interval * temp_diff_left / 60

        # self._last_update_time = new_time
        # self._last_update_temp = new_temp

        self._est = int(math.ceil(abs(res)))

    def _format_state(self, state):
        return state

    def state_get(self):
        return self._est
