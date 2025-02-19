#!/usr/bin/env python3

import displayio
from adafruit_minimqtt import adafruit_minimqtt
from blinka_displayio_pygamedisplay import PyGameDisplay

display = PyGameDisplay( width=320, height=240 )

group = displayio.Group()

display.show( group )

