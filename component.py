import logging
from time import sleep
from uuid import UUID

from hass.utils import build_component

logging.basicConfig(level=logging.DEBUG)

hass = build_component(
    id=str(UUID('12345678123456781234567812345678')),
    component='climate'
)

TOPIC_STATE = hass.get_topic('state')
TOPIC_AVAIL = hass.get_topic('available')
TOPIC_CMD_MODE = hass.get_topic('thermostatModeCmd')
TOPIC_CMD_TEMP = hass.get_topic('targetTempCmd')

CONFIG = {
    'name': 'Brew Boiler',
    'mode_cmd_t': TOPIC_CMD_MODE,
    'mode_stat_t': TOPIC_STATE,
    'mode_stat_tpl': "{{ value_json['mode'] }}",
    # 'avty_t': TOPIC_AVAIL,
    # 'pl_avail': 'online',
    # 'pl_not_avail': 'offline',
    'temp_cmd_t': TOPIC_CMD_TEMP,
    'temp_stat_t': TOPIC_STATE,
    'temp_stat_tpl': "{{ value_json['target_temp'] }}",
    'curr_temp_t': TOPIC_STATE,
    'curr_temp_tpl': "{{ value_json['current_temp'] }}",
    'min_temp': '0',
    'max_temp': '100',
    'temp_step': '0.5',
    'modes': ['off', 'heat', 'cool']
}

mode = "off"
target = 0.0
current = 0.0
available = True


@hass.send(TOPIC_STATE)
def send_update():
    return {
        "mode": mode,
        "target_temp": target,
        "current_temp": current,
    }


@hass.send(TOPIC_AVAIL)
def set_available(is_available):
    global available
    available = is_available
    return "online" if available else "offline"


@hass.receive(TOPIC_CMD_MODE)
def set_mode(new_mode):
    global mode
    mode = new_mode
    send_update()


@hass.receive(TOPIC_CMD_TEMP)
def set_target(new_tmp):
    global target
    target = float(new_tmp)
    send_update()


def set_update(self):
    global current
    current = self._current + 0.5
    send_update()


hass.connect(CONFIG)

sleep(0.5)

set_available(True)

while True:
    sleep(5)
    current = current + 0.5
    send_update()
