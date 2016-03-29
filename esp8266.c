
#include "esp8266.h"

#define ESP8266_NUMBER_MAX_DIGITS 4

static void 
	(*server_handler)( int connection_index, char* string, int length ) = NULL;
int server_handler_index = 0;
struct esp8266_response responses[ESP8266_RESPONSES_MAX];
int responses_start = 0;
int responses_end = 0;

static const char* str_error = "ERROR";
static const char* str_ok = "OK";

void esp8266_rx_handler_server( unsigned char c ) {
	char line[ESP8266_BUFFER_LEN];
	char index_raw[ESP8266_NUMBER_MAX_DIGITS];
	char line_length_raw[ESP8266_NUMBER_MAX_DIGITS];
	uint8_t i, j;
	uint8_t connection_index;
	struct esp8266_response* response_iter;

	uart_gets( line, ESP8266_BUFFER_LEN );
	if( 0 == strncmp( "+IPD,", line, 5 ) ) {
		/* Get the connection index. */
		for( i = 0 ; ESP8266_NUMBER_MAX_DIGITS > i ; i++ ) {
			if( ',' == line[5 + i] ) {
				index_raw[i] = '\0';
				break;
			}
			index_raw[i] = line[5 + i];
		}
		connection_index = atoi( index_raw );

		/* Get the line length. */
		i++; /* Skip the , */
		for( j = 0 ; ':' != line[5 + i + j] ; j++ ) {
			line_length_raw[j] = line[5 + i + j];
		}
		line_length_raw[j] = '\0';

		/* Don't try to handle empty requests. */
		if( 0 >= (atoi( line_length_raw ) - 2) ) {
			goto cleanup;
		}

		/* TODO: Don't try to handle overflowing requests. */
		
		response_iter = &responses[responses_end++];

		memset( response_iter, '\0', sizeof( struct esp8266_response ) );
		response_iter->connection = connection_index;
		response_iter->length = atoi( line_length_raw ) - 2;
		strncpy(
			response_iter->text, &line[5 + i + j + 1], response_iter->length
		);

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

void esp8266_handle_responses( void ) {
	struct esp8266_response* response_iter;

	if( responses_start == responses_end ) {
		return;
	}

	response_iter = &responses[responses_start++];
	if( ESP8266_RESPONSES_MAX - 1 <= responses_start ) {
		/* Wrap around. */
		responses_start = 0;
	}

	/* Launch the handler, if there is one. */
	if( NULL != server_handler ) {
		server_handler(
			response_iter->connection,
			response_iter->text,
			response_iter->length
		);
	}
}

void esp8266_init( void ) {
	char line[ESP8266_BUFFER_LEN];

	memset( line, '\0', ESP8266_BUFFER_LEN );

	/* Try to get a prompt. */
	__delay_cycles( ESP8266_RESPONSE_CYCLES );
	uart_puts( "\r\n" );
	uart_puts( "AT+RST\r\n" );
	do {
		uart_gets( line, ESP8266_BUFFER_LEN );
	} while( 0 != strncmp( "WIFI GOT IP", line, 11 ) );
}

uint8_t esp8266_command( const char* command ) {
	char line[ESP8266_BUFFER_LEN];
	uint8_t retval = 0;

	memset( line, '\0', ESP8266_BUFFER_LEN );

	/* Send the command and wait for a response. */
	uart_clear();
	uart_puts( command );
	uart_puts( "\r\n" );
	do {
		uart_gets( line, ESP8266_BUFFER_LEN );
		if( 0 == strncmp( str_error, line, 5 ) ) {
			retval = 1;
			break;
		}
	} while( 0 != strncmp( str_ok, line, 2 ) );

	return retval;
}

void esp8266_start_server( void (*handler)( int, char*, int ) ) {
	server_handler = handler;
	server_handler_index = uart_add_rx_handler( esp8266_rx_handler_server );
}

void esp8266_stop_server( void ) {
	uart_del_rx_handler( server_handler_index );
	server_handler = NULL;
}

uint8_t esp8266_send( int connection, char* string, int length ) {
	char length_str[ESP8266_NUMBER_MAX_DIGITS];
	char conn_str[ESP8266_NUMBER_MAX_DIGITS];
	int i;
	uint8_t retval = 0;
	char line[ESP8266_BUFFER_LEN];

	uart_itoa( length, length_str, 10 );
	uart_itoa( connection, conn_str, 10 );

	/* Start sending. */
	uart_puts( "AT+CIPSEND=" );
	uart_puts( conn_str );
	uart_putc( ',' );
	uart_puts( length_str );

	/* Wait for it to be clear to send. */
	do {
		uart_gets( line, ESP8266_BUFFER_LEN );
		if( 0 == strncmp( str_error, line, 5 ) ) {
			retval = 1;
			goto cleanup;
		}
	} while( 0 != strncmp( str_ok, line, 2 ) );

	__delay_cycles( ESP8266_RESPONSE_CYCLES );

	uart_puts( string );

cleanup:

	return;
}

