import logging


class Hass:
    _mqtt_client = None
    _mqtt_topic_prefix = None

    def __init__(
            self,
            mqtt_client,
            object_id=None,
            component=None,
            discovery_prefix='homeassistant',
            node_id=None,
    ):
        assert object_id is not None, "object id cannot be None"
        assert component is not None, "component cannot be None"

        self._mqtt_topic_prefix = '{}/{}/{}/'.format(
            discovery_prefix,
            component,
            '{}/{}'.format(node_id, object_id) if node_id else object_id
        )

        self._mqtt_client = mqtt_client

    def get_topic(self, name):
        return self._mqtt_topic_prefix + name

    def connect(self, config):
        assert config is not None, "config cannot be None"
        logging.info('Connecting to hass')
        self._mqtt_client.publish(self.get_topic('config'), config)

    def disconnect(self):
        logging.info('Exiting, removing component from hass')
        self._mqtt_client.publish(self.get_topic('config'), None)
        self._mqtt_client.disconnect()

    def send(self, topic):
        def real_decorator(func):
            def wrapper(*args, **kwargs):
                self._mqtt_client.publish(topic, func(*args, **kwargs))

            return wrapper

        return real_decorator

    def receive(self, topic):
        def real_decorator(func):
            self._mqtt_client.subscribe(topic, func)
            return func

        return real_decorator
