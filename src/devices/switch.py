import logging

from gpiozero import LED


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
