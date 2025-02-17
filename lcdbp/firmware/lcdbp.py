
class LCDBackpackModeException( Exception ):
    pass

class LCDBackpack( object ):

    SCREEN_W_CHAR = 21
    SCREEN_H_CHAR = 6

    SCREEN_W = 128
    SCREEN_H = 64

    MODE_TEXT = 0
    MODE_GFX = 1

    def __init__( self, uart, mode=0 ):
        self.x_char = 0
        self.y_char = 0
        self.uart = uart
        self.mode = mode

    def _write( self, text ):
        self.uart.write( text )

    def clear( self ):
        self.uart.write( "|\x00" )
        self.x_char = 0
        self.y_char = 0

    def backlight( self, brightness ):
        if 0 > brightness or 100 < brightness:
            raise Exception( 'brightness out of bounds' )
        xw = bytes( [0x7c, 0x02, brightness] )
        self._write( xw )

    def reverse( self, value=2 ):
        if 0 == value and 1 == self.reversed:
            self.uart.write( "|\x12" )
        elif 1 == value and 0 == self.reversed:
            self.uart.write( "|\x12" )
        elif 2 == value:
            self.reversed = 1 if 0 == self.reversed else 0
            self.uart.write( "|\x12" )

    def new_line( self ):
        if self.MODE_TEXT != self.mode:
            raise LCDBackpackModeException()
        spaces = self.SCREEN_W_CHAR - self.x_char
        for s in range( spaces ):
            self._write( ' ' )
        self.x_char = 0
        self.y_char += 1

    def write_line( self, text ):
        if self.MODE_TEXT != self.mode:
            raise LCDBackpackModeException()
        new_x = len( text ) + self.x_char
        if self.SCREEN_W_CHAR <= new_x:
            self._write( text[0:(self.SCREEN_W_CHAR - self.x_char)] )
        else:
            self._write( text )
        self.x_char = new_x
        self.new_line()

    def draw_px( self, color, x, y ):
        self.draw_pxs( color, (x, y) )

    def draw_pxs( self, color, *coords ):
        if self.MODE_GFX != self.mode:
            raise LCDBackpackModeException()
        xw = bytearray()
        for p in coords:
            xw += bytes( [0x7c, 0x10, p[0], p[1], color] )
        self._write( xw )

    def draw_line( self, color, x1, y1, x2, y2 ):
        if self.MODE_GFX != self.mode:
            raise LCDBackpackModeException()
        xw = bytes( [0x7c, 0x0c, x1, y1, x2, y2, color] )
        self._write( xw )

    def draw_box( self, color, x1, y1, x2, y2 ):
        if self.MODE_GFX != self.mode:
            raise LCDBackpackModeException()
        xw = bytes( [0x7c, 0x0f, x1, y1, x2, y2, color] )
        self._write( xw )

    def clear_box( self, color, x1, y1, x2, y2 ):
        if self.MODE_GFX != self.mode:
            raise LCDBackpackModeException()
        xw = bytes( [0x7c, 0x05, x1, y1, x2, y2] )
        self._write( xw )

