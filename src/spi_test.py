import math
import time

import spidev

spi_ch = 0

# Enable SPI
spi = spidev.SpiDev(0, spi_ch)
spi.max_speed_hz = 1200000


def read_adc(adc_ch, vref=3.3):
    # Make sure ADC channel is 0 or 1
    if adc_ch != 0:
        adc_ch = 1

    # Construct SPI message
    #  First bit (Start): Logic high (1)
    #  Second bit (SGL/DIFF): 1 to select single mode
    #  Third bit (ODD/SIGN): Select channel (0 or 1)
    #  Fourth bit (MSFB): 0 for LSB first
    #  Next 12 bits: 0 (don't care)
    msg = 0b11
    msg = ((msg << 1) + adc_ch) << 5
    msg = [msg, 0b00000000]
    reply = spi.xfer2(msg)
    print(reply)

    # Construct single integer out of the reply (2 bytes)
    adc = 0
    for n in reply:
        adc = (adc << 8) + n

    # Last bit (0) is not part of ADC value, shift to remove it
    adc = adc >> 1

    return adc


# https://www.thinksrs.com/downloads/programs/therm%20calc/ntccalibrator/ntccalculator.html
# //Steinhart-Hart model coefficients
sha = 2.114990448E-03
shb = 0.383238122E-04
shc = 5.228061052E-07

# Report the channel 0 and channel 1 voltages to the terminal
while True:
    adc_0 = read_adc(0)
    rV = (1024.0 / adc_0 - 1) * 1000.0
    tempK = 1 / (sha + (shb * math.log(rV)) + (shc * math.pow(math.log(rV), 3)))
    tempC = tempK - 273.15
    print("Ch 0:", adc_0, "Temp:", tempC)
    time.sleep(2)

# double rV = ((1024D/adcValue) - 1D)*1000D;
# //Steinhart-Hart model coefficients
#
# double tempK = 1/(9.6564E-04 + (2.1069E-04*Math.Log(rV)) + (8.5826E-08*Math.Pow(Math.Log(rV), 3)));
#  double tempC = tempK - 273.15;
