
import board
import time
from EDS import Dig2, Clock
from digitalio import DigitalInOut, Direction

DISPLAY_HR_MIN = 0
DISPLAY_MON_DAY = 1
DISPLAY_MAX = 1

HOLD_MAX = 10

i2c = board.I2C()

clk = Clock( i2c )
left = Dig2( i2c, 0x16 )
right = Dig2( i2c )

update_from_hw = True

btn = DigitalInOut( board.A0 )
btn.direction = Direction.INPUT

last_left = 0
last_right = 0

def update_clk():
    tm = clk.read()
    sec_int = tm.tm_sec
    hr_int = tm.tm_hour
    min_int = tm.tm_min
    day_int = tm.tm_mday
    mon_int = tm.tm_mon
    print( 'updated from hw' )
    return sec_int, min_int, hr_int, day_int, mon_int

def update_display( left_int, right_int ):
    global last_left
    global last_right
    if last_left != left_int:
        left.dec( left_int )
        last_left = left_int
    if last_right != right_int:
        right.dec( right_int )
        last_right = right_int

sec_int, min_int, hr_int, day_int, mon_int = update_clk()
last_tick = time.monotonic()
display_mode = 0
hold_ctr = 0
btn_last = False
held_last = False

while True:

    # If a second has elapsed since the last time we checked, increment seconds.
    loop_tick = time.monotonic()
    if last_tick + 1.0 <= loop_tick:
        sec_int += 1
        last_tick = loop_tick

    # Every minute, update the display.
    if 60 <= sec_int:
        min_int += 1
        sec_int = 0

    # Every hour, sync from hardware clock.
    if 60 <= min_int:
        sec_int, min_int, hr_int, day_int, mon_int = update_clk()

    # Detect button press (w/ debounce).
    if btn_last and btn.value:
        # Button being held.
        hold_ctr += 1
        if hold_ctr > HOLD_MAX and not held_last:
            # Button held fof HOLD_MAX.
            print( 'held' )
            held_last = True
    elif btn_last and not btn.value and not held_last:
        # Button was pressed but not held, and reelased.
        print( 'press' )
        btn_last = False
        held_last = False
        hold_ctr = 0
        display_mode += 1
        if DISPLAY_MAX < display_mode:
            display_mode = 0
    elif btn.value:
        # Buttn pressed for the first time.
        btn_last = True
    else:
        # Button not being pressed at all.
        btn_last = False
        held_last = False
        hold_ctr = 0

    if display_mode == DISPLAY_HR_MIN:
        update_display( hr_int, min_int )
    elif display_mode == DISPLAY_MON_DAY:
        update_display( mon_int, day_int )

    time.sleep( 0.1 )

