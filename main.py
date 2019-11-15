import atexit
import logging
import signal
import time

from component import Component, get_hass
from devices.ssr import get_ssr
from devices.thermometer import get_thermometer
from simulation.thermostat import FakeThermostat
from utils import env_bool, env

logging.basicConfig(level=logging.INFO)

MQTT_HOST = env('MQTT_HOST', 'hassio.local')
MQTT_USER = env('MQTT_USER')
MQTT_PASS = env('MQTT_PASS')
SIMULATE = env_bool('SIMULATE', '0')

if SIMULATE:
    logging.info('Initializing simulation devices')
    fake = FakeThermostat()
    ssr = fake.ssr
    thermometer = fake.thermometer
else:
    logging.info('Initializing thermometer')
    thermometer = get_thermometer()

    logging.info('Initializing SSR')
    ssr = get_ssr()

RUN = True


def kill(*args):
    logging.info("Exiting ...")
    global RUN
    RUN = False


signal.signal(signal.SIGINT, kill)
signal.signal(signal.SIGTERM, kill)
atexit.register(kill)

send_update = True

with get_hass(MQTT_HOST, MQTT_USER, MQTT_PASS) as hass:
    with Component(hass, thermometer, ssr) as component:
        time.sleep(1)
        component.available = True
        logging.info("Running ...")
        while RUN:
            if component.mode == 'off':
                logging.debug('System is disabled, relay will not be turned on')
                ssr(False)
            elif component.mode == 'heat' and component.target_temp > 99.0:
                logging.debug('Temperature target is higher than 99°c on a heater, relay permanently turned on')
                ssr(True)
            elif component.mode == 'cool' and component.target_temp < 1.0:
                logging.debug('Temperature target is higher lower than 1°c on a cool, relay permanently turned on')
                ssr(True)
            else:
                component.controller.__next__()

            if send_update:
                component.send_state()

            send_update = not send_update
            time.sleep(1)
