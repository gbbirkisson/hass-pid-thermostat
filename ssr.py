import logging

from gpiozero import LED


class _SSR:

    def __init__(self, pin):
        self._on = False
        self._led = LED(pin)

    def __call__(self, on):
        if self._on != on:
            logging.debug("SSR set {}".format("ON" if on else "OFF"))
            self._on = on
            self._led.value(on)


def get_ssr(pin):
    return _SSR(pin)
