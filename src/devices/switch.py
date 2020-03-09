import logging
import sys

from gpiozero import LED

from hass.components import Switch


def create_ssr(mqtt, pin, error_sensor=None):
    led = LED(pin)

    def _set_state(s):
        try:
            led.value = s
        except:
            if error_sensor is not None:
                error_sensor.register_error(
                    "Could not set pin value '{}': {}".format(s, led, sys.exc_info()[0]))

    return SSR(mqtt, _set_state)


class SSR(Switch):
    def __init__(self, mqtt, switch_func):
        super().__init__(mqtt, 'ssr')
        self._on = False
        self._switch_func = switch_func

    def state_get(self):
        return self._on

    def state_set(self, state):
        if self._on != state:
            logging.debug('SSR set {}'.format('ON' if self._on else 'OFF'))
            self._on = state
            self._switch_func(state)

    def __call__(self, state):
        self.state_set_and_send(state)


class _Switch:
    def __init__(self, pin):
        self._on = False
        logging.info('SSR will use GPIO pin "{}"'.format(pin))
        self._led = LED(pin)

    def __call__(self, on):
        if self._on != on:
            logging.debug('SSR set {}'.format('ON' if on else 'OFF'))
            self._on = on
            self._led.value = on

    def is_on(self):
        return self._on


def get_switch(pin):
    return _Switch(pin)
