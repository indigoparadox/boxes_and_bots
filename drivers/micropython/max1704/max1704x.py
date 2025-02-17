
ADDR_VCELL = 0x02
ADDR_SOC = 0x04
ADDR_VERSION = 0x08

class MAX1704x( object ):

    def __init__( self, i2c, addr=0x36 ):

        self.i2c = i2c
        self.addr = addr

    def _read( self, mem_addr, sz=2 ):
        val = self.i2c.readfrom_mem( self.addr, mem_addr, sz )
        return int.from_bytes( val, 'small' )

    @property
    def vcell( self ):
        return self._read( ADDR_VCELL )

    @property
    def version( self ):
        return self._read( ADDR_VERSION, 1 )
        
    @property
    def soc( self ):
        return self._read( ADDR_SOC, 1 )

    @property
    def 
        
