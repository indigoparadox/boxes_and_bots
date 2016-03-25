
#include <msp430g2553.h>
#include <string.h>

#include "uart.h"
#include "esp8266.h"

#define LED1 BIT0
#define LED2 BIT6

int main( void ) {
	WDTCTL = WDTPW + WDTHOLD;

	unsigned short uart_starting = 1;
	int uart_wait = 0;
	int retval = 0;
	long i;

	P1DIR |= LED1;
   P1OUT &= ~LED1;

	P1DIR |= LED2;
   P1OUT &= ~LED2;

   P1OUT |= LED1;

	uart_init();

	__bis_SR_register( GIE );

	__delay_cycles( 800000 );

	esp8266_init();

#if 0
#endif

	if( !esp8266_command( "AT+CIPMUX=1" ) ) {
		P1OUT |= LED1;
		retval = 1;
	}

	if( !esp8266_command( "AT+CIPSERVER=1,8888" ) ) {
		P1OUT |= LED1;
		retval = 1;
	}

	if( !retval ) {
		P1OUT &= ~LED1;
		P1OUT |= LED2;
	}

	while( 1 ) {

	}

	return 0;
}

