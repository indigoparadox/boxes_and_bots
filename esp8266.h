
#ifndef ESP8266_H
#define ESP8266_H

#include <string.h>
#include <stdlib.h>

#include "uart.h"

#define ESP8266_RESPONSE_CYCLES 80000
#define ESP8266_BUFFER_LEN 50

void esp8266_init( void );
int esp8266_command( const char* command );
void esp8266_start_server( void (*handler)( int, char*, int ) );
void esp8266_stop_server( void );
void esp8266_send( int connection, char* string, int length );

#endif /* ESP8266_H */

