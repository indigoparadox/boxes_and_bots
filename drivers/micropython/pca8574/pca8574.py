
class PCA8574( object ):

    class PCA8574Pin( object ):

        IN = 0
        OUT = 0

        def __init__( self, pca, pid, value=0 ):
            self.pca = pca
            self.pid = pid
            self._val = value

        def __call__( self, value ):
            self.value( value )

        def init( self, direction=None, value=0 ):
            self.value( value )

        def value( self, value=2 ):
            if 1 == value or 0 == value:
                self._val = value
                self.pca._write( self.pca._pin_byte() )
            else:
                return self._val

    def __init__( self, i2c, addr=0x20 ):
        self.i2c = i2c
        self.addr = addr
        self._pins = {}

    def _pin_byte( self ):
        p_out = 0x00
        for idx in range( 8 ):
            if idx in self._pins:
                p_out |= (self._pins[idx]._val << idx)
        return p_out

    def _write( self, b ):
        self.i2c.writeto( self.addr, bytes( [b] ) )

    def pin( self, pid ):
        if pid not in self._pins:
            self._pins[pid] = PCA8574.PCA8574Pin( self, pid )
        return self._pins[pid]

