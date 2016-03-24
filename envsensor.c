
#include <msp430g2553.h>
#include <string.h>

#include "uart.h"

#define UART_BUFFER_LEN 50
#define UART_WAIT_CYCLES 10

#define RESPONSE_CYCLES 800000

#define LED0 BIT0
#define LED1 BIT6

extern volatile unsigned int tx_flag;
extern volatile unsigned char tx_char;
extern volatile unsigned int rx_flag;
extern volatile unsigned char rx_char;

#pragma vector = USCIAB0TX_VECTOR
__interrupt void USCI0TX_ISR(void) {
	UCA0TXBUF = tx_char;
	tx_flag = 0;
	IE2 &= ~UCA0TXIE;
}

#pragma vector = USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR( void ) {
	rx_char = UCA0RXBUF;
	rx_flag = 1;
	P1OUT ^= LED1;
}

// Timer A0 interrupt service routine
#pragma vector=TIMERA0_VECTOR
__interrupt void TA0_ISR( void ) {
	P1OUT ^= 0x01; // Toggle P1.0
	CCR0 += 50000; // Add Offset to CCR0
}

int main( void ) {
	char line[UART_BUFFER_LEN];
	unsigned short uart_starting = 1;
	int uart_wait = 0;
	long i;

	WDTCTL = WDTPW + WDTHOLD;

	memset( line, '\0', UART_BUFFER_LEN );

	P1DIR |= LED0;
   P1OUT |= LED0;

	P1DIR |= LED1;
   P1OUT &= ~LED1;

	__enable_interrupt();

	while( uart_starting ) {
		P1OUT &= ~LED0;
		__delay_cycles( RESPONSE_CYCLES );
		P1OUT |= LED0;

		//uart_gets( line, UART_BUFFER_LEN );

		if( UART_WAIT_CYCLES <= uart_wait ) {
			uart_puts( "AT+RST\r\n" );
			uart_wait = 0;
			__delay_cycles( RESPONSE_CYCLES );
		}

		//uart_puts( "\n\r" );
		__delay_cycles( RESPONSE_CYCLES );

		if( 0 == strncmp( "ERROR", line, 5 ) ) {
			uart_starting = 0;
		}

		uart_wait++;
	}

   P1OUT |= LED1;
   P1OUT &= ~LED0;

	while( 1 ) {

	}

	return 0;
}

