
#include <msp430g2553.h>
#include <string.h>

#include "uart.h"
#include "esp8266.h"
#include "DHT11_LIB.h"

#define LED1 BIT0
#define LED2 BIT6

#define SENSOR BIT6

#define MAX_DIGITS 5

unsigned char volatile SECOND_TIMER = 0;
unsigned char volatile TOUT;

#pragma vector = TIMER0_A0_VECTOR
__interrupt void CCR0_ISR( void ) {
	SECOND_TIMER++;
	TOUT = 1;
	//P1OUT ^= BIT0;
	TACCTL0 &= ~CCIFG;
}

void sensor_handler( const char* conn, const char* str, const char* length ) {

	unsigned char packet[5];
	char humidity[MAX_DIGITS];
	char humidity_length[MAX_DIGITS];

	memset( humidity, '\0', MAX_DIGITS * sizeof( unsigned char ) );

	esp8266_send( conn, "Reading...", "10", TRUE );

#if 0
	TACTL |= TACLR;
	TA0CTL |= 0x10;
	TACCR0 = 50000;
	SECOND_TIMER = 0;
	
	while( 5 > SECOND_TIMER );

	/* TODO */
	//esp8266_send( connection_index, string, length );
	read_Packet( packet );

	/*
	RH_byte1 = Packet[0];
	RH_byte2 = Packet[1];
	T_byte1 = Packet[2];
	T_byte2 = Packet[3];
	checksum = Packet[4];
	*/

	if( check_Checksum( packet ) ) {
		P1OUT |= LED1;
	}

/*
	itoa( packet[0], humidity, 10 );
	itoa( strlen( humidity ), humidity_length, 10 );

	esp8266_send( conn, humidity, humidity_length, TRUE );
*/
	

#endif
}

int main( void ) {
	WDTCTL = WDTPW + WDTHOLD;

	/* Enable the LEDs. */
	P1DIR |= LED1;
   P1OUT &= ~LED1;
	P1DIR |= LED2;
   P1OUT &= ~LED2;

	uart_init();

	TACCTL0 = CCIE;
	TA0CTL = TASSEL_2 + ID_2 + MC_1 + TACLR;

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

