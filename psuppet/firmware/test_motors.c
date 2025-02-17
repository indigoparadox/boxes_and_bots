
#include <msp430g2553.h>

#define TESTBIT BIT6;

int main( void ) {
   WDTCTL = WDTPW + WDTHOLD;

   P1DIR |= TESTBIT;

   /* Move the eye to the selected position. */
   P1OUT |= TESTBIT;
   /* TODO: Use a timer for this? */
   for(;;) {}
   P1OUT &= ~TESTBIT;
}

