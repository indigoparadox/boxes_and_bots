
#include "psubot.h"

int main( void ) {
   WDTCTL = WDTPW + WDTHOLD;

   psubot_init();

   psubot_eye_enable();

   for( ; ; ) {
      if( !(P1IN & EYE_SENSE) ) {
         P2OUT = LED_RED;
      } else {
         P2OUT = LED_BLUE;
      }
   }

   return 0;
}

