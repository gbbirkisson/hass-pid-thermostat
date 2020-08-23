import time

from ds18b20 import DS18B20

from devices.spi import SpiTempSensor

# spi_ch = 0
#
# # Enable SPI
# spi = spidev.SpiDev(0, spi_ch)
# spi.max_speed_hz = 1200000
#
#
# def read_adc(adc_ch, vref=3.3):
#     # Make sure ADC channel is 0 or 1
#     if adc_ch != 0:
#         adc_ch = 1
#
#     # Construct SPI message
#     #  First bit (Start): Logic high (1)
#     #  Second bit (SGL/DIFF): 1 to select single mode
#     #  Third bit (ODD/SIGN): Select channel (0 or 1)
#     #  Fourth bit (MSFB): 0 for LSB first
#     #  Next 12 bits: 0 (don't care)
#     msg = 0b11
#     msg = ((msg << 1) + adc_ch) << 5
#     msg = [msg, 0b00000000]
#     reply = spi.xfer2(msg)
#     print(reply)
#
#     # Construct single integer out of the reply (2 bytes)
#     adc = 0
#     for n in reply:
#         adc = (adc << 8) + n
#
#     # Last bit (0) is not part of ADC value, shift to remove it
#     adc = adc >> 1
#
#     return adc
#
#
# def get_adc(channel):
#     # Only 2 channels 0 and 1 else return -1
#     if ((channel > 1) or (channel < 0)):
#         return -1
#
#     # Send start bit, sgl/diff, odd/sign, MSBF
#     # channel = 0 sends 0000 0001 1000 0000 0000 0000
#     # channel = 1 sends 0000 0001 1100 0000 0000 0000
#     # sgl/diff = 1; odd/sign = channel; MSBF = 0
#     r = spi.xfer2([1, (2 + channel) << 6, 0])
#
#     # spi.xfer2 returns same number of 8 bit bytes
#     # as sent. In this case, 3 - 8 bit bytes are returned
#     # We must then parse out the correct 10 bit byte from
#     # the 24 bits returned. The following line discards
#     # all bits but the 10 data bits from the center of
#     # the last 2 bytes: XXXX XXXX - XXXX DDDD - DDDD DDXX
#     ret = ((r[1] & 31) << 6) + (r[2] >> 2)
#     return ret


# # Steinhart-Hart model coefficients
# # https://www.thinksrs.com/downloads/programs/therm%20calc/ntccalibrator/ntccalculator.html
# sha = 2.114990448E-03
# shb = 0.383238122E-04
# shc = 5.228061052E-07
#
# # Aux resistor
# # https://www.hackster.io/ahmartareen/iot-temperature-sensor-with-raspberry-pi-2-and-thermistor-7e12db
# aux_res = 10000.0

# spi = SpiTempSensor()

ds = DS18B20.get_available_sensors()

if len(ds) == 1:
    ds = DS18B20(ds[0])
else:
    ds = None

while True:
    # t = spi.get_temperature()
    # a = spi.get_adc()
    # print("Name:", spi.get_id(), "Ch 0:", a, "Temp:", t)
    if ds is not None:
        print("Name:", ds.get_id(), "Temp:", ds.get_temperature())

    time.sleep(1)

# double rV = ((1024D/adcValue) - 1D)*1000D;
# //Steinhart-Hart model coefficients
#
# double tempK = 1/(9.6564E-04 + (2.1069E-04*Math.Log(rV)) + (8.5826E-08*Math.Pow(Math.Log(rV), 3)));
#  double tempC = tempK - 273.15;
