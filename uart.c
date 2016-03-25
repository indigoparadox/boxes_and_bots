
#include "uart.h"

#define LED2 BIT6

#define RX_BUFFER_LENGTH 128

static unsigned char rx_buffer[RX_BUFFER_LENGTH];
static unsigned char rx_buffer_index_start = 0;
static unsigned char rx_buffer_index_end = 0;

#pragma vector = USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR( void ) {
	int i;
	unsigned char rx_in = UCA0RXBUF;

	//while( !(IFG2 & UCA0RXIFG) );

	if( '\n' == rx_in ) {
		return;
	}

	rx_buffer[rx_buffer_index_end++] = rx_in;
	if( RX_BUFFER_LENGTH - 1 <= rx_buffer_index_end ) {
		/* Circle around. */
		rx_buffer_index_end = 0;
	}

	if( rx_buffer_index_end + 1 == rx_buffer_index_start ) {
		/* Overwrite old data. */
		rx_buffer_index_start++;
	}
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
	char c_out;

	/* Wait until an actual character is present. */
	while( rx_buffer_index_start == rx_buffer_index_end ) {
		__delay_cycles( 1000 );
	}

	c_out = rx_buffer[rx_buffer_index_start++];
	if( RX_BUFFER_LENGTH - 1 <= rx_buffer_index_start ) {
		/* Wrap around. */
		rx_buffer_index_start = 0;
	}

	return c_out;
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

