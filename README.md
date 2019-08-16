<h1>hass-pid-thermostat</h1>

A PID (climate) controller for [Home Assistant](https://www.home-assistant.io/) to heat/cool something using a thermometer and a SSR relay. Here is an example of a card that shows up in Home Assistant:

![Card](docs/hass_card.jpg)

## Table of Contents

- [Table of Contents](#table-of-contents)
- [Setup](#setup)
  - [Home Assistant](#home-assistant)
  - [Deploy with Balena.io](#deploy-with-balenaio)
- [Configuration](#configuration)
- [Electrical Components](#electrical-components)
  - [Parts I used](#parts-i-used)
  - [Wiring](#wiring)
  - [End result](#end-result)

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
| SSR_PIN                | no       | GPIO18                      | [Pin name](https://gpiozero.readthedocs.io/en/stable/recipes.html#pin-numbering) on the Raspberry PI the SSR is connected to |
| TEMP_POLL_INTERVAL     | no       | 0.5                         | Seconds between new temperature readings                                                                                     |
| HASS_ID                | no       | hass_thermostat_(heat/cool) | Id for component in hass.io                                                                                                  |
| HASS_NAME              | no       | Brew (Boiler/Cooler)        | Name that show up in the hass.io UI                                                                                          |
| HASS_UPDATE_INTERVAL   | no       | 2                           | Seconds between updates being sent to hass.io                                                                                |
| MQTT_HOST              | no       | hassio.local                | The host of the MQTT server to communicate with hass.io                                                                      |
| PID_P_GAIN             | no       | 2.5                         | PID proportional gain                                                                                                        |
| PID_I_GAIN             | no       | 0.005                       | PID integral gain                                                                                                            |
| PID_D_GAIN             | no       | 0.2                         | PID derivative gain                                                                                                          |
| PID_SAMPLE_TIME        | no       | 8                           | Amount of time between each PID update                                                                                       |

## Electrical Components

> **_VERY IMPORTANT NOTE:_**  THIS IS NOT A HOW-TO instructional guide. This explains how I used a Raspberry Pi to control electric current. However, I am NOT an electrician, and just because I did something doesn’t mean YOU should, particularly if you are unfamiliar with how to wire electrical devices safely. If you choose to follow the method I used, you do so at your own risk.

### Parts I used

* [Raspberry PI model B](https://www.google.com/search?q=Raspberry+PI+Model+B)
* [Kudom 40 A Solid State Relay](https://www.google.com/search?q=Kudom+40+A+Solid+State+Relay)
* [DS18b20 temperature sensor](https://www.google.com/search?q=ds18b20+temperature+sensor)
* [4.7k ohm resistor](https://www.google.com/search?q=4.7k+ohm+resistor)

### Wiring

![Wiring1](docs/wiring1.jpg)

### End result

![Wiring2](docs/wiring2.jpg)