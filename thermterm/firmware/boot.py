
from machine import Pin, I2C, PWM, freq, deepsleep, RTC
from neopixel import NeoPixel
from secrets import secrets
from dht import DHT22
import machine
import network
import ssd1306
import time
import ntptime

def update_time():
    try:
        ntptime.host = secrets['ntp']
        ntptime.settime()
        t1 = time.time()
        t2 = t1 + (secrets['tz'] * 3600)
        (yr, mn, md, hr, mn, sc, wd, yd) = time.localtime( t2 )
        rtc.datetime( (yr, mn, md, 0, hr, mn, sc, 0) )
    except OSError as e:
        print( e )

freq( 80000000 )

OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_CYAN_TOP = 16

sta_if = network.WLAN( network.STA_IF )
sta_if.active( True )
sta_if.connect( secrets['ssid'], secrets['wpa2'] )
while not sta_if.isconnected():
    pass

i2c = I2C( 0, scl=Pin( 18 ), sda=Pin( 19 ), freq=100000 )
oled = ssd1306.SSD1306_I2C( OLED_WIDTH, OLED_HEIGHT, i2c, addr=0x3c )

np = NeoPixel( Pin( 23 ), 1 )

dhts = DHT22( Pin( 16 ) )

rtc = RTC()
if machine.DEEPSLEEP != machine.reset_cause() and \
machine.SOFT_RESET != machine.reset_cause():
    update_time()

    np[0] = (0, 0, 0)
    np.write()

    buzz = PWM( Pin( 26 ) )
    buzz.freq( 800 )
    buzz.duty( 512 )
    time.sleep_ms( 200 )
    buzz.deinit()

