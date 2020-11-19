
from machine import UART, Pin, PWM
from secrets import secrets
from lcdbp import LCDBackpack
import gc
import network
import time
import webrepl

webrepl.start()

u = UART( 2 )
u.init( tx=10, rx=9 )
bp = LCDBackpack( u )
bp.clear()

fan = Pin( 2, mode=Pin.OUT )
fan.value( 1 )

bp.write_line( "Free mem: {}".format( gc.mem_free() ) )

sta_if = network.WLAN( network.STA_IF )
sta_if.active( True )
sta_if.connect( secrets['ssid'], secrets['wpa2'] )
bp.write_line( "Connecting..." )
while not sta_if.isconnected():
   pass
bp.write_line( "IP: {}".format( sta_if.ifconfig()[0] ) )

time.sleep_ms( 500 )

buzz = PWM( Pin( 25 ), freq=800, duty=1000 )
time.sleep_ms( 100 )
buzz.deinit()

