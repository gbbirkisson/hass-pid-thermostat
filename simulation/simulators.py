import logging
import time

from matplotlib import pyplot as plt

from controller import control_ssr

seconds = 1.00


def sec():
    global seconds
    seconds += 0.01
    return seconds


time.monotonic = sec

# Import after time spoof
from simple_pid import PID

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
            if self._invert_constant < 0:
                clamp = min
            else:
                clamp = max
            self._current_temperature = clamp(room_temperature, self._current_temperature - temperature_loss)

        self._last_call = now
        return self._current_temperature


def create_simulator(pid, invert):
    thermostat = FakeThermostat(invert=invert)
    return control_ssr(pid, thermostat.ssr, thermostat.thermometer)


def heater_simulator(tg):
    return create_simulator(PID(
        1,
        0.5,
        0.05,
        setpoint=tg,
        sample_time=8,
        output_limits=(0, 10)
    ), False)


def cooler_simulator(tg):
    return create_simulator(PID(
        1,
        0.5,
        0.05,
        setpoint=tg,
        sample_time=60,
        output_limits=(-10, 0)
    ), True)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    target = 45
    sim = heater_simulator(target)
    # target = 14
    # sim = cooler_simulator(target)
    x = []
    y = []
    t = []
    on = []
    for temp, on_off in sim:
        x.append(seconds / 60)
        y.append(temp)
        t.append(target)
        on.append(1 if on_off else 0)
        seconds += 1
        if seconds > 1000 + (60 * 45):
            break

    fig, ax1 = plt.subplots()
    ax1.plot(x, y)
    ax1.plot(x, t)
    ax1.set_xlabel('minutes')
    ax1.set_ylabel('°C', color='b')
    ax1.legend(['Actual', 'Target'])

    # ax2 = ax1.twinx()
    # ax2.plot(x, on, 'r.')
    # ax2.set_ylabel('on/off', color='r')
    fig.tight_layout()
    fig.savefig('simulation.png', bbox_inches='tight')
