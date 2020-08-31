import datetime
import logging

from ha_mqtt.util import env_float
from simple_pid import PID

from devices.pid import control_switch


class PidSensor:
    def __init__(self):
        self.p = 0
        self.i = 0
        self.d = 0
        self.control_percent = 0

    def __call__(self, p, i, d, control_percent):
        self.p = p
        self.i = i
        self.d = d
        self.control_percent = control_percent


class Pid:
    def __init__(
            self,
            thermometer,
            ssr,
            pid_sensor,
            p=env_float('PID_P_GAIN', 2),
            i=env_float('PID_I_GAIN', 5),
            d=env_float('PID_D_GAIN', 1),
            output_limit=env_float('PID_OUTPUT_LIMIT', 5),
            sample_time=env_float('PID_SAMPLE_TIME', 8)
    ):
        self._thermometer = thermometer
        self._ssr = ssr
        self._p = p
        self._i = i
        self._d = d
        self._output_limit = output_limit
        self._sample_time = sample_time

        self._mode = 'off'
        self._target = 0.0
        self._controller = None
        self._pid_sensor = pid_sensor

    @property
    def p(self):
        return self._p

    def set_p(self, new_p):
        self._p = new_p
        self._create_controller()

    @property
    def i(self):
        return self._i

    def set_i(self, new_i):
        self._i = new_i
        self._create_controller()

    @property
    def d(self):
        return self._d

    def set_d(self, new_d):
        self._d = new_d
        self._create_controller()

    @property
    def output_limit(self):
        return self._output_limit

    def set_output_limit(self, new_output_limit):
        self._output_limit = new_output_limit
        self._create_controller()

    @property
    def sample_time(self):
        return self._sample_time

    def set_sample_time(self, new_sample_time):
        self._sample_time = new_sample_time
        self._create_controller()

    def state_change(self, mode, target):
        logging.info('State changed [mode: {}, target: {}'.format(mode, target))
        if mode == 'off':
            self._mode = 'off'
            self._target = 0.0
            self._controller = None
        elif self._mode != mode or abs(self._target - target) > 1e-1:
            self._mode = mode
            self._target = target
            self._create_controller()

    def _create_controller(self):
        if self._mode != 'off':
            self._controller = control_switch(
                PID(
                    self.p,
                    self.i,
                    self.d,
                    setpoint=self._target,
                    sample_time=self.sample_time,
                    output_limits=[0, self.output_limit]
                ),
                self._ssr,
                self._thermometer,
                self._pid_sensor
            )

    def is_on(self):
        return self._controller is not None

    def update(self):
        if self._controller is None:
            self._ssr(False)
            self._pid_sensor(0, 0, 0, 0)
        elif self._target > 99:
            self._ssr(True)
            self._pid_sensor(0, 0, 0, 100)
        else:
            self._controller.__next__()


class TimeOnTarget:
    def __init__(self, pid_controller):
        self._pid_controller = pid_controller
        self._first_temp = None
        self._first_time = None

    def _reset(self):
        self._first_temp = None
        self._first_time = None
        return None

    def __call__(self, *args, **kwargs):
        if not self._pid_controller.is_on():
            return self._reset()

        curr = self._pid_controller._thermometer()
        target = self._pid_controller._target

        if abs(curr - target) < 1:
            return self._reset()

        if self._first_time is None:
            self._first_time = datetime.datetime.utcnow()
            self._first_temp = curr

        temp_diff = curr - self._first_temp
        if temp_diff < 1:
            return None

        seconds_so_far = (datetime.datetime.utcnow() - self._first_time).seconds
        seconds_left = (target - curr) / (temp_diff / seconds_so_far)

        return (datetime.datetime.utcnow() + datetime.timedelta(seconds=seconds_left)).replace(
            tzinfo=datetime.timezone.utc).isoformat()
