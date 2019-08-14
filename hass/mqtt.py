import json
import logging

from paho.mqtt.client import Client as MqttClient


class Mqtt:
    _mqtt_client = None
    _mqtt_topic_prefix = None
    _mqtt_subs = {}

    def __init__(
            self,
            id,
            host='localhost'
    ):
        assert id is not None, "id cannot be none"

        self._mqtt_client = MqttClient(id)
        self._mqtt_client.enable_logger(logging.getLogger(__name__))
        self._mqtt_client.connect(host)
        self._mqtt_client.on_message = self._on_message
        self._mqtt_client.loop_start()

    def publish(self, topic, message):
        if type(message) is dict:
            message = json.dumps(message)
        message = message if message is not None else ""
        logging.debug('MQTT msg sent on topic {}: {}'.format(topic, message))
        self._mqtt_client.publish(topic, message)

    def subscribe(self, topic, func):
        logging.info('MQTT subscribing to {}'.format(topic))
        sub_functions = self._mqtt_subs.get(topic, [])
        if len(sub_functions) == 0:
            self._mqtt_client.subscribe(topic)
        sub_functions.append(func)
        self._mqtt_subs[topic] = sub_functions

    def _on_message(self, client, userdata, message):
        payload = str(message.payload.decode("utf-8"))
        logging.debug('MQTT msg received on topic {}: {}'.format(message.topic, payload))
        sub_functions = self._mqtt_subs.get(message.topic, [])
        for func in sub_functions:
            func(payload)

    def disconnect(self):
        self._mqtt_client.loop_stop()
        self._mqtt_client.disconnect()
