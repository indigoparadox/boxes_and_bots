
#ifndef ESP8266_H
#define ESP8266_H

#include <string.h>
#include <stdlib.h>
#include <stdint.h>

#include "uart.h"

#define ESP8266_RESPONSE_CYCLES 80000
#define ESP8266_BUFFER_LEN 20
#define ESP8266_RESPONSES_MAX 3

struct esp8266_response {
	int connection;
	int length;
	char text[ESP8266_BUFFER_LEN];
};

uint8_t esp8266_init( const char* server_port );
void esp8266_handle_responses( void );
uint8_t esp8266_command( const char* command, const char* args );
void esp8266_start_server( void (*handler)( int, char*, int ) );
void esp8266_stop_server( void );
uint8_t esp8266_send( int connection, char* string, int length );

#endif /* ESP8266_H */

