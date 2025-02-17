
import ujson as json

class PixyBlock( object ):
    def toJSON( self ):
        return json.dumps( self.__dict__ )

class CMUcam5( object ):

    # Pre-encoded as Little Endian.
    SYNC_NOCK = [0xae, 0xc1]
    SYNC_CK = [0xaf, 0xc1]

    TYPE_GET_BLOCKS = 32
    TYPE_SET_LED = 20
    
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

    def set_led( self, r, g, b ):
        pkt = self._encode_pkt( self.TYPE_SET_LED, [r, g, b] )
        self.i2c.writeto( self.addr, pkt )

    def get_blocks( self, sig=255, max_blks=255 ):
        # Send request for blocks.
        pkt = self._encode_pkt( self.TYPE_GET_BLOCKS, [sig, max_blks] )
        self.i2c.writeto( self.addr, pkt )
        
        # Fetch and parse the header info.
        hdr = self.i2c.readfrom( self.addr, self.SZ_HEADER )
        pkt_type, l, cksum = self._decode_pkt( hdr )

        # Fetch the actual payload.
        pl = self.i2c.readfrom( self.addr, l )
        self._verify_cksum( cksum, pl )

        count = len( pl ) / self.SZ_BLOCK

        # Parse payload into block objects.
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

            # Add block to outgoing list.
            blks_out += [pb]

        return blks_out

