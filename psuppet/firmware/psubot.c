
#include "psubot.h"

#include <stdint.h>

//int gi_debounce_counter_button = 0;
BOOL gb_sleeping = 0;
int gi_eye_move_loops = 0;
DRIVING_DIR ge_driving_dir = DRIVING_STOPPED;

void psubot_init( void ) {

   /* Turn off all indicators.*/
   P1OUT = 0;
   P2OUT = 0;

   #if 0
   /* This should be used on button inputs to debounce or something,          *
    * probably. Our original intention was to use it to control wheel drivine *
    * before we switched to the new continuous driving model. The timer       *
    * itself conflicts with the low power modes.                              */

   /* Enable the maintenance timer. */
   WDTCTL = WDTPW | WDTTMSEL | WDTCNTCL;
   /* WDTCTL = WDT_ADLY_1000; */
   IE1 |= WDTIFG;
   /* BCSCTL2 = DIVS_2; */
   _EINT();
   #else
   WDTCTL = WDTPW | WDTHOLD;
   #endif
}

void psubot_eye_enable( void ) {

   /* Setup Motor I/O */
   P1DIR = 0;
   P1DIR |= EYE_R;
   P1DIR |= EYE_L;
   
   /* Setup LED I/O */
   P2DIR = 0;
   P2DIR |= LED_RED;
   P2DIR |= LED_GREEN;
   P2DIR |= LED_BLUE;
}

void psubot_wheels_enable( void ) {
   P1DIR |= WHEEL_R_F;
   P2DIR |= WHEEL_L_F | WHEEL_L_R | WHEEL_R_R;
}

/* Parameters:                                                                *
 *    i_pos_in - The percentage to the left to position the eye.              */
void psubot_eye_pos( int i_pos_in ) {
   uint8_t i_sense_count = 0;
   long l_target_pos,
      l_pos_in = i_pos_in,
      i;

   /* Figure out the position as a percentage of the eye's max range. */
   l_target_pos = l_pos_in * EYE_MAX_CYCLES_L / 100;

   /* Move the eye to position zero. */
   P1OUT |= EYE_R;
   while( 
      !(P1IN & EYE_SENSE && i_sense_count >= 200) && 
      EYE_MAX_LOOPS_R > gi_eye_move_loops
   ) {
      __delay_cycles( 10 );
      gi_eye_move_loops++;
      
      /* Don't count the sensor as being held down unless it's being held     *
       * down!                                                                */
      if( P1IN && EYE_SENSE ) {
         i_sense_count++;
      } else {
         i_sense_count = 0;
      }
   }
   P1OUT &= ~EYE_R;

   /* Make sure we didn't just time out. */
   if( EYE_MAX_LOOPS_R <= gi_eye_move_loops ) {
      psubot_halt();
   } else {
      gi_eye_move_loops = 0;
   }

   psubot_eye_move( EYE_LEFT );
   for( i = 0 ; i < l_target_pos ; i++ ) {}
   psubot_eye_move( EYE_STOPPED );
}

/* Purpose: Push the eye to the robot's left by the given increment.          */
/* TODO: Keep a global variable with the current position of the eye. Set it  *
 *       to 0 during the eye init phase and increment/decrement it whenever   *
 *       the eye is moved. Don't allow the eye to move out of its operational *
 *       range.                                                               */
void psubot_eye_move( EYE_DIR e_eye_dir_in ) {
   switch( e_eye_dir_in ) {
      case EYE_RIGHT:
         P1OUT |= EYE_R;
         break;
      case EYE_LEFT:
         P1OUT |= EYE_L;
         break;
      case EYE_STOPPED:
         P1OUT &= ~EYE_L & ~EYE_R;
         break;
   }
}

void psubot_wheel_drive( DRIVING_DIR e_direction_in ) {
   switch( e_direction_in ) {
      case DRIVING_FORWARD:
         P1OUT |= WHEEL_R_F;
         P2OUT |= WHEEL_L_F;
         break;
      case DRIVING_REVERSE:
         P2OUT |= WHEEL_L_R | WHEEL_R_R;
         break;
      case DRIVING_RIGHT:
         P2OUT |= WHEEL_L_F;
         break;
      case DRIVING_RIGHT_PIVOT:
         P2OUT |= WHEEL_L_F | WHEEL_R_R;
         break;
      case DRIVING_LEFT:
         P1OUT |= WHEEL_R_F;
         break;
      case DRIVING_LEFT_PIVOT:
         P1OUT |= WHEEL_R_F;
         P2OUT |= WHEEL_L_R;
         break;
      case DRIVING_STOPPED:
         P1OUT &= ~WHEEL_R_F;
         P2OUT &= ~WHEEL_L_F & ~WHEEL_R_R & ~WHEEL_L_R;
      default:
         return;
   }
}

/* Purpose: Halt all activity and blink the internal LED.                     */
void psubot_halt( void ) {
   
   /* Disable all interrupts. */
   P1IE = 0;
   P2IE = 0;
   IE2 = 0;

   /* Turn off all outputs. */
   P1OUT = 0;
   P2OUT = 0;

   /* Blink indefinitely. */
   P1DIR |= ILED;
   for(;;) {
      P1OUT |= ILED;
      __delay_cycles( 250000 );
      P1OUT &= ~ILED;
      __delay_cycles( 250000 );
   }
}

#if 0
/* See WDT notes above. */
#pragma vector=WDT_VECTOR
__interrupt void psubot_wdt_isr( void ) {
   P1OUT ^= BIT0;
   IFG1 &= ~WDTIFG;
}
#endif

