import logging

from hass.components import Sensor


def create_error_sensor(mqtt, manager):
    e = ErrorSensor(mqtt)
    manager.add(e, send_updates=False)
    return e


class ErrorSensor(Sensor):
    def __init__(self, mqtt):
        super().__init__(mqtt, 'errors', 'errors')
        self._errors = 0

    def _format_state(self, state):
        return state

    def register_error(self, error):
        self._errors = self._errors + 1
        logging.error(error)
        self.state_send()

    def state_get(self):
        return self._errors
