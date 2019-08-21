import logging

from simple_pid import PID

from controller import control_ssr
from hass.hass import Hass
from utils import env, env_float

COMPONENT_MODE = env('COMPONENT_MODE', 'heat')
assert COMPONENT_MODE == 'heat' or COMPONENT_MODE == 'cool', 'COMPONENT_MODE env var has to be "heat" or "cool"'

if COMPONENT_MODE == 'heat':
    PID_OUTPUT_LIMIT = (0, 10)
    PID_P_GAIN = env_float('PID_P_GAIN', 1)
    PID_I_GAIN = env_float('PID_I_GAIN', 0.5)
    PID_D_GAIN = env_float('PID_D_GAIN', 0.05)
    PID_SAMPLE_TIME = env_float('PID_SAMPLE_TIME', 8)
else:
    # TODO: Work out gain with simulation
    PID_OUTPUT_LIMIT = (-10, 0)
    PID_P_GAIN = env_float('PID_P_GAIN', 1)
    PID_I_GAIN = env_float('PID_I_GAIN', 0.5)
    PID_D_GAIN = env_float('PID_D_GAIN', 0.05)
    PID_SAMPLE_TIME = env_float('PID_SAMPLE_TIME', 8)

COMPONENT_ID = env('HASS_ID', 'hass_thermostat_' + COMPONENT_MODE)
COMPONENT_NAME = env('HASS_NAME', 'Brew Heater' if COMPONENT_MODE == 'heat' else 'Brew Cooler')


def get_hass(mqtt_host):
    return Hass(
        mqtt_host=mqtt_host,
        object_id=COMPONENT_ID,
        component='climate'
    )


class Component:

    def __init__(self, hass, thermometer, ssr):
        self._thermometer = thermometer
        self._ssr = ssr

        self._mode = 'off'
        self._target_temp = thermometer()
        self._available = False
        self._controller = None

        self._TOPIC_STATE = hass.get_topic('state')
        self._TOPIC_AVAIL = hass.get_topic('available')
        self._TOPIC_CMD_MODE = hass.get_topic('thermostatModeCmd')
        self._TOPIC_CMD_TEMP = hass.get_topic('targetTempCmd')

        self._hass = hass
        self._hass.subscribe(self._TOPIC_CMD_MODE, lambda new_mode: self._set_mode(new_mode))
        self._hass.subscribe(self._TOPIC_CMD_TEMP, lambda new_temp: self._set_target_temp(new_temp))

    def __enter__(self):
        self._hass.set_config({
            'name': COMPONENT_NAME,
            'mode_cmd_t': self._TOPIC_CMD_MODE,
            'mode_stat_t': self._TOPIC_STATE,
            'mode_stat_tpl': "{{ value_json['mode'] }}",
            'avty_t': self._TOPIC_AVAIL,
            'pl_avail': 'online',
            'pl_not_avail': 'offline',
            'temp_cmd_t': self._TOPIC_CMD_TEMP,
            'temp_stat_t': self._TOPIC_STATE,
            'temp_stat_tpl': "{{ value_json['target_temp'] }}",
            'curr_temp_t': self._TOPIC_STATE,
            'curr_temp_tpl': "{{ value_json['current_temp'] }}",
            'min_temp': '0',
            'max_temp': '100',
            'temp_step': '1',
            'modes': ['off', COMPONENT_MODE]
        })
        return self

    def __exit__(self, *args):
        pass

    def _set_mode(self, new_mode):
        if self._mode != new_mode:
            self._mode = new_mode
            self._delete_controller()
            self.send_state()

    def _set_target_temp(self, new_temp):
        new_temp = float(new_temp)
        if abs(self._target_temp - new_temp) > 1e-16:
            self._target_temp = new_temp
            self._delete_controller()
            self.send_state()

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, new_available):
        self._available = new_available
        self._hass.publish(self._TOPIC_AVAIL, 'online' if self._available else 'offline')

    def send_state(self):
        self._hass.publish(self._TOPIC_STATE, {
            'mode': self._mode,
            'target_temp': self._target_temp,
            'current_temp': self._thermometer(),
        })

    def _delete_controller(self):
        logging.debug('Deleting current controller')
        self._controller = None

    def _create_controller(self):
        logging.debug('Creating new controller')
        self._controller = control_ssr(PID(
            PID_P_GAIN,
            PID_I_GAIN,
            PID_D_GAIN,
            setpoint=self._target_temp,
            sample_time=PID_SAMPLE_TIME,
            output_limits=PID_OUTPUT_LIMIT
        ), self._ssr, self._thermometer)

    @property
    def controller(self):
        assert self._mode != 'off', 'invalid state, mode cannot be "off"'

        if self._controller is None:
            self._create_controller()

        return self._controller

    @property
    def mode(self):
        return self._mode

    @property
    def target_temp(self):
        return self._target_temp
