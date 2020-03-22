import atexit
import logging
import signal
import sys
import traceback

from devices.devices import create_ssr, create_DS18B20_all_thermometers
from devices.devices_fake import create_fake_ssr, create_fake_thermostat, create_fake_static_thermostat
from devices.errors import create_error_sensor
from devices.hvac import create_hvac
from devices.sensors import create_estimator
from devices.thermometer import create_average_thermometer, create_weighted_average_thermometer
from hass.components import Manager
from hass.mqtt import Mqtt
from utils import env, env_bool, func_wrapper

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
        return create_fake_ssr(manager), [
            create_fake_thermostat(manager, '01144e89cbaa'),
            create_fake_static_thermostat(manager, '01144e806daa', 68, error_sensor),
            create_fake_static_thermostat(manager, '000008fb871f', 42, error_sensor)
        ]
    else:
        return create_ssr(manager, env('SSR_PIN', 'GPIO18'), error_sensor), create_DS18B20_all_thermometers(mqtt,
                                                                                                            error_sensor)


def run(m, h, est):
    global RUN
    while RUN:
        try:
            h.apply_controller()
            est.calculate_estimate(h)
            func_wrapper.clear()
            m.send_updates()
            # time.sleep(0.2)
        except:  # catch *all* exceptions
            traceback.print_exc(file=sys.stdout)
            kill()


if __name__ == "__main__":
    with Mqtt(mqtt_host=MQTT_HOST, mqtt_username=MQTT_USER, mqtt_password=MQTT_PASS) as mqtt:
        logging.info('Create component manager')
        manager = Manager(mqtt)

        logging.info('Create error sensor')
        error_sensor = create_error_sensor(manager)
        manager.add_component(error_sensor)

        logging.info('Create SSR and thermometers')
        ssr, thermometers = ssr_and_thermometers(manager, error_sensor)
        manager.add_component(ssr)
        manager.add_component(thermometers)

        logging.info('Create average thermometer')
        therm_avg = create_average_thermometer(manager, thermometers)
        manager.add_component(therm_avg)

        logging.info('Create weight average thermometer')
        therm_weight_avg = create_weighted_average_thermometer(manager, thermometers)
        manager.add_component(therm_weight_avg)

        logging.info('Create hvac')
        hvac = create_hvac(manager, ssr, therm_weight_avg)
        manager.add_component(hvac)

        logging.info('Create target estimator')
        est = create_estimator(manager)
        manager.add_component(est)

        with manager:
            logging.info('Run controller')
            run(manager, hvac, est)
