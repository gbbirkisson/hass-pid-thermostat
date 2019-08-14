from hass.hass import Hass
from hass.mqtt import Mqtt


def build_component(id=None, component=None, mqtt=None):
    if mqtt is None:
        mqtt = Mqtt(id)
    return Hass(mqtt, object_id=id, component=component)
