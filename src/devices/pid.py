import logging
import time


def temperatures(thermometer):
    while True:
        current_temperature = thermometer()
        yield current_temperature


def switch_delta_time(pid, current_temperature, sensor):
    control = pid(current_temperature)

    assert pid.output_limits[0] is not None and pid.output_limits[1] is not None, 'PID output limits must be set'
    control_percent = abs(control) / (pid.output_limits[1] - pid.output_limits[0])

    assert 0 <= control_percent <= 1, 'PID control_percent has to be between 0 and 1'
    control_percent_human = "{0:.3f}".format(control_percent * 100)
    logging.debug(
        'PID:\n\tcurrent    {:.2f}\n\tsetpoint   {:.2f}\n\tcomponent  {}\n\ttunings    {}\n\tlimits     {}\n\tcontrol    {:.2f} ({} %)\n\tsampletime {}'.format(
            current_temperature,
            pid.setpoint,
            pid.components,
            pid.tunings,
            pid.output_limits,
            control,
            control_percent_human,
            pid.sample_time
        ))
    p, i, d = pid.components
    sensor(p, i, d, control_percent_human)
    return control_percent


def switch_states(pid, thermometer, sensor):
    last_time = 0
    switch_turn_off_time = None
    for current_temperature in temperatures(thermometer):
        now = time.monotonic()
        dt = now - last_time if now - last_time else 1e-16
        if dt > pid.sample_time:  # New controller cycle
            switch_dt = switch_delta_time(pid, current_temperature, sensor)
            if switch_dt > 0:  # Switch time bigger than 0
                switch_turn_off_time = now + (switch_dt * pid.sample_time)
            last_time = now
        yield current_temperature, now <= switch_turn_off_time if switch_turn_off_time else False


def control_switch(pid, switch, thermometer, sensor):
    for current_temperature, on_off in switch_states(pid, thermometer, sensor):
        switch(on_off)
        yield current_temperature, on_off
