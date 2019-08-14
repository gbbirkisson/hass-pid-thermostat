import logging
import time

from simple_pid import PID

from controller import create_controller

water_specific_heat = 4184  # 4184 watts will heat a 1L of water up by 1°C every second
room_temperature = 18
liters = 5
boiler_watts = 4184


class FakeThermometer:

    def __init__(self, fake_ssr):
        self._current_temperature = room_temperature
        self._last_call = None
        self._fake_ssr = fake_ssr

    def __call__(self):
        now = time.monotonic()
        if self._last_call is None:
            self._last_call = now
            return self._current_temperature

        dt = now - self._last_call

        if self._fake_ssr.on:
            temperature_gain = boiler_watts * dt / (liters * water_specific_heat)
            self._current_temperature = self._current_temperature + temperature_gain
            self._current_temperature = min(self._current_temperature, 100)
        else:
            temperature_loss = 1 / 60 * dt  # 60 sec to lose 1°c .... maybe use exponential decay ??
            self._current_temperature = max(room_temperature, self._current_temperature - temperature_loss)

        self._last_call = now
        return self._current_temperature


class FakeSSR:

    def __init__(self):
        self.on = False

    def __call__(self, on):
        if self.on != on:
            logging.debug("FakeSSR set {}".format("ON" if on else "OFF"))
        self.on = on


def heater_simulator():
    p_ssr = FakeSSR()
    p_therm = FakeThermometer(p_ssr)

    p_pid = PID(
        2,
        0.01,
        0.2,
        setpoint=30,
        sample_time=8,
        output_limits=(0, 20)
    )

    return create_controller(p_pid, p_ssr, p_therm, sleep_func=lambda: time.sleep(0.3))


logging.basicConfig(level=logging.DEBUG)
sim = heater_simulator()
sim()
