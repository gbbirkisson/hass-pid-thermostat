#!/bin/bash

export GPIOZERO_PIN_FACTORY="native"

modprobe w1-gpio
modprobe w1-therm

exec python -u main.py