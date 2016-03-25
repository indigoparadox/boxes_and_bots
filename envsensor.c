
#include <msp430g2553.h>
#include <string.h>

#include "uart.h"

#define UART_BUFFER_LEN 50
#define UART_WAIT_CYCLES 20

#define RESPONSE_CYCLES 80000

#define LED1 BIT0
#define LED2 BIT6

int main( void ) {
	WDTCTL = WDTPW + WDTHOLD;

	char line[UART_BUFFER_LEN];
	unsigned short uart_starting = 1;
	int uart_wait = 0;
	long i;

	memset( line, '\0', UART_BUFFER_LEN );

	P1DIR |= LED1;
   P1OUT |= LED1;

	P1DIR |= LED2;
   P1OUT &= ~LED2;

	uart_init();

	__bis_SR_register( GIE );

   P1OUT |= LED1;

	__delay_cycles( RESPONSE_CYCLES );
	do {
		P1OUT &= ~LED1;
		__delay_cycles( RESPONSE_CYCLES );
		P1OUT |= LED1;
		__delay_cycles( RESPONSE_CYCLES );
		/* Wait for reset status to finish. */
		uart_puts( "\r\n" );
		__delay_cycles( RESPONSE_CYCLES );
		uart_gets( line, UART_BUFFER_LEN );
		if( 0 != line[0] ) {
			P1OUT |= LED2;
			__delay_cycles( RESPONSE_CYCLES );
			P1OUT &= ~LED2;
			__delay_cycles( RESPONSE_CYCLES );
		}
	} while( 0 != strncmp( "ERROR", line, 5 ) );

   P1OUT |= LED2;
   P1OUT &= ~LED1;

	while( 1 ) {

	}

	return 0;
}

