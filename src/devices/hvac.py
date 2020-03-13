from simple_pid import PID

from devices.thermometer import create_average_thermometer, create_weighted_average_thermometer
from hass.components import Climate, Cover


def create_hvac(mqtt, manager, ssr, thermometers):
    manager.add(ssr, send_updates=False)

    for thermometer in thermometers:
        manager.add(thermometer, send_updates=True)

    create_average_thermometer(mqtt, manager, thermometers)
    weighted_average_thermometer = create_weighted_average_thermometer(mqtt, manager, thermometers)

    hvac = Hvac(mqtt, 'controller', ['heat', 'cool'], weighted_average_thermometer)
    manager.add(hvac, send_updates=True)

    return hvac


class HvacValue(Cover):
    def __init__(self, mqtt, name, min, current, max, on_change):
        super().__init__(mqtt, name, min, max)
        self._current = current
        self._on_change = on_change

    def position_set(self, value):
        self._current = value
        self._on_change()

    def position_get(self):
        return self._current


class Hvac(Climate):
    def __init__(self, mqtt, name, mode, thermometer):
        mode.append('off')
        super().__init__(mqtt, name, mode)
        self._mode = 'off'
        self._thermometer = thermometer
        self._target_temp = self._thermometer()
        self._pid = None

        # Values that can change
        self._pid_p = HvacValue(mqtt, name + '_p_gain', 0, 40, 100, lambda: self._handle_state_change())
        self._pid_i = HvacValue(mqtt, name + '_i_gain', 0, 0, 100, lambda: self._handle_state_change())
        self._pid_d = HvacValue(mqtt, name + '_d_gain', 0, 50, 10, lambda: self._handle_state_change())
        self._pid_sample_time = HvacValue(mqtt, name + '_sample_time', 5, 8, 60, lambda: self._handle_state_change())
        self._pid_output_limit = HvacValue(mqtt, name + '_output_limit', 50, 100, 200,
                                           lambda: self._handle_state_change())

    def turn_off(self):
        self.mode_set_and_send('off')

    def is_on(self):
        return self._pid is not None

    def mode_get(self):
        return self._mode

    def target_get(self):
        return self._target_temp

    def current_get(self):
        return self._thermometer()

    def mode_set(self, mode):
        self._mode = mode
        self._handle_state_change()

    def target_set(self, target):
        self._target_temp = target
        self._handle_state_change()

    def _handle_state_change(self):
        if self._mode == 'off':
            self._pid = None
            return

        if self._mode == 'heat':
            self._pid = PID(
                self._pid_p.position_get(),
                self._pid_i.position_get(),
                self._pid_d.position_get(),
                setpoint=self._target_temp,
                sample_time=self._pid_sample_time.position_get(),
                output_limits=[0, self._pid_output_limit.position_get()]
            )
        else:
            self._pid = PID(
                self._pid_p.position_get(),
                self._pid_i.position_get(),
                self._pid_d.position_get(),
                setpoint=self._target_temp,
                sample_time=self._pid_sample_time.position_get(),
                output_limits=[-self._pid_output_limit.position_get(), 0]
            )

        self.mode_send()

    def available(self, new_available):
        self._pid_p.available(new_available)
        self._pid_i.available(new_available)
        self._pid_d.available(new_available)
        self._pid_sample_time.available(new_available)
        self._pid_output_limit.available(new_available)

        self._available = new_available
        self.publish(self._TOPIC_AVAIL, 'online' if self._available else 'offline')

    def on_connect(self):
        self._pid_p.on_connect()
        self._pid_i.on_connect()
        self._pid_d.on_connect()
        self._pid_sample_time.on_connect()
        self._pid_output_limit.on_connect()
        super().on_connect()

    def __enter__(self):
        self._pid_p.__enter__()
        self._pid_i.__enter__()
        self._pid_d.__enter__()
        self._pid_sample_time.__enter__()
        self._pid_output_limit.__enter__()
        return super().__enter__()

    def __exit__(self, *args):
        self._pid_p.__exit__(*args)
        self._pid_i.__exit__(*args)
        self._pid_d.__exit__(*args)
        self._pid_sample_time.__exit__(*args)
        self._pid_output_limit.__exit__(*args)
        super().__exit__(*args)
