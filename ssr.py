import logging
import os

from gpiozero import LED


def get_ssr():
    pin = os.environ.get("SSR_PIN")
    assert pin is not None, "SSR pin is None, set it with env var SSR_PIN"
    ssr = LED(pin)
    is_on = False

    def toggle(on):
        global is_on
        if is_on != on:
            logging.debug("SSR set {}".format("ON" if on else "OFF"))
            is_on = on
            ssr.value(on)

    return toggle
