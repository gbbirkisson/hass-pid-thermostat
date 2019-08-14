# hass-pid-thermostat

A PID (climate) controller for [Home Assistant](https://www.home-assistant.io/) to heat/cool something using a thermometer and a SSR relay.

## Add to Home Assistant

Enable mqtt discovery by adding to HASS config:

```yaml
mqtt:
  broker: localhost # Depends on your setup
  discovery: true
```