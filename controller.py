import logging
import time


def temperatures(thermometer):
    while True:
        current_temperature = thermometer()  # TODO: Try catch?
        logging.debug("Current temperature is {0:.2f}".format(current_temperature))
        yield current_temperature


def ssr_delta_time(pid, current_temperature, on_func):
    if not on_func():
        logging.debug("System is off, relay will not be turned on")
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


def ssr_state(pid, thermometer, on_func):
    last_time = 0
    ssr_turn_off_time = None
    for current_temperature in temperatures(thermometer):
        now = time.monotonic()
        dt = now - last_time if now - last_time else 1e-16
        if dt > pid.sample_time:  # New controller cycle
            ssr_turn_off_time = now + (ssr_delta_time(pid, current_temperature, on_func) * pid.sample_time)
            last_time = now
        yield now < ssr_turn_off_time


def control_ssr(pid, ssr, thermometer, on_func=lambda: True, sleep_func=lambda: 0):
    for on_off in ssr_state(pid, thermometer, on_func):
        ssr(on_off)  # TODO: Try catch?
        sleep_func()


def create_controller(pid, ssr, thermometer, on_func=lambda: True, sleep_func=lambda: 0):
    def controller():
        control_ssr(pid, ssr, thermometer, on_func, sleep_func)

    return controller
