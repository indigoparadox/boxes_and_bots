
#ifndef UART_H
#define UART_H

#include <msp430g2553.h>
#include <string.h>
#include <stdint.h>

#define RXD BIT1
#define TXD BIT2

void uart_init( void );
void uart_clear( void );
unsigned char uart_getc( void );
void uart_gets( char* buffer, int length );
void uart_putc( const unsigned char c );
void uart_puts( const char *str );
int8_t uart_add_rx_handler( void (*handler)( unsigned char c ) );
void uart_del_rx_handler( int8_t index );

#endif /* UART_H */

