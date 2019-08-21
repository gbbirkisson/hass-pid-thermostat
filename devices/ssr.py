import logging

from gpiozero import LED

from utils import env

SSR_PIN = env('SSR_PIN', 'GPIO18')


class _SSR:

    def __init__(self):
        self._on = False
        logging.info('SSR will use GPIO pin "{}"'.format(SSR_PIN))
        self._led = LED(SSR_PIN)

    def __call__(self, on):
        if self._on != on:
            logging.debug('SSR set {}'.format('ON' if on else 'OFF'))
            self._on = on
            self._led.value = on


def get_ssr():
    return _SSR()
