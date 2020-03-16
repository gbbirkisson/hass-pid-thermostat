import atexit
import logging
import signal
import sys
import time
import traceback

from devices.devices_fake import create_fake_ssr, create_fake_thermostat
from devices.errors import create_error_sensor
from devices.hvac import create_hvac
from devices.thermometer import create_average_thermometer, create_weighted_average_thermometer
from hass.components import Manager
from hass.mqtt import Mqtt

logging.basicConfig(level=logging.DEBUG)

RUN = True


def kill(*args):
    global RUN
    RUN = False


signal.signal(signal.SIGINT, kill)
signal.signal(signal.SIGTERM, kill)
atexit.register(kill)


def ssr_and_thermometers(mqtt, error_sensor):
    return create_fake_ssr(mqtt), [create_fake_thermostat(mqtt, 'fake')]


def run(m, h):
    global RUN
    while RUN:
        try:
            time.sleep(1)
            h.apply_controller()
            m.send_updates()
        except:  # catch *all* exceptions
            traceback.print_exc(file=sys.stdout)
            kill()


manager = Manager()

with Mqtt(mqtt_host='localhost') as mqtt:
    # Create error sensor
    error_sensor = create_error_sensor(mqtt)
    manager.add(error_sensor)

    # Create SSR and thermometers
    ssr, thermometers = ssr_and_thermometers(mqtt, error_sensor)
    manager.add(ssr)
    manager.add(thermometers, send_updates=True)

    # Create average thermometer
    therm_avg = create_average_thermometer(mqtt, thermometers)
    manager.add(therm_avg, send_updates=True)

    # Create weight average thermometer
    therm_weight_avg = create_weighted_average_thermometer(mqtt, thermometers)
    manager.add(therm_weight_avg, send_updates=True)

    # Create hvac
    hvac = create_hvac(mqtt, ssr, therm_weight_avg)
    manager.add(hvac, send_updates=True)

    with manager:
        run(manager, hvac)
