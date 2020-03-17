import logging

from hass.components import Sensor


def create_error_sensor(manager):
    return ErrorSensor(manager)


class ErrorSensor(Sensor):
    def __init__(self, manager):
        super().__init__(manager, 'errors', ' ', 'mdi:alarm-light')
        self._errors = 0

    def _format_state(self, state):
        return state

    def register_error(self, error):
        self._errors = self._errors + 1
        logging.error(error)

    def state_get(self):
        return self._errors
