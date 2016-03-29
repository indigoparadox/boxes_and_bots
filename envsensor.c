
#include <msp430g2553.h>
#include <string.h>

#include "uart.h"
#include "esp8266.h"

#define LED1 BIT0
#define LED2 BIT6

void sensor_handler( const char* connection_index, const char* string, const char* length ) {
	/* TODO */
	esp8266_send( connection_index, string, length );
}

int main( void ) {
	WDTCTL = WDTPW + WDTHOLD;

	/* Enable the LEDs. */
	P1DIR |= LED1;
   P1OUT &= ~LED1;
	P1DIR |= LED2;
   P1OUT &= ~LED2;

	uart_init();

	__bis_SR_register( GIE );

	__delay_cycles( 800000 );

	if( !esp8266_init( "8888" ) ) {
		P1OUT |= LED2;
	}

	esp8266_start_server( sensor_handler );

	while( TRUE ) {
		if( !esp8266_server_waiting() ) {
			__bis_SR_register( GIE + LPM0_bits );
		}
		//uart_nputs( "mfoo\r\n", 6 );
		esp8266_handle_response_step();
	}

	return 0;
}

