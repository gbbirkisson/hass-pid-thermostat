import logging

from simple_pid import PID

from controller import control_switch
from hass.hass import Hass
from utils import env, env_float, device_and_component_info

COMPONENT_MODE = env('COMPONENT_MODE', 'heat')
assert COMPONENT_MODE == 'heat' or COMPONENT_MODE == 'cool', 'COMPONENT_MODE env var has to be "heat" or "cool"'

if COMPONENT_MODE == 'heat':
    PID_OUTPUT_LIMIT = (0, 10)
    PID_P_GAIN = env_float('PID_P_GAIN', 2)
    PID_I_GAIN = env_float('PID_I_GAIN', 0)
    PID_D_GAIN = env_float('PID_D_GAIN', 5)
    PID_SAMPLE_TIME = env_float('PID_SAMPLE_TIME', 8)
else:
    PID_OUTPUT_LIMIT = (-10, 0)
    PID_P_GAIN = env_float('PID_P_GAIN', 2)
    PID_I_GAIN = env_float('PID_I_GAIN', 0)
    PID_D_GAIN = env_float('PID_D_GAIN', 5)
    PID_SAMPLE_TIME = env_float('PID_SAMPLE_TIME', 8)

COMPONENT_ID, COMPONENT_NAME = device_and_component_info()


def hvac(mqtt, thermometer, switch):
    return Hvac(mqtt, thermometer, switch)


class Hvac(Hass):
    def __init__(self, mqtt, thermometer, switch):
        super().__init__(mqtt=mqtt, object_id=COMPONENT_ID, component='climate')

        self._thermometer = thermometer
        self._switch = switch

        self._mode = 'off'
        self._target_temp = thermometer()
        self._available = False
        self._controller = None

        self._TOPIC_STATE = self.get_topic('state')
        self._TOPIC_AVAIL = self.get_topic('available')
        self._TOPIC_CMD_MODE = self.get_topic('thermostatModeCmd')
        self._TOPIC_CMD_TEMP = self.get_topic('targetTempCmd')

        self.subscribe(self._TOPIC_CMD_MODE, lambda new_mode: self._set_mode(new_mode))
        self.subscribe(self._TOPIC_CMD_TEMP, lambda new_temp: self._set_target_temp(new_temp))

    def __enter__(self):
        self.set_config({
            'name': COMPONENT_NAME,
            'mode_command_topic': self._TOPIC_CMD_MODE,
            'mode_state_topic': self._TOPIC_STATE,
            'mode_state_template': "{{ value_json['mode'] }}",
            'availability_topic': self._TOPIC_AVAIL,
            'payload_available': 'online',
            'payload_not_available': 'offline',
            'temperature_command_topic': self._TOPIC_CMD_TEMP,
            'temperature_state_topic': self._TOPIC_STATE,
            'temperature_state_template': "{{ value_json['target_temp'] }}",
            'current_temperature_topic': self._TOPIC_STATE,
            'current_temperature_template': "{{ value_json['current_temp'] }}",
            'min_temp': '0',
            'max_temp': '100',
            'temp_step': '1',
            'modes': ['off', COMPONENT_MODE]
        })
        return self

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
        self.publish(self._TOPIC_AVAIL, 'online' if self._available else 'offline')

    def send_state(self):
        self.publish(self._TOPIC_STATE, {
            'mode': self._mode,
            'target_temp': self._target_temp,
            'current_temp': self._thermometer(),
        })

    def _delete_controller(self):
        logging.debug('Deleting current controller')
        self._controller = None

    def _create_controller(self):
        logging.debug('Creating new controller')
        self._controller = control_switch(PID(
            PID_P_GAIN,
            PID_I_GAIN,
            PID_D_GAIN,
            setpoint=self._target_temp,
            sample_time=PID_SAMPLE_TIME,
            output_limits=PID_OUTPUT_LIMIT
        ), self._switch, self._thermometer)

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
