from hass.hass import Hass
from utils import device_and_component_info

pid_p = 'pid_p'
pid_i = 'pid_i'
pid_d = 'pid_d'

pid_p_gain = 'pid_p_gain'
pid_i_gain = 'pid_i_gain'
pid_d_gain = 'pid_d_gain'

pid_output_lower = 'pid_output_lower'
pid_output_upper = 'pid_output_upper'

pid_time_interval = 'pid_time_interval'
pid_time_on = 'pid_time_on'


def sensors(mqtt):
    return _StatsSensors(mqtt)


class _StatsSensors():
    def __init__(self, mqtt):
        self._available = True
        self._sensors = {
            pid_p: _Sensor(mqtt, pid_p, ' '),
            pid_i: _Sensor(mqtt, pid_i, ' '),
            pid_d: _Sensor(mqtt, pid_d, ' '),

            pid_p_gain: _Sensor(mqtt, pid_p_gain, ' '),
            pid_i_gain: _Sensor(mqtt, pid_i_gain, ' '),
            pid_d_gain: _Sensor(mqtt, pid_d_gain, ' '),

            pid_output_lower: _Sensor(mqtt, pid_output_lower, ' '),
            pid_output_upper: _Sensor(mqtt, pid_output_upper, ' '),

            pid_time_interval: _Sensor(mqtt, pid_time_interval, 'seconds'),
            pid_time_on: _Sensor(mqtt, pid_time_on, '%'),
        }

    def __call__(self, components, weights, output_limits, interval, control_percentage):
        p_p, p_i, p_d = components
        c_p, c_i, c_d = weights
        low, high = output_limits

        self._send_state(pid_p, p_p)
        self._send_state(pid_i, p_i)
        self._send_state(pid_d, p_d)

        self._send_state(pid_p_gain, c_p)
        self._send_state(pid_i_gain, c_i)
        self._send_state(pid_d_gain, c_d)

        self._send_state(pid_output_lower, low)
        self._send_state(pid_output_upper, high)

        self._send_state(pid_time_interval, interval)
        self._send_state(pid_time_on, control_percentage)

    def _send_state(self, sensor, state):
        s = self._sensors.get(sensor)
        if s is not None:
            s.send_state(state)

    def __enter__(self):
        for name, sensor in self._sensors.items():
            sensor.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for name, sensor in self._sensors.items():
            sensor.__exit__(exc_type, exc_val, exc_tb)

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, new_available):
        self._available = new_available
        for name, sensor in self._sensors.items():
            sensor.available = new_available


class _Sensor(Hass):
    def __init__(self, mqtt, component_postfix, unit_of_measurement):
        self._component_id, self._component_name = device_and_component_info(component_postfix)
        self._unit_of_measurement = unit_of_measurement
        super().__init__(mqtt=mqtt, object_id=self._component_id, component='sensor')

        self._available = True

        self._TOPIC_AVAIL = self.get_topic('available')
        self._TOPIC_STATE = self.get_topic('state')
        self._config = {
            'name': self._component_name,
            'state_topic': self._TOPIC_STATE,
            'availability_topic': self._TOPIC_AVAIL,
            'payload_available': 'online',
            'payload_not_available': 'offline',
            'unit_of_measurement': self._unit_of_measurement
        }

    @property
    def available(self):
        return self._available

    @available.setter
    def available(self, new_available):
        self._available = new_available
        self.publish(self._TOPIC_AVAIL, 'online' if self._available else 'offline')

    def send_state(self, state):
        self.publish(self._TOPIC_STATE, state)
