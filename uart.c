
#include "uart.h"

volatile unsigned int tx_flag;
volatile unsigned char tx_char;
volatile unsigned int rx_flag;
volatile unsigned char rx_char;

void uart_init( void ) {
	P1SEL = RXD + TXD;
	P1SEL2 = RXD + TXD;

#ifdef UART_LED
	P1DIR |= LED;
   P1OUT |= LED;
#endif /* UART_LED */

	/* 8,000,000Hz, 9600Baud, UCBRx=52, UCBRSx=0, UCBRFx=1 */
	UCA0CTL1 |= UCSSEL_2;
	UCA0BR0 = 52; /* 8MHz, OSC16, 9600 */
	UCA0BR1 = 0; /* ((8MHz/9600)/16) = 52.08333 */
	UCA0MCTL = 0x10 | UCOS16; /* UCBRFx=1,UCBRSx=0, UCOS16=1 */
	UCA0CTL1 &= ~UCSWRST; /* USCI state machine */
	IE2 |= UCA0RXIE; /* Enable USCI_A0 RX interrupt */

	rx_flag = 0;
	tx_flag = 0;

	return;
}

unsigned char uart_getc( void ) {
	while( 0 == rx_flag );
	rx_flag = 0;
   return rx_char;
}

void uart_gets( char* buffer, int length ) {
	unsigned int i = 0;

	while( length > i ) {
		buffer[i] = uart_getc();
		if( '\r' == buffer[i] ) {
			for( ; length > i ; i++ ) {
				buffer[i] = '\0';
			}
			break;
		}
		i++;
	}

	return;
}

void uart_putc( const unsigned char c ) {
	tx_char = c;
	IE2 |= UCA0TXIE;
	while( 1 == tx_flag );
	tx_flag = 1;
	return;
}

void uart_puts( const char *str ) {
   while( '\0' != *str ) {
 		uart_putc( *str++ );
	}
   return;
}

