import atexit
import logging
import signal
import time

from devices.switch import get_switch
from devices.thermometer import get_thermometer
from hass.mqtt import Mqtt
from hvac import hvac
from sensor import sensors
from simulation.switch import fake_switch
from simulation.thermostat import FakeThermostat
from switch import switch
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
    pid_switch = fake.switch
    pump_switch = fake_switch('pump')
    thermometer = fake.thermometer
else:
    logging.info('Initializing thermometer')
    thermometer = get_thermometer()

    logging.info('Initializing PID relay')
    pid_switch = get_switch(env('BOIL_ELEMENT_PIN', 'GPIO18'))

    logging.info('Initializing Pump relay')
    pump_switch = get_switch(env('PUMP_ELEMENT_PIN', 'GPIO24'))

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
    with sensors(mqtt) as sensors, switch(mqtt, pid_switch, 'heater') as heater_switch:
        with hvac(mqtt, thermometer, heater_switch, sensors) as hvac, switch(mqtt, pump_switch, 'pump') as pump:
            time.sleep(1)

            heater_switch.available = True
            pump.available = True
            hvac.available = True
            sensors.available = True

            logging.info("Running ...")
            while RUN:
                if hvac.mode == 'off':
                    heater_switch(False)
                elif hvac.mode == 'heat' and hvac.target_temp > 99.0:
                    logging.debug('Temperature target is higher than 99°c on a heater, relay permanently turned on')
                    heater_switch(True)
                elif hvac.mode == 'cool' and hvac.target_temp < 1.0:
                    logging.debug('Temperature target is higher lower than 1°c on a cool, relay permanently turned on')
                    heater_switch(True)
                else:
                    hvac.controller.__next__()

                if send_update:
                    hvac.send_state()

                send_update = not send_update
                time.sleep(1)
