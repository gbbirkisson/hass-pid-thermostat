from hass.hass import Hass
from hass.mqtt import Mqtt


def build_component(id, component, host):
    mqtt = Mqtt(id, host)
    return Hass(mqtt, object_id=id, component=component)
