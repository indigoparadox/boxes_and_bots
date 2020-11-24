from ili934xnew import ILI9341, color565
import machine
import tt14
from pca8574 import PCA8574
import camera

try:
    camera.init( 0, format=camera.JPEG )
except OSError as e:
    print( e )

i2c = machine.I2C( 0, scl=machine.Pin( 0 ), sda=machine.Pin( 2 ) )
pca = PCA8574( i2c, addr=0x21 )
text = 'Foo text'
spi = machine.SPI(2, baudrate=20000000, mosi=machine.Pin(13), sck=machine.Pin(14))
display = ILI9341(spi, cs=pca.pin(5), dc=pca.pin(3), rst=pca.pin(4), w=320, h=240, r=1)
display.erase()
display.set_font(tt14)
display.set_pos(0,0)
display.print(text)
display.set_pos(0,20)
display.print(text)
display.set_pos(40,20)
display.print(text)
