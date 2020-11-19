
from machine import Pin, I2C
import ssd1306
import time
import network
from secrets import secrets
import ujson as json
import urequests as requests
from microdot import Microdot, Response
import _thread as thread

OLED_CYAN_TOP = 16
OLED_WIDTH = 128
OLED_HEIGHT = 64

WEATHER_URL = 'http://weather.interfinitydynamics.info/current.json'
WEATHER_REFRESH = 10

HTML_TEMPL = '''
<!doctype html>
<html>
<head>
</head>
<body>
Foo
</body>
</html>
'''

aux_text = ''

def update_thread():
    counter = 0
    next_weather = 0
    weather = {}
    while True:
        # Blank screen and show IP.
        oled.fill( 0 )
        oled.text( '{}'.format( sta_if.ifconfig()[0] ), 0, 0 )
        
        if next_weather <= counter:
            weather = json.loads( requests.get( WEATHER_URL ).text )
            next_weather = counter + WEATHER_REFRESH

        #print( weather['stats']['current'] )
        oled.text( 
            weather['stats']['current']['outTemp'].replace( '&#176;', '' ),
            0, OLED_CYAN_TOP )

        oled.text(
            '{} ({})'.format( counter, next_weather ), 0, OLED_CYAN_TOP + 10 )

        oled.text( aux_text, 0, OLED_CYAN_TOP + 20 )

        counter += 1

        oled.show()

        time.sleep( 1 )

# ESP32 Pin assignment 
i2c = I2C()
oled = ssd1306.SSD1306_I2C( OLED_WIDTH, OLED_HEIGHT, i2c )

# Connect to the network.
oled.text( 'Connecting...', 0, 0 )
oled.show()
sta_if = network.WLAN( network.STA_IF )
sta_if.active( True )
sta_if.connect( secrets['ssid'], secrets['wpa2'] )
while not sta_if.isconnected():
    pass

thread.start_new_thread( update_thread, () )

app = Microdot()

print( 'run' )
@app.route( '/', methods=['GET'] )
def root( req ):
    response = Response( body=HTML_TEMPL, headers={'Content-Type': 'text/html'} )

    return response

app.run()

#while True:
#    pass

