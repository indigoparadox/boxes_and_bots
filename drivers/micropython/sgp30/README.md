# SGP30 Micropython Driver

This is the Micropython driver for the SGP30 gas sensor. Originally created by
Lady Ada from Adafruit. It was adapted by various different people throughout
time and space. Git history should be able to show all of the contributors.
This fork has been refactored by Robert Hughes, because he's a nitpicking
bugger who likes things just so.

## Use

This has been used on an ESP8266. Full details of the build will be available
on my blog once I'm finished. The posts so far are:

* https://safuya.net/esp-weather-station-part-1.html
* https://safuya.net/learning-electronics-basics.html

The below code should get you going on the ESP8266.

```python
from machine import I2C, Pin
from sgp30 import SGP30

i2c = I2C(scl=Pin(5), sda=Pin(4), freq=100000)
sgp30 = SGP30(i2c)
sgp30.indoor_air_quality
```

## Contributing

Contributions are welcome. Please read the code of conduct before contributing
to help this project stay welcoming.
