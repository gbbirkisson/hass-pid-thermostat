import atexit
import logging
import signal
import time

from devices.devices_fake import create_fake_ssr, create_fake_thermostat
from devices.errors import create_error_sensor
from devices.hvac import create_hvac
from devices.sensors import create_pid_sensor
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


def ssr_and_thermometers_fake(mqtt):
    return create_fake_ssr(mqtt), [create_fake_thermostat(mqtt, 'fake')]


with Mqtt(mqtt_host='localhost') as mqtt:
    ssr, thermometers = ssr_and_thermometers_fake(mqtt)
    manager = Manager()

    error_sensor = create_error_sensor(mqtt, manager)
    pid_sensors = create_pid_sensor(mqtt, manager)
    controller = create_hvac(mqtt, manager, ssr, thermometers)

    with manager:
        while RUN:
            time.sleep(1)
            manager.send_updates()
