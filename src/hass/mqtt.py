import json
import logging

from paho.mqtt.client import Client as Client


class Mqtt():
    _mqtt_client = None
    _mqtt_subs = {}

    def __init__(self, mqtt_host=None, mqtt_username=None, mqtt_password=None):
        assert mqtt_host is not None, 'host id cannot be None'

        self._host = mqtt_host
        self._mqtt_client = Client()
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.WARN)
        self._mqtt_client.enable_logger(logger)

        if mqtt_username is not None and mqtt_password is not None:
            logging.info('MQTT connecting with user and pass')
            self._mqtt_client.username_pw_set(mqtt_username, mqtt_password)

        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.on_connect = self._on_connect

    def _on_connect(self, client, userdata, flags, rc):
        if rc != 0:
            logging.error('MQTT failed to connect to {}: {}'.format(self._host, rc))
            raise SystemExit
        else:
            logging.info('MQTT successfully connected to host {}'.format(self._host))

    def _on_message(self, client, userdata, message):
        payload = str(message.payload.decode("utf-8"))
        logging.debug('MQTT msg received on topic {}: {}'.format(message.topic, payload))
        sub_functions = self._mqtt_subs.get(message.topic, [])
        for func in sub_functions:
            func(payload)

    def subscribe(self, topic, func):
        logging.debug('MQTT subscribing to {}'.format(topic))
        sub_functions = self._mqtt_subs.get(topic, [])
        if len(sub_functions) == 0:
            self._mqtt_client.subscribe(topic)
        sub_functions.append(func)
        self._mqtt_subs[topic] = sub_functions

    def publish(self, topic, message):
        if type(message) is dict:
            message = json.dumps(message)
        message = message if message is not None else ""
        logging.debug('MQTT msg sent on topic {}: {}'.format(topic, message))
        self._mqtt_client.publish(topic, message)

    def receive(self, topic):
        def real_decorator(func):
            self._mqtt_client.subscribe(topic, func)
            return func

        return real_decorator

    def send(self, topic):
        def real_decorator(func):
            def wrapper(*args, **kwargs):
                self._mqtt_client.publish(topic, func(*args, **kwargs))

            return wrapper

        return real_decorator

    def __enter__(self):
        logging.info('MQTT connecting to host {}'.format(self._host))
        self._mqtt_client.connect(self._host)
        self._mqtt_client.loop_start()
        return self

    def __exit__(self, *args):
        logging.info('MQTT disconnecting from host {}'.format(self._host))
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()
