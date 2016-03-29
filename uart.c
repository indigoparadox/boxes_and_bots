
#include "uart.h"

#define RX_BUFFER_LENGTH 20

#define HANDLERS_COUNT_MAX 6

#define UART_COUNTER_MAX 100

/* Ring buffer to hold recieved characters. */
static uint8_t rx_buffer[RX_BUFFER_LENGTH];
static uint8_t rx_buffer_index_start = 0;
static uint8_t rx_buffer_index_end = 0;

static void (*rx_handlers[HANDLERS_COUNT_MAX])( unsigned char c );
static uint8_t rx_handlers_count = 0;

static void (*wdt_handlers[HANDLERS_COUNT_MAX])( uint8_t );
static uint8_t wdt_handlers_count = 0;
static uint8_t wdt_counter = 0;

#pragma vector = USCIAB0RX_VECTOR
__interrupt void USCI0RX_ISR( void ) {
	int8_t i;
	unsigned char rx_in = UCA0RXBUF;

	/* The esp8266 sends back \r\n, so just chop this off to prevent dupes. */
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

	/* Run any handlers we have if we've got a full line. */
	if( '\r' == rx_in ) {
		for( i = 0 ; rx_handlers_count > i ; i++ ) {
			rx_handlers[i]( rx_in );
		}
	}
}

#pragma vector = WDT_VECTOR
__interrupt void watchdog_timer( void ) {
	uint8_t i;
	static uint8_t counter = 0;

	if( UART_COUNTER_MAX < counter ) {
		counter = 0;
	} else {
		counter++;
	}

	/* Run registered handlers. */
	for( i = 0 ; wdt_handlers_count > i ; i++ ) {
		wdt_handlers[i]( counter );
	}
}

void uart_init( void ) {
	uint8_t i;

	/* Zero out our buffers for sanity. */
	memset( rx_buffer, '\0', RX_BUFFER_LENGTH );
	for( i = 0 ; HANDLERS_COUNT_MAX > i ; i++ ) {
		rx_handlers[i] = NULL;
	}

	/* The UART settings used depend on a good 1MHz clock. */
   BCSCTL1 = CALBC1_1MHZ;
   DCOCTL = CALDCO_1MHZ;

	__delay_cycles( 1000 );

	/* (1) Set state machine to the reset state. */
   UCA0CTL1 = UCSWRST;

   /* (2) Initialize USCI registers. */
   UCA0CTL1 |= UCSSEL_2;               /* CLK = SMCLK */
   UCA0BR0 = 104;                      /* 1MHz/9600 = 104 */
   UCA0BR1 = 0x00;                     
   UCA0MCTL = UCBRS0;                  /* Modulation UCBRSx = 1 */

   /* (3) Configure ports. */
   P1SEL |= RXD + TXD;              	/* P1.1 = RXD, P1.2=TXD */
   P1SEL2 |= RXD + TXD;              /* P1.1 = RXD, P1.2=TXD */

   /* (4) Clear UCSWRST flag. */
   UCA0CTL1 &= ~UCSWRST;               /* Initialize USCI state machine. */

	/* Enable watchdog timer. */
	WDTCTL = WDT_MDLY_32;
	IE1 |= WDTIE;

  	IE2 |= UCA0RXIE;                    /* Enable USCI_A0 RX interrupt. */

	return;
}

void uart_clear( void ) {
	rx_buffer_index_start = rx_buffer_index_end;
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
	/* TODO: Use a ring buffer and interrupts for TX, too. */
	while( !(IFG2 & UCA0TXIFG) );
	UCA0TXBUF = c;
	return;
}

void uart_puts( const char *str ) {
   while( '\0' != *str ) {
 		uart_putc( *str++ );
	}
   return;
}

void uart_nputs( const char *str, int length ) {
	int i;
   while( '\0' != *str && i < length ) {
 		uart_putc( *str++ );
		i++;
	}
   return;
}

int8_t uart_add_rx_handler( void (*handler)( unsigned char c ) ) {
	int8_t retval = 0;
	
	if( rx_handlers_count + 1 >= HANDLERS_COUNT_MAX ) {
		retval = -1;
		goto cleanup;
	}

	rx_handlers[rx_handlers_count] = handler;
	retval = rx_handlers_count;
	rx_handlers_count++;

cleanup:

	return retval;
}

void uart_del_rx_handler( int8_t index ) {
	int8_t i;

	if( 0 > index || index >= rx_handlers_count ) {
		goto cleanup;
	}

	/* Clear this handler and pull the subsequent ones down to it. */
	rx_handlers[0] = NULL;
	for( i = index ; i < rx_handlers_count - 2 ; i++ ) {
		rx_handlers[i] = rx_handlers[i + 1];
		rx_handlers[i + 1] = NULL;
	}

	rx_handlers_count--;

cleanup:

	return;
}

int8_t uart_add_wdt_handler( void (*handler)( uint8_t counter ) ) {
	int8_t retval = 0;
	
	if( wdt_handlers_count + 1 >= HANDLERS_COUNT_MAX ) {
		retval = -1;
		goto cleanup;
	}

	wdt_handlers[wdt_handlers_count] = handler;
	retval = wdt_handlers_count;
	wdt_handlers_count++;

cleanup:

	return retval;
}

void uart_del_wdt_handler( int8_t index ) {
	int8_t i;

	if( 0 > index || index >= wdt_handlers_count ) {
		goto cleanup;
	}

	/* Clear this handler and pull the subsequent ones down to it. */
	wdt_handlers[0] = NULL;
	for( i = index ; i < wdt_handlers_count - 2 ; i++ ) {
		wdt_handlers[i] = wdt_handlers[i + 1];
		wdt_handlers[i + 1] = NULL;
	}

	wdt_handlers_count--;

cleanup:

	return;
}

void uart_itoa( long unsigned int value, char* result, int base ) {
	char* ptr = result,
		* ptr1 = result,
		tmp_char;
	int tmp_value;

	/* Ensure base sanity. */
	if( 2 > base || 36 < base ) {
		*result = '\0';
		goto cleanup;
	}

	do {
		tmp_value = value;
		value /= base;
		*ptr++ = "zyxwvutsrqponmlkjihgfedcba9876543210123456789abcdefghijklmnopqrstuvwxyz" [35 + (tmp_value - value * base)];
	} while( value );

	/* Apply negative sign. */
	if( 0 > tmp_value ) {
		*ptr++ = '-';
	}
	*ptr-- = '\0';
	while( ptr1 < ptr ) {
		tmp_char = *ptr;
		*ptr-- = *ptr1;
		*ptr1++ = tmp_char;
	}

cleanup:
	
	return;
}

