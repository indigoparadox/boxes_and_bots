
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

class Display:

    def __init__( self, display ):
        self.group = displayio.Group()
        self.font = bitmap_font.load_font( os.getenv( 'FONT_BDF' ) )
        self.last_y = 20
        self.balloon_bmp = displayio.OnDiskBitmap( 'balloons.bmp' )
        
        # Setup background tilemap.
        if os.getenv( 'TILE_BITMAP' ):
            self.platform_bmp = displayio.OnDiskBitmap( 'platform.bmp' )
            self.platform = displayio.TileGrid(
                self.platform_bmp,
                pixel_shader=self.platform_bmp.pixel_shader,
                tile_width=16, tile_height=16, width=15, height=15,
                default_tile=0 )
            self.group.append( self.platform )

        if os.getenv( 'DISPLAY_IP' ):
            self.ip_label = label.Label(
                font=self.font, text='Connecting...' )
            self.ip_label.x = 10
            self.ip_label.y = self.last_y
            self.last_y += 20
            self.group.append( self.ip_label )
    
        if os.getenv( 'DISPLAY_MQTT' ): 
            self.mqtt_label = label.Label( font=self.font, text='Waiting for MQTT...' )
            self.mqtt_label.x = 10
            self.mqtt_label.y = self.last_y
            self.last_y += 20
            self.group.append( self.mqtt_label )

        # Setup avatar character.
        char_paths = os.getenv( 'CHAR_BITMAPS' ).split( ',' )
        if 0 < len( char_paths ):
            char_bmp_path = char_paths[random.randint( 0, len( char_paths ) - 1 )]
            self.char_bmp = displayio.OnDiskBitmap( char_bmp_path )
        self.char_sprite = displayio.TileGrid(
            self.char_bmp,
            pixel_shader=self.char_bmp.pixel_shader,
            tile_width=32, tile_height=32, width=1, height=1,
            default_tile=0 )
        self.char_frame = 0
        self.group.append( self.char_sprite )

        self.display = display
        self.display.brightness = 0.3
        self.display.root_group = self.group

    def move_char( self, x, y ):
        self.char_sprite.x = x
        self.char_sprite.y = y

    def increment_char_frame( self ):
        self.char_frame += 1
        if 3 <= self.char_frame:
            self.char_frame = 0
        if self.char_sprite:
            self.char_sprite[0, 0] = self.char_frame

    def update_ip_label( self ):
        if self.ip_label:
            self.ip_label.text = '{}'.format( wifi.radio.ipv4_address )
    
    def update_mqtt_label( self, mqtt ):
        if mqtt and self.mqtt_label:
            self.mqtt_label.text = 'MQTT Connected' if mqtt else 'MQTT Not Connected'

    def update_sensor_label( self, sensor, key ):
        display_key = sensor['display_keys'][key]

        # Draw status icon.
        if not 'balloons' in sensor:
            sensor['balloons'] = {}

        if not key in sensor['balloons']:
            sensor['balloons'][key] = displayio.TileGrid(
                self.balloon_bmp,
                pixel_shader=self.balloon_bmp.pixel_shader,
                tile_width=16, tile_height=16, width=1, height=1,
                default_tile=0 )
            sensor['balloons'][key].x = 10
            sensor['balloons'][key].y = self.last_y - int( sensor['balloons'][key].tile_height / 2 )
            self.group.append( sensor['balloons'][key] )
        
        if 'values' in sensor and sensor['values']:
            if key in sensor['thresholds'] and \
            sensor['values'][display_key] >= \
            sensor['thresholds'][key]:
                # Alert balloon.
                sensor['balloons'][key][0, 0] = 8
            else:
                # Blank balloon.
                sensor['balloons'][key][0, 0] = 0
        else:
            # Question balloon.
            sensor['balloons'][key][0, 0] = 9

        # Draw status text.
        if 'values' in sensor and sensor['values']:
            if 'display_calcs' in sensor and key in sensor['display_calcs']:
                lbl_text = '{}: {}'.format( display_key, 
                    sensor['display_calcs'][key]( sensor['values'][display_key] ) )
            else:
                lbl_text = '{}: {}'.format( display_key, sensor['values'][display_key] )
        else:
            lbl_text = '{}: Waiting...'.format( display_key )

        if not 'labels' in sensor:
            sensor['labels'] = {}

        if not key in sensor['labels']:
            sensor['labels'][key] = label.Label( font=self.font, text=lbl_text )
            sensor['labels'][key].x = 30
            sensor['labels'][key].y = self.last_y
            self.last_y += 20
            self.group.append( sensor['labels'][key] )
        else:
            sensor['labels'][key].text = lbl_text

        return sensor

def main():
    display = Display( board.DISPLAY )

    group = displayio.Group()
    check_cycles = os.getenv( 'CHECK_CYCLES' )

    #connect_label = label.Label(
    #    font=font, text='{}'.format( 'Connecting...' ) )
    #connect_label.x = int( display.width / 2 ) - int( connect_label.width / 2 )
    #connect_label.y = int( display.height / 2 )
    #group.append( connect_label )
    #display.show( group )

    socket_pool = connect_wifi()
    mqtt_client = None
    i2c = busio.I2C( board.SCL, board.SDA, frequency=50000 )
    sensors = SensorBank()

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
                display.mqtt_label( mqtt_client )
                
        elif not None in [x['sensor'] for x in sensors] and \
        not None in [x['last_resp'] for x in sensors]:
            try:
                mqtt_client = connect_mqtt( sensors, socket_pool )
            except Exception as e:
                print( 'MQTT: {}: {}'.format( type( e ), e ) )
                mqtt_client = None

        display.move_char(
            int( display.display.width / 2 ) - 16,
            display.display.height - 32 )
        display.increment_char_frame()
        display.update_ip_label()
        display.update_mqtt_label( mqtt_client )

        if os.getenv( 'CHECK_CYCLES' ) <= check_cycles:
            sensors = poll_all_sensors( sensors, mqtt_client, i2c )
            check_cycles = 0
        else:
            check_cycles += 1

        for i in range( 0, sensors.count()  ):
            for key in sensors[i]['display_keys']:
                #try:
                sensors[i] = display.update_sensor_label( sensors[i], key )
                #except Exception as e:
                #    print( 'label error: {}: {}'.format( type( e ), e ) )
                #    if os.getenv( 'DEBUG' ):
                #        traceback.print_exception( e )

        time.sleep( 0.1 )

if '__main__' == __name__:
    main()

