
class Screen( object ):

    def __init__( self, oled, w, h, top, rtc ):
        self.oled = oled
        self.w = w
        self.h = h
        self.top = top
        self.rtc = rtc
        self.cursor = 0

    def cursor_inc( self ):
        self.cursor += 1
        if len( self.menu ) <= self.cursor:
            self.cursor = 0

    def cursor_dec( self ):
        self.cursor -= 1
        if 0 > self.cursor:
            self.cursor = len( self.menu ) - 1

    def update_screen( self ):
        self.oled.fill( 0 )
        
        dt = self.rtc.datetime()
        self.oled.text( 'ThermTerm  {:2d}:{:02d}'.format( dt[4], dt[5] ), 0, 0 )

        self.draw()

        self.oled.show()

class MenuScreen( Screen ):

    def __init__( self, oled, w, h, top, rtc, menu ):
        super().__init__( oled, w, h, top, rtc )
        self.menu = menu

    def draw( self ):
        idx = 0
        for item in self.menu:
            txt_color = 1
            txt_offset_y = self.top + (idx * 10)
            txt_offset_x = 0
            if self.cursor == idx:
                txt_color = 0
                self.oled.fill_rect( txt_offset_x, txt_offset_y,
                    int( self.w / 2 ), 10, 1 )
            if 'icon' in item:
                self.oled.bitmap(
                    txt_offset_x + 1, txt_offset_y + 1, item['icon'], txt_color )
                try:
                    self.oled.text( '{:5} {}'.format( item['callback'](),
                        item['u'] ), 9, txt_offset_y + 1, col=txt_color )
                except Exception as e:
                    print( e )
            else:
                self.oled.text( item['label'] + '{:3d} {}'.format(
                    item['callback'](), item['u'] ),
                    0, txt_offset_y + 1, col=txt_color )
            idx += 1

