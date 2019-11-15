import atexit
import logging
import signal
import time

from hvac import Hvac, hvac
from devices.ssr import get_ssr
from devices.thermometer import get_thermometer
from hass.mqtt import Mqtt
from simulation.thermostat import FakeThermostat
from utils import env_bool, env


LOG_LEVEL = env('LOG_LEVEL', 'info').lower()
LOG_LEVEL_DICT = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARN,
    'error': logging.ERROR
}
logging.basicConfig(level=LOG_LEVEL_DICT.get(LOG_LEVEL, logging.INFO))

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

with Mqtt(mqtt_host=MQTT_HOST, mqtt_username=MQTT_USER, mqtt_password=MQTT_PASS) as mqtt:
    time.sleep(1)
    with hvac(mqtt, thermometer, ssr) as component:
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
