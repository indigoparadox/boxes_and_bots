
import time

class RoboBusyException( Exception ):
    pass

class RoboController( object ):
    pass

class SixLegsController( object ):

    def __init__( self, spin_cw, spin_ccw, move_fwd, move_back ):
        self.busy = False
        self.spin_cw = spin_cw
        self.spin_ccw = spin_ccw
        self.move_fwd = move_fwd
        self.move_back = move_back

    def _exec_motor( self, motor, ms ):
        if self.busy:
            raise RoboBusyException( 'controller busy' )
        self.busy = True
        motor.value( 1 )
        time.sleep_ms( ms )
        motor.value( 0 )
        self.busy = False

    def rotate_cw( self, ms ):
        self._exec_motor( self.spin_cw, ms )

    def rotate_ccw( self, ms ):
        self._exec_motor( self.spin_ccw, ms )

    def walk_fwd( self, ms ):
        self._exec_motor( self.move_fwd, ms )

    def walk_rev( self, ms ):
        self._exec_motor( self.move_back, ms )

