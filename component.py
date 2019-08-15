import logging
import signal
import time

from simple_pid import PID

from controller import create_controller
from hass.utils import build_component
from simulation.simulators import FakeThermostat
from thermometer import get_thermometer
from utils import env, Component, env_float, call_repeatedly

logging.basicConfig(level=logging.DEBUG)

# Setup variables from the environment

SSR_PIN = env('SSR_PIN', 'XXX')
TEMP_POLL_INTERVAL = env_float("TEMP_POLL_INTERVAL", 0.5)

COMPONENT_MODE = env('COMPONENT_MODE', 'heat')
assert COMPONENT_MODE == 'heat' or COMPONENT_MODE == 'cool', "COMPONENT_MODE env var has to be 'heat' or 'cool'"
PID_OUTPUT_LIMIT = (0, 20) if COMPONENT_MODE == 'heat' else (-20, 0)

HASS_ID = env("HASS_ID", "hass_thermostat_" + COMPONENT_MODE)
HASS_NAME = env("HASS_NAME", "Brew Boiler" if COMPONENT_MODE == 'heat' else "Brew Cooler")
HASS_UPDATE_INTERVAL = env_float("HASS_UPDATE_INTERVAL", 2)
HASS_HOST = env("HASS_HOST", "hassio.local")

# Setup HASS connection

hass = build_component(
    HASS_ID,
    'climate',
    HASS_HOST
)

TOPIC_STATE = hass.get_topic('state')
TOPIC_AVAIL = hass.get_topic('available')
TOPIC_CMD_MODE = hass.get_topic('thermostatModeCmd')
TOPIC_CMD_TEMP = hass.get_topic('targetTempCmd')

CONFIG = {
    'name': HASS_NAME,
    'mode_cmd_t': TOPIC_CMD_MODE,
    'mode_stat_t': TOPIC_STATE,
    'mode_stat_tpl': "{{ value_json['mode'] }}",
    'avty_t': TOPIC_AVAIL,
    'pl_avail': 'online',
    'pl_not_avail': 'offline',
    'temp_cmd_t': TOPIC_CMD_TEMP,
    'temp_stat_t': TOPIC_STATE,
    'temp_stat_tpl': "{{ value_json['target_temp'] }}",
    'curr_temp_t': TOPIC_STATE,
    'curr_temp_tpl': "{{ value_json['current_temp'] }}",
    'min_temp': '0',
    'max_temp': '100',
    'temp_step': '0.5',
    'modes': ['off', COMPONENT_MODE]
}

# Setup controller components

thermometer = get_thermometer()
fake = FakeThermostat()  # TODO: Switch to the real deal
ssr = fake.ssr

component = Component()
component.mode = "off"
component.kill = False
component.pid = PID(
    env_float('PID_P_GAIN', 2.5),
    env_float('PID_I_GAIN', 0.005),
    env_float('PID_D_GAIN', 0.2),
    setpoint=0,
    sample_time=env_float('PID_SAMPLE_TIME', 8),
    output_limits=PID_OUTPUT_LIMIT
)
component.thermometer = thermometer
component.ssr = ssr


def controller_enabled():
    return component.mode != 'off'


def kill_controller():
    return component.kill


controller = create_controller(
    component.pid,
    component.ssr,
    component.thermometer,
    enabled_func=controller_enabled,
    delay_func=lambda: time.sleep(TEMP_POLL_INTERVAL),
    kill_func=kill_controller
)


# Setup queues

@hass.send(TOPIC_STATE)
def send_update():
    return {
        "mode": component.mode,
        "target_temp": component.pid.setpoint,
        "current_temp": component.thermometer(),
    }


@hass.send(TOPIC_AVAIL)
def send_available(is_available):
    return "online" if is_available else "offline"


@hass.receive(TOPIC_CMD_MODE)
def set_mode(new_mode):
    component.mode = new_mode
    send_update()


@hass.receive(TOPIC_CMD_TEMP)
def set_target(new_tmp):
    component.pid.setpoint = float(new_tmp)
    send_update()


# Start component

if __name__ == "__main__":
    hass.connect(CONFIG)

    time.sleep(1)

    send_available(True)

    stop_update_thread = call_repeatedly(HASS_UPDATE_INTERVAL, send_update)


    def exit_gracefully(signum, frame):
        logging.info("Killing everything")
        stop_update_thread()
        hass.disconnect()
        component.kill = True


    signal.signal(signal.SIGINT, exit_gracefully)
    signal.signal(signal.SIGTERM, exit_gracefully)

    controller()
