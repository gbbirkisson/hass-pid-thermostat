from devices import call_children
from hass.components import Sensor


def create_pid_sensor(mqtt):
    p = Generic(mqtt, 'p', ' ')
    i = Generic(mqtt, 'i', ' ')
    d = Generic(mqtt, 'd', ' ')
    percent_on = Generic(mqtt, 'percent_on', '%', 'mdi:power-socket-eu')
    return PidSensor(p, i, d, percent_on)


class Generic(Sensor):
    def __init__(self, mqtt, name, unit_of_measurement, icon=None):
        super().__init__(mqtt, name, unit_of_measurement, icon=icon)
        self._state = 0

    def _format_state(self, state):
        return state

    def state_get(self):
        return self._state

    def set_and_send(self, state):
        self._state = state
        self.state_send()


class PidSensor:
    def __init__(self, p, i, d, percent_on):
        self._p = p
        self._i = i
        self._d = d
        self._percent_on = percent_on
        self._children = [self._p, self._i, self._d, self._percent_on]

    def available(self, new_available):
        call_children(self._children, 'available', new_available)

    def __call__(self, p, i, d, percent_on):
        self._p.set_and_send(p)
        self._i.set_and_send(i)
        self._d.set_and_send(d)
        self._percent_on.set_and_send(percent_on)
        
    def on_connect(self):
        call_children(self._children, 'on_connect')

    def __enter__(self):
        call_children(self._children, '__enter__')
        return self

    def __exit__(self, *args):
        call_children(self._children, '__exit__', *args)
