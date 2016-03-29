
#include "esp8266.h"

#define ESP8266_NUMBER_MAX_DIGITS 4

static void 
	(*server_handler)( const char* connection_index, const char* string, const char* length ) = NULL;
int server_handler_index = 0;
char recieves[ESP8266_RESPONSES_MAX][ESP8266_BUFFER_LEN];
int recieves_start = 0;
int recieves_end = 0;

static const char* str_error = "ERROR";
static const char* str_ok = "OK";

void esp8266_rx_handler_server( unsigned char c ) {
	char line[ESP8266_BUFFER_LEN];

	uart_gets( line, ESP8266_BUFFER_LEN, TRUE );

	if( 0 == strncmp( "+IPD,", line, 5 ) ) {

		strncpy( recieves[recieves_end++], line, ESP8266_BUFFER_LEN );

		if( ESP8266_RESPONSES_MAX - 1 <= recieves_end ) {
			/* Circle around. */
			recieves_end = 0;
		}

		if( recieves_end + 1 == recieves_start ) {
			/* Overwrite old data. */
			recieves_start++;
		}
	}
}

void esp8266_handle_response_step( void ) {
	char connection_raw[ESP8266_NUMBER_MAX_DIGITS];
	char line_length_raw[ESP8266_NUMBER_MAX_DIGITS];
	char* line_iter;
	char* char_iter;
	int line_length;
	uint8_t i;

	if( recieves_start == recieves_end ) {
		return;
	}

	line_iter = recieves[recieves_start++];
	if( ESP8266_RESPONSES_MAX - 1 <= recieves_start ) {
		/* Wrap around. */
		recieves_start = 0;
	}

	char_iter = line_iter;

	char_iter += 5; /* Skip the +IPD, */

	/* Get the connection index. */
	i = 0;
	while( ',' != *char_iter && ESP8266_NUMBER_MAX_DIGITS - 1 > i ) {
		connection_raw[i] = *char_iter;
		i++;
		char_iter++;
	}
	char_iter++; /* Skip the , */
	connection_raw[i] = '\0';

	/* Get the line length. */
	i = 0;
	while( ':' != *char_iter && ESP8266_NUMBER_MAX_DIGITS - 1 > i ) {
		line_length_raw[i] = *char_iter;
		i++;
		char_iter++;
	}
	char_iter++; /* Skip the : */
	line_length_raw[i] = '\0';
	line_length = atoi( line_length_raw ) - 2;

	/* Don't try to handle empty requests. */
	if( 0 >= line_length ) {
		goto cleanup;
	}

	memset( line_length_raw, '\0', ESP8266_NUMBER_MAX_DIGITS );
	itoa( line_length, line_length_raw, 10 );

	/* Don't try to handle overflowing requests. */
	if( ESP8266_BUFFER_LEN <= line_length ) {
		goto cleanup;
	}

	if( NULL != server_handler ) {
		server_handler(
			connection_raw,
			char_iter,
			line_length_raw
		);
	}

cleanup:

	return;
}

uint8_t esp8266_init( const char* server_port ) {
	char line[ESP8266_BUFFER_LEN];
	uint8_t retval = 0;

	memset( line, '\0', ESP8266_BUFFER_LEN );

	/* Try to get a prompt. */
	uart_puts( "\r\n" );
	uart_puts( "AT+RST\r\n" );
	do {
		__bis_SR_register( GIE + LPM0_bits );
		uart_gets( line, ESP8266_BUFFER_LEN, TRUE );
	} while( 0 != strncmp( "WIFI GOT IP", line, 11 ) );

	if( NULL != server_port ) {
		if( esp8266_command( "AT+CIPMUX=1", NULL ) ) {
			retval = 1;
			goto cleanup;
		}

		if( esp8266_command( "AT+CIPSERVER=1,", server_port ) ) {
			retval = 1;
			goto cleanup;
		}
	}

cleanup:

	return retval;
}

uint8_t esp8266_command( const char* command, const char* args ) {
	char line[ESP8266_BUFFER_LEN];
	uint8_t retval = 0;

	memset( line, '\0', ESP8266_BUFFER_LEN );

	/* Send the command and wait for a response. */
	uart_clear();
	uart_puts( command );
	if( NULL != args ) {
		uart_puts( args );
	}
	uart_puts( "\r\n" );
	do {
		__bis_SR_register( GIE + LPM0_bits );
		uart_gets( line, ESP8266_BUFFER_LEN, TRUE );
		if( 0 == strncmp( str_error, line, 5 ) ) {
			retval = 1;
			break;
		}
	} while( 0 != strncmp( str_ok, line, 2 ) );

	return retval;
}

void esp8266_start_server( void (*handler)( const char*, const char*, const char* ) ) {
	server_handler = handler;
	server_handler_index = uart_add_rx_handler( esp8266_rx_handler_server );
}

void esp8266_stop_server( void ) {
	uart_del_rx_handler( server_handler_index );
	server_handler = NULL;
}

void esp8266_send( const char* connection, const char* string, const char* length ) {
	
	/* Start sending. */
	uart_puts( "AT+CIPSEND=" );
	uart_puts( connection );
	uart_putc( ',' );
	uart_puts( length );
	uart_puts( "\r\n" );

	/* Wait for it to be clear to send. */
	__bis_SR_register( GIE + LPM0_bits );

	uart_puts( string );

	return;
}

BOOL esp8266_server_waiting( void ) {
	BOOL retval = FALSE;

	if( recieves_start != recieves_end ) {
		retval = TRUE;
	}

	return retval;
}

