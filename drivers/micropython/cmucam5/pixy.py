# for encoding/decoding see https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:protocol_reference

import utime as time
import ujson as json

class PixyBlock( object ):
    def toJSON( self ):
        return json.dumps( self.__dict__ )

class CMUcam5( object ):

    # Pre-encoded as Little Endian.
    SYNC_NOCK = [0xae, 0xc1]
    SYNC_CK = [0xaf, 0xc1]

    TYPE_GET_RESOLUTION = 12
    TYPE_GET_VERSION = 14
    TYPE_GET_BLOCKS = 32
    TYPE_GET_RGB = 112

    TYPE_SET_BRIGHTNESS = 16
    TYPE_SET_LED = 20
    TYPE_SET_LAMP = 22

    SZ_HEADER = 6
    SZ_BLOCK = 14

    def __init__( self, i2c, addr=0x54 ):
        self.i2c = i2c
        self.addr = addr

    def _encode_pkt( self, pkt_type, pl_bytes ):
        l = len( pl_bytes )
        return bytearray( self.SYNC_NOCK + [pkt_type, l] + pl_bytes )

    def _decode_pkt( self, hdr ):
        if hdr[0] != self.SYNC_CK[0] or hdr[1] != self.SYNC_CK[1]:
            raise Exception( 'Invalid sync' )
        # Parse header info.
        pkt_type = int( hdr[2] )
        l = int( hdr[3] )
        cksum = (int( hdr[5] ) << 8) + int( hdr[4] )

        return pkt_type, l, cksum

    def _verify_cksum( self, cksum, pl ):
        # Sum and verify payload.
        cktmp = 0
        for b in pl:
            cktmp += int( b )
        if cktmp != cksum:
            raise Exception( 'cksum failure.' )

    def _call( self, type, args ):
        pkt = self._encode_pkt( type, args )
        self.i2c.writeto( self.addr, pkt )

        hdr = self.i2c.readfrom( self.addr, self.SZ_HEADER )
        pkt_type, l, cksum = self._decode_pkt( hdr )
        payload = self.i2c.readfrom( self.addr, l )

        self._verify_cksum( cksum, payload )
        return pkt_type, payload

    def init( self, wait_ms=5000, callback=None):
        """wait for connection, typically takes 2-3 seconds after power on"""
        t = time.ticks_ms()
        while True:
            try:
                if callback:
                    callback()
                self.get_version() # device connection test
                break
            except:
                if time.ticks_diff(time.ticks_ms(), t) > wait_ms:
                    raise

    def get_version( self ):
        _, pl = self._call( self.TYPE_GET_VERSION, [] )
        return pl # todo: split payload

    def get_resolution( self ):
        _, pl = self._call( self.TYPE_GET_RESOLUTION, [0] )
        return pl[0] + (pl[1]<<8), pl[2] + (pl[3]<<8)

    def set_brightness( self, value ):
        self._call( self.TYPE_SET_BRIGHTNESS, [value] )

    def set_lamp( self, upper, lower):
        self._call( self.TYPE_SET_LAMP, [upper, lower] )

    def set_led( self, r, g, b ):
        self._call( self.TYPE_SET_LED, [r, g, b] )

    def get_blocks( self, sig=255, max_blks=255 ):
        _, pl = self._call( self.TYPE_GET_BLOCKS, [sig, max_blks] )

        count = len( pl ) / self.SZ_BLOCK
        blks_out = []
        for i in range( count ):
            if 0xfe == pl[0]:
                # No blocks.
                break
            offset = i * self.SZ_BLOCK
            pb = PixyBlock()
            pb.sig = (pl[offset + 1] << 8) + pl[offset]
            pb.x = (pl[offset + 3] << 8) + pl[offset + 2]
            pb.y = (pl[offset + 5] << 8) + pl[offset + 4]
            pb.w = (pl[offset + 7] << 8) + pl[offset + 6]
            pb.h = (pl[offset + 9] << 8) + pl[offset + 8]
            pb.a = (pl[offset + 11] << 8) + pl[offset + 10]
            pb.idx = pl[offset + 12]
            pb.age = pl[offset + 13]
            blks_out += [pb]
        return blks_out

    def get_rgb( self, x, y, saturate):
        pt, pl = self._call( self.TYPE_GET_RGB, [x & 0xff, x << 8, y & 0xff, y << 8, saturate] )
        return pl[2], pl[1], pl[0]
