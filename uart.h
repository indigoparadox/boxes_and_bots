
#ifndef UART_H
#define UART_H

#include <msp430g2553.h>
#include <string.h>
#include <stdint.h>

#ifndef BOOL
typedef uint8_t BOOL;
#endif

#ifndef TRUE
#define TRUE 1
#endif

#ifndef FALSE
#define FALSE 0
#endif

#define RXD BIT1
#define TXD BIT2

void uart_init( void );
void uart_clear( void );
unsigned char uart_getc( uint8_t block );
void uart_gets( char* buffer, int length, uint8_t block );
void uart_putc( const unsigned char c );
void uart_puts( const char *str );
void uart_nputs( const char *str, int length );
int8_t uart_add_rx_handler( void (*handler)( unsigned char c ) );
void uart_del_rx_handler( int8_t index );
void uart_itoa( long unsigned int value, char* result, int base );

#endif /* UART_H */

