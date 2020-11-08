# This file is executed on every boot (including wake-boot from deepsleep)
#import esp
#esp.osdebug(None)

from secrets import secrets
import network
sta_if = network.WLAN( network.STA_IF )
sta_if.active( True )
sta_if.connect( secrets['ssid'], secrets['wpa2'] )

import webrepl
webrepl.start()

from machine import Pin

spin1 = Pin( 15, Pin.OUT )
spin1.value( 0 )
spin2 = Pin( 5, Pin.OUT )
spin2.value( 0 )

motor1 = Pin( 4, Pin.OUT )
motor1.value( 0 )
motor2 = Pin( 2, Pin.OUT )
motor2.value( 0 )

from neopixel import NeoPixel

np = NeoPixel( Pin( 27 ), 1 )
np[0] = (0, 255, 0)
np.write()

