
import time
from umqttsimple import MQTTClient
import gc
import esp
import ubinascii
import machine
import ujson as json
from secrets import secrets

esp.osdebug( None )
gc.collect()

def update_thread( mqtt ):
    while True:
        #try:
        mqtt.wait_msg()
        #except OSError as e:
        #    print( 'err' )
        time.sleep( 1 )

def mqtt_sub_cb( topic, msg ):
    if b'beepterm/display' == topic:
        try:
            msg = json.loads( str( msg, 'utf-8' ) )
            x = 0
            if 'x' in msg:
                x = msg['x']
            y = 0
            if 'y' in msg:
                y = msg['y']
            if 'c' in msg and msg['c']:
                oled.fill( 0 )
            oled.text( msg['m'], x, OLED_CYAN_TOP + y )
            oled.show()
        except:
            print( 'bad msg' )
    
    elif b'beepterm/color' == topic:
        try:
            msg = json.loads( str( msg, 'utf-8' ) )
            np[0] = (msg['r'], msg['g'], msg['b'])
            np.write()
        except:
            print( 'bad msg' )

    elif b'beepterm/beep' == topic:
        try:
            msg = json.loads( str( msg, 'utf-8' ) )
            buzz.duty( msg['d'] )
            buzz.freq( msg['f'] )
            time.sleep_ms( msg['ms'] )
            buzz.deinit()
        except:
            print( 'bad msg' )

oled.fill( 0 )
#oled.text( '{}'.format( sta_if.ifconfig()[0] ), 0, 0 )
oled.text( 'Connecting MQTT...', 0, OLED_CYAN_TOP )
oled.show()

mqtt = MQTTClient(
    ubinascii.hexlify( machine.unique_id() ),
    secrets['mqtt_srv'], ssl=True )
mqtt.set_callback( mqtt_sub_cb )
mqtt.connect()
mqtt.subscribe( b'beepterm/display' ) 
mqtt.subscribe( b'beepterm/color' ) 
mqtt.subscribe( b'beepterm/beep' ) 

update_thread( mqtt )

oled.fill( 0 )
oled.text( 'Ready.', 0, OLED_CYAN_TOP )
oled.show()

