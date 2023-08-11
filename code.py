
import busio
import board
import os
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import time
import displayio
import atexit
import traceback
import random
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from sensors import SensorBank

def on_reload( mqtt_client ):
    print( 'disconnecting MQTT...' )
    mqtt_client.disconnect()

def on_mqtt_connect( mqtt_client, userdata, flags, rc ):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print( 'connected to MQTT broker' )

def connect_wifi():
    connected = False
    while not connected:
        try:
            wifi.radio.connect(
                os.getenv( 'CIRCUITPY_WIFI_SSID' ),
                os.getenv( 'CIRCUITPY_WIFI_PASSWORD' ) )
            connected = True
        except ConnectionError as e:
            print( '{}: {}'.format( type( e ), e ) )
    return socketpool.SocketPool( wifi.radio )

def connect_mqtt( sensors, socket_pool ):
    if not os.getenv( 'MQTT_HOST' ):
        return None

    mqtt_client = MQTT.MQTT(
        broker=os.getenv( 'MQTT_HOST' ),
        port=os.getenv( 'MQTT_PORT' ),
        username=os.getenv( 'MQTT_USER' ),
        password=os.getenv( 'MQTT_PASSWORD' ),
        socket_pool=socket_pool
    )

    mqtt_client.will_set(
        'funhouse/{}/ip'.format( os.getenv( 'FUNHOUSE_ID' ) ),
        '',
        0,
        True )
    for sensor in sensors:
        for key in sensor['last_resp']:
            print( 'setting will for funhouse/{}/{}/{}'.format(
                    os.getenv( 'FUNHOUSE_ID' ),
                    sensor['name'],
                    key.replace( ' ', '_' ) ) )
            mqtt_client.will_set(
                'funhouse/{}/{}/{}'.format(
                    os.getenv( 'FUNHOUSE_ID' ),
                    sensor['name'],
                    key.replace( ' ', '_' ) ),
                '',
                0,
                True )
    mqtt_client.on_connect = on_mqtt_connect
    print( 'connecting to MQTT...' )
    mqtt_client.connect()
    atexit.register( on_reload, mqtt_client )
    return mqtt_client

def poll_sensor( idx : int, sensor : dict, i2c : busio.I2C, mqtt_client : MQTT.MQTT ) -> dict:
    try:

        if 'multiplex' in sensor:
            i2c = sensor['multiplex']( sensor, i2c )

        # Grab the sensor value dict from poller functions.
        poll_res = sensor['processor']( sensor['sensor'] )

        sensor['last_resp'] = poll_res

        # Create display string.
        try:
            sensor['values'] = {}
            sensor['values'] = {sensor['display_keys'][x]: poll_res[x] \
                for x in sensor['display_keys']}
        except Exception as e:
            print( 'poll error: {}: {} ({})'.format( type( e ), e, poll_res ) )

        # Publish all values to MQTT.
        for key in poll_res:
            if mqtt_client:
                mqtt_client.publish(
                    'funhouse/{}/{}/{}'.format(
                        os.getenv( 'FUNHOUSE_ID' ),
                        sensor['name'],
                        key.replace( ' ', '_' ) ),
                    poll_res[key],
                    True if os.getenv( 'MQTT_RETAIN' ) > 0 else False,
                    0 )
    except (KeyError, AttributeError, RuntimeError) as e:
        try:
            # Try to setup the sensor for the first time.
            print( 'read failed: {}: setting up {}...'.format( e, sensor['name'] ) )
            if 'class_args' in sensor:
                sensor['sensor'] = \
                    sensor['class']( i2c, **sensor['class_args'] )
            else:   
                sensor['sensor'] = sensor['class']( i2c )
        except Exception as e:
            # Sensor failure.
            print( 'setup error: {}: could not find sensor: {}'.format( sensor['name'], e ) )
            if os.getenv( 'DEBUG' ):
                traceback.print_exception( e )
    return sensor

def poll_all_sensors( sensors, mqtt_client, i2c ):

    for i in range( 0, sensors.count()  ):
        try:
            sensors[i] = poll_sensor( i, sensors[i], i2c, mqtt_client )
        except (MQTT.MMQTTException, OSError) as e:
            print( 'MQTT: {}: {}', type( e ), e )
            mqtt_client = None
    return sensors

