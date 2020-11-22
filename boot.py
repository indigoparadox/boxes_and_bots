
from secrets import secrets
import network

sta_if = network.WLAN( network.STA_IF )
sta_if.active( True )
sta_if.connect( secrets['ssid'], secrets['wpa2'] )
while not sta_if.isconnected():
    pass

