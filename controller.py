import logging
import time


def temperatures(thermometer):
    while True:
        current_temperature = thermometer()
        logging.debug("Current temperature is {0:.2f}".format(current_temperature))
        yield current_temperature


def ssr_delta_time(pid, current_temperature):
    control = pid(current_temperature)

    assert pid.output_limits[0] is not None and pid.output_limits[1] is not None, "PID output limits must be set"
    control_percent = abs(control) / (pid.output_limits[1] - pid.output_limits[0])

    assert 0 <= control_percent <= 1, "PID control_percent has to be between 0 and 1"
    logging.debug(
        'PID:\n\tsetpoint  {}\n\tcomponent {}\n\ttunings   {}\n\tlimits    {}\n\tcontrol   {:.2f} ({:.2f}%)'.format(
            pid.setpoint,
            pid.components,
            pid.tunings,
            pid.output_limits,
            control,
            control_percent * 100
        ))
    return control_percent


def ssr_state(pid, thermometer):
    last_time = 0
    ssr_turn_off_time = None
    for current_temperature in temperatures(thermometer):
        now = time.monotonic()
        dt = now - last_time if now - last_time else 1e-16
        if ssr_turn_off_time is None or dt > pid.sample_time:  # New controller cycle
            ssr_dt = ssr_delta_time(pid, current_temperature)
            if ssr_dt > 0:  # SSR time bigger than 0
                ssr_turn_off_time = now + (ssr_dt * pid.sample_time)
            last_time = now
        yield current_temperature, now <= ssr_turn_off_time


def control_ssr(pid, ssr, thermometer):
    for current_temperature, on_off in ssr_state(pid, thermometer):
        ssr(on_off)
        yield current_temperature, on_off
