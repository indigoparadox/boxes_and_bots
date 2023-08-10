
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
    wifi.radio.connect( os.getenv( 'WIFI_SSID' ), os.getenv( 'WIFI_PASSWORD' ) )
    return socketpool.SocketPool(wifi.radio)

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

def poll_sensor( idx : int, sensor : dict, i2c : busio.I2C, mqtt_client : MQTT.MQTT, display, font ) -> dict:
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

def main():
    display = board.DISPLAY

    group = displayio.Group()
    font = bitmap_font.load_font( os.getenv( 'FONT_BDF' ) )
    display.brightness = 0.3

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

    sprite_sheet_bmp = displayio.OnDiskBitmap( 'balloons.bmp' )

    while True:
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

        y_top = 20
        group = displayio.Group()

        if os.getenv( 'DISPLAY_IP' ):
            ip_label = label.Label(
                font=font, text='{}'.format( wifi.radio.ipv4_address ) )
            ip_label.x = 10
            ip_label.y = y_top
            group.append( ip_label )
            y_top += 20

        if os.getenv( 'DISPLAY_MQTT' ): 
            mqtt_label = label.Label( \
                font=font, text='MQTT Connected' \
                if mqtt_client else 'MQTT Not Connected' )
            mqtt_label.x = 10
            mqtt_label.y = y_top
            group.append( mqtt_label )
            y_top += 20

        last_y = y_top;
        for i in range( 0, sensors.count()  ):
            try:
                sensors[i] = poll_sensor( \
                    i, sensors[i], i2c, mqtt_client, board.DISPLAY, font )
            except (MQTT.MMQTTException, OSError) as e:
                print( 'MQTT: {}: {}', type( e ), e )
                mqtt_client = None

            for key in sensors[i]['display_keys']:
                try:
                    display_key = sensors[i]['display_keys'][key]

                    # Draw status icon.
                    sprite = displayio.TileGrid(
                        sprite_sheet_bmp,
                        pixel_shader=sprite_sheet_bmp.pixel_shader,
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

        display.show( group )

        time.sleep( 5 )

if '__main__' == __name__:
    main()
