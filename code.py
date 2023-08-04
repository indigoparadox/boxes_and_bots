
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
from adafruit_pm25.i2c import PM25_I2C
from adafruit_scd30 import SCD30
from adafruit_sgp30 import Adafruit_SGP30
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

LABEL_Y_START = 60

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
    mqtt_client = MQTT.MQTT(
        broker=os.getenv( 'MQTT_HOST' ),
        port=os.getenv( 'MQTT_PORT' ),
        username=os.getenv( 'MQTT_USER' ),
        password=os.getenv( 'MQTT_PASSWORD' ),
        socket_pool=socket_pool
    )
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
        # Grab the sensor value dict from poller functions.
        poll_res = sensor['processor']( sensor['sensor'] )

        sensor['last_resp'] = poll_res

        # Create display string.
        try:
            sensor['label'] = label.Label( font, text=','.join( ['{}: {}'.format( x, poll_res[x] ) for x in sensor['display_keys']] ) )
            sensor['label'].x = 10
            sensor['label'].y = LABEL_Y_START + (20 * idx)
        except Exception as e:
            print( '{}: {} ({})'.format( type( e ), e, poll_res ) )

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
    except Exception as e:
        try:
            # Try to setup the sensor for the first time.
            print( 'read failed: {}: setting up {}...'.format( e, sensor['name'] ) )
            sensor['sensor'] = sensor['class']( i2c )
        except Exception as e:
            # Sensor failure.
            print( '{}: could not find sensor: {}'.format( sensor['name'], e ) )
    return sensor

def main():
    display = board.DISPLAY
    socket_pool = connect_wifi()
    mqtt_client = None
    i2c = busio.I2C( board.SCL, board.SDA, frequency=50000 )

    font = bitmap_font.load_font( os.getenv( 'FONT_BDF' ) )
    color = 0xFF00FF
    display.brightness = 0.3

    sensors = [
        {
            'sensor': None,
            'name': 'sgp30',
            'class': Adafruit_SGP30,
            'display_keys': ['tvoc'],
            'processor': lambda x: dict( zip( ['eco2', 'tvoc'], x.iaq_measure() ) ),
            'last_resp': None
        },
        {
            'sensor': None,
            'name': 'pmsa',
            'class': PM25_I2C,
            'display_keys': ['pm25 env'],
            'processor': lambda x: x.read(),
            'last_resp': None
        },
        {
            'sensor': None,
            'name': 'scd30',
            'class': SCD30,
            'display_keys': ['co2', 'temperature', 'relative_humidity'],
            'processor': lambda y: {x.lower(): getattr( y, x ) for x in ['CO2', 'temperature', 'relative_humidity']} if y.data_available else {},
            'last_resp': None
        }
    ]

    while True:
        if mqtt_client:
            mqtt_client.loop()

        group = displayio.Group()

        ip_label = label.Label( font=font, text='{}'.format( wifi.radio.ipv4_address ) )
        ip_label.x = 10
        ip_label.y = 20
        group.append( ip_label )

        mqtt_label = label.Label( font=font, text='MQTT Connected' if mqtt_client else 'MQTT Not Connected' )
        mqtt_label.x = 10
        mqtt_label.y = 40
        group.append( mqtt_label )

        for i in range( 0, 3 ):
            sensors[i] = poll_sensor( i, sensors[i], i2c, mqtt_client, board.DISPLAY, font )
            try:
                group.append( sensors[i]['label'] )
            except Exception as e:
                print( 'label error: {}'.format( e ) )

        display.show( group )

        if not mqtt_client and \
        not None in [x['sensor'] for x in sensors] and \
        not None in [x['last_resp'] for x in sensors]:
            mqtt_client = connect_mqtt( sensors, socket_pool )

        time.sleep( 5 )

if '__main__' == __name__:
    main()
