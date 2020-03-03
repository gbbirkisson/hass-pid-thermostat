import atexit
import logging
import random
import signal
import time

from hass.components import Manager, Sensor, Switch, Climate, Cover
from hass.mqtt import Mqtt

logging.basicConfig(level=logging.DEBUG)

RUN = True


def kill(*args):
    global RUN
    RUN = False


signal.signal(signal.SIGINT, kill)
signal.signal(signal.SIGTERM, kill)
atexit.register(kill)


class TestSensor(Sensor):
    def __init__(self, mqtt):
        super().__init__(mqtt, 'sensortest', "°C")

    def state_get(self):
        return random.randint(0, 100)


class TestSwitch(Switch):
    def __init__(self, mqtt):
        super().__init__(mqtt, 'switchtest')
        self._on = False

    def state_get(self):
        return self._on

    def state_set(self, state):
        self._on = state


class TestClimate(Climate):
    def __init__(self, mqtt):
        super().__init__(mqtt, 'climatetest', ['off', 'heat', 'cool'])
        self._mode = 'off'
        self._target = 50

    def mode_get(self):
        return self._mode

    def mode_set(self, mode):
        self._mode = mode

    def target_get(self):
        return self._target

    def target_set(self, target):
        self._target = target

    def current_get(self):
        return random.randint(0, 100)


class TestCover(Cover):
    def __init__(self, mqtt):
        super().__init__(mqtt, 'covertest')
        self._pos = 4

    def position_set(self, value):
        self._pos = value

    def position_get(self):
        return self._pos


def create_components(mqtt):
    c = []
    #c.append(TestSensor(mqtt))
    #c.append(TestSwitch(mqtt))
    #c.append(TestClimate(mqtt))
    #c.append(TestCover(mqtt))
    return c


with Mqtt(mqtt_host='localhost') as mqtt:
    components = create_components(mqtt)

    manager = Manager()
    manager.add(components, True)

    with manager:
        while RUN:
            time.sleep(1)
            manager.send_updates()
