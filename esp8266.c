
#include "esp8266.h"

#define ESP8266_NUMBER_MAX_DIGITS 4

typedef enum {
	ESP8266_STATUS_WAITING,
	ESP8266_STATUS_READY,
	ESP8266_STATUS_OK,
	ESP8266_STATUS_ERROR
} esp8266_status;

static esp8266_status status;
static uint8_t esp8266_wifi_up = 0;
static void 
	(*server_handler)( int connection_index, char* string, int length ) = NULL;
int server_handler_index = 0;

void esp8266_rx_handler_generic( unsigned char c ) {
	char line[ESP8266_BUFFER_LEN];

	uart_gets( line, ESP8266_BUFFER_LEN );
	if( 0 == strncmp( "ERROR", line, 5 ) ) {
		status = ESP8266_STATUS_ERROR;
	} else if( 0 == strncmp( "ready", line, 5 ) ) {
		status = ESP8266_STATUS_READY;
	} else if( 0 == strncmp( "OK", line, 2 ) ) {
		status = ESP8266_STATUS_OK;
	} else if( 0 == strncmp( "WIFI GOT IP", line, 11 ) ) {
		esp8266_wifi_up = 1;
	} else if( 0 == strncmp( "WIFI DISCO", line, 10 ) ) {
		esp8266_wifi_up = 0;
	}
}

void esp8266_rx_handler_server( unsigned char c ) {
	char line[ESP8266_BUFFER_LEN];
	char index_raw[ESP8266_NUMBER_MAX_DIGITS];
	char line_length_raw[ESP8266_NUMBER_MAX_DIGITS];
	uint8_t i, j;
	uint8_t connection_index;

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

		/* Launch the handler, if there is one. */
		if( NULL != server_handler ) {
			server_handler(
				connection_index,
				&line[5 + i + j + 1],
				atoi( line_length_raw ) - 2
			);
		}
	}

cleanup:

	return;
}

void esp8266_init( void ) {
	char line[ESP8266_BUFFER_LEN];
	int i;

	memset( line, '\0', ESP8266_BUFFER_LEN );

	/* Try to get a prompt. */
	__delay_cycles( ESP8266_RESPONSE_CYCLES );
	status = ESP8266_STATUS_WAITING;
	uart_puts( "\r\n" );
	i = uart_add_rx_handler( esp8266_rx_handler_generic );
	uart_puts( "AT+RST\r\n" );
	do {
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
	} while( !esp8266_wifi_up );
	uart_del_rx_handler( i );
}

int esp8266_command( const char* command ) {
	int retval = 0;
	int i;

	/* Send the command and wait for a response. */
	status = ESP8266_STATUS_WAITING;
	i = uart_add_rx_handler( esp8266_rx_handler_generic );
	uart_clear();
	uart_puts( command );
	uart_puts( "\r\n" );
	do {
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		if( ESP8266_STATUS_ERROR == status ) {
			retval = 1;
			break;
		} else if( ESP8266_STATUS_OK == status ) {
			break;
		}
	} while( ESP8266_STATUS_WAITING == status );
	uart_del_rx_handler( i );

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

void esp8266_send( int connection, char* string, int length ) {
	char length_str[ESP8266_NUMBER_MAX_DIGITS];
	char conn_str[ESP8266_NUMBER_MAX_DIGITS];
	int i;

	uart_itoa( length, length_str, 10 );
	uart_itoa( connection, conn_str, 10 );

	/* Prepare to send. */
#if 0
	status = ESP8266_STATUS_WAITING;
	i = uart_add_rx_handler( esp8266_rx_handler_generic );
#endif

	/* Start sending. */
	uart_puts( "AT+CIPSEND=" );
	uart_puts( conn_str );
	uart_putc( ',' );
	uart_puts( length_str );
	__delay_cycles( ESP8266_RESPONSE_CYCLES * 4 );

	/* TODO: Implement a queue so we don't send from inside interrupts. */
#if 0
	/* Wait for it to be clear to send. */
	do {
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		if( ESP8266_STATUS_ERROR == status ) {
			goto cleanup;
		} else if( ESP8266_STATUS_OK == status ) {
			break;
		}
	} while( ESP8266_STATUS_WAITING == status );
	P1OUT |= BIT1;
	uart_del_rx_handler( i );
#endif

	uart_puts( string );

cleanup:

	return;
}

