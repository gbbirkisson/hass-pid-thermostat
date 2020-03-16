import atexit
import logging
import signal
import sys
import time
import traceback

from devices.devices import create_ssr, create_DS18B20_all_thermometers
from devices.devices_fake import create_fake_ssr, create_fake_thermostat
from devices.errors import create_error_sensor
from devices.hvac import create_hvac
from devices.thermometer import create_average_thermometer, create_weighted_average_thermometer
from hass.components import Manager
from hass.mqtt import Mqtt
from utils import env, env_bool

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

RUN = True


def kill(*args):
    global RUN
    RUN = False


signal.signal(signal.SIGINT, kill)
signal.signal(signal.SIGTERM, kill)
atexit.register(kill)


def ssr_and_thermometers(mqtt, error_sensor):
    if SIMULATE:
        return create_fake_ssr(mqtt), [
            create_fake_thermostat(mqtt, '01144e89cbaa'),
            create_fake_thermostat(mqtt, '01144e806daa'),
            create_fake_thermostat(mqtt, '000008fb871f')
        ]
    else:
        return create_ssr(mqtt, env('SSR_PIN', 'GPIO18'), error_sensor), create_DS18B20_all_thermometers(mqtt,
                                                                                                         error_sensor)


def run(m, h):
    global RUN
    while RUN:
        try:
            time.sleep(0.5)
            h.apply_controller()
            m.send_updates()
        except:  # catch *all* exceptions
            traceback.print_exc(file=sys.stdout)
            kill()


if __name__ == "__main__":
    logging.info('Create component manager')
    manager = Manager()

    with Mqtt(mqtt_host=MQTT_HOST, mqtt_username=MQTT_USER, mqtt_password=MQTT_PASS) as mqtt:
        logging.info('Create error sensor')
        error_sensor = create_error_sensor(mqtt)
        manager.add(error_sensor)

        logging.info('Create SSR and thermometers')
        ssr, thermometers = ssr_and_thermometers(mqtt, error_sensor)
        manager.add(ssr)
        manager.add(thermometers, send_updates=True)

        logging.info('Create average thermometer')
        therm_avg = create_average_thermometer(mqtt, thermometers)
        manager.add(therm_avg, send_updates=True)

        logging.info('Create weight average thermometer')
        therm_weight_avg = create_weighted_average_thermometer(mqtt, thermometers)
        manager.add(therm_weight_avg, send_updates=True)

        logging.info('Create hvac')
        hvac = create_hvac(mqtt, ssr, therm_weight_avg)
        manager.add(hvac, send_updates=True)

        with manager:
            logging.info('Run controller')
            run(manager, hvac)
