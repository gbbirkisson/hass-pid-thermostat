import logging

from hass.components import Sensor


class ErrorSensor(Sensor):
    def __init__(self, mqtt):
        super().__init__(mqtt, 'errors', 'errors')
        self._errors = 0

    def register_error(self, error):
        self._errors = self._errors + 1
        logging.error(error)
        self.state_send()

    def state_get(self):
        return self._errors
