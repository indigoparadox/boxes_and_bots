
from machine import ADC
from machine import I2C
from machine import unique_id
from sgp30 import SGP30
from pixy import CMUcam5
from simple2 import MQTTClient, MQTTException
from robocon import SixLegsController
import ubinascii
import gc
import esp
import ujson as json

DEBUG = False
esp.osdebug( None )
gc.collect()

def wheel( pos ):
    # Input a value 0 to 255 to get a color value.
    # The colours are a transition r - g - b - back to r.
    if pos < 0 or pos > 255:
        return (0, 0, 0)
    if pos < 85:
        return (255 - pos * 3, pos * 3, 0)
    if pos < 170:
        pos -= 85
        return (0, 255 - pos * 3, pos * 3)
    pos -= 170
    return (pos * 3, 0, 255 - pos * 3)

from neopixel import NeoPixel
import time

RANGE_MAX = 2000
RANGE_THRESH = 700

force_color = 0

def mqtt_sub_cb( topic, msg, retained, dup ):
    global force_color
    if b'sixlegs/color' == topic:
        if b'#000000' == msg:
            force_color = 0
        else:
            try:
                msg = str( msg, 'utf-8' ).lstrip( '#' )
                force_color = tuple( int( msg[i:i+2], 16 ) for i in (0, 2, 4) )
            except Exception as e:
                print( 'bad msg ({}): {}'.format( e, msg ) )

    elif b'sixlegs/rotate-ccw' == topic:
        try:
            delay = int( str( msg, 'utf-8' ) )
            robo.rotate_ccw( delay )
        except Exception as e:
            print( 'bad msg ({}): {}'.format( e, msg ) )

    elif b'sixlegs/rotate-cw' == topic:
        try:
            delay = int( str( msg, 'utf-8' ) )
            robo.rotate_cw( delay )
        except Exception as e:
            print( 'bad msg ({}): {}'.format( e, msg ) )

def idle_thread():
    global force_color
    global mqtt
    counter = 0
    while True:
        for rc_index in range( 255 ):
            check_mqtt()

            # Grab front rangefinder distance.
            r = adc.read()
            if r > RANGE_THRESH:
                try:
                    mqtt.publish( 'sixlegs/range', str( r ) )
                except Exception as e:
                    print( e )
    
            # Detect visual objects (blocks) from PixyCam.
            try:
                blks = px.get_blocks( 1, 1 )
                if 0 < len( blks ):
                    for b in blks:
                        mqtt.publish( 'sixlegs/objects', b.toJSON() )
            except Exception as e:
                # Sometimes we fail for some reason.
                print( e )
    
            # Figure out what to do with LED.
            if 0 != force_color:
                np[0] = force_color

            elif r > RANGE_THRESH:
                # Change LED if obstacle in range.
                if r > RANGE_MAX:
                    # Sanity cap so that cross-multiply below works.
                    r = RANGE_MAX
                new_col = int( 255 * r / RANGE_MAX )
                np[0] = (255, 255 - new_col, 255 - new_col)
    
            elif len( blks ) > 0:
                # Blink LED if objects found.
                if counter > 5000:
                    counter = 0
                    np[0] = (0, 255, 0)
                elif counter > 2500:
                    np[0] = (0, 255, 0)
                else:
                    np[0] = (255, 255, 255)
    
                if DEBUG:
                    print( '---blk found---' )
                    print( 'sig: {}'.format( blks[0].sig ) )
                    print( 'x: {}'.format( blks[0].x ) )
                    print( 'y: {}'.format( blks[0].y ) )
                    print( 'idx: {}'.format( blks[0].idx ) )
                    print( '---end blk---' )
    
            else:
                # Cycle through rainbow if nothing else going on.
                np[0] = wheel( rc_index & 255 )
    
            #print( sgp.indoor_air_quality )
    
            # Perform housekeeping for this loop iter (write LED, sleep, etc.)
            np.write()
            counter += 1
            time.sleep_ms( 25 )

def check_mqtt():
    global mqtt

    # Grab any MQTT messages, or reconnect on failure.
    if None != mqtt:
        try:
            mqtt.check_msg()
        except MQTTException as e:
            if 0 < len( e.args ) and 1 == e.args[0]:
                mqtt = connect_mqtt( **secrets )
            print( 'mqtt error: {}'.format( e.args ) )
    else:
        # Last connect failed, so try again.
        mqtt = connect_mqtt( **secrets )

def connect_mqtt( **kwargs ):
    mqtt_out = MQTTClient(
        ubinascii.hexlify( unique_id() ),
        kwargs['mqtt_srv'],
        ssl=True if kwargs['ssl'] else False,
        socket_timeout=20 if kwargs['ssl'] else 5 )
    mqtt_out.set_callback( mqtt_sub_cb )
    try:
        mqtt_out.connect()
    except OSError as e:
        print( 'error connecting to mqtt: {}'.format( e ) )
        return None
    mqtt_out.subscribe( b'sixlegs/#' ) 
    return mqtt_out

mqtt = connect_mqtt( **secrets )
np = NeoPixel( Pin( 27 ), 1 )
adc = ADC( Pin( 36 ) )
adc.read()
adc.atten( ADC.ATTN_11DB )
i2c = I2C( scl=Pin( 22 ), sda=Pin( 21 ), freq=100000 )
sgp = SGP30( i2c )
px = CMUcam5( i2c )
#px.set_led( 0, 255, 0 )
robo = SixLegsController( spin2, spin1, motor1, motor2 )

idle_thread()

