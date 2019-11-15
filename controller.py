import logging
import time


def temperatures(thermometer):
    while True:
        current_temperature = thermometer()
        logging.debug('Current temperature is {0:.2f}'.format(current_temperature))
        yield current_temperature


def switch_delta_time(pid, current_temperature, sensors):
    control = pid(current_temperature)

    assert pid.output_limits[0] is not None and pid.output_limits[1] is not None, 'PID output limits must be set'
    control_percent = abs(control) / (pid.output_limits[1] - pid.output_limits[0])

    assert 0 <= control_percent <= 1, 'PID control_percent has to be between 0 and 1'
    logging.info(
        'PID:\n\tcurrent   {:.2f}\n\tsetpoint  {:.2f}\n\tcomponent {}\n\ttunings   {}\n\tlimits    {}\n\tcontrol   {:.2f} ({:.2f}%)'.format(
            current_temperature,
            pid.setpoint,
            pid.components,
            pid.tunings,
            pid.output_limits,
            control,
            control_percent * 100
        ))
    sensors(pid.components, pid.tunings, pid.output_limits, pid.sample_time, control_percent)
    return control_percent


def switch_states(pid, thermometer, sensors):
    last_time = 0
    switch_turn_off_time = None
    for current_temperature in temperatures(thermometer):
        now = time.monotonic()
        dt = now - last_time if now - last_time else 1e-16
        if dt > pid.sample_time:  # New controller cycle
            switch_dt = switch_delta_time(pid, current_temperature, sensors)
            if switch_dt > 0:  # Switch time bigger than 0
                switch_turn_off_time = now + (switch_dt * pid.sample_time)
            last_time = now
        yield current_temperature, now <= switch_turn_off_time if switch_turn_off_time else False


def control_switch(pid, switch, thermometer, sensors):
    for current_temperature, on_off in switch_states(pid, thermometer, sensors):
        switch(on_off)
        yield current_temperature, on_off
