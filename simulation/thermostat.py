import logging
import time

water_specific_heat = 4184  # 4184 watts will heat a 1L of water up by 1°C every second
room_temperature = 18
liters = 30
boiler_watts = 3000


class FakeThermostat:

    def __init__(self, invert=False):
        self._invert_constant = -1 if invert else 1
        self._ssr_on = False
        self._current_temperature = room_temperature
        self._last_call = None

    def ssr(self, on):
        if self._ssr_on != on:
            logging.debug('FakeSSR set {}'.format('ON' if on else 'OFF'))
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
            if self._invert_constant < 0:
                clamp = min
            else:
                clamp = max
            self._current_temperature = clamp(room_temperature, self._current_temperature - temperature_loss)

        self._last_call = now
        return self._current_temperature
