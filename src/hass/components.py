import time

from hass.hass import Hass
from utils import env


def component_info(postfix=None):
    cid = env('COMPONENT_ID', 'brew')
    if postfix is not None:
        cid = cid + "_" + postfix
    return cid, cid.replace('_', ' ')


class Manager:
    def __init__(self):
        self._send_updates = []
        self._all = []

    def add(self, c, send_updates=False):
        if type(c) is list:
            self._all = self._all + c
            if send_updates:
                self._send_updates = self._send_updates + c
        else:
            self._all.append(c)
            if send_updates:
                self._send_updates.append(c)

    def send_updates(self):
        for component in self._send_updates:
            component.state_send()

    def __enter__(self):
        for component in self._all:
            component.__enter__()

        time.sleep(1)  # Give home assistant a chance to catch up

        for component in self._all:
            component.available = True

        for component in self._all:
            component.on_connect()

    def __exit__(self, *args):
        for component in self._all:
            component.__enter__()


class _Base(Hass):
    def __init__(self, mqtt=None, component=None, name=None):
        cid, cname = component_info(name)
        super().__init__(mqtt=mqtt, object_id=cid, component=component)

        self._available = True

        self._TOPIC_AVAIL = self.get_topic('available')

        self._config = {
            'name': cname,
            'availability_topic': self._TOPIC_AVAIL,
            'payload_available': 'online',
            'payload_not_available': 'offline',
        }

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, new_available):
        self._available = new_available
        self.publish(self._TOPIC_AVAIL, 'online' if self._available else 'offline')

    def state_send(self):
        raise NotImplemented

    def on_connect(self):
        pass


class Sensor(_Base):
    def __init__(self, mqtt, name, unit_of_measurement):
        super().__init__(mqtt=mqtt, component='sensor', name=name)

        self._TOPIC_STATE = self.get_topic('state')

        self._config.update({
            'state_topic': self._TOPIC_STATE,
            'unit_of_measurement': unit_of_measurement,
        })

    def state_send(self):
        self.publish(self._TOPIC_STATE, self.state_get())

    def state_get(self):
        raise NotImplementedError


class Switch(_Base):
    def __init__(self, mqtt, name):
        super().__init__(mqtt=mqtt, component='switch', name=name)

        self._TOPIC_STATE = self.get_topic('state')
        self._TOPIC_CMD_SET = self.get_topic('cmdSet')

        self._config.update({
            'state_topic': self._TOPIC_STATE,
            'command_topic': self._TOPIC_CMD_SET,
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'state_on': 'ON',
            'state_off': 'OFF'
        })

        self.subscribe(self._TOPIC_CMD_SET, lambda new_state: self.state_set_and_send(new_state == 'ON'))

    @staticmethod
    def parse_state(state):
        return 'ON' if state else 'OFF'

    def state_send(self):
        self.publish(self._TOPIC_STATE, self.parse_state(self.state_get()))

    def state_get(self):
        raise NotImplementedError

    def state_set(self, state):
        raise NotImplementedError

    def state_set_and_send(self, state):
        self.state_set(state)
        self.state_send()


class Climate(_Base):
    def __init__(self, mqtt, name, modes):  # ['off', 'heating', 'cooling']
        super().__init__(mqtt=mqtt, component='climate', name=name)

        self._TOPIC_STATE_MODE = self.get_topic('stateMode')
        self._TOPIC_STATE_TARGET = self.get_topic('stateTargetTemp')
        self._TOPIC_STATE_CURRENT = self.get_topic('stateCurrentTemp')

        self._TOPIC_CMD_MODE = self.get_topic('cmdMode')
        self._TOPIC_CMD_TEMP = self.get_topic('cmdTargetTemp')

        self._config.update({
            'mode_state_topic': self._TOPIC_STATE_MODE,
            'temperature_state_topic': self._TOPIC_STATE_TARGET,
            'current_temperature_topic': self._TOPIC_STATE_CURRENT,
            'mode_command_topic': self._TOPIC_CMD_MODE,
            'temperature_command_topic': self._TOPIC_CMD_TEMP,
            'min_temp': '0',
            'max_temp': '100',
            'temp_step': '1',
            'modes': modes
        })

        self.subscribe(self._TOPIC_CMD_MODE, lambda new_mode: self.mode_set_and_send(new_mode))
        self.subscribe(self._TOPIC_CMD_TEMP, lambda new_temp: self.target_set_and_send(new_temp))

    def mode_send(self):
        self.publish(self._TOPIC_STATE_MODE, self.mode_get())

    def mode_get(self):
        raise NotImplementedError

    def mode_set(self, mode):
        raise NotImplementedError

    def mode_set_and_send(self, mode):
        self.mode_set(mode)
        self.mode_send()

    def target_send(self):
        self.publish(self._TOPIC_STATE_TARGET, self.target_get())

    def target_get(self):
        raise NotImplementedError

    def target_set(self, target):
        raise NotImplementedError

    def target_set_and_send(self, target):
        self.target_set(target)
        self.target_send()

    def current_get(self):
        raise NotImplementedError

    def state_send(self):
        self.publish(self._TOPIC_STATE_CURRENT, self.current_get())

    def on_connect(self):
        self.mode_set_and_send('off')
        self.target_set_and_send(self.current_get())


class Cover(_Base):
    def __init__(self, mqtt, name, min=0, max=100):
        super().__init__(mqtt=mqtt, component='cover', name=name)

        self._TOPIC_STATE = self.get_topic('state')
        self._TOPIC_CMD_SET = self.get_topic('cmdSet')

        self._config.update({
            'position_topic': self._TOPIC_STATE,
            'set_position_topic': self._TOPIC_CMD_SET,
            'position_closed': min,
            'position_open': max,
            'optimistic': False,
            'retain': True,
            'qos': 1
        })

        self.subscribe(self._TOPIC_CMD_SET, lambda new_value: self.position_set(new_value))

    def position_set(self, value):
        raise NotImplementedError

    def position_get(self):
        raise NotImplementedError

    def state_send(self):
        self.publish(self._TOPIC_STATE, self.position_get())