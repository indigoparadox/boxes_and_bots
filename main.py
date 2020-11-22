
from machine import Pin, I2C, PWM
from neopixel import NeoPixel
import ssd1306
import dht
import time

OLED_WIDTH = 128
OLED_HEIGHT = 64
OLED_CYAN_TOP = 16

CLK = 22
DT = 21
ROT_NONE = 0
ROT_CW = 1
ROT_CCW = 2

DHT_DELAY = 2000

i2c = I2C( 0, scl=Pin( 18 ), sda=Pin( 19 ) )
oled = ssd1306.SSD1306_I2C( OLED_WIDTH, OLED_HEIGHT, i2c, addr=0x3c )

np = NeoPixel( Pin( 23 ), 1 )
np[0] = (0, 0, 255)
np.write()

d = dht.DHT22( Pin( 16 ) )
cur_ticks = time.ticks_ms()
prev_ticks_dht = cur_ticks
prev_ticks_clk = cur_ticks
cur_clk = Pin( CLK ).value()
prev_clk = cur_clk
prev_rot = ROT_NONE
rot_cursor = 0

while True:
    cur_clk = Pin( CLK ).value()
    cur_dt = Pin( DT ).value()

    cur_ticks = time.ticks_ms()
    if prev_ticks_dht + DHT_DELAY < cur_ticks:
        # Only update the ticks if they cross the delay.
        prev_ticks_dht = cur_ticks
        try:
            d.measure()
        except OSError as e:
            print( e )

    oled.fill( 0 )
    if cur_clk != prev_clk and 1 == cur_clk:
        if Pin( DT ).value() != cur_clk:
            prev_rot = ROT_CCW
            prev_ticks_clk = cur_ticks
            rot_cursor -= 1
        else:
            prev_rot = ROT_CW
            prev_ticks_clk = cur_ticks
            rot_cursor += 1

    if ROT_NONE != prev_rot:
        oled.text( 'CW' if ROT_CW == prev_rot else 'CCW', 0, OLED_CYAN_TOP )
        oled.text( '{}'.format( rot_cursor ), 0, OLED_CYAN_TOP + 10 )
        if prev_ticks_clk + 1000 < cur_ticks:
            prev_rot = ROT_NONE   
        
    else:
        oled.text( 'ThermTerm', 0, 0 )
        oled.text( 'Hum: {}'.format( d.humidity() ), 0, OLED_CYAN_TOP )
        temp_f = (d.temperature() * 1.8) + 32
        oled.text( 'Temp: {}'.format( temp_f ), 0, OLED_CYAN_TOP + 10 )

    oled.show()

    prev_clk = cur_clk

