import logging
import time


def temperatures(thermometer, kill_func):
    while not kill_func():
        current_temperature = thermometer()
        logging.debug("Current temperature is {0:.2f}".format(current_temperature))
        yield current_temperature


def ssr_delta_time(pid, current_temperature, enabled_func):
    if not enabled_func():
        logging.debug("System is disabled, relay will not be turned on")
        return 0
    if pid.setpoint > 99:
        logging.debug("Temperature target is higher than 99°c, relay turned on manually for boil")
        return 1

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


def ssr_state(pid, thermometer, enabled_func, kill_func):
    last_time = 0
    ssr_turn_off_time = None
    for current_temperature in temperatures(thermometer, kill_func):
        now = time.monotonic()
        dt = now - last_time if now - last_time else 1e-16
        if dt > pid.sample_time:  # New controller cycle
            ssr_turn_off_time = now + (ssr_delta_time(pid, current_temperature, enabled_func) * pid.sample_time)
            last_time = now
        yield now < ssr_turn_off_time


def control_ssr(pid, ssr, thermometer, enabled_func, delay_func, kill_func):
    for on_off in ssr_state(pid, thermometer, enabled_func, kill_func):
        ssr(on_off)
        delay_func()


def create_controller(pid, ssr, thermometer, enabled_func=lambda: True, delay_func=lambda: 0, kill_func=lambda: False):
    def controller():
        control_ssr(pid, ssr, thermometer, enabled_func, delay_func, kill_func)

    return controller
