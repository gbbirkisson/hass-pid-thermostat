import logging

from gpiozero import LED

from hass.components import Switch


class SSR(Switch):
    def __init__(self, mqtt, pin=None):
        super().__init__(mqtt, 'ssr')
        self._on = False
        self._led = None
        if pin is not None:
            self._led = LED(pin)

    def state_get(self):
        return self._on

    def state_set(self, state):
        if self._on != state:
            logging.debug('SSR set {}'.format('ON' if on else 'OFF'))
            self._on = state
            if self._led is not None:
                self._led.value = state

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