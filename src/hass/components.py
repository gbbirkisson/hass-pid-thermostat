import time

from hass.hass import Hass, DISCOVERY_PREFIX
from utils import env


def component_info(postfix=None):
    cid = env('COMPONENT_ID', 'brew')
    if postfix is not None:
        cid = cid + "_" + postfix
    return cid, cid.replace('_', ' ')


class SharedTopic:
    def __init__(self, mqtt, topic):
        self._mqtt = mqtt
        c, _ = component_info(topic)
        self._topic = '{}/shared/{}'.format(DISCOVERY_PREFIX, c)

    def __call__(self, *args, **kwargs):
        return self._topic

    def send_value(self, val):
        self._mqtt.publish(self._topic, val)


class SharedTemplateTopic(SharedTopic):
    def __init__(self, mqtt, topic):
        super().__init__(mqtt, topic)
        self._fetch_funcs = {}

    def add(self, key, fetch_func):
        self._fetch_funcs[key] = fetch_func
        return "{{ value_json." + key + "}}"

    def send_template_value(self):
        msg = {}
        for k, f in self._fetch_funcs.items():
            msg[k] = f()
        self.send_value(msg)


class Manager:
    def __init__(self, mqtt):
        self.mqtt = mqtt
        self.topic_available = SharedTopic(mqtt, 'available')
        self.topic_state = SharedTemplateTopic(mqtt, 'state')
        self._all = []

    def add_component(self, c):
        if type(c) is list:
            self._all = self._all + c
        else:
            self._all.append(c)
        return c

    def add_state_func(self, key, func):
        return self.topic_state.add(key, func)

    def send_updates(self):
        self.topic_state.send_template_value()

    def __enter__(self):
        for component in self._all:
            component.__enter__()

        time.sleep(1)  # Give home assistant a chance to catch up

        self.topic_available.send_value('online')

        for component in self._all:
            component.on_connect()

    def __exit__(self, *args):
        for component in self._all:
            component.__exit__()


class _Base(Hass):
    def __init__(self, manager=None, component=None, name=None, icon=None):
        cid, cname = component_info(name)
        super().__init__(mqtt=manager.mqtt, object_id=cid, component=component)

        self._config = {
            'name': cname.title(),
            'availability_topic': manager.topic_available(),
            'payload_available': 'online',
            'payload_not_available': 'offline',

        }
        if icon is not None:
            self._config.update({
                'icon': icon
            })

    def on_connect(self):
        pass


class Sensor(_Base):
    def __init__(self, manager, name, unit_of_measurement, icon=None):
        super().__init__(manager=manager, component='sensor', name=name, icon=icon)

        self._config.update({
            'state_topic': manager.topic_state(),
            'value_template': manager.add_state_func(name, lambda: self._format_state(self.state_get())),
            'unit_of_measurement': unit_of_measurement,
        })

    def _format_state(self, state):
        return "{0:.3f}".format(state)

    def state_get(self):
        raise NotImplementedError


class SettableSensor(Sensor):
    def __init__(self, manager, name, min_val, start_val, max_val):
        super(Sensor, self).__init__(manager=manager, component='sensor', name=name)

        self._TOPIC_STATE = self.get_topic('state')
        self._TOPIC_CMD_SET = self.get_topic('cmdSet')

        self._config.update({
            'state_topic': self._TOPIC_STATE,
            'value_template': self._TOPIC_CMD_SET,
            'unit_of_measurement': ' ',
        })

        self._start_val = start_val
        self._min_val = min_val
        self._max_val = max_val
        self._val = start_val
        self.subscribe(self._TOPIC_CMD_SET, lambda new_state: self.state_set(self._format_state(new_state)))

    def _format_state(self, state):
        state = float(state)
        if state > self._max_val:
            return self._max_val
        elif state < self._min_val:
            return self._min_val
        else:
            return state

    def state_set(self, state):
        if abs(state - self._val) < 1e-1:
            self._mqtt.publish(self._TOPIC_STATE, state)
        self._val = state

    def state_get(self):
        return self._val

    def on_connect(self):
        self._val = self._start_val
        self._mqtt.publish(self._TOPIC_STATE, self._val)


class Switch(_Base):
    def __init__(self, manager, name):
        super().__init__(manager=manager, component='switch', name=name)

        self._TOPIC_CMD_SET = self.get_topic('cmdSet')

        self._config.update({
            'state_topic': manager.topic_state(),
            'value_template': manager.add_state_func(name, lambda: self._format_state(self.state_get())),
            'command_topic': self._TOPIC_CMD_SET,
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'state_on': 'ON',
            'state_off': 'OFF'
        })

        self.subscribe(self._TOPIC_CMD_SET, lambda new_state: self.state_set(self._format_state(new_state)))

    def _format_state(self, state):
        return 'ON' if state else 'OFF'

    def state_get(self):
        raise NotImplementedError

    def state_set(self, state):
        raise NotImplementedError


class Climate(_Base):
    def __init__(self, manager, name, modes):  # ['off', 'heating', 'cooling']
        super().__init__(manager=manager, component='climate', name=name)

        self._TOPIC_STATE_TARGET = self.get_topic('stateTargetTemp')

        self._TOPIC_CMD_MODE = self.get_topic('cmdMode')
        self._TOPIC_CMD_TEMP = self.get_topic('cmdTargetTemp')

        self._config.update({
            'mode_state_topic': manager.topic_state(),
            'mode_state_template': manager.add_state_func("brew_mode", lambda: self.mode_get()),
            'temperature_state_topic': self._TOPIC_STATE_TARGET,
            'current_temperature_topic': manager.topic_state(),
            'current_temperature_template': manager.add_state_func("brew_temp", lambda: self.current_get()),
            'mode_command_topic': self._TOPIC_CMD_MODE,
            'temperature_command_topic': self._TOPIC_CMD_TEMP,
            'min_temp': '0',
            'max_temp': '100',
            'temp_step': '1',
            'modes': modes
        })

        self.subscribe(self._TOPIC_CMD_MODE, lambda new_mode: self.mode_set(new_mode))
        self.subscribe(self._TOPIC_CMD_TEMP, lambda new_temp: self.target_set_and_send(new_temp))

    def mode_get(self):
        raise NotImplementedError

    def mode_set(self, mode):
        raise NotImplementedError

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

    def on_connect(self):
        self.target_set_and_send(self.current_get())
