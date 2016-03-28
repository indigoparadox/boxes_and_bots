
#include "esp8266.h"

typedef enum {
	ESP8266_STATUS_WAITING,
	ESP8266_STATUS_READY,
	ESP8266_STATUS_OK,
	ESP8266_STATUS_ERROR
} esp8266_status;

static esp8266_status status;
static uint8_t esp8266_wifi_up = 0;

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