def redraw( last_y, char_frame, sensors, char_bmp, balloon_bmp, font, mqtt ):

    display = board.DISPLAY
    group = displayio.Group()

    # Refresh character sprite.
    char_sprite = None
    if char_bmp:
        char_sprite = displayio.TileGrid(
            char_bmp,
            pixel_shader=char_bmp.pixel_shader,
            tile_width=32, tile_height=32, width=1, height=1,
            default_tile=0 )
        char_sprite.y = display.height - 32
        char_sprite.x = int( display.width / 2 ) - 16
        char_sprite[0, 0] = char_frame

    if os.getenv( 'DISPLAY_IP' ):
        ip_label = label.Label(
            font=font, text='{}'.format( wifi.radio.ipv4_address ) )
        ip_label.x = 10
        ip_label.y = last_y
        group.append( ip_label )
        last_y += 20

    if os.getenv( 'DISPLAY_MQTT' ): 
        mqtt_label = label.Label( \
            font=font, text='MQTT Connected' \
            if mqtt else 'MQTT Not Connected' )
        mqtt_label.x = 10
        mqtt_label.y = last_y
        group.append( mqtt_label )
        last_y += 20

    for i in range( 0, sensors.count()  ):
        for key in sensors[i]['display_keys']:
            try:
                display_key = sensors[i]['display_keys'][key]

                # Draw status icon.
                sprite = displayio.TileGrid(
                    balloon_bmp,
                    pixel_shader=balloon_bmp.pixel_shader,
                    tile_width=16, tile_height=16, width=1, height=1,
                    default_tile=0 )
                sprite.x = 10
                sprite.y = last_y - int( sprite.tile_height / 2 )
                if 'values' in sensors[i] and sensors[i]['values']:
                    if key in sensors[i]['thresholds'] and \
                    sensors[i]['values'][display_key] >= \
                    sensors[i]['thresholds'][key]:
                        # Alert balloon.
                        sprite[0, 0] = 8
                else:
                    # Question balloon.
                    sprite[0, 0] = 9
                group.append( sprite )

                # Draw status text.
                if 'values' in sensors[i] and sensors[i]['values']:
                    lbl_text = '{}: {}'.format(
                        display_key, sensors[i]['values'][display_key] )
                else:
                    lbl_text = '{}: Waiting...'.format( display_key )

                lbl = label.Label( font=font, text=lbl_text )
                lbl.x = 30
                lbl.y = last_y
                last_y += 20
                group.append( lbl )
            except Exception as e:
                print( 'label error: {}: {}'.format( type( e ), e ) )
                if os.getenv( 'DEBUG' ):
                    traceback.print_exception( e )

    if char_sprite:
        group.append( char_sprite )

    display.show( group )

def main():
    display = board.DISPLAY

    group = displayio.Group()
    font = bitmap_font.load_font( os.getenv( 'FONT_BDF' ) )
    display.brightness = 0.3
    check_cycles = os.getenv( 'CHECK_CYCLES' )

    connect_label = label.Label(
        font=font, text='{}'.format( 'Connecting...' ) )
    connect_label.x = int( display.width / 2 ) - int( connect_label.width / 2 )
    connect_label.y = int( display.height / 2 )
    group.append( connect_label )
    display.show( group )

    socket_pool = connect_wifi()
    mqtt_client = None
    i2c = busio.I2C( board.SCL, board.SDA, frequency=50000 )
    sensors = SensorBank()

    balloon_bmp = displayio.OnDiskBitmap( 'balloons.bmp' )

    char_bmp = None
    char_sprite = None
    char_frame = 0
    if os.getenv( 'CHAR_BITMAPS' ):
        char_paths = os.getenv( 'CHAR_BITMAPS' ).split( ',' )
        if 0 < len( char_paths ):
            char_bmp_path = \
                char_paths[random.randint( 0, len( char_paths ) - 1 )]
            char_bmp = displayio.OnDiskBitmap( char_bmp_path )

    while True:
        # Update MQTT client if exists/connected, or reconnect.
        if mqtt_client:
            try:
                mqtt_client.loop()

                mqtt_client.publish(
                    'funhouse/{}/ip'.format( os.getenv( 'FUNHOUSE_ID' ) ),
                    str( wifi.radio.ipv4_address ),
                    True if os.getenv( 'MQTT_RETAIN' ) > 0 else False,
                    0 )
            except (MQTT.MMQTTException, OSError) as e:
                print( 'MQTT: {}: {}', type( e ), e )
                mqtt_client = None
                
        elif not None in [x['sensor'] for x in sensors] and \
        not None in [x['last_resp'] for x in sensors]:
            try:
                mqtt_client = connect_mqtt( sensors, socket_pool )
            except Exception as e:
                print( 'MQTT: {}: {}'.format( type( e ), e ) )
                mqtt_client = None

        char_frame += 1
        if 3 <= char_frame:
            char_frame = 0

        if os.getenv( 'CHECK_CYCLES' ) <= check_cycles:
            sensors = poll_all_sensors( sensors, mqtt_client, i2c )
            check_cycles = 0
        else:
            check_cycles += 1

        redraw(
            20, char_frame, sensors, char_bmp, balloon_bmp, font, mqtt_client )

        time.sleep( 0.1 )

if '__main__' == __name__:
    main()
