import math

import spidev

# Steinhart-Hart model coefficients
# R1: 100000 T1: 27
# R2: 31500  T2: 55
# R3: 9850  T3: 90

# https://www.thinksrs.com/downloads/programs/therm%20calc/ntccalibrator/ntccalculator.html
SHC_A = 0.2610558231E-03
SHC_B = 2.787741809E-04
SHC_C = -0.9101826706E-07

# Aux resistor
# https://www.hackster.io/ahmartareen/iot-temperature-sensor-with-raspberry-pi-2-and-thermistor-7e12db
AUX_RES = 10000.0

# Adc resolution
ADC_RES = 1024.0


class SpiTempSensor:
    def __init__(self, device=0, channel=0):
        self._spi = spidev.SpiDev(0, device)
        self._spi.max_speed_hz = 1200000
        self._channel = channel
        self._last_adc = 0

    def _get_adc(self):
        # Only 2 channels 0 and 1 else return -1
        if ((self._channel > 1) or (self._channel < 0)):
            return -1

        # Send start bit, sgl/diff, odd/sign, MSBF
        # channel = 0 sends 0000 0001 1000 0000 0000 0000
        # channel = 1 sends 0000 0001 1100 0000 0000 0000
        # sgl/diff = 1; odd/sign = channel; MSBF = 0
        r = self._spi.xfer2([1, (2 + self._channel) << 6, 0])

        # spi.xfer2 returns same number of 8 bit bytes
        # as sent. In this case, 3 - 8 bit bytes are returned
        # We must then parse out the correct 10 bit byte from
        # the 24 bits returned. The following line discards
        # all bits but the 10 data bits from the center of
        # the last 2 bytes: XXXX XXXX - XXXX DDDD - DDDD DDXX
        self._last_adc = ((r[1] & 31) << 6) + (r[2] >> 2)
        return self._last_adc

    def get_adc(self):
        return self._last_adc

    def get_temperature(self):
        adc = self._get_adc()
        if adc == 0:
            return None
        rv = (ADC_RES / adc - 1) * AUX_RES
        temp_kelvin = 1 / (SHC_A + (SHC_B * math.log(rv)) + (SHC_C * math.pow(math.log(rv), 3)))
        # = (1 / ($F$1 + ($F$2 * LN(D1)) + ($F$3 * POW(LN(D1),3)))) - 273.15
        return temp_kelvin - 273.15

    def get_id(self):
        return 'MCP3002_{}'.format(self._channel)
