
import busio
import board
import os
import ipaddress
import ssl
import wifi
import socketpool
import adafruit_requests
import time
from adafruit_pm25.i2c import PM25_I2C
from adafruit_scd30 import SCD30
from adafruit_sgp30 import Adafruit_SGP30
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

def on_mqtt_connect( mqtt_client, userdata, flags, rc ):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    print( 'connected to MQTT broker' )

def connect_wifi():
    wifi.radio.connect( os.getenv( 'WIFI_SSID' ), os.getenv( 'WIFI_PASSWORD' ) )
    pool = socketpool.SocketPool(wifi.radio)
    mqtt_client = MQTT.MQTT(
        broker=os.getenv( 'MQTT_HOST' ),
        port=os.getenv( 'MQTT_PORT' ),
        username=os.getenv( 'MQTT_USER' ),
        password=os.getenv( 'MQTT_PASSWORD' ),
        socket_pool=pool
    )
    mqtt_client.on_connect = on_mqtt_connect
    print( 'connecting to MQTT...' )
    mqtt_client.connect()
    return mqtt_client

def poll_sensor( sensor, sensor_name : str, sensor_class, poll_func, i2c, mqtt_client : MQTT.MQTT, display ):
    try:
        # Grab the sensor value dict from poller functions.
        poll_res = poll_func( sensor )
        for key in poll_res:
            mqtt_client.publish(
                'funhouse/{}/{}/{}'.format( os.getenv( 'FUNHOUSE_ID' ), sensor_name, key.replace( ' ', '_' ) ), poll_res[key] )
    except Exception as e:
        try:
            # Try to setup the sensor for the first time.
            print( 'read failed: {}: setting up {}...'.format( e, sensor_name ) )
            sensor = sensor_class( i2c )
        except Exception as e:
            # Sensor failure.
            print( '{}: could not find sensor: {}'.format( sensor_name, e ) )
    return sensor

def main():
    display = board.DISPLAY
    mqtt_client = None
    mqtt_client = connect_wifi()
    i2c = busio.I2C( board.SCL, board.SDA, frequency=50000 )
    pmsa = None
    scd30 = None
    sgp30 = None

    font = bitmap_font.load_font( os.getenv( 'FONT_BDF' ) )
    color = 0xFF00FF

    while True:
        mqtt_client.loop()
        #try:
        #    print( wifi.radio.ipv4_address )
        #except Exception as e:
        #    print( "connection failure: " + str( e ) )

        pmsa = poll_sensor( pmsa, 'pmsa', PM25_I2C, lambda x: x.read(), i2c, mqtt_client, board.DISPLAY )
        sgp30 = poll_sensor( sgp30, 'sgp30', Adafruit_SGP30, lambda x: dict( zip( ['eco2', 'tvoc'], sgp30.iaq_measure() ) ), i2c, mqtt_client, board.DISPLAY )
        scd30 = poll_sensor( scd30, 'scd30', SCD30, lambda y: {x.lower(): getattr( y, x ) for x in ['CO2', 'temperature', 'relative_humidity']} if scd30.data_available else {}, i2c, mqtt_client, board.DISPLAY )

        time.sleep( 5 )

if '__main__' == __name__:
    main()
