
from machine import Pin, I2C, PWM, freq, deepsleep
from sgp30 import SGP30
from screen import MenuScreen
import time
import esp32
import machine

CLK = 32
DT = 21
ROTARY_DEBOUNCE = 50

pclk = Pin( CLK, Pin.IN )
pdt = Pin( DT, Pin.IN )

sgp = SGP30( i2c )
iaq = sgp.indoor_air_quality

clk_prev = pclk.value()
rot_handling = False
rot_prev_ticks = time.ticks_ms()

rotary_menu = [
    {'label': 'Humidity', 'callback': lambda: dhts.humidity(), 'u': '%',
    'icon': [
        0b00000,
        0b00100,
        0b01110,
        0b11111,
        0b11101,
        0b11101,
        0b01110,
        0b00000,
    ]},
    {'label': 'Temperature',
    'callback': lambda: round( (dhts.temperature() * 1.8) + 32, 2 ), 'u': 'F',
    'icon': [
        0b00010,
        0b10101,
        0b00101,
        0b10101,
        0b00111,
        0b10111,
        0b00111,
        0b00010,
    ]},
    {'label': 'eCO2', 'callback': lambda: iaq[0], 'u': 'p', 'icon': [
        0b00000,
        0b01110,
        0b11011,
        0b11000,
        0b11000,
        0b11011,
        0b01110,
        0b00000,
    ]},
    {'label': 'TVOC', 'callback': lambda: iaq[1], 'u': 'p', 'icon': [
        0b00000,
        0b01010,
        0b11011,
        0b10101,
        0b00100,
        0b01110,
        0b00000,
        0b00000,
    ]},
    {'label': 'Magnet', 'callback': lambda: esp32.hall_sensor(), 'u': 'm',
    'icon': [
        0b11111,
        0b10111,
        0b10111,
        0b10101,
        0b10101,
        0b10001,
        0b01110,
        0b00000,
    ]},
]

def handle_rotary( pin ):
    global clk_prev
    global rot_handling
    global rot_prev_ticks
    global scr

    # Debounce timer.
    rot_cur_ticks = time.ticks_ms()
    if rot_prev_ticks + ROTARY_DEBOUNCE > rot_cur_ticks:
        return
    rot_prev_ticks = rot_cur_ticks

    if rot_handling:
        return
    rot_handling = True
    clk_cur = pclk.value()
    if clk_cur != clk_prev and clk_cur == 0:
        if pdt.value() != clk_cur:
            scr.cursor_dec()
        else:
            scr.cursor_inc()
    clk_prev = clk_cur

    scr.update_screen()
    rot_handling = False
    
pclk.irq( trigger=Pin.IRQ_RISING|Pin.IRQ_FALLING, handler=handle_rotary )
esp32.wake_on_ext0( pin=pclk, level=esp32.WAKEUP_ALL_LOW )

scr = MenuScreen(
    oled, OLED_WIDTH, OLED_HEIGHT, OLED_CYAN_TOP, rtc, rotary_menu )

scr.menu = rotary_menu
while True:
    try:
        print( 'updating...' )
        dhts.measure()
        iaq = sgp.indoor_air_quality
    except OSError as e:
        print( e )

    scr.update_screen()

    time.sleep_ms( 2000 )
    #machine.deepsleep( 2000 )

