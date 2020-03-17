import random
import time

from devices.switch import SSR
from devices.thermometer import Thermometer
from utils import func_wrapper

water_specific_heat = 4184  # 4184 watts will heat a 1L of water up by 1°C every second
room_temperature = 9
liters = 20
boiler_watts = 2500
minutes_down_one_degree = 5
invert_constant = 1

current_temp = 15
target_temp = 15
on = False
last_call = None


def create_fake_ssr(mqtt):
    def _set_state(s):
        global on
        on = s

    return SSR(mqtt, _set_state)


def create_fake_static_thermostat(manager, name, temp, error_sensor):
    def _fake_errors():
        if random.randint(0, 50) == 8:
            error_sensor.register_error("Fake error")
        return temp

    return Thermometer(manager, name, func_wrapper.wrap(_fake_errors))


def create_fake_thermostat(manager, name):
    def _read_temp():
        global last_call, current_temp, on

        now = time.monotonic()
        if last_call is None:
            last_call = now
            return current_temp

        dt = now - last_call

        if on:
            temperature_gain = boiler_watts * dt / (liters * water_specific_heat)
            temperature_gain = temperature_gain * invert_constant
            current_temp = current_temp + temperature_gain
            current_temp = min(current_temp, 100)
        else:
            temperature_loss = (1 / (60 * minutes_down_one_degree)) * dt
            temperature_loss = temperature_loss * invert_constant
            if invert_constant < 0:
                clamp = min
            else:
                clamp = max
            current_temp = clamp(room_temperature, current_temp - temperature_loss)

        last_call = now
        return current_temp  # + ((random.random() - 0.5) / 2)

    return Thermometer(manager, name, _read_temp)
