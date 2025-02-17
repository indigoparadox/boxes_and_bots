
#include "psubot.h"
#include "uart.h"
#include "shell.h"

#include <msp430g2553.h>

int i_led_current = LED_RED;

int main( void ) {
   WDTCTL = WDTPW + WDTHOLD;

   psubot_init();

   psubot_eye_enable();
   psubot_eye_pos( EYE_MAX_CYCLES_L / 2 );

   P2OUT = i_led_current;

   uart_serial_init();
   shell_init();

   for( ; ; ) {
      /* Go to sleep. */
      __bis_SR_register( LPM3_bits + GIE );
   }

   return 0;
}

#if 0
void uart_command_handler( char* pc_command_in ) {
   if( uart_strcmp( pc_command_in, "LED" ) ) {
      psubot_eye_pos( EYE_MAX_CYCLES_L / 2 );
      __delay_cycles( 500000 );

      switch( i_led_current ) {
         case LED_RED:
            i_led_current = LED_GREEN;
            break;

         case LED_GREEN:
            i_led_current = LED_BLUE;
            break;
   
         case LED_BLUE:
            i_led_current = LED_RED;
            break;

      }

      P2OUT = i_led_current;
   }
}
#endif

