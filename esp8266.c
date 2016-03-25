
#include "esp8266.h"

void esp8266_init( void ) {
	char line[ESP8266_BUFFER_LEN];
	int i;

	memset( line, '\0', ESP8266_BUFFER_LEN );

	/* Try to get a prompt. */
	__delay_cycles( ESP8266_RESPONSE_CYCLES );
	do {
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		uart_puts( "\r\n" );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		uart_gets( line, ESP8266_BUFFER_LEN );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
	} while( 0 != strncmp( "ERROR", line, 5 ) );

	/* Reset to clear status. */
	uart_puts( "AT+RST\r\n" );
	do {
		uart_gets( line, ESP8266_BUFFER_LEN );
	} while( 0 != strncmp( "ready", line, 5 ) );

	/* Wait for reset status to finish. */
	do {
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		uart_puts( "\r\n" );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		uart_gets( line, ESP8266_BUFFER_LEN );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
		__delay_cycles( ESP8266_RESPONSE_CYCLES );
	} while( 0 != strncmp( "ERROR", line, 5 ) );
}

int esp8266_command( const char* command ) {
	int retval = 0;
	char line[ESP8266_BUFFER_LEN];

	memset( line, '\0', ESP8266_BUFFER_LEN );

	/* Send the command and wait for a response. */
	uart_puts( command );
	uart_puts( "\r\n" );
	__delay_cycles( ESP8266_RESPONSE_CYCLES );
	do {
		uart_gets( line, ESP8266_BUFFER_LEN );
		if( 0 == strncmp( "ERROR", line, 5 ) ) {
			retval = 1;
			break;
		}
	} while( 0 != strncmp( "OK", line, 2 ) );

	return retval;
}

