import logging
import time

from simple_pid import PID

from controller import create_controller

water_specific_heat = 4184  # 4184 watts will heat a 1L of water up by 1°C every second
room_temperature = 18
liters = 1
boiler_watts = 4184


class FakeThermostat:

    def __init__(self, invert=False):
        self._invert_constant = -1 if invert else 1
        self._ssr_on = False
        self._current_temperature = room_temperature
        self._last_call = None

    def ssr(self, on):
        if self._ssr_on != on:
            logging.debug("FakeSSR set {}".format("ON" if on else "OFF"))
            self._ssr_on = on

    def thermometer(self):
        now = time.monotonic()
        if self._last_call is None:
            self._last_call = now
            return self._current_temperature

        dt = now - self._last_call

        if self._ssr_on:
            temperature_gain = boiler_watts * dt / (liters * water_specific_heat)
            temperature_gain = temperature_gain * self._invert_constant
            self._current_temperature = self._current_temperature + temperature_gain
            self._current_temperature = min(self._current_temperature, 100)
        else:
            temperature_loss = 1 / 60 * dt  # 60 sec to lose 1°c .... maybe use exponential decay ??
            temperature_loss = temperature_loss * self._invert_constant
            if self._invert_constant:
                clamp = min
            else:
                clamp = max
            self._current_temperature = clamp(room_temperature, self._current_temperature - temperature_loss)

        self._last_call = now
        return self._current_temperature


def create_simulator(pid, invert):
    thermostat = FakeThermostat(invert=invert)
    return create_controller(pid, thermostat.ssr, thermostat.thermometer, sleep_func=lambda: time.sleep(0.3))


def heater_simulator():
    return create_simulator(PID(
        2,
        0.01,
        0.2,
        setpoint=30,
        sample_time=8,
        output_limits=(0, 20)
    ), False)


def cooler_simulator():
    return create_simulator(PID(
        2,
        0.01,
        0.2,
        setpoint=4,
        sample_time=8,
        output_limits=(-20, 0)
    ), True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    sim = heater_simulator()
    # sim = cooler_simulator()
    sim()
