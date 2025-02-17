
#include <msp430g2553.h>

#include "psubot.h"

int i_led_current = LED_RED;

int main( void ) {
   WDTCTL = WDTPW + WDTHOLD;

   psubot_init();

   psubot_eye_enable();
   for(;;) {
      psubot_eye_pos( EYE_MAX_CYCLES_L );
      __delay_cycles( 500000 );
   }

   return 0;
}

