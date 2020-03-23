import logging

from simple_pid import PID

from devices import call_children
from devices.pid import control_switch
from devices.sensors import create_pid_sensor
from hass.components import Climate, SettableSensor


def create_hvac(manager, ssr, thermometer):
    return Hvac(manager, None, ['heat', 'cool'], ssr, thermometer)


class HvacValue(SettableSensor):
    def __init__(self, manager, name, min_val, start_val, max_val, on_change):
        super().__init__(manager, name, min_val, start_val, max_val)
        self._on_change = on_change

    def state_set(self, val):
        super().state_set(val)
        self._on_change()


class Hvac(Climate):
    def __init__(self, manager, name, mode, ssr, thermometer):
        mode.append('off')
        super().__init__(manager, name, mode)
        self._manager = manager
        self._mode = 'off'
        self._ssr = ssr
        self._thermometer = thermometer
        self._target_temp = self._thermometer()
        self._controller = None

        # Values that can change
        self._pid_p = HvacValue(manager, 'p_gain', 0, 2.5, 10, lambda: self._handle_state_change())
        self._pid_i = HvacValue(manager, 'i_gain', 0, 0, 10, lambda: self._handle_state_change())
        self._pid_d = HvacValue(manager, 'd_gain', 0, 1, 10, lambda: self._handle_state_change())
        self._pid_output_limit = HvacValue(manager, 'output_limit', 1, 5, 20,
                                           lambda: self._handle_state_change())
        self._pid_sample_time = HvacValue(manager, 'sample_time', 5, 8, 600, lambda: self._handle_state_change())
        self._pid_sensor = create_pid_sensor(manager)
        self._children = [self._pid_p, self._pid_i, self._pid_d, self._pid_sample_time, self._pid_output_limit]

    def mode_get(self):
        return self._mode

    def target_get(self):
        return self._target_temp

    def current_get(self):
        return self._thermometer()

    def mode_set(self, mode):
        if self._mode != mode:
            self._mode = mode
            self._handle_state_change()

    def target_set(self, target):
        self._target_temp = float(target)
        self._handle_state_change()

    def _handle_state_change(self):
        if self._mode == 'off':
            self._controller = None
            self._pid_sensor(0.0, 0.0, 0.0, 0.0)
            self._ssr(False)
        elif self._mode == 'heat':
            self._controller = control_switch(
                PID(
                    self._pid_p.state_get(),
                    self._pid_i.state_get(),
                    self._pid_d.state_get(),
                    setpoint=self._target_temp,
                    sample_time=self._pid_sample_time.state_get(),
                    output_limits=[0, self._pid_output_limit.state_get()]
                )
                , self._ssr, self._thermometer, self._pid_sensor)
        elif self._mode == 'cool':
            self._controller = control_switch(
                PID(
                    self._pid_p.state_get(),
                    self._pid_i.state_get(),
                    self._pid_d.state_get(),
                    setpoint=self._target_temp,
                    sample_time=self._pid_sample_time.state_get(),
                    output_limits=[-self._pid_output_limit.state_get(), 0]
                )
                , self._ssr, self._thermometer, self._pid_sensor)
        self._manager.send_updates()

    def on_connect(self):
        call_children(self._children, 'on_connect')
        call_children([self._pid_sensor], 'on_connect')
        super().on_connect()

    def __enter__(self):
        call_children(self._children, '__enter__')
        call_children([self._pid_sensor], '__enter__')
        return super().__enter__()

    def __exit__(self, *args):
        call_children(self._children, '__exit__', *args)
        call_children([self._pid_sensor], '__exit__', *args)
        super().__exit__(*args)

    def apply_controller(self):
        if self._controller is None:
            self._ssr(False)
        elif self.mode_get() == 'heat' and self.target_get() > 99.0:
            logging.debug('Temperature target is higher than 99°c on a heater, relay permanently turned on')
            self._ssr(True)
        elif self.mode_get() == 'cool' and self.target_get() < 1.0:
            logging.debug('Temperature target is higher lower than 1°c on a cool, relay permanently turned on')
            self._ssr(True)
        else:
            self._controller.__next__()
