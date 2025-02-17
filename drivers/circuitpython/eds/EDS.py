"""
Drivers for electricdollarstore I2C parts
"""
import struct
import time
#import datetime

class EDS:

    def __init__( self, i2, a ):
        self.i2 = i2
        self.a = a

    def _write( self, data ):
        self.i2.unlock()
        while not self.i2.try_lock():
            pass
        self.i2.writeto( self.a, bytearray( data ) )
        self.i2.unlock()

    def _read( self, sz ):
        buf = bytearray( sz )
        self.i2.unlock()
        while not self.i2.try_lock():
            pass
        self.i2.readfrom_into( self.a, buf )
        self.i2.unlock()
        return buf

    def _write_reg( self, mem_addr, data ):
        data.insert( 0, mem_addr & 0xff )
        self._write( data )

    #def _read_reg( self, mem_addr, sz ):
    #    #int.from_bytes( buf, 'little' )

class Dig2( EDS ):
    """ DIG2 is a 2-digit 7-segment LED display """

    def __init__( self, i2, a = 0x14 ):
        super().__init__( i2, a )

    def raw( self, b0, b1 ):
        """ Set all 8 segments from the bytes b0 and b1 """
        self._write_reg( 0x0, [b0, b1] )

    def hex( self, b ):
        """ Display a hex number 0-0xff """
        self._write_reg( 0x1, [b] )

    def dec( self, b ):
        """ Display a decimal number 00-99 """
        self._write_reg( 0x2, [b] )

    def dp( self, p0, p1 ):
        """ Set the state the decimal point indicators """
        self._write_reg( 0x3, [(p1 << 1) | p0] )

    def brightness( self, b ):
        """ Set the brightness from 0 (off) to 255 (maximum) """
        self._write_reg( 0x4, [b] )

class Clock( EDS ):
    """ CLOCK is a HT1382 I2C/3-Wire Real Time Clock with a 32 kHz crystal """
    def __init__( self, i2, a = 0x68 ):
        super().__init__( i2, a )

    def set( self, t=None ):
        def bcd( x ):
            return (x % 10) + 16 * (x // 10)
        self._write_reg( 0x7, 0 )
        self._write_reg( 0x6, bcd( t.tm_year % 100 ) )
        self._write_reg( 0x5, 1 + t.tm_wday )
        self._write_reg( 0x4, bcd( t.tm_mon )  )
        self._write_reg( 0x3, bcd( t.tm_mday ) )
        self._write_reg( 0x2, 0x80 | bcd( t.tm_hour ) ) # use 24-hour mode
        self._write_reg( 0x1, bcd( t.tm_min ) )
        self._write_reg( 0x0, bcd( t.tm_sec ) )

    def read( self ):
        #self.i2.start(self.a, 0)
        #self.i2.write([0])
        #self.i2.stop()
        self._write( [0] )
        #self.i2.start(self.a, 1)
        buf = self._read( 7 )
        #print( buf )
        (ss, mm, hh, dd, MM, ww, yy) = (struct.unpack( "7B", buf ))
        #self.i2.stop()
        def dec( x ):
            return (x % 16) + 10 * (x // 16)
        return time.struct_time(
            2000 + dec( yy ),
            dec( MM ),
            dec( dd ),
            dec( hh & 0x7f ),
            dec( mm),
            dec( ss ),
            -1,
            -1,
            -1 )

    def dump(self):
        #self.i2.start(self.a, 0)
        #self.i2.write([0])
        #self.i2.stop()
        #self.i2.start(self.a, 1)
        print( list( self._read( 16 ) ) )
        #self.i2.stop()
        #return self._read( 16 )