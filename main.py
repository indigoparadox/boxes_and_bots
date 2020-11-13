
from machine import ADC, I2C, unique_id
from sgp30 import SGP30
from pixy import CMUcam5
from simple2 import MQTTClient, MQTTException
from robocon import SixLegsController
from neopixel import NeoPixel
import ubinascii
import gc
import esp
import ujson as json
import time


DEBUG = False
esp.osdebug( None )
gc.collect()

SENSOR_COUNTDOWN_START = 10

RANGE_MAX = 2000
RANGE_THRESH = 1000

force_color = 0

def play_buzz( freq, duty, ms ):
    buzz = PWM( Pin( 14 ) )
    try:
        buzz.duty( duty )
        buzz.freq( freq )
        time.sleep_ms( ms )
    except Exception as e:
        print( e )
    buzz.deinit()

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

def mqtt_sub_cb( topic, msg, retained, dup ):
    global force_color
    try:
        if b'sixlegs/color' == topic:
            if b'#000000' == msg:
                force_color = 0
            else:
                msg = str( msg, 'utf-8' ).lstrip( '#' )
                force_color = tuple( int( msg[i:i+2], 16 ) for i in (0, 2, 4) )

        elif b'sixlegs/rotate-ccw' == topic:
            delay = int( str( msg, 'utf-8' ) )
            robo.rotate_ccw( delay )

        elif b'sixlegs/rotate-cw' == topic:
            delay = int( str( msg, 'utf-8' ) )
            robo.rotate_cw( delay )

        elif b'sixlegs/walk-fwd' == topic:
            delay = int( str( msg, 'utf-8' ) )
            robo.walk_fwd( delay )

        elif b'sixlegs/walk-rev' == topic:
            delay = int( str( msg, 'utf-8' ) )
            robo.walk_rev( delay )

        elif b'sixlegs/buzz' == topic:
            buzz_data = json.loads( str( msg, 'utf-8' ) )
            if not isinstance( buzz_data, list ):
                buzz_data = [buzz_data]
            for b in buzz_data:
                duty = b['d']
                freq = b['f']
                ms = b['ms']
                play_buzz( freq, duty, ms )

    except Exception as e:
        print( 'bad msg ({}): {}'.format( e, msg ) )

def idle_thread():
    global force_color
    global mqtt
    counter = 0
    sensor_countdown = SENSOR_COUNTDOWN_START
    while True:
        for rc_index in range( 255 ):
            check_mqtt()

            # Grab sensor data.
            r = adc.read() # Rangefinder.
            iaq = sgp.indoor_air_quality

            # Publish sensor data.
            if 0 >= sensor_countdown:
                sensor_countdown = SENSOR_COUNTDOWN_START
                try:
                    if r > RANGE_THRESH:
                        mqtt.publish( 'sixlegs/range', str( r ) )
                    else:
                        mqtt.publish( 'sixlegs/range', '0' )

                    mqtt.publish( 'sixlegs/iaq-co2', str( iaq[0] ) )
                    mqtt.publish( 'sixlegs/iaq-tvoc', str( iaq[1] ) )
                except Exception as e:
                    print( 'mqtt error publishing sensors: {}'.format( e ) )
            else:
                sensor_countdown -= 1
                if DEBUG:
                    print( sensor_countdown )
    
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
        ssl=kwargs['mqtt_ssl'],
        port=kwargs['mqtt_port'],
        user=kwargs['mqtt_user'],
        password=kwargs['mqtt_pass'],
        socket_timeout=kwargs['mqtt_timeout'] )
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

