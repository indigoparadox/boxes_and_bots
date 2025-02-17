#from ili934xnew import ILI9341, color565
import machine
#import tt14
from pca8574 import PCA8574
from ads1x15 import ADS1115
import camera
import time
import framebuf
import ili9341
from xglcd_font import XglcdFont

try:
    camera.init( 0, format=camera.JPEG )
except OSError as e:
    print( e )

SCREEN_W = 320
SCREEN_H = 240

i2c = machine.I2C( 0, scl=machine.Pin( 0 ), sda=machine.Pin( 2 ) )
pca = PCA8574( i2c, addr=0x21 )
adc = ADS1115( i2c, address=0x48 )
text = 'Foo text'
spi = machine.SPI( 1, baudrate=80000000, mosi=machine.Pin( 13 ), sck=machine.Pin( 14 ) )
display = ili9341.Display( spi, cs=pca.pin(5), dc=pca.pin(3), rst=pca.pin(4), width=SCREEN_W, height=SCREEN_H, rotation=270 )
#display = ILI9341( spi, cs=pca.pin(5), dc=pca.pin(3), rst=pca.pin(4), w=SCREEN_W, h=SCREEN_H, r=1)
#display.set_font(tt14)
#display.erase()
#buf = bytearray( SCREEN_W * SCREEN_H * 2 )
#fb = framebuf.FrameBuffer( buf, SCREEN_W, SCREEN_H, framebuf.RGB565 )
arcadepix = XglcdFont('ArcadePix9x11.c', 9, 11)

buzz = machine.PWM( machine.Pin( 4 ), freq=800, duty=512 )
time.sleep_ms( 500 )
buzz.deinit()

while True:
    #display.erase()
    #display.fill_rectangle( 0, 0, 100, 40 )
    #display.set_pos( 20, 20 )
    display.draw_text( 20, 20, '{:8d}, {:8d}'.format( adc.read( channel1=0 ), adc.read( channel1=1 ) ), font=arcadepix, color=0xffff )
    #display.print( '{:8d}, {:8d}'.format( adc.read( channel1=0 ), adc.read( channel1=1 ) ) )
#    fb.fill( 0x0 )
#    fb.text( '{:8d}, {:8d}'.format( adc.read( channel1=0 ), adc.read( channel1=1 ) ), 20, 20 )
#    display.blit( fb, 0, 0, SCREEN_W, SCREEN_H )
    time.sleep_ms( 500 )

#display.set_pos(0,0)
#display.print(text)
#display.set_pos(0,20)
#display.print(text)
#display.set_pos(40,20)
#display.print(text)
