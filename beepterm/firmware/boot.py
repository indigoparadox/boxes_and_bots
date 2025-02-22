# This is script that run when device boot up or wake from sleep.

from machine import Pin, I2C, PWM
from neopixel import NeoPixel
from secrets import secrets
import ssd1306
import network
import time
import machine

OLED_CYAN_TOP = 16
OLED_WIDTH = 128
OLED_HEIGHT = 64

i2c = I2C( -1, scl=Pin( 5 ), sda=Pin( 4 ) )
oled = ssd1306.SSD1306_I2C( OLED_WIDTH, OLED_HEIGHT, i2c )

oled.text( 'BeepTerm', 0, OLED_CYAN_TOP )
oled.show()

np = NeoPixel( Pin( 13 ), 1 )
np[0] = (255, 0, 0)
np.write()
time.sleep_ms( 300 )
np[0] = (0, 255, 0)
np.write()
time.sleep_ms( 300 )
np[0] = (0, 0, 255)
np.write()
time.sleep_ms( 300 )

buzz = PWM( Pin( 14 ) )
buzz.duty( 400 )
buzz.freq( 1800 )
time.sleep_ms( 200 )
buzz.deinit()

# Connect to the network.
oled.fill( 0 )
oled.text( 'Connecting WiFi...', 0, 0 )
oled.show()
sta_if = network.WLAN( network.STA_IF )
sta_if.active( True )
sta_if.connect( secrets['ssid'], secrets['wpa2'] )
while not sta_if.isconnected():
    pass

oled.fill( 0 )
oled.text( '{}'.format( sta_if.ifconfig()[0] ), 0, 0 )
oled.text( 'Connected.', 0, OLED_CYAN_TOP )
oled.show()

