import time

water_specific_heat = 4184  # 4184 watts will heat a 1L of water up by 1°C every second
room_temperature = 15
liters = 60
boiler_watts = 4000
minutes_down_one_degree = 5
invert_constant = 1

current_temp = 15
target_temp = 15
on = False
last_call = None


class FakeTemp:
    def __init__(self, tid, tempfunc):
        self._id = tid
        self._tempfunc = tempfunc

    def get_id(self):
        return self._id

    def get_temperature(self):
        return self._tempfunc()


def temp_func():
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
    return current_temp  # + ((random() - 0.5) / 2)


def create_temp_sensors():
    return [
        FakeTemp('outer', temp_func),
        FakeTemp('aux', lambda: 20),
        FakeTemp('inner', lambda: 40),
        FakeTemp('bottom', lambda: 60),
        FakeTemp('faucet', lambda: 80)
    ]


def create_ssr(error_sensor=None):
    def _set_state(s):
        global on
        on = s

    return _set_state
