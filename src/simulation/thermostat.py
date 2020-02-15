import time
from random import randint

from simulation.switch import fake_switch

water_specific_heat = 4184  # 4184 watts will heat a 1L of water up by 1°C every second
room_temperature = 9
liters = 20
boiler_watts = 2500
minutes_down_one_degree = 10


class FakeThermostat:

    def __init__(self, invert=False):
        self._switch = fake_switch('heater')
        self._thermometeres = FakeThermometers(invert, self._switch)

    @property
    def switch(self):
        return self._switch

    def thermometers(self):
        return self._thermometeres


class FakeThermometers:
    def __init__(self, invert, switch):
        self._invert_constant = -1 if invert else 1
        self._current_temperature = room_temperature
        self._switch = switch
        self._last_call = None
        self._sensors = [
            _FakeSensor('sens1'),
            _FakeSensor('sens2'),
        ]

    def __call__(self):
        now = time.monotonic()
        if self._last_call is None:
            self._last_call = now
            return self._current_temperature

        dt = now - self._last_call

        if self._switch.is_on():
            temperature_gain = boiler_watts * dt / (liters * water_specific_heat)
            temperature_gain = temperature_gain * self._invert_constant
            self._current_temperature = self._current_temperature + temperature_gain
            self._current_temperature = min(self._current_temperature, 100)
        else:
            temperature_loss = (1 / (60 * minutes_down_one_degree)) * dt
            temperature_loss = temperature_loss * self._invert_constant
            if self._invert_constant < 0:
                clamp = min
            else:
                clamp = max
            self._current_temperature = clamp(room_temperature, self._current_temperature - temperature_loss)

        self._last_call = now
        return self._current_temperature

    def sensors(self):
        return self._sensors


class _FakeSensor:
    def __init__(self, i):
        self._id = i

    def get_id(self):
        return self._id

    def get_temperature(self):
        return randint(0, 100)
