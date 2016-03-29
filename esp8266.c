
#include "esp8266.h"

#define ESP8266_NUMBER_MAX_DIGITS 4

static void 
	(*server_handler)( const char* connection_index, const char* string, const char* length ) = NULL;
int server_handler_index = 0;
//struct esp8266_response responses[ESP8266_RESPONSES_MAX];
char recieves[ESP8266_RESPONSES_MAX][ESP8266_BUFFER_LEN];
int responses_start = 0;
int responses_end = 0;

static const char* str_error = "ERROR";
static const char* str_ok = "OK";

void esp8266_rx_handler_server( unsigned char c ) {
	char line[ESP8266_BUFFER_LEN];
	struct esp8266_response* response_iter;
	int line_length;

	uart_gets( line, ESP8266_BUFFER_LEN, TRUE );

	if( 0 == strncmp( "+IPD,", line, 5 ) ) {

		strncpy( recieves[responses_end++], line, ESP8266_BUFFER_LEN );

		if( ESP8266_RESPONSES_MAX - 1 <= responses_end ) {
			/* Circle around. */
			responses_end = 0;
		}

		if( responses_end + 1 == responses_start ) {
			/* Overwrite old data. */
			responses_start++;
		}
	}

cleanup:

	return;
}

void esp8266_handle_response_step( void ) {
	char connection_raw[ESP8266_NUMBER_MAX_DIGITS];
	char line_length_raw[ESP8266_NUMBER_MAX_DIGITS];
	char* line_iter;
	char* char_iter;
	int connection;
	int line_length;
	uint8_t i;

	if( responses_start == responses_end ) {
		return;
	}

	line_iter = recieves[responses_start++];
	if( ESP8266_RESPONSES_MAX - 1 <= responses_start ) {
		/* Wrap around. */
		responses_start = 0;
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
	connection = atoi( connection_raw );

	/* Get the line length. */
	i = 0;
	while( ':' != *char_iter && ESP8266_NUMBER_MAX_DIGITS - 1 > i ) {
		line_length_raw[i] = *char_iter;
		i++;
		char_iter++;
	}
	i++; /* Skip the : */
	line_length_raw[i] = '\0';
	line_length = atoi( line_length_raw ) - 2;

	/* Don't try to handle empty requests. */
	if( 0 >= line_length ) {
		goto cleanup;
	}

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
	__delay_cycles( ESP8266_RESPONSE_CYCLES );
	uart_puts( "\r\n" );
	uart_puts( "AT+RST\r\n" );
	do {
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

uint8_t esp8266_send( const char* connection, const char* string, const char* length ) {
	//char length_str[ESP8266_NUMBER_MAX_DIGITS];
	//char conn_str[ESP8266_NUMBER_MAX_DIGITS];
	int i;
	uint8_t retval = 0;
	//char line[ESP8266_BUFFER_LEN];

	//memset( length_str, '\0', ESP8266_NUMBER_MAX_DIGITS );
	//memset( length_str, '\0', ESP8266_NUMBER_MAX_DIGITS );

	//itoa( length, length_str, 10 );
	//itoa( connection, conn_str, 10 );
	
	/* Start sending. */
	uart_puts( "AT+CIPSEND=" );
	uart_puts( connection );
	uart_putc( ',' );
	uart_puts( length );
	uart_puts( "\r\n" );

	/* Wait for it to be clear to send. */
#if 0
	do {
		uart_gets( line, ESP8266_BUFFER_LEN, TRUE );
		if( 0 == strncmp( str_error, line, 5 ) ) {
			retval = 1;
			goto cleanup;
		}
	} while( 0 != strncmp( str_ok, line, 2 ) );
#endif

	__delay_cycles( ESP8266_RESPONSE_CYCLES );

	uart_puts( string );

cleanup:

	return;
}

