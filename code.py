
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
import digitalio
import asyncio
from adafruit_minimqtt import adafruit_minimqtt
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font
from sensors import SensorBank

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

class MQTTHandler:

    def __init__( self, display : DisplayHandler, socket_pool ):
        self.client = None
        self.display = display
        self.socket_pool = socket_pool

    def on_reload( self ):
        print( 'disconnecting MQTT...' )
        self.client.disconnect()
    
    def on_connect( self, mqtt_client, userdata, flags, rc ):
        # This function will be called when the mqtt_client is connected
        # successfully to the broker.
        print( 'connected to MQTT broker' )
        self.display.update_mqtt_label( self )

    def on_disconnected( self ):
        self.client = None
        self.display.update_mqtt_label( self )
    
    def connect( self, sensors : SensorBank ):
        if not os.getenv( 'MQTT_HOST' ):
            return None
    
        self.client = adafruit_minimqtt.MQTT(
            broker=os.getenv( 'MQTT_HOST' ),
            port=os.getenv( 'MQTT_PORT' ),
            username=os.getenv( 'MQTT_USER' ),
            password=os.getenv( 'MQTT_PASSWORD' ),
            socket_pool=self.socket_pool )
    
        self.client.will_set(
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
                self.client.will_set(
                    'funhouse/{}/{}/{}'.format(
                        os.getenv( 'FUNHOUSE_ID' ),
                        sensor['name'],
                        key.replace( ' ', '_' ) ),
                    '',
                    0,
                    True )
        self.client.on_connect = self.on_connect
        print( 'connecting to MQTT...' )
        self.client.connect()
        atexit.register( self.on_reload )

    def publish( self, topic : str, message : str ):
        if self.client:
            try:
                self.client.publish(
                    topic, message,
                    True if os.getenv( 'MQTT_RETAIN' ) > 0 else False,
                    0 )
            except (adafruit_minimqtt.MMQTTException, OSError) as e:
                print( 'MQTT: {}: {}', type( e ), e )
                self.on_disconnected()

def poll_sensor( idx : int, sensor : dict, i2c : busio.I2C, mqtt : MQTTHandler ) -> dict:
    try:

        if 'multiplex' in sensor:
            i2c = sensor['multiplex']( sensor, i2c )

        # Grab the sensor value dict from poller functions.
        poll_res = sensor['processor']( sensor['sensor'] )

        sensor['last_resp'] = poll_res

        # Create display string.
        #try:
        sensor['values'] = {}
        sensor['values'] = {sensor['display_keys'][x]: poll_res[x] \
            for x in sensor['display_keys']}
        #except Exception as e:
        #    print( 'poll error: {}: {} ({})'.format( type( e ), e, poll_res ) )

        # TODO: Only push MQTT/display if value changed.
                
        # Publish all values to MQTT.
        for key in poll_res:
            mqtt.publish(
                'funhouse/{}/{}/{}'.format(
                    os.getenv( 'FUNHOUSE_ID' ),
                    sensor['name'],
                    key.replace( ' ', '_' ) ),
                poll_res[key] )
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

class DisplayHandler:

    balloon_x = 20
    label_x = 46
    label_color = 0
    label_y_inc = 24

    def __init__( self, display : displayio.Display, sensor_display_count : int ):
        self.group = displayio.Group()
        self.font = bitmap_font.load_font( os.getenv( 'FONT_BDF' ) )
        self.last_y = 10
        self.sensor_display_count = sensor_display_count
        self.balloon_bmp = displayio.OnDiskBitmap( 'balloons.bmp' )
        self.ui_bmp = displayio.OnDiskBitmap( 'uiwin.bmp' )
        self.selected_idx = 2
        
        # Setup background tilemap.
        if os.getenv( 'TILE_BITMAP' ):
            self.platform_bmp = displayio.OnDiskBitmap( 'platform.bmp' )
            self.platform = displayio.TileGrid(
                self.platform_bmp,
                pixel_shader=self.platform_bmp.pixel_shader,
                tile_width=16, tile_height=16, width=15, height=4,
                default_tile=0 )
            self.platform.y = 176

            # Draw a pastoral scene.
            for x in range( 0, 15 ):
                self.platform[x, 0] = 12
                self.platform[x, 1] = 12
                rand_num = random.randint( 0, 5 )
                if 4 < rand_num:
                    self.platform[x, 2] = 75
                elif 3 < rand_num:
                    self.platform[x, 2] = 76
                else:
                    self.platform[x, 2] = 12
                self.platform[x, 3] = 2

            self.group.append( self.platform )
            
        if os.getenv( 'DISPLAY_IP' ):
            self.sensor_display_count += 1
            
        if os.getenv( 'DISPLAY_MQTT' ):
            self.sensor_display_count += 1

        # Draw UI elements.
        self.ui = displayio.TileGrid(
            self.ui_bmp,
            pixel_shader=self.ui_bmp.pixel_shader,
            tile_width=24, tile_height=24, width=8, height=self.sensor_display_count )
        self.ui.x = 40
        for y in range( 0, self.sensor_display_count ):
            self.set_ui_line( y, False, True if self.selected_idx == y else False )
        self.group.append( self.ui )

        # Draw IP label.
        if os.getenv( 'DISPLAY_IP' ):
            self.ip_label = label.Label(
                font=self.font, color=self.label_color, text='Connecting...' )
            self.ip_label.x = self.label_x
            self.ip_label.y = self.last_y
            self.last_y += self.label_y_inc
            self.group.append( self.ip_label )

        # Draw MQTT label.
        if os.getenv( 'DISPLAY_MQTT' ): 
            self.mqtt_label = label.Label(
                font=self.font, color=self.label_color, text='Waiting for MQTT...' )
            self.mqtt_label.x = self.label_x
            self.mqtt_label.y = self.last_y
            self.last_y += self.label_y_inc
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

    def set_ui_line( self, y : int, warning : bool, selected : bool ):
        for x in range( 0, 8 ):
            if selected:
                if 0 == x:
                    self.ui[x, y] = 6 if warning else 0
                elif 10 == x:
                    self.ui[x, y] = 8 if warning else 2
                else:
                    self.ui[x, y] = 7 if warning else 1
            else:
                if 0 == x:
                    self.ui[x, y] = 21 if warning else 15
                elif 10 == x:
                    self.ui[x, y] = 23 if warning else 17
                else:
                    self.ui[x, y] = 22 if warning else 16

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
    
    def update_mqtt_label( self, mqtt : MQTTHandler ):
        if self.mqtt_label:
            self.mqtt_label.text = 'MQTT Connected' if mqtt.client else 'MQTT Not Connected'

    def update_sensor_label( self, idx : int, sensor : dict, key : str ):
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
            sensor['balloons'][key].x = self.balloon_x
            sensor['balloons'][key].y = self.last_y - int( sensor['balloons'][key].tile_height / 2 )
            self.group.append( sensor['balloons'][key] )
        
        if 'values' in sensor and sensor['values']:
            if key in sensor['thresholds'] and \
            sensor['values'][display_key] >= \
            sensor['thresholds'][key]:
                # Alert balloon.
                sensor['balloons'][key][0, 0] = 8
                self.set_ui_line( idx, True, True if self.selected_idx == idx else False )
            else:
                # Blank balloon.
                sensor['balloons'][key][0, 0] = 0
                self.set_ui_line( idx, False, True if self.selected_idx == idx else False )
        else:
            # Question balloon.
            sensor['balloons'][key][0, 0] = 9
            self.set_ui_line( idx, True, True if self.selected_idx == idx else False )

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
            sensor['labels'][key] = label.Label( font=self.font, color=self.label_color, text=lbl_text )
            sensor['labels'][key].x = self.label_x
            sensor['labels'][key].y = self.last_y
            self.last_y += self.label_y_inc
            self.group.append( sensor['labels'][key] )
        else:
            sensor['labels'][key].text = lbl_text

        return sensor

async def poll_all_sensors( sensors : SensorBank, mqtt : MQTTHandler, i2c ):

    while True:
        for i in range( 0, sensors.count()  ):
            sensors[i] = poll_sensor( i, sensors[i], i2c, mqtt )
            await asyncio.sleep( 3 )

async def refresh_mqtt( mqtt : MQTTHandler, display : DisplayHandler, sensors : SensorBank ):

    '''Update MQTT client if exists/connected, or reconnect. '''
    
    while True:
        if mqtt.client:
            try:
                mqtt.client.loop()
                mqtt.publish(
                    'funhouse/{}/ip'.format( os.getenv( 'FUNHOUSE_ID' ) ),
                    str( wifi.radio.ipv4_address ) )
            except (adafruit_minimqtt.MMQTTException, OSError) as e:
                print( 'MQTT: {}: {}', type( e ), e )
                mqtt.on_disconnected()
                
        elif not None in [x['sensor'] for x in sensors] and \
        not None in [x['last_resp'] for x in sensors]:
            try:
                mqtt.connect( sensors )
            except (adafruit_minimqtt.MMQTTException, OSError) as e:
                print( 'MQTT: {}: {}'.format( type( e ), e ) )
                mqtt.on_disconnected()
        await asyncio.sleep( 1 )

async def refresh_display( display : DisplayHandler, sensors : SensorBank ):
    while True:
        
        display.move_char(
            int( display.display.width / 2 ) - 16,
            display.display.height - 64 )
        display.increment_char_frame()
        display.update_ip_label()
        
        # Redraw sensors.
        j = 0
        if os.getenv( 'DISPLAY_IP' ):
            j += 1
        if os.getenv( 'DISPLAY_MQTT' ):
            j += 1
        for i in range( 0, sensors.count()  ):
            for key in sensors[i]['display_keys']:
                #try:
                sensors[i] = display.update_sensor_label( j, sensors[i], key )
                j += 1
                #except Exception as e:
                #    print( 'label error: {}: {}'.format( type( e ), e ) )
                #    if os.getenv( 'DEBUG' ):
                #        traceback.print_exception( e )
    
        await asyncio.sleep( 0.33 )

async def main():
    sensors = SensorBank()
    sensor_display_count = 0
    for i in range( 0, sensors.count()  ):
        sensor_display_count += len( sensors[i]['display_keys'] )

    button_up = digitalio.DigitalInOut( board.BUTTON_UP )
    button_up.switch_to_input( pull=digitalio.Pull.DOWN )
    button_down = digitalio.DigitalInOut( board.BUTTON_DOWN )
    button_down.switch_to_input( pull=digitalio.Pull.DOWN )
    
    display = DisplayHandler( board.DISPLAY, sensor_display_count )

    socket_pool = connect_wifi()
    mqtt = MQTTHandler( display, socket_pool )
    i2c = busio.I2C( board.SCL, board.SDA, frequency=50000 )

    while True:
        
        # Check buttons state.
        if button_down.value:
            display.selected_idx += 1
            if sensor_display_count <= display.selected_idx:
                display.selected_idx = 0
        elif button_up.value:
            display.selected_idx -= 1
            if sensor_display_count <= display.selected_idx:
                display.selected_idx = sensor_display_count - 1

        poller_task = asyncio.create_task( poll_all_sensors( sensors, mqtt, i2c ) )
        mqtt_task = asyncio.create_task( refresh_mqtt( mqtt, display, sensors ) )
        redraw_task = asyncio.create_task( refresh_display( display, sensors ) )
        await asyncio.gather( poller_task, mqtt_task, redraw_task )
        
if '__main__' == __name__:
    asyncio.run( main() )

