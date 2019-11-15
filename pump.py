from hass.hass import Hass
from utils import device_and_component_info

COMPONENT_ID, COMPONENT_NAME = device_and_component_info('pump')


def pump(mqtt, switch):
    return Switch(mqtt, switch)


class Switch(Hass):
    def __init__(self, mqtt, switch):
        super().__init__(mqtt=mqtt, object_id=COMPONENT_ID, component='switch')

        self._switch = switch
        self._available = 'online'

        self._TOPIC_STATE = self.get_topic('state')
        self._TOPIC_AVAIL = self.get_topic('available')
        self._TOPIC_CMD = self.get_topic('set')

        self.subscribe(self._TOPIC_CMD, lambda new_state: self._set(new_state == 'ON'))

    def __enter__(self):
        self.set_config({
            'name': COMPONENT_NAME,
            'command_topic': self._TOPIC_CMD,
            'state_topic': self._TOPIC_STATE,
            'availability_topic': self._TOPIC_AVAIL,
            'payload_available': 'online',
            'payload_not_available': 'offline',
            'payload_on': 'ON',
            'payload_off': 'OFF',
            'state_on': 'ON',
            'state_off': 'OFF'
        })
        return self

    def _set(self, new_state):
        self._switch(new_state)
        self.send_state()

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, new_available):
        self._available = new_available
        self.publish(self._TOPIC_AVAIL, 'online' if self._available else 'offline')

    def send_state(self):
        self.publish(self._TOPIC_STATE, 'ON' if self._switch.is_on() else 'OFF')
