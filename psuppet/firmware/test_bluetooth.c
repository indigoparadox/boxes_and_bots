
#include <msp430.h>

#include "psubot.h"
#include "uart.h"
#include "shell.h"
#include "beep.h"

#include <stdlib.h>

SHELL_ENABLE();

int i_led_current = LED_RED;

int main( void ) {

   psubot_init();

   psubot_eye_enable();
   psubot_eye_pos( 50 );

   psubot_wheels_enable();

   P2OUT = i_led_current;

   uart_serial_init();

   beep_init();

   // TODO: Check to see if we're connected.
   uart_echo( "\r\n+STWMOD=0\r\n" );
   uart_echo( "\r\n+STNA=PSUBot\r\n" );
   uart_echo( "\r\n+STAAUTO=1\r\n" );
   uart_echo( "\r\n+STOAUT=1\r\n" );
   /*uart_echo( "\r\n+STPIN=0000\r\n" );*/

   __delay_cycles( 1000000 );
   uart_echo( "\r\n+INQ=1\r\n" );
   __delay_cycles( 1000000 );

   /* uart_echo( "\r\n+CONN=00:10:C6:C3:E6:4D\r\n" ); */

   shell_init();

   /* Play a little tune to signal we're ready. */
   BEEP_NOTE gae_startup[4] = {
      BEEP_C, BEEP_E, BEEP_D, BEEP_NULL
   };
   beep_string( &gae_startup, 100 );

   /* Go to sleep. */
   /* TODO: Find a way to sleep without disabling the maintenance timer. */
   __bis_SR_register( LPM0_bits + GIE );

   return 0;
}

void command_led( void ) {
   
   if( shell_strcmp( "RED", gac_args[1] ) ) {
      i_led_current = LED_RED;
   } else if( shell_strcmp( "GREEN", gac_args[1] ) ) {
      i_led_current = LED_GREEN;
   } else if( shell_strcmp( "BLUE", gac_args[1] ) ) {
      i_led_current = LED_BLUE;
   }

   #if 0
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
   #endif

   P2OUT = i_led_current;
}

void command_eye( void ) {
   if( shell_strcmp( "POS", gac_args[1] ) ) {
      psubot_eye_pos( atoi( gac_args[2] ) );
   } else if( shell_strcmp( "R", gac_args[1] ) ) {
      psubot_eye_move( EYE_RIGHT );
   } else if( shell_strcmp( "L", gac_args[1] ) ) {
      psubot_eye_move( EYE_LEFT );
   } else if( shell_strcmp( "S", gac_args[1] ) ) {
      psubot_eye_move( EYE_STOPPED );
   }
}

void command_beep( void ) {
   beep( atoi( gac_args[1] ), atoi( gac_args[2] ) );
}

void command_drive( void ) {
   if( shell_strcmp( "R", gac_args[1] ) ) {
      psubot_wheel_drive( DRIVING_RIGHT );
   } else if( shell_strcmp( "L", gac_args[1] ) ) {
      psubot_wheel_drive( DRIVING_LEFT );
   } else if( shell_strcmp( "PR", gac_args[1] ) ) {
      psubot_wheel_drive( DRIVING_RIGHT_PIVOT );
   } else if( shell_strcmp( "PL", gac_args[1] ) ) {
      psubot_wheel_drive( DRIVING_LEFT_PIVOT );
   } else if( shell_strcmp( "F", gac_args[1] ) ) {
      psubot_wheel_drive( DRIVING_FORWARD );
   } else if( shell_strcmp( "B", gac_args[1] ) ) {
      psubot_wheel_drive( DRIVING_REVERSE );
   } else if( shell_strcmp( "S", gac_args[1] ) ) {
      psubot_wheel_drive( DRIVING_STOPPED );
   }
}

SHELL_COMMANDS_BLOCK_START( 4 )
SHELL_COMMANDS_BLOCK_ITEM( "LED", "[EYE COLOR]", command_led ),
SHELL_COMMANDS_BLOCK_ITEM( "EYE", "[POS] [INCR] OR [R/L] [INCR]", command_eye ),
SHELL_COMMANDS_BLOCK_ITEM( "BEEP", "[FREQ] [TIME]", command_beep ),
SHELL_COMMANDS_BLOCK_ITEM( "DRIVE", "[F/B/R/L/RP/LP] [TIME]", command_drive ),
SHELL_COMMANDS_BLOCK_END()

