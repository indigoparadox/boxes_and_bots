
#include "uart.h"

void uart_serial_init( void ) {
   
   /* Set DCO to 1MHz. */
   BCSCTL1 = CALBC1_1MHZ;
   DCOCTL = CALDCO_1MHZ;
   
   /* Set P1.1 and P1.2 to RX and TX. */
   P1SEL = BIT1 + BIT2;                
   P1SEL2 = BIT1 + BIT2;
   
   /* Use SMCLK. */
   UCA0CTL1 |= UCSSEL_2;

   /* Set bitrate to 9600. */
   UCA0BR0 = UART_UCA0BR0;
   UCA0BR1 = UART_UCA0BR1;
   
   /* Use modulation. */
   UCA0MCTL = UCBRS_1;

   /* Start USCI. */
   UCA0CTL1 &= ~UCSWRST;
}

void uart_putc( const char c_char_in ) {
   while( !(IFG2 & UCA0TXIFG) );
   UCA0TXBUF = c_char_in;
}

void uart_echo( char* pc_string_in ) {
   char* pc_iter = pc_string_in;

   while( 0 != *pc_iter ) {
      uart_putc( *pc_iter );

      /* Next character. */
      pc_iter++;
   }
}

