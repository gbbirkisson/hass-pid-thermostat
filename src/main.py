import atexit
import logging
import signal

from ha_mqtt.climate import Climate
from ha_mqtt.components import create_last_update_sensor, create_func_call_limiter, create_func_result_cache, \
    create_average_sensor, create_weighted_average_sensor
from ha_mqtt.mqtt import Mqtt, MqttSharedTopic
from ha_mqtt.registry import ComponentRegistry
from ha_mqtt.sensor import ErrorSensor, Sensor, SettableSensor
from ha_mqtt.switch import Switch
from ha_mqtt.util import setup_logging, sleep_for, env_bool, env, id_from_name, env_name, env_float

from devices.rpi import cpu_temp
from pid import Pid, PidSensor, TimeOnTarget

SIMULATE = env_bool('SIMULATE', False)

if SIMULATE:
    from devices.devices_fake import create_ssr, create_temp_sensors
else:
    from devices.devices import create_ssr, create_temp_sensors


def with_prefix(s=None):
    p = env('HA_COMPONENT_PREFIX', 'Brew')
    if s is None:
        return p
    return p + ' ' + s


def create_components(mqtt_broker):
    # Get settings
    availability_topic = env_bool('HA_AVAILABLE', False)
    auto_discovery = env_bool('HA_AUTO', False)

    # Setup registry
    reg = ComponentRegistry()
    state = MqttSharedTopic(mqtt_broker, id_from_name("/{}".format(with_prefix('state'))))
    reg.add_shared_topic(state)

    # Setup standard config
    standard_config = {
        'mqtt': mqtt_broker,
        'state_topic': state,
        'availability_topic': availability_topic,
        'auto_discovery': auto_discovery
    }

    # Create error sensor
    errors = ErrorSensor(with_prefix('Errors'), **standard_config)
    reg.add_component(errors)

    # Create last update sensor
    last_update = create_last_update_sensor(with_prefix('Last Update'), **standard_config)
    reg.add_component(last_update)

    # Setup temperature sensors
    func_limit = create_func_call_limiter()
    ha_sensors = []
    for s in create_temp_sensors():
        logging.info("Found temp sensor: {}".format(s.get_id()))
        # Wrap state function to catch errors
        state_func = func_limit.wrap(create_func_result_cache(errors.wrap_function(s.get_temperature)))
        ha_sensors.append(Sensor(
            with_prefix('Temp ' + env_name(s.get_id())),
            '°C',
            state_func=state_func,
            **standard_config
        ))
    reg.add_component(ha_sensors)

    # Setup temp sensor counter
    reg.add_component(
        Sensor(with_prefix('Temp Sensor Count'), '',
               state_func=lambda: len(ha_sensors),
               state_formatter_func=lambda x: x,
               icon='mdi:magnify-plus',
               **standard_config)
    )

    # Create average temperature
    avg = create_average_sensor(
        with_prefix('Temp Average'),
        '°C',
        ha_sensors,
        icon='mdi:thermometer-lines',
        **standard_config
    )
    reg.add_component(avg)

    # Create weighted average temperature
    avg_w, weights = create_weighted_average_sensor(
        with_prefix('Temp Average Weighted'),
        '°C',
        0,
        100,
        1,
        50,
        ha_sensors,
        icon='mdi:thermometer-lines',
        **standard_config
    )
    reg.add_component(avg_w)
    reg.add_component(weights, send_updates=False)

    # Create SSR
    ssr = Switch(with_prefix('SSR'), state_change_func=create_ssr(errors), **standard_config)
    reg.add_component(ssr)

    # Create PID sensor
    pid_sensor = PidSensor()
    s_p = Sensor(with_prefix('P'), ' ', sensor_id=id_from_name(with_prefix('pid_p')),
                 state_func=lambda: pid_sensor.p, **standard_config)
    s_i = Sensor(with_prefix('I'), ' ', sensor_id=id_from_name(with_prefix('pid_i')),
                 state_func=lambda: pid_sensor.i, **standard_config)
    s_d = Sensor(with_prefix('D'), ' ', sensor_id=id_from_name(with_prefix('pid_d')),
                 state_func=lambda: pid_sensor.d, **standard_config)
    s_o = Sensor(with_prefix('Percent On'), '%', icon='mdi:power-socket-eu',
                 state_func=lambda: float(pid_sensor.control_percent), **standard_config)
    reg.add_component([s_p, s_i, s_d, s_o])

    # Create PID controller
    s_def = {
        'mqtt': mqtt_broker,
        'availability_topic': availability_topic,
        'auto_discovery': auto_discovery,
        'icon': 'mdi:cursor-move'
    }
    pid_controller = Pid(avg_w, ssr, pid_sensor)
    reg.add_component(SettableSensor('P', '', 0, 10, 0.1,
                                     pid_controller.p, lambda v: pid_controller.set_p(v),
                                     sensor_id=id_from_name(with_prefix('pid_p_gain')),
                                     **s_def
                                     ), send_updates=False)
    reg.add_component(SettableSensor('I', '', 0, 10, 0.1,
                                     pid_controller.i, lambda v: pid_controller.set_i(v),
                                     sensor_id=id_from_name(with_prefix('pid_i_gain')),
                                     **s_def), send_updates=False)
    reg.add_component(SettableSensor('D', '', 0, 10, 0.1,
                                     pid_controller.d, lambda v: pid_controller.set_d(v),
                                     sensor_id=id_from_name(with_prefix('pid_d_gain')),
                                     **s_def), send_updates=False)
    reg.add_component(SettableSensor('Out Limit', '', 0, 10, 1,
                                     pid_controller.output_limit,
                                     lambda v: pid_controller.set_output_limit(v),
                                     sensor_id=id_from_name(with_prefix('pid_output_limit')),
                                     **s_def), send_updates=False)
    reg.add_component(SettableSensor('Time', '', 0, 10, 1,
                                     pid_controller.sample_time,
                                     lambda v: pid_controller.set_sample_time(v),
                                     sensor_id=id_from_name(with_prefix('pid_sample_time')),
                                     **s_def), send_updates=False)

    # Create Time On Target sensor
    tat = TimeOnTarget(pid_controller)
    reg.add_component(Sensor(with_prefix('Time On Target'), '',
                             state_func=errors.wrap_function(tat),
                             icon='mdi:clock',
                             device_class='timestamp',
                             state_formatter_func=lambda s: s,
                             **standard_config))

    # Create HA climate
    climate = Climate(
        with_prefix(),
        avg_w,
        state_change_func=lambda mode, target: pid.state_change(mode, target),
        mqtt=mqtt_broker,
        availability_topic=availability_topic,
        auto_discovery=auto_discovery,
        # state_topic=state
    )
    reg.add_component(climate)

    if not SIMULATE:
        # RPI temp sensor
        reg.add_component(Sensor(
            with_prefix('Temp CPU'),
            '°C',
            state_func=cpu_temp,
            **standard_config
        ))

    cfg = reg.create_config()
    file = '/tmp/ha-cfg.yml'
    logging.info("Writing HA config to file: {}".format(file))
    with open(file, 'w') as f:
        f.write(cfg)

    if env_bool('HA_PRINT_CONFIG', False):
        logging.info("HA config:\n{}".format(cfg))

    return func_limit, pid_controller, reg, climate


RUN = True


def kill(*args):
    global RUN
    if RUN:
        logging.info("Stopping controller")
    RUN = False


signal.signal(signal.SIGINT, kill)
signal.signal(signal.SIGTERM, kill)
atexit.register(kill)

if __name__ == "__main__":
    logging.getLogger().handlers = []
    setup_logging()
    logging.info("Starting controller")
    with Mqtt(env('MQTT_HOST', 'localhost'), env('MQTT_USER'), env('MQTT_PASS')) as mqtt:
        func_limiter, pid, registry, climate = create_components(mqtt)
        with registry:
            registry.send_updates(force_all=True)
            climate.send_update(all_topics=True)

            logging.info("Entering main loop")
            while RUN:
                func_limiter.clear()
                pid.update()
                registry.send_updates()
                sleep_for(env_float('SLEEP_PER_ITERATION', 0))
            logging.info("Exiting main loop")
