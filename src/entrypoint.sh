#!/bin/bash

modprobe w1-gpio
modprobe w1-therm

#exec python -u main.py
exec python -u spi_test.py