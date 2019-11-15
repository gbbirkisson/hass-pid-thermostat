import logging


class Hass():
    def __init__(
            self,
            mqtt=None,
            object_id=None,
            component=None,
            discovery_prefix='homeassistant',
            node_id=None,
    ):
        assert mqtt is not None, "object id cannot be None"
        assert object_id is not None, "object id cannot be None"
        assert component is not None, "component cannot be None"

        self._mqtt = mqtt
        self._config = None
        self._object_id = object_id
        self._component = component

        self._mqtt_topic_prefix = '{}/{}/{}/'.format(
            discovery_prefix,
            component,
            '{}/{}'.format(node_id, object_id) if node_id else object_id
        )

    def subscribe(self, topic, func):
        self._mqtt.subscribe(topic, func)

    def publish(self, topic, message):
        self._mqtt.publish(topic, message)

    def set_config(self, config):
        logging.info('HASS adding component {}.{}'.format(self._component, self._object_id))
        self._mqtt.publish(self.get_topic('config'), config)

    def get_topic(self, name):
        return self._mqtt_topic_prefix + name

    def __enter__(self):
        return self

    def __exit__(self, *args):
        logging.info('HASS removing component {}.{}'.format(self._component, self._object_id))
        self._mqtt.publish(self.get_topic('config'), None)
