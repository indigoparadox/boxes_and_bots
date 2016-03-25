
#include "uart.h"

#define LED2 BIT6

#define RX_BUFFER_LENGTH 30

static unsigned char rx_buffer[RX_BUFFER_LENGTH];
static char rx_buffer_index = 0;

#pragma vector = USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR( void ) {
	//P1OUT ^= LED2;
	int i;

	rx_buffer[rx_buffer_index++] = UCA0RXBUF;
	if( RX_BUFFER_LENGTH - 1 <= rx_buffer_index ) {
		/* TODO: Should we wrap or discard? */
		rx_buffer_index = 0;
	}

	IFG2 &= ~ UCA0RXIFG;

#if 0
	/* Wrap-around buffer. */
	rx_buffer[rx_buffer_index++] = UCA0RXBUF;
	if( RX_BUFFER_LENGTH - 1 <= rx_buffer_index ) {
		rx_buffer_index = 0;
	}
#endif
}

void uart_init( void ) {

	memset( rx_buffer, '\0', RX_BUFFER_LENGTH );

	// The UART settings used depend on a good 1MHz clock
   BCSCTL1 = CALBC1_1MHZ;
   DCOCTL = CALDCO_1MHZ;

	__delay_cycles( 1000 );

   //P1DIR &= ~BIT3;                     // P1.3 is an input pin
   //P1IE |= BIT3;                       // Switch S2 triggers an interrupt
   //P1IES |= BIT3;                      // on falling edge

	// (1) Set state machine to the reset state
   UCA0CTL1 = UCSWRST;

   // (2) Initialize USCI registers
   UCA0CTL1 |= UCSSEL_2;               // CLK = SMCLK
   UCA0BR0 = 104;                      // 1MHz/9600 = 104
   UCA0BR1 = 0x00;                     //
   UCA0MCTL = UCBRS0;                  // Modulation UCBRSx = 1

   // (3) Configure ports
   P1SEL |= BIT1 + BIT2;                // P1.1 = RXD, P1.2=TXD
   P1SEL2 |= BIT1 + BIT2;               // P1.1 = RXD, P1.2=TXD

   // (4) Clear UCSWRST flag
   UCA0CTL1 &= ~UCSWRST;               // **Initialize USCI state machine**

  	IE2 |= UCA0RXIE;                          // Enable USCI_A0 RX interrupt

	return;
}

unsigned char uart_getc( void ) {
#if 0
	while( !(IFG2 & UCA0RXIFG) ) {
		//timeout--;
	}
	//IFG2 &= ~ UCA0RXIFG;

	if( 0 >= timeout ) {
		/* Time out. */
		return '\0';
	} else {
		/* Get was successful! */
	   return UCA0RXBUF;
	}
#endif
	int i;
	char c_out = '\0';

	/* Wait until an actual character is present. */
	while( '\0' == rx_buffer[0] );

	c_out = rx_buffer[0];
	for( i = 0 ; RX_BUFFER_LENGTH - i > i ; i++ ) {
		rx_buffer[i] = rx_buffer[i + 1];
	}
	rx_buffer_index--;

	return c_out;
}

void uart_gets( char* buffer, int length ) {
	unsigned int i = 0;

	while( length > i ) {
		buffer[i] = uart_getc();
		if( '\r' == buffer[i] || '\n' == buffer[i] ) {
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
	while( !(IFG2 & UCA0TXIFG) );
	UCA0TXBUF = c;

#if 0
	P1OUT |= LED2;
	__delay_cycles( 800000 );
	P1OUT &= ~LED2;
	__delay_cycles( 800000 );
#endif

	return;
}

void uart_puts( const char *str ) {
   while( '\0' != *str ) {
 		uart_putc( *str++ );
	}
   return;
}

