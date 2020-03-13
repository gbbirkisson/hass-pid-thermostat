from hass.components import Sensor


def create_pid_sensor(mqtt, manager):
    p = Generic(mqtt, 'p', ' ')
    i = Generic(mqtt, 'i', ' ')
    d = Generic(mqtt, 'd', ' ')
    percent_on = Generic(mqtt, 'percent_on', '%')

    manager.add(p, send_updates=False)
    manager.add(i, send_updates=False)
    manager.add(d, send_updates=False)
    manager.add(percent_on, send_updates=False)

    return PidSensor(p, i, d, percent_on)


class Generic(Sensor):
    def __init__(self, mqtt, name, unit_of_measurement):
        super().__init__(mqtt, name, unit_of_measurement)
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

    def set(self, p, i, d, percent_on):
        self._p.set_and_send(p)
        self._i.set_and_send(i)
        self._d.set_and_send(d)
        self._percent_on.set_and_send(percent_on)
