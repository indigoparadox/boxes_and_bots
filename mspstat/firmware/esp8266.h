
#ifndef ESP8266_H
#define ESP8266_H

#include <string.h>
#include <stdlib.h>
#include <stdint.h>

#include "uart.h"

#define ESP8266_RESPONSE_CYCLES 80000
#define ESP8266_BUFFER_LEN 20
#define ESP8266_RESPONSES_MAX 3

uint8_t esp8266_init( const char* server_port );
void esp8266_handle_response_step( void );
uint8_t esp8266_command( const char* command, const char* args );
void esp8266_start_server( void (*handler)( const char*, const char*, const char* ) );
void esp8266_stop_server( void );
void esp8266_send( const char* connection, const char* string, const char* length, BOOL newline );
BOOL esp8266_server_waiting( void );

#endif /* ESP8266_H */

