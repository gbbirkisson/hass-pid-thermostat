import logging

from hass.mqtt import Mqtt


class Hass(Mqtt):

    def __init__(
            self,
            mqtt_host=None,
            object_id=None,
            component=None,
            discovery_prefix='homeassistant',
            node_id=None,
    ):
        super(Hass, self).__init__(mqtt_host, object_id)

        assert object_id is not None, "object id cannot be None"
        assert component is not None, "component cannot be None"

        self._config = None

        self._mqtt_topic_prefix = '{}/{}/{}/'.format(
            discovery_prefix,
            component,
            '{}/{}'.format(node_id, object_id) if node_id else object_id
        )

    def set_config(self, config):
        logging.info('Sending config to hass')
        self.publish(self.get_topic('config'), config)

    def get_topic(self, name):
        return self._mqtt_topic_prefix + name

    def __exit__(self, *args):
        logging.info('Removing component from hass')
        self.publish(self.get_topic('config'), None)
        super(Hass, self).__exit__(args)
