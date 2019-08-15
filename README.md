<h1>hass-pid-thermostat<h1>

A PID (climate) controller for [Home Assistant](https://www.home-assistant.io/) to heat/cool something using a thermometer and a SSR relay.

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Setup](#setup)
  - [Home Assistant](#home-assistant)
  - [Deploy with Balena.io](#deploy-with-balenaio)
- [Configuration](#configuration)
- [Electrical Components](#electrical-components)

## Setup

### Home Assistant

Enable mqtt discovery by adding to HASS config:

```yaml
mqtt:
  broker: localhost # Depends on your setup
  discovery: true
```

### Deploy with Balena.io

* Edit the `config.txt` in balena-boot partition of the SD card and append the following lines:
    * `dtoverlay=w1-gpio`
* Add remote your balena remote:
    * `git remote add balena <USERNAME>@git.balena-cloud.com:<USERNAME>/<APPNAME>.git`
* Push to balena:
    * `git push balena master`

## Configuration

| Environmental variable | Required | Default                     | Description                                                                                                                  |
| ---------------------- | -------- | --------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| SSR_PIN                | yes      | None                        | [Pin name](https://gpiozero.readthedocs.io/en/stable/recipes.html#pin-numbering) on the Raspberry PI the SSR is connected to |
| TEMP_POLL_INTERVAL     | no       | 0.5                         | Seconds between new temperature readings                                                                                     |
| HASS_ID                | no       | hass_thermostat_(heat/cool) | Id for component in hass.io                                                                                                  |
| HASS_NAME              | no       | Brew (Boiler/Cooler)        | Name that show up in the hass.io UI                                                                                          |
| HASS_UPDATE_INTERVAL   | no       | 2                           | Seconds between updates being sent to hass.io                                                                                |
| HASS_HOST              | no       | hassio.local                | The host of hass.io                                                                                                          |
| PID_P_GAIN             | no       | 2.5                         | PID proportional gain                                                                                                        |
| PID_I_GAIN             | no       | 0.005                       | PID integral gain                                                                                                            |
| PID_D_GAIN             | no       | 0.2                         | PID derivative gain                                                                                                          |
| PID_SAMPLE_TIME        | no       | 8                           | Amount of time between each PID update                                                                                       |

## Electrical Components

TODO...