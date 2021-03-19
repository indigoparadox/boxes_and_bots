
from machine import Pin, I2C, PWM, freq, deepsleep
from sgp30 import SGP30
from bme680 import BME680_I2C

from screen import MenuScreen
import time
import esp32
import machine

ICONS = {
    'tvoc': [
        0b00000,
        0b01010,
        0b11011,
        0b10101,
        0b00100,
        0b01110,
        0b00000,
        0b00000,
    ],
    'pressure': [
        0b1001,
        0b0111,
        0b1011,
        0b0101,
        0b1011,
        0b0111,
        0b1001,
        0b0111,
    ],
    'therm': [
        0b00010,
        0b10101,
        0b00101,
        0b10101,
        0b00111,
        0b10111,
        0b00111,
        0b00010,
    ],
    'magnet': [
        0b11111,
        0b10111,
        0b10111,
        0b10101,
        0b10101,
        0b10001,
        0b01110,
        0b00000,
    ],
    'carbon': [
        0b00000,
        0b01110,
        0b11011,
        0b11000,
        0b11000,
        0b11011,
        0b01110,
        0b00000,
    ],
    'humidity': [
        0b00000,
        0b00100,
        0b01110,
        0b11111,
        0b11101,
        0b11101,
        0b01110,
        0b00000,
    ],
}

CLK = 25
DT = 21
ROTARY_DEBOUNCE = 50

pclk = Pin( CLK, Pin.IN )
pdt = Pin( DT, Pin.IN )

clk_prev = pclk.value()
rot_handling = False
rot_prev_ticks = time.ticks_ms()

rotary_menu = [
    {'label': 'Humidity', 'callback': lambda: round( dhts.humidity(), 1 ), 'u': '%',
    'icon': ICONS['humidity']},
    #{'label': 'Temperature',
    #'callback': lambda: round( (dhts.temperature() * 1.8) + 32, 1 ), 'u': 'F',
    #'icon': ICONS['therm']},
    #{'label': 'Magnet', 'callback': lambda: esp32.hall_sensor(), 'u': 'm',
    #'icon': ICONS['magnet']},
]

bme = None
sgp = None
iaq = None
try:
    sgp = SGP30( i2c )
    iaq = sgp.indoor_air_quality
    rotary_menu.append(
        {'label': 'TVOC', 'callback': lambda: iaq[1], 'u': 'p',
            'icon': ICONS['tvoc'] } )
    rotary_menu.append(
        {'label': 'eCO2', 'callback': lambda: iaq[0], 'u': 'p',
            'icon':  ICONS['carbon']} )
except Exception as e:
    try:
        bme = BME680_I2C( i2c=i2c )
        rotary_menu.append(
            {'label': 'Temp', 'u': 'F', 'icon': ICONS['therm'],
                'callback': lambda: round( bme.temperature, 1 )} )
        rotary_menu.append(
            {'label': 'Humidity', 'icon': ICONS['humidity'], 'u': '%',
                'callback': lambda: round( bme.humidity, 1 )} )
        rotary_menu.append(
            {'label': 'TVOC', 'callback': lambda: round( bme.gas / 1000, 1 ),
                'u': 'p', 'icon': ICONS['tvoc'] } )
        rotary_menu.append(
            {'label': 'Pressure', 'callback': lambda: round( bme.pressure, 1 ),
                'u': 'p', 'icon': ICONS['pressure'] } )
    except Exception as e:
        print( e )

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
    except Exception as e:
        print( e )

    scr.update_screen()

    time.sleep_ms( 2000 )
    #machine.deepsleep( 2000 )

